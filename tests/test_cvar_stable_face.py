import json
from pathlib import Path

import numpy as np
import pytest
from numpy.testing import assert_allclose,assert_array_equal
from scipy.linalg import null_space
from scipy.optimize import minimize

from continuous_cvar.model import active_geometry,fit_smooth as original_fit,smooth_terms
from continuous_cvar_face.model import correct_locked,face_geometry,fit_smooth,local_influence
from selection_risk.core import legacy

CFG=json.loads((Path(__file__).resolve().parents[1]/'continuous_cvar_face/config.json').read_text())


def vertex_fixture():
    x=np.random.default_rng(99344).normal(size=(512,8))
    x[:,2:]-=5
    return x


def test_redundant_vertex_has_positive_certificate_and_threshold_only_if():
    x=vertex_fixture();old=original_fit(x,.1,CFG);fit=correct_locked(x,old,.1,CFG)
    assert not old.diagnostics['numerical_gate']
    assert fit.diagnostics['numerical_gate'] and fit.diagnostics['face_margin']>0
    assert fit.diagnostics['face_dimension']==1
    assert_array_equal(old.theta,fit.theta)
    assert old.objective==fit.objective
    _,_,h,scores,_=smooth_terms(x,fit.theta,.1)
    influence=local_influence(x,fit,.1,CFG)
    assert_array_equal(influence[:,:-1],np.zeros((len(x),8)))
    assert_allclose(fit.correction,np.mean(scores[:,-1]**2)/(len(x)*h[-1,-1]),rtol=1e-12)


@pytest.mark.parametrize('seed',[2026107101,2026107106,2026107154,2026107158])
def test_old_seen_vertex_is_development_regression_only(seed):
    x,_=legacy.generate(seed,'asymmetric_crash')
    old=original_fit(x,.1,CFG);fit=correct_locked(x,old,.1,CFG)
    assert not old.diagnostics['numerical_gate'] and fit.diagnostics['numerical_gate']
    assert_array_equal(fit.theta,old.theta)


@pytest.mark.parametrize('kind',['vertex','nonvertex'])
def test_face_operator_invariant_to_duplicate_rescaled_reordered_normals(kind):
    theta=np.r_[[.5,.5,0.,0.],1.] if kind=='vertex' else np.r_[[.5,.3,.2,0.],1.]
    gradient=np.array([-1.,-1.,1.,1.,0.]) if kind=='vertex' else np.array([-1.,0.,0.,1.,0.])
    a=np.random.default_rng(335).normal(size=(5,5));h=a.T@a+np.eye(5)
    diag,n,r=face_geometry(theta,gradient,h,CFG)
    assert diag['numerical_gate']
    operator=n@np.linalg.solve(r,n.T)
    c,*_=active_geometry(theta,CFG)
    redundant=np.vstack([c,c[::-1]*np.arange(1,len(c)+1)[:,None]])
    other=null_space(redundant)
    assert_allclose(operator,other@np.linalg.solve(other.T@h@other,other.T),atol=1e-12)


@pytest.mark.parametrize('eps',[1e-5,1e-6])
@pytest.mark.parametrize('family',['vertex','gaussian','asymmetric_crash'])
def test_two_sided_sample_probability_derivative(family,eps):
    x=vertex_fixture() if family=='vertex' else legacy.generate(2026107998,family)[0]
    fit=fit_smooth(x,.1,CFG);influence=local_influence(x,fit,.1,CFG)
    i=int(np.argmax(np.linalg.norm(influence,axis=1)));direction=-np.ones(len(x))/len(x);direction[i]+=1
    plus=fit_smooth(x,.1,CFG,p=np.ones(len(x))/len(x)+eps*direction,initial=fit.theta)
    minus=fit_smooth(x,.1,CFG,p=np.ones(len(x))/len(x)-eps*direction,initial=fit.theta)
    for changed in [plus,minus]:
        assert changed.diagnostics['numerical_gate']
        assert changed.diagnostics['face_free_weights']==fit.diagnostics['face_free_weights']
    assert_allclose((plus.theta-minus.theta)/(2*eps),influence[i],rtol=.004,atol=.002)


def test_weak_face_is_rejected_and_directional_derivative_is_not_linear():
    theta=np.array([.5,.5,0.,0.,0.]);g=np.array([0.,0.,0.,1.,0.]);h=np.eye(5)
    diag,_,_=face_geometry(theta,g,h,CFG)
    assert diag['face_margin']==0 and not diag['numerical_gate']
    a=np.array([1.,0.,-1.,0.,0.]);eps=1e-4
    def solve(sign):
        result=minimize(lambda t:(.5*np.sum((t-theta)**2)+(g+sign*eps*a)@t,t-theta+g+sign*eps*a),
                        theta,jac=True,bounds=[(0,.5)]*4+[(-50,50)],
                        constraints={'type':'eq','fun':lambda t:t[:-1].sum()-1,'jac':lambda t:np.r_[np.ones(4),0.]},
                        method='SLSQP',options={'ftol':1e-14,'maxiter':100})
        assert result.success
        return (result.x-theta)/eps
    assert np.linalg.norm(solve(1)+solve(-1))>.5


def test_small_margin_and_singular_curvature_stay_invalid():
    theta=np.array([.5,.5,0.,0.,0.])
    assert not face_geometry(theta,np.array([0.,0.,1e-6,1.,0.]),np.eye(5),CFG)[0]['numerical_gate']
    assert not face_geometry(theta,np.array([0.,0.,1.,1.,0.]),np.zeros((5,5)),CFG)[0]['numerical_gate']


def test_existing_valid_correction_is_preserved_without_refit_change():
    x,_=legacy.generate(2026107998,'gaussian')
    old=original_fit(x,.1,CFG);fit=fit_smooth(x,.1,CFG)
    assert old.diagnostics['numerical_gate'] and fit.diagnostics['numerical_gate']
    assert_array_equal(old.theta,fit.theta)
    assert_allclose(old.correction,fit.correction,atol=1e-12)


def test_face_runner_requires_audit_and_resumes_without_refit(tmp_path):
    from continuous_cvar_face.run import config,execute,sources
    from selection_risk.runtime import atomic_json,object_hash
    identity={'config_sha256':object_hash(config()),'sources':sources()}
    atomic_json(tmp_path/'preflight.json',identity)
    with pytest.raises(FileNotFoundError):execute('development',tmp_path)
    atomic_json(tmp_path/'face_audit.json',dict(identity,status='FAIL'))
    with pytest.raises(ValueError,match='audit'):execute('development',tmp_path)
    atomic_json(tmp_path/'face_audit.json',dict(identity,status='PASS',scope='test fixture'))
    execute('development',tmp_path)
    out=tmp_path/'development';before={p.name:p.read_bytes() for p in out.glob('*.csv')}
    execute('development',tmp_path)
    receipt=json.loads((out/'receipt.json').read_text())
    assert receipt['new_cases']==0 and receipt['resumed_cases']==2
    assert before=={p.name:p.read_bytes() for p in out.glob('*.csv')}


def test_face_null_preserves_primary_incomplete():
    from continuous_cvar_face.run import summarize
    cfg=dict(CFG,families=['gaussian'],taus=[.1],bootstrap_reps=10)
    rows=[]
    for seed in [1,2]:
        for policy in ['full512','A256','B256']:
            for method in ['raw','oic_face']+(['independent'] if policy!='full512' else []):
                value=None if method=='oic_face' and seed==2 else .1
                rows.append(dict(family='gaussian',seed=seed,tau=.1,policy=policy,estimator=method,
                                 **{k:value for k in ['signed_relative_error','absolute_relative_error','squared_relative_error','relative_regret','true_es','smoothing_gap','threshold_gap']}))
    _,paired=summarize(rows,cfg,[1,2]);primary=[r for r in paired if r['primary']]
    assert len(primary)==1 and primary[0]['status']=='INCOMPLETE' and primary[0]['mean'] is None


def test_face_preflight_rejects_previously_observed_seed(tmp_path,monkeypatch):
    import continuous_cvar_face.run as runner
    monkeypatch.setattr(runner,'ROOT',tmp_path)
    monkeypatch.setattr(runner,'sources',lambda:{})
    monkeypatch.setattr(runner.subprocess,'check_output',lambda args,**kw:'' if 'ls-files' in args else 'base')
    (tmp_path/'observed.json').write_text(json.dumps({'seed':101}))
    with pytest.raises(ValueError,match='collision'):
        runner.preflight(tmp_path/'new',dict(CFG,seeds={'start':100,'stop':102}))
