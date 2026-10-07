#!/usr/bin/env python3
"""Post-run numerical audit of the 14 seen vertex targets; no new inference."""
import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from scipy.optimize import linprog
from scipy.special import expit

ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(base):
    started=time.perf_counter()
    cfg=json.loads((ROOT/'continuous_cvar_face/config.json').read_text())
    old=ROOT/cfg['seen_regression_run']
    historical=json.loads((old/'resume_verification.json').read_text())['hashes']
    audit=json.loads((base/'face_audit.json').read_text())
    for path,expected in audit['old_array_hashes'].items():
        assert sha(ROOT/path)==expected==historical[str((ROOT/path).relative_to(old))]
    targets=[r for r in json.loads((base/'face_audit_details.json').read_text()) if not r['old_gate']]
    rows=[]
    for r in targets:
        with np.load(old/'pilot/arrays'/f"{r['case']}.npz",allow_pickle=False) as a:
            x=a['returns'];x=x if r['policy']=='full512' else x[:256] if r['policy']=='A256' else x[256:]
            theta=a[f"{r['policy']}_{r['tau']}_theta"];w,v=theta[:-1],theta[-1]
        scores=expit((-x@w-v)/r['tau'])[:,None]*(-x)/cfg['alpha'];q=scores.mean(axis=0)
        lower=np.flatnonzero(w<=cfg['active_tol']);upper=np.flatnonzero(cfg['weight_cap']-w<=cfg['active_tol'])
        assert len(lower)+len(upper)==8
        # Max t, with q_L+lambda >= t and -(q_U+lambda) >= t.
        aa=np.array([[-1.,1.]]*len(lower)+[[1.,1.]]*len(upper));bb=np.r_[q[lower],-q[upper]]
        lp=linprog([0.,-1.],A_ub=aa,b_ub=bb,bounds=[(None,None),(None,None)],method='highs')
        assert lp.success and -lp.fun>cfg['face_margin_tol']
        error=abs(-lp.fun-r['face_margin']);assert error<1e-10
        rows.append(dict(case=r['case'],policy=r['policy'],tau=r['tau'],lp_margin=-lp.fun,discrepancy=error))
    pilot=json.loads((base/'pilot/diagnostics.json').read_text())
    fresh_vertices=sum(d['face_dimension']==1 for case in pilot for d in case['diagnostics'].values())
    result={'status':'PASS','scope':'POST_RUN numerical verification on old seen cases only; not fresh vertex evidence',
            'verifier_sha256':sha(__file__),'historical_arrays_matched_previous_receipt':len(audit['old_array_hashes']),
            'vertex_targets':len(rows),'fresh_pilot_vertex_targets':fresh_vertices,'details':rows,
            'seconds':time.perf_counter()-started}
    (base/'vertex_lp_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='details'},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    verify(parser.parse_args().out)
