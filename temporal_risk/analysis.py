"""Path-cluster summaries: overlapping origins never become independent units."""
import numpy as np


def interval(values,cfg):
    x=np.asarray(values,dtype=float)
    ix=np.random.default_rng(cfg['bootstrap_seed']).integers(len(x),size=(cfg['bootstrap_reps'],len(x)))
    low,high=np.quantile(x[ix].mean(axis=1),[.025,.975])
    return float(x.mean()),float(low),float(high)


def selected_origins(cfg,period):
    return [o for o in cfg['origins'] if period=='all' or (o<cfg['dgp']['shift_time'])==(period=='before')]


def aggregate(rows,cfg,seeds):
    lookup={(r['world'],r['seed'],r['origin'],r['policy'],r['method']):r for r in rows}
    if len(lookup)!=len(rows):raise ValueError('Duplicate evaluation cell')
    common=['raw','iid_oic','hac','gaussian_iid','ar_gaussian','ewma_gaussian']
    methods={'full512':sorted(common+['block_bootstrap']),'equal512':sorted(common+['block_bootstrap']),
             'older256':sorted(common+['chronological','blocked_holdout'])}
    expected={(w,s,o,p,m) for w in cfg['worlds'] for s in seeds for o in cfg['origins'] for p,mm in methods.items() for m in mm}
    if set(lookup)!=expected:raise ValueError('Missing evaluation cell or unexpected cell')
    summaries=[];paired=[];shift=[]
    def values(world,policy,method,metric,origins):
        result=[]
        for seed in seeds:
            cells=[]
            for origin in origins:
                key=(world,seed,origin,policy,method)
                if key not in lookup:raise ValueError('Missing evaluation cell')
                value=lookup[key][metric]
                if value is None:return None
                cells.append(value)
            result.append(np.mean(cells))
        return np.array(result)
    def stats(x):
        mean,lo,hi=interval(x,cfg) if x is not None else (None,None,None)
        return {'mean':mean,'ci_low':lo,'ci_high':hi,'status':'COMPLETE' if x is not None else 'INCOMPLETE','n_clusters':len(seeds)}
    for world in cfg['worlds']:
        for policy,estimators in methods.items():
            for period in ['all','before','after']:
                origins=selected_origins(cfg,period)
                metrics=['conditional_signed_relative_error','conditional_squared_relative_error',
                         'marginal_signed_relative_error','marginal_squared_relative_error',
                         'estimation_relative','mismatch_relative','estimation_square','mismatch_square','cross_term',
                         'conditional_es','hhi','latent_information_gap']
                cache={}
                for method in estimators:
                    for metric in metrics:
                        v=values(world,policy,method,metric,origins);cache[method,metric]=v
                        item=dict(world=world,policy=policy,period=period,method=method,metric=metric,**stats(v))
                        if metric=='latent_information_gap' and world=='ar1_stationary':item['status']='NOT_APPLICABLE'
                        summaries.append(item)
                for method in estimators:
                    for baseline in ['raw','iid_oic']:
                        if method==baseline:continue
                        for target in ['conditional','marginal']:
                            for metric in ['signed_relative_error','squared_relative_error']:
                                a,b=cache[method,target+'_'+metric],cache[baseline,target+'_'+metric]
                                delta=a-b if a is not None and b is not None else None
                                key=dict(world=world,policy=policy,period=period,method=method,baseline=baseline,target=target,metric=metric)
                                paired.append(dict(key,primary=all(key[k]==v for k,v in cfg['primary'].items()),**stats(delta)))
    for policy,estimators in methods.items():
        for period in ['all','before','after']:
            origins=selected_origins(cfg,period)
            for method in estimators:
                for target in ['conditional','marginal']:
                    metric=target+'_squared_relative_error'
                    a=values('markov_shift',policy,method,metric,origins)
                    b=values('markov_stationary',policy,method,metric,origins)
                    shift.append(dict(policy=policy,period=period,method=method,metric=metric,
                                      interpretation='coupled pipeline shift effect, not same portfolio across worlds',
                                      **stats(a-b if a is not None and b is not None else None)))
    return summaries,paired,shift
