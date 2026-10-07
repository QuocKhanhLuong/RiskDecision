"""Development/regression gate: previously seen arrays only, no risk comparisons."""
import argparse
import json
import time
from pathlib import Path

from .run import config,sources
import numpy as np
from scipy.linalg import null_space
from tqdm import tqdm

from continuous_cvar.model import Fit,active_geometry,geometry_diagnostics,smooth_terms
from .model import correct_locked
from selection_risk.runtime import atomic_json,digest,object_hash,utc


def independent_correction(x,theta,tau,cfg):
    """Augmented KKT solve after independent SVD row reduction of normals."""
    _,_,h,scores,_=smooth_terms(x,theta,tau,cfg['alpha'])
    dim=x.shape[1]
    c=[np.r_[np.ones(dim),0.]]
    for j in range(dim):
        if theta[j]<=cfg['active_tol']:c.append(-np.eye(dim+1)[j])
        if cfg['weight_cap']-theta[j]<=cfg['active_tol']:c.append(np.eye(dim+1)[j])
    c=np.asarray(c)
    _,s,vh=np.linalg.svd(c,full_matrices=False)
    rank=int(np.sum(s>1e-12));independent=vh[:rank]
    kkt=np.block([[h,independent.T],[independent,np.zeros((rank,rank))]])
    rhs=np.vstack([scores.T,np.zeros((rank,len(x)))])
    influence=-np.linalg.solve(kkt,rhs)[:dim+1].T
    return -float(np.mean(np.sum(scores*influence,axis=1)))/len(x)


def run(base):
    cfg=config();preflight=json.loads((base/'preflight.json').read_text())
    assert preflight['sources']==sources() and preflight['config_sha256']==object_hash(cfg)
    old=Path(cfg['seen_regression_run'])/'pilot/arrays'
    paths=sorted(old.glob('*.npz'))
    if len(paths)!=128:raise ValueError('Require all 128 seen regression array files')
    rows=[];started=time.perf_counter();kkt_error=0.;unchanged_error=0.;hashes={}
    progress=base/'face_audit_progress.jsonl'
    for i,path in enumerate(tqdm(paths,desc='seen-array face audit',unit='case'),1):
        hashes[str(path)]=digest(path)
        with np.load(path) as a:
            x=a['returns']
            for policy,past in [('full512',x),('A256',x[:256]),('B256',x[256:])]:
                for tau in cfg['taus']:
                    theta=a[f'{policy}_{tau}_theta']
                    value,g,h,scores,_=smooth_terms(past,theta,tau,cfg['alpha'])
                    diag,n,r=geometry_diagnostics(theta,g,h,cfg)
                    correction=float(np.mean(np.sum((scores@n)*np.linalg.solve(r,(scores@n).T).T,axis=1)))/len(past) if diag['numerical_gate'] else None
                    fit=correct_locked(past,Fit(theta,value,correction,diag),tau,cfg)
                    assert np.array_equal(fit.theta,theta) and fit.objective==value
                    error=None
                    if fit.correction is not None:
                        error=abs(fit.correction-independent_correction(past,theta,tau,cfg))
                        kkt_error=max(kkt_error,error)
                        if correction is not None:unchanged_error=max(unchanged_error,abs(fit.correction-correction))
                    rows.append({'case':path.stem,'policy':policy,'tau':tau,'old_gate':diag['numerical_gate'],
                                 'face_gate':fit.diagnostics['numerical_gate'],'face_margin':fit.diagnostics['face_margin'],
                                 'face_dimension':fit.diagnostics['face_dimension'],'kkt_difference':error})
        event={'utc':utc(),'completed':i,'total':128,'elapsed_seconds':time.perf_counter()-started}
        event['eta_seconds']=event['elapsed_seconds']/i*(128-i)
        with progress.open('a') as f:f.write(json.dumps(event)+'\n')
    assert kkt_error<1e-9 and unchanged_error<1e-9
    assert hashes=={str(p):digest(p) for p in paths}
    result={'status':'PASS','scope':'DEVELOPMENT_REGRESSION_SEEN_ARRAYS; no population risk metrics read or combined',
            'sources':sources(),'config_sha256':object_hash(cfg),'old_array_hashes':hashes,
            'cases':128,'fit_targets':len(rows),'old_invalid':sum(not r['old_gate'] for r in rows),
            'face_invalid':sum(not r['face_gate'] for r in rows),'max_kkt_difference':kkt_error,
            'max_existing_correction_difference':unchanged_error,'decisions_and_arrays_unchanged':True,
            'seconds':time.perf_counter()-started,'finished_utc':utc()}
    atomic_json(base/'face_audit_details.json',rows);atomic_json(base/'face_audit.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in {'sources','old_array_hashes'}},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    run(parser.parse_args().out)
