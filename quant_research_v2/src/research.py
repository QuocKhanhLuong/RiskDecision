#!/usr/bin/env python3
"""Auditable portfolio tail-risk research. Simulated data, NOT market backtests.
Finite common portfolio bank; validation selects candidate before test outcomes.
"""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key]='1'
import argparse, csv, hashlib, json, time, warnings
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from scipy.optimize import minimize, minimize_scalar
from scipy.special import logsumexp, ndtr, gammaln
from scipy.stats import norm, t as tdist
from sklearn.mixture import GaussianMixture
from sklearn.covariance import LedoitWolf

ROOT=Path(__file__).resolve().parents[1]
FAMILIES=['gaussian','asymmetric_crash','student_t4','markov_volatility']
CANDIDATES=['support_mix25','support_mix50','support_band25','support_band50','support_point50','filtered_support_band50']
CFG={'dim':8,'n_train':512,'n_scenarios':1536,'n_random_weights':256,'cap':.5,'q':.95,
 'gmm_components':3,'rounds':8,'rho':1.,'band':1.,'validation_seeds':list(range(2000,2020)),
 'test_seeds':list(range(4000,4080)), 'families':FAMILIES,'candidate_names':CANDIDATES,
 'selection_metric':'equal-family mean absolute error of selected portfolio ES / true ES',
 'data_status':'All experiments in this script are synthetic. No market backtest.',
 'note':'Reported underestimation/ES regret is computed by population evaluator AFTER prediction. It is never a training input.'}

def bank(seed,d=8,n=256):
    rng=np.random.default_rng(seed+45678); rows=[np.full(d,1/d)]
    for a in range(d):
        for b in range(a+1,d):
            w=np.zeros(d);w[a]=w[b]=.5;rows.append(w)
    while len(rows)<1+d*(d-1)//2+n:
        w=rng.dirichlet(np.ones(d))
        if w.max()<=.5:rows.append(w)
    return np.array(rows)

class Risk:
    def __init__(self,z,w):
        self.loss=-z@w.T;self.order=np.argsort(self.loss,axis=0)
        self.sorted=np.take_along_axis(self.loss,self.order,axis=0)
    def eval(self,p=None,q=.95):
        if p is None:p=np.full(len(self.loss),1/len(self.loss))
        cs=np.cumsum(p[self.order],axis=0)
        ix=np.argmax(cs>=q-1e-12,axis=0)
        v=self.sorted[ix,np.arange(len(ix))]
        e=v+(p[:,None]*np.maximum(self.loss-v,0)).sum(0)/(1-q)
        return v,e

def covariance(rng,d):
    s=rng.uniform(.65,1.35,d)
    return np.outer(s,s)*(.25*np.ones((d,d))+.75*np.eye(d)),s

def generate(seed,family,n=512,d=8):
    r=np.random.default_rng(seed);c,s=covariance(np.random.default_rng(seed+12345),d)
    if family=='gaussian':
        pars=(np.array([1.]),np.zeros((1,d)),c[None])
    elif family=='asymmetric_crash':
        perm=np.random.default_rng(seed+12345).permutation(d)
        a=np.full(d,-.45);a[perm[:d//2]]=-3.5
        b=np.full(d,-.35);b[perm[d//2:]]=-4.5
        p=np.array([.92,.05,.03]);mu=np.array([np.zeros(d),a,b]);mu-=p@mu
        cc=np.outer(s,s)*(.65*np.ones((d,d))+.35*np.eye(d))
        pars=(p,mu,np.array([c,1.65**2*cc,1.9**2*cc]))
    elif family=='student_t4':
        nu=4.;shape=c*(nu-2)/nu
        x=r.multivariate_normal(np.zeros(d),shape,n)/np.sqrt(r.chisquare(nu,n)/nu)[:,None]
        return x,{'kind':'t','df':nu,'mean':np.zeros(d),'shape':shape}
    elif family=='markov_volatility':
        transition=np.array([[.985,.015],[.12,.88]])
        cc=np.outer(s,s)*(.70*np.ones((d,d))+.30*np.eye(d))*6.25
        covs=np.array([c,cc]);mu=np.zeros((2,d));state=0;xs=[]
        for _ in range(n+256):
            state=int(r.choice(2,p=transition[state]));xs.append(r.multivariate_normal(mu[state],covs[state]))
        return np.array(xs[-n:]),{'kind':'mix','p':transition[state].copy(),'mu':mu,'cov':covs,'latent_state_eval_only':state}
    else:raise ValueError(family)
    p,mu,cs=pars;states=r.choice(len(p),n,p=p);x=np.zeros((n,d))
    for k in range(len(p)):
        ind=np.flatnonzero(states==k);x[ind]=r.multivariate_normal(mu[k],cs[k],len(ind))
    return x,{'kind':'mix','p':p,'mu':mu,'cov':cs}

def truth(w,pars,q=.95):
    if pars['kind']=='t':
        nu=pars['df'];sd=np.sqrt(np.einsum('ij,jk,ik->i',w,pars['shape'],w));m=-w@pars['mean'];z=tdist.ppf(q,nu)
        return m+z*sd,m+sd*(nu+z*z)/(nu-1)*tdist.pdf(z,nu)/(1-q)
    p,mu,cs=pars['p'],pars['mu'],pars['cov'];m=-w@mu.T
    sd=np.sqrt(np.einsum('ij,kjl,il->ik',w,cs,w));lo=(m-18*sd).min(1);hi=(m+18*sd).max(1)
    for _ in range(60):
        mid=(lo+hi)/2;cdf=(p*ndtr((mid[:,None]-m)/sd)).sum(1);lo=np.where(cdf<q,mid,lo);hi=np.where(cdf>=q,mid,hi)
    v=(lo+hi)/2;z=(v[:,None]-m)/sd;e=(p*(m*ndtr(-z)+sd*norm.pdf(z))).sum(1)/(1-q)
    return v,e

def gmm(x,seed,n=1536):
    scale=np.maximum(x.std(0),.05);mu=x.mean(0)
    mod=GaussianMixture(3,covariance_type='full',reg_covar=.01,n_init=2,max_iter=150,random_state=seed)
    with warnings.catch_warnings(record=True) as ww:
        warnings.simplefilter('always');mod.fit((x-mu)/scale)
    z,_=mod.sample(n)
    return z*scale+mu,{'converged':bool(mod.converged_),'warnings':[str(w.message) for w in ww]}

def gaussian(x,w,q=.95):
    f=LedoitWolf().fit(x);sd=np.sqrt(np.einsum('ij,jk,ik->i',w,f.covariance_,w));m=-w@f.location_;z=norm.ppf(q)
    return m+z*sd,m+norm.pdf(z)*sd/(1-q)

def student_fit(x,w,q=.95):
    f=LedoitWolf().fit(x);cov=f.covariance_;d=x.shape[1];y=x-f.location_
    mah=np.einsum('ij,jk,ik->i',y,np.linalg.inv(cov),y);ld=np.linalg.slogdet(cov)[1]
    def nll(nu):
        a=(nu-2)/nu
        ll=gammaln((nu+d)/2)-gammaln(nu/2)-.5*(d*np.log(nu*np.pi)+ld+d*np.log(a))-.5*(nu+d)*np.log1p(mah/(a*nu))
        return -float(ll.mean())
    fit=minimize_scalar(nll,bounds=(3.,50.),method='bounded');nu=fit.x
    sd=np.sqrt(np.einsum('ij,jk,ik->i',w,cov*((nu-2)/nu),w));m=-w@f.location_;z=tdist.ppf(q,nu)
    return (m+z*sd,m+sd*(nu+z*z)/(nu-1)*tdist.pdf(z,nu)/(1-q)),float(nu)

def filter_returns(x,lam=.94):
    # Fifty observations initialize variance. Residual i uses variance through i-1.
    init=50;var=np.maximum(np.mean(x[:init]**2,axis=0),1e-6);res=[]
    for i in range(init,len(x)):
        res.append(x[i]/np.sqrt(var));var=lam*var+(1-lam)*x[i]**2
    return np.array(res),np.sqrt(var)

def entropy_solve(A,B,p0,rho=1.,band=0.):
    m=A.shape[1];logp=np.log(np.maximum(p0,1e-300))
    if band==0:
        def fg(v):
            logits=logp-A@v;l=logsumexp(logits);p=np.exp(logits-l)
            return float(l+B@v+.5*rho*(v@v)),B-A.T@p+rho*v
        opt=minimize(fg,np.zeros(m),jac=True,method='L-BFGS-B',options={'maxiter':160,'ftol':1e-10,'gtol':1e-7});v=opt.x
    else:
        def fg(u):
            v=u[:m]-u[m:];logits=logp-A@v;l=logsumexp(logits);p=np.exp(logits-l);g=B-A.T@p+rho*v
            return float(l+B@v+band*u.sum()+.5*rho*(v@v)),np.r_[g+band,-g+band]
        opt=minimize(fg,np.zeros(2*m),jac=True,bounds=[(0,None)]*(2*m),method='L-BFGS-B',options={'maxiter':200,'ftol':1e-10,'gtol':1e-7});v=opt.x[:m]-opt.x[m:]
    pp=np.exp(logp-A@v-logsumexp(logp-A@v))
    return pp,bool(opt.success)

def calibrate(z,cal,w,beta=.5,band=1.,seed=0,old=False,random=False):
    if beta:
        z=np.vstack([z,cal]);p0=np.r_[np.full(len(z)-len(cal),(1-beta)/(len(z)-len(cal))),np.full(len(cal),beta/len(cal))]
    else:p0=np.full(len(z),1/len(z))
    rb=Risk(z,w);v,e=rb.eval(p0);h=np.maximum(rb.loss-v,0);hc=np.maximum(-cal@w.T-v,0)
    b=hc.mean(0)
    if old:b=.5*b+.5*(p0@h)
    # Relative floor avoids arbitrary currency-unit dependence.
    scales=np.maximum(hc.std(0,ddof=1)/np.sqrt(len(cal)),.025*np.maximum(np.std(-cal@w.T,axis=0),.05))
    A=h/scales;B=b/scales;sel=[];p=p0.copy();ok=[];order=np.random.default_rng(seed).permutation(len(w))
    for it in range(8):
        if random:j=int(order[it])
        else:
            cur=rb.eval(p)[1];best=int(np.argmin(cur));dis=np.maximum(np.abs(B-A.T@p)-band,0)
            if sel:dis[sel]=-np.inf
            j=best if it%3==0 and best not in sel else int(np.argmax(dis))
        sel.append(j);p,success=entropy_solve(A[:,sel],B[sel],p0,1.,band);ok.append(success)
    return rb.eval(p),{'converged':all(ok),'ess':float(1/(p@p)),'directions':sel}

def one(job):
    stage,family,seed=job;start=time.perf_counter();x,pars=generate(seed,family);w=bank(seed);q=.95
    a,b=x[:256],x[256:];risk={};diag={}
    risk['historical']=Risk(x,w).eval();risk['equal_weight']=risk['historical'];risk['gaussian_LW']=gaussian(x,w)
    risk['student_t_LW'],diag['student_df']=student_fit(x,w)
    z,diag['gmm_base']=gmm(a,seed);zp,diag['gmm_pooled']=gmm(x,seed)
    risk['gmm_base']=Risk(z,w).eval();risk['gmm_pooled']=Risk(zp,w).eval()
    risk['aptc_v1'],diag['aptc_v1']=calibrate(z,b,w,beta=0,band=0,seed=seed,old=True)
    risk['random_calibration'],diag['random_calibration']=calibrate(z,b,w,beta=0,band=0,seed=seed+1,old=True,random=True)
    for beta in (.25,.5):
        zz=np.vstack([z,b]);pp=np.r_[np.full(len(z),(1-beta)/len(z)),np.full(len(b),beta/len(b))]
        risk[f'support_mix{int(beta*100)}']=Risk(zz,w).eval(pp)
        risk[f'support_band{int(beta*100)}'],diag[f'support_band{int(beta*100)}']=calibrate(z,b,w,beta=beta,band=1,seed=seed)
    risk['support_point50'],diag['support_point50']=calibrate(z,b,w,beta=.5,band=0,seed=seed)
    res,vol=filter_returns(x);xx=res*vol
    risk['filtered_historical']=Risk(xx,w).eval();risk['filtered_gaussian']=gaussian(xx,w)
    ia=len(res)//2;zr,diag['filtered_gmm']=gmm(res[:ia],seed)
    risk['filtered_support_band50'],diag['filtered_support_band50']=calibrate(zr*vol,res[ia:]*vol,w,beta=.5,band=1,seed=seed)
    # Regularized historical ES controls; risk estimate and decision penalty are kept separate.
    vh,eh=risk['historical'];hh=np.maximum(-x@w.T-vh,0)/.05;se=hh.std(0,ddof=1)/np.sqrt(len(x))
    decisions={'historical_se_penalty':int(np.argmin(eh+se)), 'historical_concentration_penalty':int(np.argmin(eh+.2*np.median(eh)*(w*w).sum(1)))}
    risk['historical_se_penalty']=risk['historical'];risk['historical_concentration_penalty']=risk['historical']
    # No estimator above receives pars or future outcomes.
    tv,te=truth(w,pars);oracle=float(te.min());rows=[]
    for meth,(v,e) in risk.items():
        j=0 if meth=='equal_weight' else decisions.get(meth,int(np.argmin(e)))
        rows.append({'stage':stage,'family':family,'seed':seed,'method':meth,'portfolio_id':j,
          'predicted_es':float(e[j]),'true_es':float(te[j]),'absolute_error':float(abs(e[j]-te[j])),
          'relative_error':float(abs(e[j]-te[j])/te[j]),'regret':float(te[j]-oracle),
          'relative_regret':float(te[j]/oracle-1),'underestimation':float(te[j]-e[j]),
          'equal_predicted_es':float(e[0]),'equal_true_es':float(te[0]),'all_portfolio_mae':float(np.mean(abs(e-te))),
          'hhi':float(w[j]@w[j]),'population_state':pars.get('latent_state_eval_only',-1)})
    out=ROOT/'results'/stage;out.mkdir(exist_ok=True,parents=True)
    np.savez_compressed(out/f'{family}_{seed}.npz',weights=w,returns=x,true_es=te,true_var=tv,
         **{f'{k}_es':v[1] for k,v in risk.items()},**{f'{k}_var':v[0] for k,v in risk.items()})
    diag['elapsed_seconds']=time.perf_counter()-start;diag['x_sha256']=hashlib.sha256(x.tobytes()).hexdigest()
    (out/f'{family}_{seed}.json').write_text(json.dumps(diag,indent=2))
    return rows

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--stage',choices=['validation','test','smoke'],default='smoke');ap.add_argument('--workers',type=int,default=3);args=ap.parse_args()
    if args.stage=='test' and not (ROOT/'results'/'selection_freeze.json').exists():raise RuntimeError('Freeze validation selection before test')
    seeds=CFG['validation_seeds'] if args.stage=='validation' else CFG['test_seeds'] if args.stage=='test' else [999]
    jobs=[(args.stage,f,s) for f in FAMILIES for s in seeds];allrows=[];start=time.perf_counter()
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        for k,rows in enumerate(ex.map(one,jobs)):
            allrows.extend(rows)
            if k%10==0:print(args.stage,k+1,'/',len(jobs),'elapsed',round(time.perf_counter()-start,1),flush=True)
    out=ROOT/'results'/f'{args.stage}.csv'
    with out.open('w',newline='') as fp:
        writer=csv.DictWriter(fp,fieldnames=allrows[0].keys());writer.writeheader();writer.writerows(allrows)
    (ROOT/'results'/f'{args.stage}_receipt.json').write_text(json.dumps({'seconds':time.perf_counter()-start,'jobs':len(jobs),'rows':len(allrows),'workers':args.workers,'source_hash':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2))
    print('DONE',out,len(allrows),flush=True)
if __name__=='__main__':main()
