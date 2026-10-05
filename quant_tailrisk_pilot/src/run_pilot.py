#!/usr/bin/env python3
"""Reproducible synthetic mechanism pilot. No market data or trading backtest.

The candidate is finite-bank portfolio-tail moment calibration, a statistical-ML
prototype related to entropy pooling, NOT a claimed new theorem/algorithm.
Only exact mixture parameters are passed to the final population-risk evaluator.
"""
from __future__ import annotations
import os
for v in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[v] = '1'
import argparse, hashlib, json, platform, time, warnings
from pathlib import Path
import numpy as np
import pandas as pd
import scipy
from scipy.optimize import minimize
from scipy.special import logsumexp, ndtr
from scipy.stats import norm
from sklearn.mixture import GaussianMixture
from sklearn.covariance import LedoitWolf
from sklearn.exceptions import ConvergenceWarning

ROOT=Path(__file__).resolve().parents[1]
DEFAULT={
 'study':'finite-bank portfolio-tail calibration mechanism pilot',
 'seeds':list(range(100,130)), 'dimension':8,
 'n_base':256, 'n_calibration':256, 'n_scenarios':2048,
 'n_random_portfolios':256, 'weight_cap':0.5, 'confidence':0.95,
 'critic_rounds':12, 'target_calibration_fraction':0.5,
 'kl_dual_ridge':1.0, 'moment_scale_floor':0.025,
 'distribution_families':['gaussian_control','asymmetric_crash_mixture'],
 'gmm_components':3, 'gmm_n_init':2,
 'methods':['equal_weight','historical_CVaR','LedoitWolf_Gaussian','GMM_base',
            'GMM_pooled','nominal_half_equal','random_tail_calibration','adaptive_tail_calibration'],
 'risk_unit':'percentage points of one-period portfolio loss',
 'selection_rule':'minimum predicted CVaR on the SAME fixed candidate bank',
 'fixed_portfolio_audit':'equal weight (not used to tune the method)',
 'parameters_tuned_on_reported_outcomes':False,
 'statement':'Exploratory design frozen before inspecting the main results. Not an external preregistration.',
}


def create_population(seed:int,d:int,family:str):
    rng=np.random.default_rng(seed+12345)
    sig=rng.uniform(0.65,1.35,d)
    # Heterogeneous but exchangeable asset ordering. No special portfolio chosen by method.
    perm=rng.permutation(d)
    corr=0.25*np.ones((d,d))+0.75*np.eye(d)
    cov0=np.outer(sig,sig)*corr
    if family=='gaussian_control':
        return np.array([1.]),np.zeros((1,d)),cov0[None,:,:]
    a=np.full(d,-0.45); a[perm[:d//2]]=-3.5
    b=np.full(d,-0.35); b[perm[d//2:]]=-4.5
    weights=np.array([.92,.05,.03])
    means=np.stack([np.zeros(d),a,b]); means-=weights@means
    corr_crash=.65*np.ones((d,d))+.35*np.eye(d)
    cov1=np.outer(1.65*sig,1.65*sig)*corr_crash
    cov2=np.outer(1.9*sig,1.9*sig)*corr_crash
    return weights,means,np.stack([cov0,cov1,cov2])


def draw_population(n,rng,params):
    p,mu,cov=params
    z=rng.choice(len(p),size=n,p=p)
    x=np.empty((n,mu.shape[1]))
    for k in range(len(p)):
        ix=np.flatnonzero(z==k)
        x[ix]=rng.multivariate_normal(mu[k],cov[k],size=len(ix))
    return x


def portfolio_bank(seed,d,n,cap):
    rng=np.random.default_rng(seed+45678)
    rows=[np.full(d,1/d)]
    # Pair portfolios touch the boundary of the 50%-cap simplex.
    for a in range(d):
        for b in range(a+1,d):
            w=np.zeros(d);w[a]=w[b]=.5;rows.append(w)
    got=[]
    while len(got)<n:
        batch=rng.dirichlet(np.full(d,1.0),size=n)
        got.extend(batch[batch.max(axis=1)<=cap].tolist())
    rows.extend(got[:n])
    w=np.array(rows)
    assert np.allclose(w.sum(1),1) and w.min()>=0 and w.max()<=cap+1e-12
    return w


class RiskBank:
    def __init__(self, scenarios:np.ndarray, portfolios:np.ndarray):
        self.loss=-scenarios@portfolios.T
        self.order=np.argsort(self.loss,axis=0)
        self.sorted=np.take_along_axis(self.loss,self.order,axis=0)
    def evaluate(self,p:np.ndarray,q:float):
        ps=p[self.order]
        cumulative=np.cumsum(ps,axis=0)
        ids=np.argmax(cumulative>=q-1e-14,axis=0)
        cols=np.arange(self.loss.shape[1])
        var=self.sorted[ids,cols]
        # Fractional tail mass at the quantile atom: valid for nonuniform finite bank.
        es=var+(p[:,None]*np.maximum(self.loss-var[None,:],0)).sum(0)/(1-q)
        return var,es


def population_var_es(portfolios,params,q):
    p,mu,covs=params
    m=-(portfolios@mu.T)
    sd=np.sqrt(np.maximum(np.einsum('id,kde,ie->ik',portfolios,covs,portfolios),1e-14))
    lo=(m-15*sd).min(1); hi=(m+15*sd).max(1)
    for _ in range(70):
        mid=(lo+hi)/2
        cdf=(ndtr((mid[:,None]-m)/sd)*p).sum(1)
        lo=np.where(cdf<q,mid,lo); hi=np.where(cdf>=q,mid,hi)
    var=(lo+hi)/2
    z=(var[:,None]-m)/sd
    phi=np.exp(-z*z/2)/np.sqrt(2*np.pi)
    es=((m*ndtr(-z)+sd*phi)*p).sum(1)/(1-q)
    return var,es


def gaussian_risk(x,w,q):
    fit=LedoitWolf().fit(x)
    means=-(w@fit.location_)
    sd=np.sqrt(np.maximum(np.einsum('id,de,ie->i',w,fit.covariance_,w),1e-14))
    z=norm.ppf(q)
    return means+z*sd,means+norm.pdf(z)/(1-q)*sd


def fit_gmm(x,seed,cfg):
    # Full covariance handles dependence; finite covariance regularization is explicit.
    model=GaussianMixture(n_components=cfg['gmm_components'],covariance_type='full',
                          random_state=seed,n_init=cfg['gmm_n_init'],
                          max_iter=150,reg_covar=.01)
    with warnings.catch_warnings(record=True) as ws:
        warnings.simplefilter('always',ConvergenceWarning)
        model.fit(x)
    samples,_=model.sample(cfg['n_scenarios'])
    status={'converged':bool(model.converged_),'iterations':int(model.n_iter_),
            'warnings':[str(v.message) for v in ws]}
    return samples,status


def solve_entropy_moments(a:np.ndarray,b:np.ndarray,ridge:float):
    # Primal: KL(p || uniform) + 1/(2*ridge) ||a.T p-b||^2.
    # Dual minimization below preserves nonnegative scenario probabilities summing to 1.
    n=a.shape[0]
    def fg(z):
        logits=-a@z; lse=logsumexp(logits)
        p=np.exp(logits-lse)
        return float(lse-np.log(n)+b@z+.5*ridge*(z@z)), b-a.T@p+ridge*z
    result=minimize(fg,np.zeros(a.shape[1]),jac=True,method='L-BFGS-B',
                    options={'maxiter':200,'ftol':1e-11,'gtol':1e-7})
    logits=-a@result.x;p=np.exp(logits-logsumexp(logits))
    if not np.isfinite(p).all() or abs(p.sum()-1)>1e-10:
        raise RuntimeError('Invalid scenario weights')
    return p,{'success':bool(result.success),'nit':int(result.nit),'message':str(result.message)}


def calibrate(bank:RiskBank,cal:np.ndarray,w:np.ndarray,cfg,seed:int,adaptive:bool):
    n=bank.loss.shape[0]; q=cfg['confidence']; p0=np.full(n,1/n)
    var0,es0=bank.evaluate(p0,q)
    cal_loss=-cal@w.T
    # Freeze hinges at base VaRs. This finite critic is NOT a uniform continuum certificate.
    a=np.maximum(bank.loss-var0,0)
    hcal=np.maximum(cal_loss-var0,0)
    b0=a.mean(0)
    b=(1-cfg['target_calibration_fraction'])*b0+cfg['target_calibration_fraction']*hcal.mean(0)
    scale=np.maximum(hcal.std(0,ddof=1)/np.sqrt(len(cal)),cfg['moment_scale_floor'])
    A=a/scale; B=b/scale
    selected=[]; status=[]; p=p0.copy()
    rng=np.random.default_rng(seed+54321)
    random_order=rng.permutation(len(w))
    for it in range(cfg['critic_rounds']):
        if adaptive:
            _,es=bank.evaluate(p,q)
            opt=int(np.argmin(es))
            if it%3==0 and opt not in selected:
                ix=opt
            else:
                score=np.abs(B-A.T@p)
                if selected: score[selected]=-np.inf
                ix=int(np.argmax(score))
        else:
            ix=int(random_order[it])
        selected.append(ix)
        p,st=solve_entropy_moments(A[:,selected],B[selected],cfg['kl_dual_ridge'])
        status.append(st)
    final_var,final_es=bank.evaluate(p,q)
    effective_n=1/np.sum(p*p)
    return final_var,final_es,{'critic_indices':selected,'ess':float(effective_n),
                             'min_probability':float(p.min()),'max_probability':float(p.max()),
                             'dual_runs':status}


def run_seed(seed:int,family:str,cfg):
    t=time.perf_counter();d=cfg['dimension'];q=cfg['confidence']
    rng=np.random.default_rng(seed)
    # Params are accessible ONLY to simulator and final evaluator, not fitting functions.
    params=create_population(seed,d,family)
    base=draw_population(cfg['n_base'],rng,params)
    cal=draw_population(cfg['n_calibration'],rng,params)
    pooled=np.concatenate([base,cal])
    W=portfolio_bank(seed,d,cfg['n_random_portfolios'],cfg['weight_cap'])
    fit_time={}; risks={}; metadata={}
    s=time.perf_counter()
    saa=RiskBank(pooled,W);risks['historical_CVaR']=saa.evaluate(np.full(len(pooled),1/len(pooled)),q)
    risks['equal_weight']=risks['historical_CVaR']
    fit_time['historical_CVaR']=time.perf_counter()-s;fit_time['equal_weight']=0.
    s=time.perf_counter();risks['LedoitWolf_Gaussian']=gaussian_risk(pooled,W,q)
    fit_time['LedoitWolf_Gaussian']=time.perf_counter()-s
    s=time.perf_counter();z,metadata['gmm_base']=fit_gmm(base,seed,cfg)
    bank=RiskBank(z,W);risks['GMM_base']=bank.evaluate(np.full(len(z),1/len(z)),q)
    fit_time['GMM_base']=time.perf_counter()-s
    s=time.perf_counter();zp,metadata['gmm_pooled']=fit_gmm(pooled,seed,cfg)
    bp=RiskBank(zp,W);risks['GMM_pooled']=bp.evaluate(np.full(len(zp),1/len(zp)),q)
    fit_time['GMM_pooled']=time.perf_counter()-s
    for name,ad in [('random_tail_calibration',False),('adaptive_tail_calibration',True)]:
        s=time.perf_counter();v,e,m=calibrate(bank,cal,W,cfg,seed,ad)
        risks[name]=(v,e);metadata[name]=m;fit_time[name]=time.perf_counter()-s
    # Only now use population formula, after all policies are fixed.
    truev,truee=population_var_es(W,params,q)
    optimal=float(truee.min())
    rows=[]
    for method,(v,e) in risks.items():
        ix=0 if method=='equal_weight' else int(np.argmin(e))
        chosen=W[ix]
        m={'seed':seed,'family':family,'method':method,'portfolio_index':ix,
           'predicted_ES':float(e[ix]),'true_ES':float(truee[ix]),
           'signed_underestimate':float(truee[ix]-e[ix]),
           'relative_underestimate_pct':float(100*(truee[ix]-e[ix])/truee[ix]),
           'absolute_risk_error':float(abs(truee[ix]-e[ix])),
           'regret_vs_candidate_oracle':float(truee[ix]-optimal),
           'fixed_equal_signed_error':float(truee[0]-e[0]),
           'selection_excess_error':float((truee[ix]-e[ix])-(truee[0]-e[0])),
           'hhi':float(chosen@chosen),'max_weight':float(chosen.max()),
           'fit_and_scoring_seconds':fit_time[method],
           **{f'w_{j}':float(chosen[j]) for j in range(d)}}
        rows.append(m)
    # Very strong simple shrinkage control. Not in common finite W; explicitly documented.
    opt=int(np.argmin(risks['GMM_base'][1]));ws=.5*W[opt]+.5*W[0]
    vs,es=RiskBank(z,ws[None,:]).evaluate(np.full(len(z),1/len(z)),q)
    _,ets=population_var_es(ws[None,:],params,q)
    rows.append({'seed':seed,'family':family,'method':'nominal_half_equal','portfolio_index':-1,
                 'predicted_ES':float(es[0]),'true_ES':float(ets[0]),
                 'signed_underestimate':float(ets[0]-es[0]),
                 'relative_underestimate_pct':float(100*(ets[0]-es[0])/ets[0]),
                 'absolute_risk_error':float(abs(ets[0]-es[0])),
                 'regret_vs_candidate_oracle':float(ets[0]-optimal),
                 'fixed_equal_signed_error':float(truee[0]-risks['GMM_base'][1][0]),
                 'selection_excess_error':float((ets[0]-es[0])-(truee[0]-risks['GMM_base'][1][0])),
                 'hhi':float(ws@ws),'max_weight':float(ws.max()),'fit_and_scoring_seconds':0.,
                 **{f'w_{j}':float(ws[j]) for j in range(d)}})
    # Save the full risk surface for sanity/recomputation, not only winning portfolios.
    surface={'weights':W,'population_ES':truee,'population_VaR':truev}
    for k,(v,e) in risks.items(): surface[k+'_ES']=e;surface[k+'_VaR']=v
    np.savez_compressed(ROOT/'results'/f'{family}_{seed}_surfaces.npz',**surface)
    metadata['wall_seconds']=time.perf_counter()-t
    metadata['population_evaluator']='exact Gaussian-mixture formula, numerical VaR root'
    metadata['data_sha256']=hashlib.sha256(pooled.tobytes()).hexdigest()
    return rows,metadata


def sanity_tests():
    rng=np.random.default_rng(3)
    W=np.array([[1.,0.],[.5,.5],[0.,1.]])
    x=rng.normal(size=(10000,2))
    rb=RiskBank(x,W);v,e=rb.evaluate(np.full(len(x),1/len(x)),.95)
    assert np.all(e>=v)
    loss=np.array([0.,1.,2.,3.]); p=np.array([.1,.2,.3,.4])
    r=RiskBank((-loss)[:,None],np.ones((1,1)))
    _,er=r.evaluate(p,.7)
    assert abs(er[0]-3)<1e-10
    _,er=r.evaluate(p,.5)
    assert abs(er[0]-2.8)<1e-10
    pars=(np.array([1.]),np.zeros((1,2)),np.eye(2)[None])
    _,ea=population_var_es(W,pars,.95)
    assert abs(ea[0]-norm.pdf(norm.ppf(.95))/.05)<1e-10
    assert np.max(abs(e-ea))<.12
    a=rng.normal(size=(100,3));b=a.mean(0)
    pe,st=solve_entropy_moments(a,b,1.)
    assert np.max(abs(pe-.01))<1e-9
    w=portfolio_bank(5,8,256,.5)
    assert np.allclose(w.sum(1),1) and w.max()<=.5+1e-12
    # CVaR is bounded below by any finite-bank mean and above by the worst loss.
    assert np.all(e>=np.mean(rb.loss,axis=0)) and np.all(e<=np.max(rb.loss,axis=0))
    return {'assertion_groups':8,'passed':True}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--sanity-only',action='store_true')
    ap.add_argument('--start',type=int);ap.add_argument('--stop',type=int)
    args=ap.parse_args();ROOT.joinpath('results').mkdir(exist_ok=True)
    test=sanity_tests();print('SANITY',test,flush=True)
    if args.sanity_only:return
    config_path=ROOT/'config.json'
    if not config_path.exists():
        config_path.write_text(json.dumps(DEFAULT,indent=2))
    cfg=json.loads(config_path.read_text())
    seeds=cfg['seeds']
    if args.start is not None:seeds=[s for s in seeds if s>=args.start]
    if args.stop is not None:seeds=[s for s in seeds if s<args.stop]
    stamp={'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,
           'config_sha256':hashlib.sha256(config_path.read_bytes()).hexdigest(),
           'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           'sanity':test,'execution_device':'CPU in ChatGPT container, not user Mac'}
    (ROOT/'results'/'run_manifest.json').write_text(json.dumps(stamp,indent=2))
    all_rows=[];metas={};start=time.perf_counter()
    for family in cfg['distribution_families']:
        for seed in seeds:
            rows,meta=run_seed(seed,family,cfg)
            all_rows+=rows;metas[family+'_'+str(seed)]=meta
            pd.DataFrame(all_rows).to_csv(ROOT/'results'/f'raw_{seeds[0]}_{seeds[-1]}.csv',index=False)
            (ROOT/'results'/f'diagnostics_{seeds[0]}_{seeds[-1]}.json').write_text(json.dumps(metas,indent=2))
            print(f'{family} seed={seed} done time={meta["wall_seconds"]:.2f}s',flush=True)
    print('TOTAL_SECONDS',time.perf_counter()-start,flush=True)
if __name__=='__main__':main()
