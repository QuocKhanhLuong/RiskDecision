import copy
import itertools
import json
from pathlib import Path

import numpy as np
import pytest
from numpy.testing import assert_allclose,assert_array_equal
from scipy.stats import multivariate_normal

from temporal_risk.dgp import generate,parameters,transition,marginal_probs,filtered_next,laws
from temporal_risk.models import hac_covariance,block_indices,fit_forecasts,statistical_models

CFG=json.loads((Path(__file__).resolve().parents[1]/'temporal_risk/config.json').read_text())
MC=dict(CFG['model'],block_length=16,bootstrap_refits=2)


def test_coupled_worlds_identical_until_transition_break_and_reproducible():
    a=generate(CFG['development_seeds'][0],CFG);b=generate(CFG['development_seeds'][0],CFG)
    shift=CFG['dgp']['shift_time']
    for world in a:
        for key in a[world]:assert_array_equal(a[world][key],b[world][key])
    assert_array_equal(a['markov_stationary']['returns'][:shift],a['markov_shift']['returns'][:shift])
    assert_array_equal(a['markov_stationary']['states'][:shift],a['markov_shift']['states'][:shift])
    assert not np.array_equal(a['markov_stationary']['returns'][shift:],a['markov_shift']['returns'][shift:])
    assert_array_equal(transition('markov_shift',shift-1,CFG),np.array(CFG['dgp']['transition0']))
    assert_array_equal(transition('markov_shift',shift,CFG),np.array(CFG['dgp']['transition1']))


def test_forward_filter_matches_exhaustive_enumeration_and_ignores_hidden_state():
    cfg=copy.deepcopy(CFG);cfg['dgp']['shift_time']=2
    past=generate(2026108998,cfg)['markov_shift']['returns'][:4]
    _,_,mu,cov=parameters(cfg);initial=marginal_probs('markov_shift',1,cfg)[0]
    probabilities=np.zeros(2)
    for states in itertools.product([0,1],repeat=len(past)):
        prob=initial[states[0]]
        for t,state in enumerate(states):
            if t:prob*=transition('markov_shift',t,cfg)[states[t-1],state]
            prob*=multivariate_normal.pdf(past[t],mean=mu[state],cov=cov[state])
        probabilities[states[-1]]+=prob
    expected=(probabilities/probabilities.sum())@transition('markov_shift',len(past),cfg)
    assert_allclose(filtered_next(past,'markov_shift',0,cfg),expected,rtol=1e-11,atol=1e-12)
    c0,_,l0=laws(past,'markov_shift',4,cfg,4,0)
    c1,_,l1=laws(past,'markov_shift',4,cfg,4,1)
    assert_array_equal(c0['p'],c1['p']);assert not np.array_equal(l0['p'],l1['p'])


def test_marginal_and_ar_conditional_laws_have_correct_timing():
    x=generate(2026108998,CFG)['ar1_stationary']['returns'][:512]
    cond,ref,latent=laws(x,'ar1_stationary',512,CFG,512,-1)
    mu,cov,_,_=parameters(CFG);phi=CFG['dgp']['phi']
    assert_allclose(cond['mu'][0],mu+phi*(x[-1]-mu))
    assert_allclose(cond['cov'][0],(1-phi**2)*cov)
    assert_allclose(ref['mu'][0],mu);assert_allclose(ref['cov'][0],cov);assert latent is None
    p=marginal_probs('markov_stationary',961,CFG)
    assert_allclose(p,np.broadcast_to(p[0],p.shape),atol=1e-13)
    q=marginal_probs('markov_shift',961,CFG)
    assert_allclose(q[:768],p[:768]);assert q[768,1]>q[767,1]


@pytest.mark.parametrize('lag',[0,1,7,31])
def test_hac_matches_dense_bartlett_kernel_and_is_psd(lag):
    x=np.random.default_rng(501).normal(size=(64,5));centered=x-x.mean(axis=0)
    index=np.arange(len(x));kernel=np.maximum(1-np.abs(index[:,None]-index)/(lag+1),0)
    expected=centered.T@kernel@centered/len(x);actual=hac_covariance(x,lag)
    assert_allclose(actual,expected,atol=1e-12)
    assert np.linalg.eigvalsh(actual).min()>-1e-10
    if lag==0:assert_allclose(actual,np.cov(x,rowvar=False,bias=True))


def test_circular_block_indices_preserve_order_inside_each_block():
    index=block_indices(63,8,np.random.default_rng(911))
    assert len(index)==63 and np.min(index)>=0 and np.max(index)<63
    for i in range(0,63,8):assert_array_equal(index[i:min(i+8,63)],(index[i]+np.arange(min(8,63-i)))%63)
    assert_array_equal(index,block_indices(63,8,np.random.default_rng(911)))


def test_past_only_forecasts_deterministic_and_common_decisions():
    data=generate(2026108998,CFG);past=data['ar1_stationary']['returns'][:512].copy()
    a=fit_forecasts(past,CFG['fit'],MC,120)
    data['ar1_stationary']['returns'][512:]=1e6;data['ar1_stationary']['states'][:]=-99
    b=fit_forecasts(past,CFG['fit'],MC,120)
    assert a==b
    for policy,result in a['policies'].items():
        assert all(v is not None and np.isfinite(v) for v in result['estimates'].values())
        assert np.isclose(sum(result['theta'][:-1]),1)
        assert len(result['theta'])==9
        assert result['n_fit']==(256 if policy=='older256' else 512)
    assert_array_equal(a['policies']['equal512']['theta'][:-1],np.full(8,.125))


def test_statistical_ar_is_estimated_from_past_and_has_no_oracle_argument():
    past=generate(2026108998,CFG)['ar1_stationary']['returns'][:512]
    models,diag=statistical_models(past,MC)
    assert len(diag['ar_phi'])==8 and not np.allclose(diag['ar_phi'],CFG['dgp']['phi'])
    for p in models.values():assert np.linalg.eigvalsh(p['cov'][0]).min()>0
    changed=past.copy();changed[-1]+=1
    other,_=statistical_models(changed,MC)
    assert not np.allclose(models['ar_gaussian']['mu'],other['ar_gaussian']['mu'])


def test_block_selection_only_uses_development_past_acfs():
    from temporal_risk.run import choose_block
    cfg=copy.deepcopy(CFG);cfg['development_seeds']=cfg['development_seeds'][:1];cfg['origins']=[512]
    b,records=choose_block(cfg)
    assert b in cfg['block_candidates'] and len(records)==6
    assert all(r['seed']==cfg['development_seeds'][0] for r in records)
    assert b>=max(r['cutoff'] for r in records)


def test_case_decomposition_and_path_cluster_missing_cell_gate(tmp_path):
    from temporal_risk.run import TemporalRun,one_case
    from temporal_risk.analysis import aggregate
    cfg=copy.deepcopy(CFG);cfg['origins']=[512,768];cfg['bootstrap_reps']=20
    run=TemporalRun(tmp_path,cfg,{})
    payload=one_case(run,'ar1_stationary',2026108998,512,cfg,MC,{})
    assert len(payload['rows'])==22
    for row in payload['rows']:
        assert_allclose(row['estimation_relative']+row['mismatch_relative'],row['conditional_signed_relative_error'],atol=1e-12)
        assert_allclose(row['estimation_square']+row['mismatch_square']+row['cross_term'],row['conditional_squared_relative_error'],atol=1e-12)
        assert row['information_stop']==512 and row['holding_horizon']==1
    with pytest.raises(ValueError,match='Missing evaluation'):aggregate(payload['rows'],cfg,[2026108998])


def test_preflight_rejects_seen_seed(tmp_path,monkeypatch):
    import temporal_risk.run as runner
    cfg=copy.deepcopy(CFG);cfg['seeds']={'start':100,'stop':102}
    monkeypatch.setattr(runner,'ROOT',tmp_path);monkeypatch.setattr(runner,'config',lambda:cfg)
    monkeypatch.setattr(runner,'sources',lambda:{})
    (tmp_path/'observed.json').write_text(json.dumps({'seed':100}))
    with pytest.raises(ValueError,match='collision'):runner.preflight(tmp_path/'out')


def test_primary_aggregates_paths_and_retains_a_null_in_any_origin():
    from temporal_risk.analysis import aggregate
    cfg=copy.deepcopy(CFG);cfg['origins']=[512,768];cfg['bootstrap_reps']=30
    common=['raw','iid_oic','hac','gaussian_iid','ar_gaussian','ewma_gaussian'];rows=[]
    metrics=['conditional_signed_relative_error','conditional_squared_relative_error','marginal_signed_relative_error',
             'marginal_squared_relative_error','estimation_relative','mismatch_relative','estimation_square','mismatch_square',
             'cross_term','conditional_es','hhi','latent_information_gap']
    for world in cfg['worlds']:
        for seed in [1,2]:
            for origin in cfg['origins']:
                for policy in ['full512','equal512','older256']:
                    for method in common+(['block_bootstrap'] if policy!='older256' else ['chronological','blocked_holdout']):
                        v=(seed+1)*(1 if origin==512 else 3) if method=='ar_gaussian' else 0.
                        rows.append(dict(world=world,seed=seed,origin=origin,policy=policy,method=method,**{m:v for m in metrics}))
    _,paired,_=aggregate(rows,cfg,[1,2]);primary=[r for r in paired if r['primary']][0]
    assert primary['n_clusters']==2 and primary['mean']==5.
    rows[0]['conditional_squared_relative_error']=None
    # Specifically null the comparator in the registered primary at one origin.
    for row in rows:
        if (row['world'],row['seed'],row['origin'],row['policy'],row['method'])==('ar1_stationary',1,512,'full512','iid_oic'):
            row['conditional_squared_relative_error']=None
    _,paired,_=aggregate(rows,cfg,[1,2]);primary=[r for r in paired if r['primary']][0]
    assert primary['status']=='INCOMPLETE' and primary['mean'] is None
    with pytest.raises(ValueError,match='Missing evaluation'):
        aggregate([r for r in rows if r['method']!='ar_gaussian'],cfg,[1,2])
