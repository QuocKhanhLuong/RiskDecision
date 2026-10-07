"""Q2 preflight, development selection, frozen pilot, progress and resume."""
import os
for _key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[_key]='1'

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
from selection_risk.runtime import ROOT,Run,atomic_json,digest,object_hash,utc
from continuous_cvar.evaluation import population_smooth,population_es
from .dgp import generate,laws
from .models import fit_forecasts
from .analysis import aggregate


def config():return json.loads((ROOT/'temporal_risk/config.json').read_text())


def sources():
    paths=list((ROOT/'temporal_risk').glob('*.py'))
    paths += [ROOT/p for p in ['temporal_risk/PROTOCOL.md','selection_risk/runtime.py','continuous_cvar/model.py',
                              'continuous_cvar/evaluation.py','continuous_cvar_face/model.py']]
    return {str(p.relative_to(ROOT)):digest(p) for p in sorted(paths)}


def write_csv(path,rows):
    if not rows:return
    path=Path(path);tmp=path.with_suffix(path.suffix+'.tmp')
    with tmp.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=sorted(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
    tmp.replace(path)


class TemporalRun(Run):
    def __init__(self,out,cfg,inputs):
        super().__init__(out,cfg,inputs);self.identity['sources']=sources();self.fingerprint=object_hash(self.identity)


def preflight(base):
    cfg=config();candidate=set(range(cfg['seeds']['start'],cfg['seeds']['stop']));seen=set();files={}
    for path in ROOT.rglob('*'):
        rel=path.relative_to(ROOT)
        if any(k in {'.git','.venv','__pycache__','.pytest_cache','data'} for k in rel.parts):continue
        if not path.is_file() or rel.parts[0]=='temporal_risk' or base.resolve() in path.resolve().parents:continue
        found=re.search(r'_(\d+)\.(npz|json)$',path.name)
        if found:seen.add(int(found[1]))
        if path.suffix not in {'.json','.csv','.py'} or path.stat().st_size>20_000_000:continue
        files[str(rel)]=digest(path)
        if path.suffix=='.csv':
            with path.open() as f:
                reader=csv.DictReader(f);keys=[k for k in reader.fieldnames or [] if 'seed' in k.lower()]
                if keys:
                    for row in reader:
                        for key in keys:
                            if row.get(key) and row[key].isdigit():seen.add(int(row[key]))
        elif path.suffix=='.py':
            seen.update(map(int,re.findall(r'(?<![\w.])\d+(?![\w.])',path.read_text(errors='replace'))))
        else:
            def visit(value,key=''):
                if isinstance(value,dict):
                    for k,v in value.items():visit(v,key+'.'+k)
                elif isinstance(value,list):
                    for v in value:visit(v,key)
                elif isinstance(value,int) and (key.endswith('.seed') or key.endswith('_seed')):seen.add(value)
            visit(json.loads(path.read_text()))
    collisions=sorted(candidate&seen)
    if collisions:raise ValueError(f'Fresh pilot seed collision: {collisions}')
    tracked=subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines()
    receipt={'utc':utc(),'config_sha256':object_hash(cfg),'sources':sources(),'scanned_files':files,'scanned_file_count':len(files),
             'collisions':collisions,'protected_files':{p:digest(ROOT/p) for p in tracked},
             'base_sha':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
             'candidate_seeds':sorted(candidate),'scope':'available local source/config/case/CSV; unavailable external runs not covered'}
    if (base/'preflight.json').exists():
        old=json.loads((base/'preflight.json').read_text())
        if old['sources']!=sources() or old['config_sha256']!=object_hash(cfg):raise ValueError('Changed preflight; use a separate run')
        return old
    atomic_json(base/'preflight.json',receipt);return receipt


def choose_block(cfg):
    records=[]
    for seed in cfg['development_seeds']:
        worlds=generate(seed,cfg)
        for world,data in worlds.items():
            for origin in cfg['origins']:
                y=data['returns'][origin-cfg['window']:origin].mean(axis=1)
                for label,series in [('return',y),('squared_return',y*y)]:
                    centered=series-series.mean();den=float(centered@centered)
                    acf=[float(centered[k:]@centered[:-k]/den) for k in range(1,cfg['acf_max_lag']+1)]
                    cutoff=cfg['acf_max_lag']
                    for k in range(len(acf)-cfg['acf_consecutive']+1):
                        if max(abs(a) for a in acf[k:k+cfg['acf_consecutive']])<cfg['acf_threshold']:
                            cutoff=k+1;break
                    records.append(dict(seed=seed,world=world,origin=origin,series=label,acf=acf,cutoff=cutoff))
    maximum=max(r['cutoff'] for r in records)
    block=min(b for b in cfg['block_candidates'] if b>=maximum)
    return block,records


def ensure_selection(base,cfg):
    path=base/'development_selection.json'
    if path.exists():
        old=json.loads(path.read_text())
        if old['sources']!=sources() or old['config_sha256']!=object_hash(cfg):raise ValueError('Development selection identity changed')
        return old
    block,records=choose_block(cfg)
    receipt={'utc':utc(),'sources':sources(),'config_sha256':object_hash(cfg),'block_length':block,'records':records,
             'rule':'max past-only development ACF cutoff rounded up to candidate','population_errors_used':False}
    atomic_json(path,receipt);return receipt


def one_case(run,world,seed,origin,cfg,mc,cache):
    started=time.perf_counter()
    if seed not in cache:
        generated=generate(seed,cfg);array=run.out/'paths'/f'path_{seed}.npz';array.parent.mkdir(parents=True,exist_ok=True)
        arrays={f'{w}_{k}':v for w,dd in generated.items() for k,v in dd.items()}
        if array.exists():
            with np.load(array,allow_pickle=False) as saved:
                for k,v in arrays.items():np.testing.assert_array_equal(saved[k],v)
        else:
            tmp=array.with_suffix('.tmp')
            with tmp.open('wb') as f:np.savez_compressed(f,**arrays)
            tmp.replace(array)
        cache[seed]=(generated,array,digest(array))
    worlds,array,array_sha=cache[seed];data=worlds[world]
    past=data['returns'][origin-cfg['window']:origin].copy();rng_seed=seed*10000+origin
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        locked=fit_forecasts(past,cfg['fit'],mc,rng_seed)
        # No DGP parameters/states are passed to fitting. Every estimate is now locked.
        rows=[];evaluation={}
        for policy,result in locked['policies'].items():
            diag=result['fit_diagnostics']
            if diag['convex_gap_bound']>cfg['fit']['gap_tol'] or diag.get('feasibility',0)>cfg['fit']['feasibility_tol']:
                raise ValueError(f'Optimizer gap/feasibility failed: {policy}')
            theta=np.array(result['theta']);n_fit=result['n_fit']
            conditional,marginal,latent=laws(past,world,origin,cfg,n_fit,int(data['states'][origin-1]))
            next_cost,next_quad=population_smooth(theta,conditional,mc['tau'],cfg['fit']['alpha'])
            ref_cost,ref_quad=population_smooth(theta,marginal,mc['tau'],cfg['fit']['alpha'])
            latent_cost=population_smooth(theta,latent,mc['tau'],cfg['fit']['alpha'])[0] if latent is not None else None
            true_es=population_es(theta[:-1],conditional,cfg['fit']['alpha'])[1]
            if min(next_cost,ref_cost)<=1e-10:raise ValueError('Undefined relative target near zero')
            evaluation[policy]={'conditional':{k:v.tolist() for k,v in conditional.items()},
                                'marginal':{k:v.tolist() for k,v in marginal.items()},
                                'latent':None if latent is None else {k:v.tolist() for k,v in latent.items()},
                                'conditional_quadrature':next_quad,'marginal_quadrature':ref_quad}
            for method,estimate in result['estimates'].items():
                error=None if estimate is None else estimate/next_cost-1
                ref_error=None if estimate is None else estimate/ref_cost-1
                a=None if estimate is None else (estimate-ref_cost)/next_cost;b=(ref_cost-next_cost)/next_cost
                eval_n=256 if method=='chronological' else 256-mc['block_length'] if method=='blocked_holdout' else 0
                row={'world':world,'seed':seed,'origin':origin,'period':'before' if origin<cfg['dgp']['shift_time'] else 'after',
                     'policy':policy,'method':method,'estimate':estimate,'n_fit':n_fit,'information_n':len(past),
                     'fit_start':origin-len(past),'fit_stop':origin-len(past)+n_fit,'information_stop':origin,
                     'evaluation_n':eval_n,'gap':mc['block_length'] if method=='blocked_holdout' else 0,'holding_horizon':1,
                     'threshold':float(theta[-1]),'weights':json.dumps(theta[:-1].tolist()),'hhi':float(theta[:-1]@theta[:-1]),
                     'conditional_objective':next_cost,'marginal_objective':ref_cost,'latent_objective':latent_cost,
                     'conditional_es':true_es,'conditional_signed_relative_error':error,
                     'conditional_squared_relative_error':None if error is None else error**2,
                     'marginal_signed_relative_error':ref_error,'marginal_squared_relative_error':None if ref_error is None else ref_error**2,
                     'estimation_relative':a,'mismatch_relative':b,'estimation_square':None if a is None else a*a,
                     'mismatch_square':b*b,'cross_term':None if a is None else 2*a*b,
                     'latent_information_gap':None if latent_cost is None else (latent_cost-next_cost)/next_cost}
                if error is not None and not np.isclose(a+b,error,atol=1e-12):raise ValueError('Decomposition failed')
                rows.append(row)
    return {'status':'COMPLETE','world':world,'seed':seed,'origin':origin,'rows':rows,'locked':locked,'evaluation':evaluation,
            'warnings':[str(w.message) for w in caught],'seconds':time.perf_counter()-started,
            'past_sha256':hashlib.sha256(past.tobytes()).hexdigest(),'artifacts':{str(array.relative_to(run.out)):array_sha}}


def execute(stage,base,limit=0):
    cfg=config();audit=json.loads((base/'preflight.json').read_text())
    if audit['sources']!=sources() or audit['config_sha256']!=object_hash(cfg):raise ValueError('Frozen preflight mismatch')
    selection=ensure_selection(base,cfg);mc=dict(cfg['model'],block_length=selection['block_length'])
    inputs={'preflight_sha256':digest(base/'preflight.json'),'selection_sha256':digest(base/'development_selection.json')}
    if stage=='pilot':
        benchmark=json.loads((base/'development/benchmark.json').read_text())
        if benchmark['sources']!=sources() or benchmark['config_sha256']!=object_hash(cfg):raise ValueError('Development identity changed')
        if not benchmark['numerical_gate'] or benchmark['estimated_pilot_seconds']>cfg['compute_cap_seconds']:
            raise ValueError('Pilot NOT_RUN: development numerical/compute gate failed')
        inputs['benchmark_sha256']=digest(base/'development/benchmark.json')
    seeds=cfg['development_seeds'] if stage=='development' else list(range(cfg['seeds']['start'],cfg['seeds']['stop']))
    jobs=[(w,s,o) for s in seeds for w in cfg['worlds'] for o in cfg['origins']]
    np.random.default_rng(cfg['job_order_seed']).shuffle(jobs)
    run=TemporalRun(base/stage,dict(cfg,stage=stage,effective_model=mc),inputs);cache={}
    with run.session():
        payloads=[];new=0;resumed=0
        with tqdm(total=len(jobs),desc=stage,unit='origin') as bar:
            for world,seed,origin in jobs:
                key=f'{world}_{seed}_{origin}';payload=run.case(key)
                if payload is None:
                    if limit and new>=limit:break
                    case_started=time.perf_counter()
                    try:payload=one_case(run,world,seed,origin,cfg,mc,cache)
                    except Exception as exc:payload={'status':'FAILED','world':world,'seed':seed,'origin':origin,'rows':[],'error':repr(exc),'seconds':time.perf_counter()-case_started}
                    run.save(key,payload);new+=1
                    run.event('case_complete',world=world,seed=seed,origin=origin,status=payload['status'],completed=len(payloads)+1,total=len(jobs),
                              seconds=payload['seconds'],eta_seconds=(len(jobs)-len(payloads)-1)*sum(p['seconds'] for p in payloads+[payload])/(len(payloads)+1))
                else:resumed+=1;run.event('case_resumed',world=world,seed=seed,origin=origin)
                payloads.append(payload);bar.update(1)
        rows=[r for p in payloads for r in p['rows']];complete=len(payloads)==len(jobs);failures=[p for p in payloads if p['status']!='COMPLETE']
        write_csv(run.out/'estimates.csv',rows)
        write_csv(run.out/'case_index.csv',[{k:p.get(k) for k in ['world','seed','origin','status','seconds','past_sha256','error']} for p in payloads])
        atomic_json(run.out/'diagnostics.json',[{k:v for k,v in p.items() if k not in {'rows','artifacts'}} for p in payloads])
        if complete and not failures and stage=='pilot':
            summary,paired,shift=aggregate(rows,cfg,seeds)
            write_csv(run.out/'summary.csv',summary);write_csv(run.out/'paired.csv',paired);write_csv(run.out/'shift_effect.csv',shift)
        if complete and stage=='development':
            gates=not failures and all(r['estimate'] is not None for r in rows)
            seconds=sum(p['seconds'] for p in payloads)
            atomic_json(run.out/'benchmark.json',{'sources':sources(),'config_sha256':object_hash(cfg),'numerical_gate':gates,
                        'block_length':mc['block_length'],'observed_case_seconds':seconds,'development_origins':len(jobs),
                        'estimated_pilot_seconds':seconds/len(jobs)*len(cfg['worlds'])*len(cfg['origins'])*(cfg['seeds']['stop']-cfg['seeds']['start'])*cfg['compute_gate_margin'],
                        'metrics_used_to_select_model':False})
        receipt={'status':('COMPLETE' if not failures else 'INCOMPLETE_FAILED_CASES') if complete else 'PARTIAL_RESUMABLE',
                 'cases_present':len(payloads),'failed_cases':len(failures),'new_cases':new,'resumed_cases':resumed,'rows':len(rows),
                 'fingerprint':run.fingerprint,'session_seconds':time.perf_counter()-run.started,'finished_utc':utc()}
        atomic_json(run.out/'receipt.json',receipt);run.event('session_end',**receipt);print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('stage',choices=['preflight','development','pilot'])
    parser.add_argument('--out',type=Path,required=True);parser.add_argument('--max-new-cases',type=int,default=0);args=parser.parse_args()
    if args.max_new_cases<0:parser.error('negative case limit')
    if args.stage=='preflight':
        r=preflight(args.out);print(json.dumps({k:r[k] for k in ['scanned_file_count','collisions','config_sha256']}))
    else:execute(args.stage,args.out,args.max_new_cases)
