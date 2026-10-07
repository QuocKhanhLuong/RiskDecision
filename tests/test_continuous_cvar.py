import json
from pathlib import Path

import numpy as np
import pytest
from numpy.testing import assert_allclose
from scipy.integrate import quad
from scipy.stats import norm

from continuous_cvar.model import (active_geometry, fit_empirical_lp, fit_smooth,
                                    local_influence, smooth_terms)
from continuous_cvar.evaluation import (continuous_oracle, population_es,
                                         population_hinge, population_smooth)
from selection_risk.core import legacy

CONFIG = json.loads((Path(__file__).resolve().parents[1]/"continuous_cvar/config.json").read_text())


def finite_gradient(fun, theta, eps=1e-5):
    eye = np.eye(len(theta))
    return np.array([(fun(theta+eps*e)-fun(theta-eps*e))/(2*eps) for e in eye])


def test_softplus_gradient_and_hessian_finite_differences():
    x = np.random.default_rng(921).normal(size=(80,4))
    theta = np.array([.2,.3,.2,.3,1.])
    value, grad, hessian, _, _ = smooth_terms(x,theta,.1)
    assert np.isfinite(value)
    assert_allclose(grad,finite_gradient(lambda t:smooth_terms(x,t,.1)[0],theta),rtol=1e-6,atol=1e-7)
    hd = np.column_stack([(smooth_terms(x,theta+1e-5*e,.1)[1]-smooth_terms(x,theta-1e-5*e,.1)[1])/2e-5 for e in np.eye(5)])
    assert_allclose(hessian,hd,rtol=1e-6,atol=1e-7)
    assert np.linalg.eigvalsh(hessian).min()>0


@pytest.mark.parametrize("family",["gaussian","asymmetric_crash"])
def test_solver_kkt_gap_and_active_influence(family):
    x,_ = legacy.generate(91004,family)
    fit = fit_smooth(x,.1,CONFIG)
    assert fit.diagnostics["numerical_gate"]
    assert fit.diagnostics["convex_gap_bound"] < 1e-6
    assert fit.correction >= 0
    influence = local_influence(x,fit,.1,CONFIG)
    assert_allclose(influence.mean(axis=0),0,atol=1e-10)
    c,_,_,_ = active_geometry(fit.theta,CONFIG)
    assert_allclose(c@influence.T,0,atol=1e-10)
    sample = int(np.argmax(np.linalg.norm(influence,axis=1)))
    eps = 1e-6
    p = np.full(len(x),(1-eps)/len(x));p[sample]+=eps
    perturbed = fit_smooth(x,.1,CONFIG,p=p,initial=fit.theta)
    assert perturbed.diagnostics["active_lower"] == fit.diagnostics["active_lower"]
    assert perturbed.diagnostics["active_upper"] == fit.diagnostics["active_upper"]
    assert_allclose((perturbed.theta-fit.theta)/eps,influence[sample],rtol=3e-3,atol=2e-3)


def test_projection_around_inverse_is_not_reduced_inverse():
    h = np.array([[2.,1.],[1.,2.]])
    n = np.array([[0.],[1.]])
    p = n@n.T
    correct = n@np.linalg.inv(n.T@h@n)@n.T
    bracketed = p@np.linalg.inv(h)@p
    assert correct[1,1] == pytest.approx(.5)
    assert bracketed[1,1] == pytest.approx(2/3)


def test_smoothing_lp_bracket_on_identical_feasible_set():
    x,_ = legacy.generate(91005,"asymmetric_crash")
    lp = fit_empirical_lp(x,CONFIG)
    smooth = fit_smooth(x,.1,CONFIG)
    assert lp.diagnostics["primal_residual"]<1e-8
    assert lp.diagnostics["dual_stationarity"]<1e-8
    raw_at_smooth = smooth.theta[-1]+np.maximum(-x@smooth.theta[:-1]-smooth.theta[-1],0).mean()/.05
    assert lp.objective <= raw_at_smooth+1e-9 <= smooth.objective+1e-9
    assert smooth.objective <= lp.objective+.1*np.log(2)/.05+1e-9
    assert lp.correction is None


def test_invalid_curvature_is_null_not_regularized_or_dropped():
    x=np.tile(np.arange(8)[None,:],(64,1)).astype(float)
    fit=fit_smooth(x,.1,CONFIG)
    assert not fit.diagnostics["numerical_gate"]
    assert fit.correction is None


def test_population_hinge_gradient_hessian_and_oracle():
    _,p=legacy.generate(91006,"asymmetric_crash")
    theta=np.r_[np.full(8,1/8),2.]
    _,g,h=population_hinge(theta,p)
    assert_allclose(g,finite_gradient(lambda t:population_hinge(t,p)[0],theta),atol=1e-7,rtol=1e-6)
    hd=np.column_stack([(population_hinge(theta+1e-5*e,p)[1]-population_hinge(theta-1e-5*e,p)[1])/2e-5 for e in np.eye(9)])
    assert_allclose(h,hd,atol=1e-7,rtol=1e-6)
    oracle=continuous_oracle(p,CONFIG)
    assert oracle.diagnostics['numerical_gate']
    assert oracle.objective <= population_es(theta[:-1],p)[1]+1e-9


@pytest.mark.parametrize('tau',[.05,.1,.2])
def test_population_smooth_matches_direct_integration(tau):
    _,p=legacy.generate(91006,"asymmetric_crash")
    theta=np.r_[np.full(8,1/8),2.]
    actual,receipt=population_smooth(theta,p,tau)
    w,v=theta[:-1],theta[-1]
    m=-p['mu']@w;sd=np.sqrt(np.einsum('i,kij,j->k',w,p['cov'],w))
    direct=0.
    for k,prob in enumerate(p['p']):
        # Split at the threshold so sharp smoothing is resolved by quadrature.
        z0=(v-m[k])/sd[k]
        f=lambda z:(v+tau*np.logaddexp(0,(m[k]+sd[k]*z-v)/tau)/.05)*norm.pdf(z)
        direct+=prob*(quad(f,-12,z0,epsabs=1e-10)[0]+quad(f,z0,12,epsabs=1e-10)[0])
    assert_allclose(actual,direct,atol=1e-8,rtol=1e-8)
    assert receipt['smoothing_excess']>0 and receipt['quadrature_error']<1e-8


def test_oic_does_not_change_selected_weights_or_threshold():
    x,_=legacy.generate(91007,'gaussian')
    fit=fit_smooth(x,.1,CONFIG)
    original=fit.theta.copy()
    adjusted=fit.objective+fit.correction
    assert adjusted>=fit.objective
    assert_allclose(fit.theta,original,atol=0,rtol=0)
    assert smooth_terms(x,fit.theta,.1)[0]==fit.objective


def test_continuous_csv_is_identical_after_checkpoint_key_sort(tmp_path):
    from continuous_cvar.run import write_csv
    rows=[{'z':3,'a':'gaussian','nullable':None}]
    path=tmp_path/'rows.csv';write_csv(path,rows);before=path.read_bytes()
    reloaded=json.loads(json.dumps(rows,sort_keys=True));write_csv(path,reloaded)
    assert before==path.read_bytes() and b'\r' not in before


def test_invalid_oic_makes_registered_primary_incomplete():
    from continuous_cvar.run import summarize
    cfg=dict(CONFIG,families=['gaussian'],taus=[.1],bootstrap_reps=10)
    rows=[]
    for seed in [1,2]:
        for policy in ['full512','A256','B256']:
            for method in ['raw','oic_kkt']+(['independent'] if policy!='full512' else []):
                value=None if method=='oic_kkt' and seed==2 else .1
                rows.append(dict(family='gaussian',seed=seed,tau=.1,policy=policy,estimator=method,
                                 **{k:value for k in ['signed_relative_error','absolute_relative_error','squared_relative_error','relative_regret','true_es','smoothing_gap','threshold_gap']}))
    _,paired=summarize(rows,cfg,[1,2]);primary=[r for r in paired if r['primary']]
    assert len(primary)==1 and primary[0]['status']=='INCOMPLETE' and primary[0]['mean'] is None
    with pytest.raises(ValueError,match='Missing/duplicate'):
        summarize(rows[:-1],cfg,[1,2])


def test_development_end_to_end_and_zero_refit_resume(tmp_path):
    from continuous_cvar.run import config,execute,sources
    from selection_risk.runtime import atomic_json,object_hash
    atomic_json(tmp_path/'preflight.json',{'config_sha256':object_hash(config()),'sources':sources()})
    execute('development',tmp_path)
    out=tmp_path/'development'
    before={p.name:p.read_bytes() for p in out.glob('*.csv')}
    execute('development',tmp_path)
    receipt=json.loads((out/'receipt.json').read_text())
    assert receipt['status']=='COMPLETE' and receipt['new_cases']==0 and receipt['resumed_cases']==2
    assert before=={p.name:p.read_bytes() for p in out.glob('*.csv')}


def test_seed_audit_distinguishes_registration_from_observed_case(tmp_path,monkeypatch):
    import continuous_cvar.run as runner
    monkeypatch.setattr(runner,'ROOT',tmp_path)
    monkeypatch.setattr(runner,'sources',lambda:{})
    monkeypatch.setattr(runner.subprocess,'check_output',lambda args,**kw:'' if 'ls-files' in args else 'base')
    (tmp_path/'registration.json').write_text(json.dumps({'seeds':{'start':100,'stop':102}}))
    cfg=dict(CONFIG,seeds={'start':100,'stop':102})
    receipt=runner.preflight(tmp_path/'current',cfg)
    assert receipt['collisions']==[] and receipt['registered_but_not_observed_pilot_seeds']==[100,101]
    (tmp_path/'observed.json').write_text(json.dumps({'seed':100}))
    with pytest.raises(ValueError,match='collision'):
        runner.preflight(tmp_path/'different',cfg)


def test_vertex_oracle_is_certified_without_relaxing_oic_gate():
    _,p=legacy.generate(2026107112,'asymmetric_crash')
    oracle=continuous_oracle(p,CONFIG)
    assert oracle.diagnostics['oracle_global_gap_gate']
    assert oracle.diagnostics['constraint_rank'] < oracle.diagnostics['constraint_rows']
    assert not oracle.diagnostics['numerical_gate']
    assert oracle.diagnostics['convex_gap_bound']<1e-8
