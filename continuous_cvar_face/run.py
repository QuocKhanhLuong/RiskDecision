"""Stable-face continuation: immutable historical fitter, fresh iid pilot, resume."""
import os
for _key in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","VECLIB_MAXIMUM_THREADS","NUMEXPR_NUM_THREADS"):
    os.environ[_key] = "1"

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
import warnings

import numpy as np
from tqdm import tqdm

from selection_risk.core import legacy
from selection_risk.runtime import ROOT, Run, atomic_json, digest, object_hash, utc
from continuous_cvar.model import fit_empirical_lp, smooth_terms
from .model import fit_smooth
from continuous_cvar.evaluation import continuous_oracle, population_es, population_hinge, population_smooth


def config():
    return json.loads((ROOT/"continuous_cvar_face/config.json").read_text())


def sources():
    paths=list((ROOT/"continuous_cvar_face").glob("*.py"))
    paths += [ROOT/p for p in ["continuous_cvar_face/APPLICABILITY.md","continuous_cvar/model.py",
                               "continuous_cvar/evaluation.py","selection_risk/core.py",
                               "selection_risk/runtime.py","quant_research_v2/src/research.py"]]
    return {str(p.relative_to(ROOT)):digest(p) for p in sorted(paths)}


class ContinuousRun(Run):
    def __init__(self,out,cfg,inputs):
        super().__init__(out,cfg,inputs)
        self.identity["sources"]=sources()
        self.fingerprint=object_hash(self.identity)


def write_csv(path,rows):
    """Stable headers and LF for identical fresh/resumed serialization."""
    if not rows:
        return
    path=Path(path);tmp=path.with_suffix(path.suffix+".tmp")
    with tmp.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=sorted(rows[0]),lineterminator='\n')
        writer.writeheader();writer.writerows(rows)
    tmp.replace(path)


def preflight(base,cfg,replay_from=None):
    candidates=set(range(cfg['seeds']['start'],cfg['seeds']['stop']))
    files,seen,reserved={},set(),set()
    for p in ROOT.rglob('*'):
        relative=p.relative_to(ROOT)
        if any(x in {'.git','.venv','__pycache__','.pytest_cache','data'} for x in relative.parts):
            continue
        if not p.is_file() or relative.parts[0]=='continuous_cvar_face' or base.resolve() in p.resolve().parents:
            continue
        match=re.search(r'_(\d+)\.(json|npz)$',p.name)
        if match:seen.add(int(match[1]))
        if p.suffix not in {'.py','.json','.csv'} or p.stat().st_size>20_000_000:
            continue
        files[str(relative)]=digest(p)
        if p.suffix=='.csv':
            with p.open() as f:
                reader=csv.DictReader(f)
                fields=[k for k in reader.fieldnames or [] if 'seed' in k.lower()]
                if fields:
                    for row in reader:
                        for k in fields:
                            if row[k] and row[k].isdigit():seen.add(int(row[k]))
        else:
            text=p.read_text(errors='replace')
            if p.suffix=='.py':
                seen.update(map(int,re.findall(r'(?<![\w.])\d+(?![\w.])',text)))
            if p.suffix=='.json':
                def visit(value,key=''):
                    if isinstance(value,dict):
                        if 'seed' in key.lower() and {'start','stop'}<=value.keys():
                            reserved.update(s for s in candidates if int(value['start'])<=s<int(value['stop']))
                        for k,v in value.items():visit(v,key+'.'+k)
                    elif isinstance(value,list):
                        if 'seed' in key.lower():
                            reserved.update(s for s in value if isinstance(s,int) and s in candidates)
                        for v in value:visit(v,key)
                    elif isinstance(value,int) and (key.lower().endswith('.seed') or key.lower().endswith('_seed')):
                        seen.add(value)
                visit(json.loads(text))
    collisions=sorted(candidates&seen)
    replay=None
    if replay_from is not None:
        replay_from=Path(replay_from)
        previous=json.loads((replay_from/'preflight.json').read_text())
        if previous['config_sha256']!=object_hash(cfg):raise ValueError('Replay config changed')
        for path in ['continuous_cvar_face/model.py','continuous_cvar/model.py','selection_risk/core.py','quant_research_v2/src/research.py']:
            if previous['sources'][path]!=digest(ROOT/path):raise ValueError('Replay fitting/generator source changed')
        with (replay_from/'pilot/case_index.csv').open() as stream:cases=list(csv.DictReader(stream))
        if {(r['family'],int(r['seed'])) for r in cases}!={(f,s) for f in cfg['families'] for s in candidates}:
            raise ValueError('Replay requires the complete original registered job set, including failures')
        replay={'status':'SOFTWARE_REPLAY_SEEN_SEEDS','from':str(replay_from),'original_preflight_sha256':digest(replay_from/'preflight.json'),
                'original_case_index_sha256':digest(replay_from/'pilot/case_index.csv'),
                'reason':'Explicit software replay with unchanged correction/fitter/generator; not unseen evidence',
                'additional_independent_cases':0,'fitting_config_and_source_unchanged':True}
    elif collisions:raise ValueError(f'Local seed collision: {collisions}')
    # All previously tracked paths, including preceding research receipts, are protected.
    tracked=subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines()
    receipt={'utc':utc(),'config_sha256':object_hash(cfg),'sources':sources(),
             'base_sha':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
             'candidate_seeds':sorted(candidates),'collisions':collisions,
             'replay':replay,
             'development_seed':cfg['development_seed'],'development_seed_seen_locally':cfg['development_seed'] in seen,
             'registered_but_not_observed_pilot_seeds':sorted(candidates&reserved),
             'development_reuse_policy':'Fixed development seed may be repeated for software repair; never included in fresh pilot inference',
             'scanned_files':files,'scanned_file_count':len(files),
             'protected_files':{p:digest(ROOT/p) for p in tracked},
             'scope':'Local source/config/seed fields/filenames; no guarantee for unavailable external runs; no prior market outcome selection'}
    dest=base/'preflight.json'
    if dest.exists():
        old=json.loads(dest.read_text())
        if old['config_sha256']!=object_hash(cfg) or old['sources']!=sources():
            raise ValueError('Preflight source/config changed; use a separate run directory')
        return old
    atomic_json(dest,receipt)
    return receipt


def estimation_row(family,seed,tau,policy,method,estimate,fit,truth,true_es,oracle,quad_diag,n_fit):
    error=None if estimate is None else estimate/truth-1
    return {'family':family,'seed':seed,'tau':tau,'policy':policy,'estimator':method,
            'n_fit':n_fit,'n_total_available':512,'n_independent_eval':256 if method=='independent' else 0,
            'estimate':estimate,'true_objective':truth,'true_es':true_es,'continuous_oracle_es':oracle,
            'relative_regret':true_es/oracle-1,'hhi':float(fit.theta[:-1]@fit.theta[:-1]),
            'threshold':float(fit.theta[-1]),'weights':json.dumps(fit.theta[:-1].tolist()),
            'correction':fit.correction if method=='oic_face' else 0.,
            'signed_relative_error':error,'absolute_relative_error':None if error is None else abs(error),
            'squared_relative_error':None if error is None else error*error,
            'threshold_gap':quad_diag['hinge_objective']-true_es,'smoothing_gap':quad_diag['smoothing_excess'],
            'numerical_gate':fit.diagnostics.get('numerical_gate',True),
            'weak_active_set':fit.diagnostics.get('weak_active_set',False),
            'target':'smooth_objective' if tau else 'hinge_objective'}


def one_case(base,family,seed,cfg):
    started=time.perf_counter();x,parameters=legacy.generate(seed,family)
    fits={};estimated={}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        for policy,past in [('full512',x),('A256',x[:256]),('B256',x[256:])]:
            for tau in cfg['taus']:
                fit=fit_smooth(past,tau,cfg)
                key=(policy,tau);fits[key]=fit
                estimated[key]={'raw':fit.objective,'oic_face':None if fit.correction is None else fit.objective+fit.correction}
                if policy!='full512':
                    held=x[256:] if policy=='A256' else x[:256]
                    estimated[key]['independent']=smooth_terms(held,fit.theta,tau,cfg['alpha'])[0]
        lp=fit_empirical_lp(x,cfg)
    # All data-only fits, thresholds and corrections are locked before this line.
    oracle=continuous_oracle(parameters,cfg)
    rows=[];truth_receipts={}
    for (policy,tau),fit in fits.items():
        truth,quadrature=population_smooth(fit.theta,parameters,tau,cfg['alpha'])
        _,es=population_es(fit.theta[:-1],parameters,cfg['alpha'])
        if truth < es-1e-8 or es < oracle.objective-1e-8:raise ValueError('Population evaluator ordering violation')
        truth_receipts[f'{policy}_{tau}']=quadrature
        for method,value in estimated[policy,tau].items():
            rows.append(estimation_row(family,seed,tau,policy,method,value,fit,truth,es,oracle.objective,
                                       quadrature,512 if policy=='full512' else 256))
    _,lp_es=population_es(lp.theta[:-1],parameters,cfg['alpha'])
    lp_truth=population_hinge(lp.theta,parameters,cfg['alpha'])[0]
    rows.append(estimation_row(family,seed,0.,'exact_lp512','raw',lp.objective,lp,lp_truth,lp_es,oracle.objective,
                               {'hinge_objective':lp_truth,'smoothing_excess':0.},512))
    array_path=base/'arrays'/f'{family}_{seed}.npz';array_path.parent.mkdir(parents=True,exist_ok=True)
    tmp=array_path.with_suffix('.npz.tmp')
    with tmp.open('wb') as f:
        np.savez_compressed(f,returns=x,lp_theta=lp.theta,oracle_theta=oracle.theta,
                            **{f'{policy}_{tau}_theta':fit.theta for (policy,tau),fit in fits.items()})
    tmp.replace(array_path)
    return {'family':family,'seed':seed,'status':'COMPLETE','rows':rows,
            'diagnostics':{f'{policy}_{tau}':fit.diagnostics for (policy,tau),fit in fits.items()},
            'lp_diagnostics':lp.diagnostics,'oracle_diagnostics':oracle.diagnostics,
            'population_quadrature':truth_receipts,'warnings':[str(w.message) for w in caught],
            'data_sha256':hashlib.sha256(x.tobytes()).hexdigest(),'seconds':time.perf_counter()-started,
            'artifacts':{str(array_path.relative_to(base)):digest(array_path)}}


def interval(x,cfg):
    x=np.asarray(x)
    if len(x)<2:return float(x.mean()),None,None
    indices=np.random.default_rng(cfg['bootstrap_seed']).integers(len(x),size=(cfg['bootstrap_reps'],len(x)))
    lo,hi=np.quantile(x[indices].mean(axis=1),[.025,.975])
    return float(x.mean()),float(lo),float(hi)


def summarize(rows,cfg,expected_seeds):
    summary=[]
    scopes=[('overall',cfg['families'])]+[(f,[f]) for f in cfg['families']]
    keys=sorted({(r['tau'],r['policy'],r['estimator']) for r in rows})
    for scope,families in scopes:
        for tau,policy,estimator in keys:
            subset=[r for r in rows if r['tau']==tau and r['policy']==policy and r['estimator']==estimator and r['family'] in families]
            lookup={(r['family'],r['seed']):r for r in subset}
            expected={(f,s) for f in families for s in expected_seeds}
            if len(lookup)!=len(subset) or set(lookup)!=expected:raise ValueError('Missing/duplicate cluster cells')
            for metric in ['signed_relative_error','absolute_relative_error','squared_relative_error','relative_regret','true_es','smoothing_gap','threshold_gap']:
                valid=all(r[metric] is not None for r in subset)
                values=[np.mean([lookup[f,s][metric] for f in families]) for s in expected_seeds] if valid else None
                mean,lo,hi=interval(values,cfg) if valid else (None,None,None)
                summary.append(dict(scope=scope,tau=tau,policy=policy,estimator=estimator,metric=metric,
                                    status='COMPLETE' if valid else 'INCOMPLETE',mean=mean,ci_low=lo,ci_high=hi,n_clusters=len(expected_seeds)))
    contrasts=[]
    for scope,families in scopes:
        for tau in cfg['taus']:
            for policy in ['full512','A256','B256']:
                for baseline in ['raw']+(['independent'] if policy!='full512' else []):
                    for metric in ['signed_relative_error','squared_relative_error']:
                        lookup={(r['family'],r['seed'],r['estimator']):r for r in rows if r['tau']==tau and r['policy']==policy and r['family'] in families}
                        valid=all(lookup[f,s,'oic_face'][metric] is not None for f in families for s in expected_seeds)
                        delta=[np.mean([lookup[f,s,'oic_face'][metric]-lookup[f,s,baseline][metric] for f in families]) for s in expected_seeds] if valid else None
                        mean,lo,hi=interval(delta,cfg) if valid else (None,None,None)
                        contrasts.append(dict(scope=scope,tau=tau,policy=policy,baseline=baseline,metric=metric,
                                              mean=mean,ci_low=lo,ci_high=hi,status='COMPLETE' if valid else 'INCOMPLETE',
                                              n_clusters=len(expected_seeds),primary=scope=='overall' and tau==cfg['primary_tau'] and policy=='full512' and baseline=='raw' and metric=='squared_relative_error'))
    return summary,contrasts


def execute(stage,base,limit=0):
    cfg=config();audit=json.loads((base/'preflight.json').read_text())
    if audit['config_sha256']!=object_hash(cfg) or audit['sources']!=sources():raise ValueError('Frozen preflight mismatch')
    face_audit=json.loads((base/'face_audit.json').read_text())
    if face_audit['status']!='PASS' or face_audit['sources']!=sources() or face_audit['config_sha256']!=object_hash(cfg):
        raise ValueError('Stable-face development audit missing or changed')
    inputs={'preflight_sha256':digest(base/'preflight.json'),'face_audit_sha256':digest(base/'face_audit.json')}
    seeds=[cfg['development_seed']] if stage=='development' else list(range(cfg['seeds']['start'],cfg['seeds']['stop']))
    if stage=='pilot':
        benchmark=json.loads((base/'development/benchmark.json').read_text())
        if benchmark['sources']!=sources() or benchmark['config_sha256']!=object_hash(cfg):raise ValueError('Development identity mismatch')
        if not benchmark['numerical_gates_pass'] or benchmark['estimated_pilot_seconds']>cfg['compute_cap_seconds']:
            raise ValueError('Pilot NOT_RUN: development numerical/compute gate failed')
        inputs['development_benchmark_sha256']=digest(base/'development/benchmark.json')
    run=ContinuousRun(base/stage,dict(cfg,stage=stage),inputs)
    jobs=[(f,s) for s in seeds for f in cfg['families']]
    np.random.default_rng(cfg['job_order_seed']).shuffle(jobs)
    with run.session():
        payloads=[];new=0;resumed=0
        with tqdm(total=len(jobs),desc=stage,unit='case') as bar:
            for family,seed in jobs:
                key=f'{family}_{seed}';payload=run.case(key)
                if payload is None:
                    if limit and new>=limit:break
                    try:
                        payload=one_case(run.out,family,seed,cfg)
                    except Exception as exc:
                        payload={'family':family,'seed':seed,'status':'FAILED','error':repr(exc),'rows':[],'seconds':0.}
                    run.save(key,payload);new+=1
                    run.event('case_complete',family=family,seed=seed,status=payload['status'],seconds=payload['seconds'],
                              completed=len(payloads)+1,total=len(jobs),eta_seconds=(len(jobs)-len(payloads)-1)*sum(p['seconds'] for p in payloads+[payload])/(len(payloads)+1))
                else:
                    resumed+=1;run.event('case_resumed',family=family,seed=seed)
                payloads.append(payload);bar.update(1)
        rows=[r for p in payloads for r in p['rows']]
        complete=len(payloads)==len(jobs);failures=[p for p in payloads if p['status']!='COMPLETE']
        write_csv(run.out/'estimates.csv',rows)
        write_csv(run.out/'case_index.csv',[{'family':p['family'],'seed':p['seed'],'status':p['status'],'seconds':p['seconds'],
                                           'data_sha256':p.get('data_sha256'),'case_sha256':digest(run.out/'cases'/f'{p["family"]}_{p["seed"]}.json')} for p in payloads])
        atomic_json(run.out/'diagnostics.json',[{k:v for k,v in p.items() if k not in {'rows','artifacts'}} for p in payloads])
        if complete and not failures:
            summary,paired=summarize(rows,cfg,seeds)
            write_csv(run.out/'summary.csv',summary);write_csv(run.out/'paired.csv',paired)
        if stage=='development' and complete:
            gates=not failures and all(d['numerical_gate'] for p in payloads for d in p['diagnostics'].values())
            atomic_json(run.out/'benchmark.json',{'sources':sources(),'config_sha256':object_hash(cfg),
                        'numerical_gates_pass':gates,'observed_case_seconds':sum(p['seconds'] for p in payloads),
                        'estimated_pilot_seconds':sum(p['seconds'] for p in payloads)/len(payloads)*128*cfg['compute_gate_margin'],
                        'metrics_used_to_select_model_or_tau':False})
        receipt={'status':('COMPLETE' if not failures else 'INCOMPLETE_FAILED_CASES') if complete else 'PARTIAL_RESUMABLE',
                 'fingerprint':run.fingerprint,'cases_present':len(payloads),'failed_cases':len(failures),
                 'new_cases':new,'resumed_cases':resumed,'rows':len(rows),'session_seconds':time.perf_counter()-run.started,'finished_utc':utc()}
        atomic_json(run.out/'receipt.json',receipt);run.event('session_end',**receipt);print(json.dumps(receipt,indent=2))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['preflight','development','pilot']);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--replay-from',type=Path,help='Explicit same-config, same-fitter software replay, never new unseen evidence')
    parser.add_argument('--max-new-cases',type=int,default=0);args=parser.parse_args()
    if args.max_new_cases<0:parser.error('negative case limit')
    if args.stage=='preflight':
        audit=preflight(args.out,config(),args.replay_from);print(json.dumps({'scanned_files':audit['scanned_file_count'],'collisions':audit['collisions'],'replay':audit['replay']}))
    else:execute(args.stage,args.out,args.max_new_cases)


if __name__=='__main__':main()
