#!/usr/bin/env python3
"""Independent stable-face audit: KKT/SVD, vertex dual LP, quadrature, all paired CIs."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from scipy.integrate import quad
from scipy.special import expit, ndtr
from scipy.stats import norm

ROOT=Path(__file__).resolve().parents[1]


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def verify(base):
    started=time.perf_counter()
    import sys
    sys.path.insert(0,str(ROOT))
    from selection_risk.core import legacy
    cfg=json.loads((ROOT/'continuous_cvar_face/config.json').read_text())
    preflight=json.loads((base/'preflight.json').read_text())
    for p,h in preflight['protected_files'].items():assert sha(ROOT/p)==h,p
    freeze=json.loads((base/'pilot/freeze.json').read_text())
    for p,h in freeze['identity']['sources'].items():assert sha(ROOT/p)==h,p
    with (base/'pilot/estimates.csv').open() as stream:rows=list(csv.DictReader(stream))
    assert len(rows)==3200
    cases={}
    for r in rows:cases.setdefault((r['family'],int(r['seed'])),[]).append(r)
    diagnostics={(d['family'],d['seed']):d for d in json.loads((base/'pilot/diagnostics.json').read_text())}
    assert len(cases)==128
    quadrature_max=0.;correction_max=0.;na_corrections=0
    for (family,seed),rr in cases.items():
        with np.load(base/'pilot/arrays'/f'{family}_{seed}.npz',allow_pickle=False) as a:
            x=a['returns'];regenerated,p=legacy.generate(seed,family)
            np.testing.assert_array_equal(x,regenerated)
            for policy in ['full512','A256','B256']:
                past=x if policy=='full512' else x[:256] if policy=='A256' else x[256:]
                for tau in cfg['taus']:
                    theta=a[f'{policy}_{tau}_theta'];w,v=theta[:-1],theta[-1]
                    aa=np.column_stack([-past,-np.ones(len(past))]);z=aa@theta/tau
                    scores=expit(z)[:,None]*aa/.05;scores[:,-1]+=1
                    hessian=aa.T@((expit(z)*expit(-z)/(.05*tau*len(past)))[:,None]*aa)
                    raw=v+tau*np.logaddexp(0,z).mean()/.05
                    relevant={r['estimator']:r for r in rr if r['policy']==policy and float(r['tau'])==tau}
                    np.testing.assert_allclose(raw,float(relevant['raw']['estimate']),atol=1e-11)
                    diag=diagnostics[family,seed]['diagnostics'][f'{policy}_{tau}']
                    for row in relevant.values():
                        np.testing.assert_allclose(json.loads(row['weights']),w,atol=0,rtol=0)
                        assert float(row['threshold'])==v
                    lower=np.flatnonzero(w<=cfg['active_tol'])
                    upper=np.flatnonzero(cfg['weight_cap']-w<=cfg['active_tol'])
                    free=np.setdiff1d(np.arange(8),np.r_[lower,upper])
                    q=scores.mean(axis=0)[:-1]
                    if not len(free):
                        # Independent 2-variable LP: maximize strictly positive dual margin.
                        from scipy.optimize import linprog
                        aa=np.array([[-1.,1.]]*len(lower)+[[1.,1.]]*len(upper))
                        bb=np.r_[q[lower],-q[upper]]
                        certificate=linprog([0.,-1.],A_ub=aa,b_ub=bb,bounds=[(None,None),(None,None)],method='highs')
                        assert certificate.success
                        np.testing.assert_allclose(-certificate.fun,diag['face_margin'],atol=1e-10)
                        if diag['numerical_gate']:assert -certificate.fun>cfg['face_margin_tol']
                    # Solve the augmented KKT system, independent of null-space implementation.
                    if diag['numerical_gate']:
                        c=[np.r_[np.ones(8),0.]]
                        for j in lower:c.append(-np.eye(9)[j])
                        for j in upper:c.append(np.eye(9)[j])
                        c=np.asarray(c)
                        _,singular,vh=np.linalg.svd(c,full_matrices=False)
                        c=vh[:int(np.sum(singular>1e-12))]
                        kkt=np.block([[hessian,c.T],[c,np.zeros((len(c),len(c)))]])
                        rhs=np.vstack([scores.T,np.zeros((len(c),len(past)))])
                        influence=-np.linalg.solve(kkt,rhs)[:9,:].T
                        correction=-np.mean(np.sum(scores*influence,axis=1))/len(past)
                        discrepancy=abs(correction-float(relevant['oic_face']['correction']))
                        correction_max=max(correction_max,discrepancy);assert discrepancy<1e-9
                    else:
                        na_corrections+=1
                        assert relevant['oic_face']['estimate']=='' and relevant['oic_face']['squared_relative_error']==''
                    if policy!='full512':
                        held=x[256:] if policy=='A256' else x[:256]
                        independent=v+tau*np.logaddexp(0,(-held@w-v)/tau).mean()/.05
                        np.testing.assert_allclose(independent,float(relevant['independent']['estimate']),atol=1e-11)
                    mean=-p['mu']@w;sd=np.sqrt(np.einsum('i,kij,j->k',w,p['cov'],w))
                    target=0.
                    for component,prob in enumerate(p['p']):
                        z0=(v-mean[component])/sd[component]
                        integrand=lambda u:(v+tau*np.logaddexp(0,(mean[component]+sd[component]*u-v)/tau)/.05)*norm.pdf(u)
                        val=quad(integrand,-12,z0,epsabs=1e-9)[0]+quad(integrand,z0,12,epsabs=1e-9)[0]
                        target+=prob*val
                    discrepancy=abs(target-float(relevant['raw']['true_objective']))
                    quadrature_max=max(quadrature_max,discrepancy);assert discrepancy<1e-7
                    true_es=legacy.truth(w[None],p)[1][0]
                    for row in relevant.values():
                        np.testing.assert_allclose(float(row['true_es']),true_es,atol=1e-10)
                        if row['estimate']:
                            error=float(row['estimate'])/target-1
                            np.testing.assert_allclose(error*error,float(row['squared_relative_error']),atol=1e-8)
            # Independently evaluate the population oracle and its global convex gap.
            w,v=a['oracle_theta'][:-1],a['oracle_theta'][-1]
            mean=-p['mu']@w;covw=p['cov']@w;sd=np.sqrt(covw@w);z=(v-mean)/sd
            gw=p['p']@(-p['mu']*ndtr(-z)[:,None]+covw*(norm.pdf(z)/sd)[:,None])/.05
            gv=1-p['p']@ndtr(-z)/.05
            linear_min=.5*np.sort(gw)[:2].sum()+(-50 if gv>=0 else 50)*gv
            gap=gw@w+gv*v-linear_min
            assert -1e-8<=gap<1e-5
    with (base/'pilot/paired.csv').open() as stream:paired=list(csv.DictReader(stream))
    primary=[r for r in paired if r['primary']=='True']
    assert len(primary)==1
    # Recompute every registered paired contrast independently, including null logic.
    for contrast in paired:
        families=cfg['families'] if contrast['scope']=='overall' else [contrast['scope']]
        table={(r['family'],int(r['seed']),r['estimator']):r[contrast['metric']] for r in rows
               if r['policy']==contrast['policy'] and r['tau']==contrast['tau']}
        delta=[];valid=True
        for seed in range(cfg['seeds']['start'],cfg['seeds']['stop']):
            values=[]
            for family in families:
                a,b=table[family,seed,'oic_face'],table[family,seed,contrast['baseline']]
                if a=='' or b=='':valid=False;break
                values.append(float(a)-float(b))
            if not valid:break
            delta.append(np.mean(values))
        if not valid:
            assert contrast['status']=='INCOMPLETE' and contrast['mean']==''
            continue
        delta=np.array(delta)
        indices=np.random.default_rng(cfg['bootstrap_seed']).integers(len(delta),size=(cfg['bootstrap_reps'],len(delta)))
        low,high=np.quantile(delta[indices].mean(axis=1),[.025,.975])
        assert contrast['status']=='COMPLETE'
        np.testing.assert_allclose([delta.mean(),low,high],[float(contrast[k]) for k in ['mean','ci_low','ci_high']],atol=1e-12)
    return {'status':'PASS','verifier_sha256':sha(__file__),'protected_files_unchanged':len(preflight['protected_files']),
            'instances':128,'estimate_rows':3200,'fit_targets_checked':1152,'null_oic_preserved':na_corrections,
            'primary_status_verified':primary[0]['status'],'paired_cluster_contrasts_reproduced':len(paired),
            'max_augmented_kkt_correction_difference':correction_max,'max_direct_quadrature_difference':quadrature_max,
            'seconds':time.perf_counter()-started,'scope':'Numerical audit, not independent peer review or general OIC theorem'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    result=verify(args.out)
    (args.out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
