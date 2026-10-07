#!/usr/bin/env python3
"""Independent post-run numerical audit; no portfolio refits or model selection."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key]='1'
import argparse
import csv
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from scipy.integrate import quad
from scipy.linalg import null_space
from scipy.special import expit
from scipy.stats import norm,multivariate_normal
from tqdm import tqdm

ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def value(x,theta,tau,alpha):
    return float(theta[-1]+tau*np.logaddexp(0,(-x@theta[:-1]-theta[-1])/tau).mean()/alpha)


def direct_cost(theta,p,tau,alpha):
    w,v=theta[:-1],theta[-1];mean=-np.asarray(p['mu'])@w
    sd=np.sqrt(np.einsum('i,kij,j->k',w,np.asarray(p['cov']),w));total=0.
    for weight,m,s in zip(p['p'],mean,sd):
        z0=(v-m)/s
        fun=lambda z:(v+tau*np.logaddexp(0,(m+s*z-v)/tau)/alpha)*norm.pdf(z)
        total+=weight*(quad(fun,-12,z0,epsabs=1e-9)[0]+quad(fun,z0,12,epsabs=1e-9)[0])
    return float(total)


def independent_filter(x,start,world,cfg,mu,cov):
    d=cfg['dgp'];p0=np.array(d['transition0']);p1=np.array(d['transition1'])
    pi=np.array([p0[1,0],p0[0,1]])/(p0[1,0]+p0[0,1]);shift=d['shift_time']
    if world=='markov_shift' and start>=shift:pi=pi@np.linalg.matrix_power(p1,start-shift+1)
    probability=pi[1]
    lp=np.column_stack([multivariate_normal.logpdf(x,mean=mu[k],cov=cov[k]) for k in range(2)])
    for i,row in enumerate(lp):
        posterior=expit(np.log(probability/(1-probability))+row[1]-row[0])
        matrix=p1 if world=='markov_shift' and start+i+1>=shift else p0
        probability=(1-posterior)*matrix[0,1]+posterior*matrix[1,1]
    return np.array([1-probability,probability])


def verify(base):
    started=time.perf_counter();cfg=json.loads((ROOT/'temporal_risk/config.json').read_text())
    freeze=json.loads((base/'pilot/freeze.json').read_text());mc=freeze['identity']['config']['effective_model']
    tau=mc['tau'];alpha=cfg['fit']['alpha'];block=mc['block_length']
    preflight=json.loads((base/'preflight.json').read_text())
    for path,h in preflight['protected_files'].items():assert sha(ROOT/path)==h,path
    for path,h in freeze['identity']['sources'].items():assert sha(ROOT/path)==h,path
    rows=list(csv.DictReader((base/'pilot/estimates.csv').open()))
    index={(r['world'],int(r['seed']),int(r['origin']),r['policy'],r['method']):r for r in rows}
    assert len(index)==len(rows)==32*3*8*22
    source=json.loads((base/'development_selection.json').read_text())
    assert not source['population_errors_used'] and source['block_length']==block
    paths=sorted((base/'pilot/cases').glob('*.json'));assert len(paths)==768
    maxima={'objective':0.,'hac':0.,'bootstrap':0.,'filter':0.,'decomposition':0.}
    nulls=0;bootstrap_targets=0;coupled={};array_cache={}
    for path in tqdm(paths,desc='independent temporal audit',unit='origin'):
        envelope=json.loads(path.read_text());case=envelope['payload'];assert case['status']=='COMPLETE'
        seed=case['seed'];origin=case['origin'];world=case['world']
        if seed not in array_cache:
            with np.load(base/'pilot/paths'/f'path_{seed}.npz',allow_pickle=False) as arr:
                array_cache[seed]={k:arr[k] for k in arr.files}
            arr=array_cache[seed];cut=cfg['dgp']['shift_time']
            np.testing.assert_array_equal(arr['markov_stationary_returns'][:cut],arr['markov_shift_returns'][:cut])
        arr=array_cache[seed];x=arr[world+'_returns'][origin-512:origin]
        assert hashlib.sha256(x.tobytes()).hexdigest()==case['past_sha256']
        rng=np.random.default_rng(case['locked']['resampling_seed'])
        stored=case['locked']['statistical_diagnostics']['forecast_parameters']
        mean=x.mean(axis=0);weights=np.exp(np.log(mc['ewma_lambda'])*np.arange(len(x)-1,-1,-1));weights/=weights.sum()
        np.testing.assert_allclose(stored['gaussian_iid']['mu'],mean[None,:],atol=1e-12)
        np.testing.assert_allclose(stored['gaussian_iid']['cov'][0],np.cov(x.T),atol=1e-12)
        np.testing.assert_allclose(stored['ewma_gaussian']['cov'][0],np.einsum('n,ni,nj->ij',weights,x-mean,x-mean),atol=1e-10)
        predicted=[];residual=[]
        for j in range(x.shape[1]):
            design=np.column_stack([np.ones(len(x)-1),x[:-1,j]])
            coefficient=np.linalg.lstsq(design,x[1:,j],rcond=None)[0]
            phi=np.clip(coefficient[1],-mc['ar_clip'],mc['ar_clip'])
            intercept=x[1:,j].mean()-phi*x[:-1,j].mean()
            predicted.append(intercept+phi*x[-1,j]);residual.append(x[1:,j]-intercept-phi*x[:-1,j])
        np.testing.assert_allclose(stored['ar_gaussian']['mu'][0],predicted,atol=1e-10)
        np.testing.assert_allclose(stored['ar_gaussian']['cov'][0],np.cov(np.array(residual)),atol=1e-10)
        # Checkpoint JSON keys are sorted; restore the original RNG consumption order.
        for policy in ['full512','equal512','older256']:
            result=case['locked']['policies'][policy]
            theta=np.array(result['theta']);past=x[:256] if policy=='older256' else x
            rr={m:index[world,seed,origin,policy,m] for m in result['estimates']}
            for row in rr.values():
                np.testing.assert_array_equal(json.loads(row['weights']),theta[:-1]);assert float(row['threshold'])==theta[-1]
                assert int(row['information_stop'])==origin and int(row['holding_horizon'])==1
                if row['estimate']:
                    a=float(row['estimation_relative']);b=float(row['mismatch_relative']);err=float(row['conditional_signed_relative_error'])
                    residual=max(abs(a+b-err),abs(a*a+b*b+2*a*b-float(row['conditional_squared_relative_error'])))
                    maxima['decomposition']=max(maxima['decomposition'],residual);assert residual<1e-10
                else:nulls+=1
            np.testing.assert_allclose(value(past,theta,tau,alpha),float(rr['raw']['estimate']),atol=1e-10)
            if policy=='older256':
                np.testing.assert_allclose(value(x[256:],theta,tau,alpha),float(rr['chronological']['estimate']),atol=1e-10)
                np.testing.assert_allclose(value(x[256+block:],theta,tau,alpha),float(rr['blocked_holdout']['estimate']),atol=1e-10)
            else:
                deltas=[]
                for rep in result['bootstrap_diagnostics']['replicates']:
                    starts=rng.integers(len(past),size=int(np.ceil(len(past)/block)))
                    ix=np.concatenate([(s+np.arange(block))%len(past) for s in starts])[:len(past)]
                    assert hashlib.sha256(ix.tobytes()).hexdigest()==rep['indices_sha256']
                    bt=np.array(rep['theta']);delta=value(past,bt,tau,alpha)-value(past[ix],bt,tau,alpha)
                    maxima['bootstrap']=max(maxima['bootstrap'],abs(delta-rep['delta']));assert abs(delta-rep['delta'])<1e-10
                    deltas.append(delta);bootstrap_targets+=1
                if rr['block_bootstrap']['estimate']:
                    np.testing.assert_allclose(float(rr['block_bootstrap']['estimate']),float(rr['raw']['estimate'])+np.mean(deltas),atol=1e-10)
            aa=np.column_stack([-past,-np.ones(len(past))]);z=aa@theta/tau
            score=expit(z)[:,None]*aa/alpha;score[:,-1]+=1
            h=aa.T@((expit(z)*expit(-z)/(alpha*tau*len(past)))[:,None]*aa)
            if policy=='equal512':n=np.eye(9)[:,-1:]
            else:
                c=[np.r_[np.ones(8),0.]]
                for j in range(8):
                    if theta[j]<=cfg['fit']['active_tol'] or cfg['fit']['weight_cap']-theta[j]<=cfg['fit']['active_tol']:c.append(np.eye(9)[j])
                n=null_space(np.array(c))
            projected=score@n;centered=projected-projected.mean(axis=0)
            reduced=n.T@h@n
            if rr['iid_oic']['estimate']:
                iid=float(np.mean(np.sum(projected*np.linalg.solve(reduced,projected.T).T,axis=1))/len(past))
                np.testing.assert_allclose(float(rr['iid_oic']['estimate']),float(rr['raw']['estimate'])+iid,atol=1e-9)
            if rr['hac']['estimate']:
                t=np.arange(len(past));kernel=np.maximum(1-np.abs(t[:,None]-t)/block,0.)
                s=centered.T@kernel@centered/len(past)
                expected=float(rr['raw']['estimate'])+float(np.trace(np.linalg.solve(reduced,s))/len(past))
                error=abs(expected-float(rr['hac']['estimate']));maxima['hac']=max(maxima['hac'],error);assert error<1e-9
            params=case['evaluation'][policy]
            if world.startswith('markov'):
                actual=independent_filter(x,origin-512,world,cfg,np.array(params['conditional']['mu']),np.array(params['conditional']['cov']))
                error=float(np.max(np.abs(actual-np.array(params['conditional']['p']))));maxima['filter']=max(maxima['filter'],error);assert error<1e-10
                matrix=np.array(cfg['dgp']['transition1'] if world=='markov_shift' and origin>=cfg['dgp']['shift_time'] else cfg['dgp']['transition0'])
                np.testing.assert_array_equal(params['latent']['p'],matrix[int(arr[world+'_states'][origin-1])])
            for name,column in [('conditional','conditional_objective'),('marginal','marginal_objective')]:
                truth=direct_cost(theta,params[name],tau,alpha)
                error=abs(truth-float(rr['raw'][column]));maxima['objective']=max(maxima['objective'],error);assert error<1e-7
            for method,p in case['locked']['statistical_diagnostics']['forecast_parameters'].items():
                expected=direct_cost(theta,p,tau,alpha)
                np.testing.assert_allclose(expected,float(rr[method]['estimate']),atol=1e-7)
            if world.startswith('markov') and origin<=cfg['dgp']['shift_time']:
                key=(seed,origin,policy)
                if key in coupled:assert coupled[key]==result
                else:coupled[key]=result
    paired=list(csv.DictReader((base/'pilot/paired.csv').open()))
    primary=[r for r in paired if r['primary']=='True'];assert len(primary)==1
    seeds=list(range(cfg['seeds']['start'],cfg['seeds']['stop']))
    boot=np.random.default_rng(cfg['bootstrap_seed']).integers(len(seeds),size=(cfg['bootstrap_reps'],len(seeds)))
    for contrast in paired:
        origins=[o for o in cfg['origins'] if contrast['period']=='all' or (o<cfg['dgp']['shift_time'])==(contrast['period']=='before')]
        metric=contrast['target']+'_'+contrast['metric'];delta=[];valid=True
        for seed in seeds:
            within=[]
            for origin in origins:
                a=index[contrast['world'],seed,origin,contrast['policy'],contrast['method']][metric]
                b=index[contrast['world'],seed,origin,contrast['policy'],contrast['baseline']][metric]
                if not a or not b:valid=False;break
                within.append(float(a)-float(b))
            if not valid:break
            delta.append(np.mean(within))
        if not valid:assert contrast['status']=='INCOMPLETE' and not contrast['mean'];continue
        delta=np.array(delta);lo,hi=np.quantile(delta[boot].mean(axis=1),[.025,.975])
        np.testing.assert_allclose([delta.mean(),lo,hi],[float(contrast[k]) for k in ['mean','ci_low','ci_high']],atol=1e-12)
    return {'status':'PASS','verifier_sha256':sha(__file__),'origins':len(paths),'path_clusters':len(seeds),'rows':len(rows),
            'bootstrap_refits_recomputed_without_refitting':bootstrap_targets,'null_estimates_retained':nulls,
            'primary_status':primary[0]['status'],'paired_contrasts_verified':len(paired),'maximum_discrepancies':maxima,
            'protected_files_unchanged':len(preflight['protected_files']),'seconds':time.perf_counter()-started,
            'scope':'numerical/statistical verification, not independent peer review or temporal calibration guarantee'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();result=verify(args.out)
    (args.out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
