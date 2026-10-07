#!/usr/bin/env python3
"""Separate array/KKT-block/quadrature verification; does not fit any model."""
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


def verify(base,previous):
    started=time.perf_counter()
    import sys
    sys.path.insert(0,str(ROOT))
    from selection_risk.core import legacy
    cfg=json.loads((ROOT/'continuous_cvar/config.json').read_text())
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
    quadrature_max=0.;correction_max=0.;unchanged_arrays=0;na_corrections=0
    for (family,seed),rr in cases.items():
        with np.load(base/'pilot/arrays'/f'{family}_{seed}.npz',allow_pickle=False) as a:
            x=a['returns'];regenerated,p=legacy.generate(seed,family)
            np.testing.assert_array_equal(x,regenerated)
            if previous is not None:
                old_path=previous/'pilot/arrays'/f'{family}_{seed}.npz'
                if old_path.exists():
                    with np.load(old_path,allow_pickle=False) as old:
                        for key in old.files:np.testing.assert_array_equal(a[key],old[key])
                    unchanged_arrays+=1
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
                    # Solve the augmented KKT system, independent of null-space implementation.
                    if diag['numerical_gate']:
                        c=[np.r_[np.ones(8),0.]]
                        for j in diag['active_lower']:c.append(-np.eye(9)[j])
                        for j in diag['active_upper']:c.append(np.eye(9)[j])
                        c=np.asarray(c)
                        kkt=np.block([[hessian,c.T],[c,np.zeros((len(c),len(c)))]])
                        rhs=np.vstack([scores.T,np.zeros((len(c),len(past)))])
                        influence=-np.linalg.solve(kkt,rhs)[:9,:].T
                        correction=-np.mean(np.sum(scores*influence,axis=1))/len(past)
                        discrepancy=abs(correction-float(relevant['oic_kkt']['correction']))
                        correction_max=max(correction_max,discrepancy);assert discrepancy<1e-9
                    else:
                        na_corrections+=1
                        assert relevant['oic_kkt']['estimate']=='' and relevant['oic_kkt']['squared_relative_error']==''
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
    assert len(primary)==1 and primary[0]['status']=='INCOMPLETE' and not primary[0]['mean']
    # Recompute a complete predeclared secondary contrast, preserving cluster units.
    table={(r['family'],int(r['seed']),r['estimator']):float(r['squared_relative_error']) for r in rows
           if r['policy']=='A256' and float(r['tau'])==.1}
    delta=np.array([np.mean([table[f,s,'oic_kkt']-table[f,s,'independent'] for f in cfg['families']])
                    for s in range(cfg['seeds']['start'],cfg['seeds']['stop'])])
    indices=np.random.default_rng(cfg['bootstrap_seed']).integers(64,size=(10000,64))
    lo,hi=np.quantile(delta[indices].mean(axis=1),[.025,.975])
    target=[r for r in paired if r['scope']=='overall' and r['policy']=='A256' and r['tau']=='0.1'
            and r['baseline']=='independent' and r['metric']=='squared_relative_error'][0]
    np.testing.assert_allclose([delta.mean(),lo,hi],[float(target[k]) for k in ['mean','ci_low','ci_high']],atol=1e-12)
    return {'status':'PASS','verifier_sha256':sha(__file__),'protected_files_unchanged':len(preflight['protected_files']),
            'instances':128,'estimate_rows':3200,'fit_targets_checked':1152,'null_oic_preserved':na_corrections,
            'primary_incomplete_preserved':True,'secondary_cluster_ci_reproduced':True,
            'previous_completed_case_arrays_identical':unchanged_arrays,
            'max_augmented_kkt_correction_difference':correction_max,'max_direct_quadrature_difference':quadrature_max,
            'seconds':time.perf_counter()-started,'scope':'Numerical audit, not independent peer review or general OIC theorem'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--previous',type=Path);args=parser.parse_args()
    result=verify(args.out,args.previous)
    (args.out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
