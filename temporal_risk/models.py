"""All estimators receive past observations only, never simulation parameters."""
import hashlib
import numpy as np
from scipy.optimize import brentq
from scipy.special import expit

from continuous_cvar.model import Fit,smooth_terms,validate_data
from continuous_cvar_face.model import fit_smooth,face_geometry
from continuous_cvar.evaluation import population_smooth


def hac_covariance(scores,lag):
    u=np.asarray(scores)-np.mean(scores,axis=0);n=len(u)
    if not 0<=lag<n:raise ValueError('HAC lag outside sample')
    value=u.T@u/n
    for k in range(1,lag+1):
        cross=u[k:].T@u[:-k]/n;value+=(1-k/(lag+1))*(cross+cross.T)
    return (value+value.T)/2


def block_indices(n,b,rng):
    if not 1<=b<=n:raise ValueError('Invalid block length')
    starts=rng.integers(n,size=int(np.ceil(n/b)))
    return ((starts[:,None]+np.arange(b))%n).ravel()[:n]


def fixed_weight_fit(x,tau,fit_cfg):
    w=np.full(x.shape[1],1/x.shape[1]);lo,hi=fit_cfg['threshold_bounds']
    root=lambda v:1-expit((-x@w-v)/tau).mean()/fit_cfg['alpha']
    v=brentq(root,lo,hi,xtol=1e-13);theta=np.r_[w,v]
    value,g,h,scores,_=smooth_terms(x,theta,tau,fit_cfg['alpha'])
    good=bool(abs(g[-1])<fit_cfg['stationarity_tol'] and h[-1,-1]>=fit_cfg['min_eigenvalue'])
    correction=float(np.mean(scores[:,-1]**2)/h[-1,-1]/len(x)) if good else None
    return Fit(theta,value,correction,{'numerical_gate':good,'optimizer_success':True,'threshold_stationarity':float(g[-1]),
                                     'threshold_curvature':float(h[-1,-1]),'convex_gap_bound':abs(float(g[-1]))*(hi-lo)})


def corrections(x,fit,tau,cfg,fixed,lag):
    _,g,h,scores,_=smooth_terms(x,fit.theta,tau,cfg['alpha'])
    if fixed:
        n=np.eye(len(fit.theta))[:,-1:];reduced=h[-1:,-1:];valid=fit.diagnostics['numerical_gate']
    else:
        diag,n,reduced=face_geometry(fit.theta,g,h,cfg);valid=diag['numerical_gate']
    if not valid:return None,{'valid':False,'lag':lag}
    s=hac_covariance(scores@n,lag);eig=float(np.linalg.eigvalsh(s).min())
    correction=float(np.trace(np.linalg.solve(reduced,s))/len(x))
    good=bool(eig>=-1e-10 and correction>=-1e-12 and np.isfinite(correction))
    return (correction if good else None),{'valid':good,'lag':lag,'score_lrv_min_eigenvalue':eig,'correction':correction}


def statistical_models(past,mc):
    x=validate_data(past);mean=x.mean(axis=0);centered=x-mean
    iid={'p':np.ones(1),'mu':mean[None,:],'cov':np.cov(x,rowvar=False)[None,:,:]}
    weights=mc['ewma_lambda']**np.arange(len(x)-1,-1,-1);weights/=weights.sum()
    ewma={'p':np.ones(1),'mu':mean[None,:],'cov':(centered.T@(weights[:,None]*centered))[None,:,:]}
    before,after=x[:-1],x[1:];xb=before.mean(axis=0);yb=after.mean(axis=0)
    phi_raw=np.sum((before-xb)*(after-yb),axis=0)/np.sum((before-xb)**2,axis=0)
    phi=np.clip(phi_raw,-mc['ar_clip'],mc['ar_clip']);intercept=yb-phi*xb
    residual=after-intercept-phi*before
    ar={'p':np.ones(1),'mu':(intercept+phi*x[-1])[None,:],'cov':np.cov(residual,rowvar=False)[None,:,:]}
    return {'gaussian_iid':iid,'ewma_gaussian':ewma,'ar_gaussian':ar}, {'ar_phi':phi.tolist(),'ar_clipped_count':int(np.sum(phi!=phi_raw)),
           'forecast_parameters':{k:{kk:vv.tolist() for kk,vv in v.items()} for k,v in {'gaussian_iid':iid,'ewma_gaussian':ewma,'ar_gaussian':ar}.items()}}


def bootstrap_optimism(x,tau,fit_cfg,mc,fixed,rng):
    values=[];replicates=[];all_valid=True
    for _ in range(mc['bootstrap_refits']):
        index=block_indices(len(x),mc['block_length'],rng);sample=x[index]
        fit=fixed_weight_fit(sample,tau,fit_cfg) if fixed else fit_smooth(sample,tau,fit_cfg)
        gate=bool(np.isfinite(fit.objective) and fit.diagnostics['convex_gap_bound']<=fit_cfg['gap_tol'])
        if not fixed:gate=gate and fit.diagnostics['feasibility']<=fit_cfg['feasibility_tol']
        original=smooth_terms(x,fit.theta,tau,fit_cfg['alpha'])[0]
        delta=original-fit.objective;values.append(delta);all_valid=all_valid and gate
        replicates.append({'theta':fit.theta.tolist(),'delta':delta,'valid':gate,'optimizer_success':fit.diagnostics['optimizer_success'],
                           'gap':fit.diagnostics['convex_gap_bound'],'indices_sha256':hashlib.sha256(index.tobytes()).hexdigest()})
    return (float(np.mean(values)) if all_valid else None),{'replicates':replicates,'valid':all_valid,
             'mc_standard_error':float(np.std(values,ddof=1)/np.sqrt(len(values))),'negative_replications':int(np.sum(np.array(values)<0))}


def fit_forecasts(past,fit_cfg,mc,rng_seed):
    """Return every decision/estimate locked before population evaluation."""
    x=validate_data(past);tau=mc['tau'];rng=np.random.default_rng(rng_seed)
    statistical,stat_diag=statistical_models(x,mc);outputs={}
    for policy in ['full512','equal512','older256']:
        train=x[:len(x)//2] if policy=='older256' else x;fixed=policy=='equal512'
        fit=fixed_weight_fit(train,tau,fit_cfg) if fixed else fit_smooth(train,tau,fit_cfg)
        hac,hac_diag=corrections(train,fit,tau,fit_cfg,fixed,mc['block_length']-1)
        estimates={'raw':fit.objective,'iid_oic':None if fit.correction is None else fit.objective+fit.correction,
                   'hac':None if hac is None else fit.objective+hac}
        extras={}
        if policy=='older256':
            estimates['chronological']=smooth_terms(x[len(x)//2:],fit.theta,tau,fit_cfg['alpha'])[0]
            estimates['blocked_holdout']=smooth_terms(x[len(x)//2+mc['block_length']:],fit.theta,tau,fit_cfg['alpha'])[0]
        else:
            correction,extras=bootstrap_optimism(train,tau,fit_cfg,mc,fixed,rng)
            estimates['block_bootstrap']=None if correction is None else fit.objective+correction
        for method,params in statistical.items():
            estimates[method]=population_smooth(fit.theta,params,tau,fit_cfg['alpha'])[0]
        outputs[policy]={'theta':fit.theta.tolist(),'n_fit':len(train),'estimates':estimates,'fit_diagnostics':fit.diagnostics,
                         'hac_diagnostics':hac_diag,'bootstrap_diagnostics':extras}
    return {'policies':outputs,'statistical_diagnostics':stat_diag,'resampling_seed':rng_seed}
