import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
from numpy.testing import assert_allclose
from scipy.stats import norm
from research import bank,Risk,generate,truth,entropy_solve,filter_returns,calibrate,CFG

def test_weights():
    w=bank(42);assert w.shape==(285,8);assert w.min()>=0;assert w.max()<=.5+1e-12;assert_allclose(w.sum(1),1)
def test_bank_deterministic():assert_allclose(bank(42),bank(42))
def test_bank_seed_changes():assert not np.allclose(bank(42),bank(43))
def test_splits_disjoint():assert not set(CFG['validation_seeds'])&set(CFG['test_seeds'])
def test_cvar_fractional_atom():
    z=-np.array([[0.],[1.],[2.],[10.]])
    v,e=Risk(z,np.array([[1.]])).eval(q=.6)
    assert_allclose(v,[2.]);assert_allclose(e,[(.15*2+.25*10)/.4])
def test_weighted_cvar_atoms():
    z=-np.array([[0.],[1.],[2.],[10.]])
    v,e=Risk(z,np.array([[1.]])).eval(np.array([.1,.2,.4,.3]),q=.8)
    assert_allclose(v,[10.]);assert_allclose(e,[10.])
def test_weighted_cvar_uniform():
    z=np.random.default_rng(1).normal(size=(31,8));w=bank(1);r=Risk(z,w)
    assert_allclose(r.eval()[1],r.eval(np.ones(31)/31)[1])
def test_translation_equivariance():
    z=np.random.default_rng(1).normal(size=(100,8));w=bank(1)
    assert_allclose(Risk(z+1,w).eval()[1],Risk(z,w).eval()[1]-1)
def test_positive_scale():
    z=np.random.default_rng(1).normal(size=(100,8));w=bank(1)
    assert_allclose(Risk(z*2,w).eval()[1],Risk(z,w).eval()[1]*2)
def test_gaussian_truth():
    x,p=generate(25,'gaussian');w=bank(25);v,e=truth(w,p);s=np.sqrt(np.einsum('ij,jk,ik->i',w,p['cov'][0],w))
    assert_allclose(v,norm.ppf(.95)*s);assert_allclose(e,norm.pdf(norm.ppf(.95))/.05*s)
def test_truth_finite_all_families():
    for f in CFG['families']:
        x,p=generate(81,f);v,e=truth(bank(81),p);assert x.shape==(512,8);assert np.isfinite(x).all();assert np.isfinite(e).all();assert (e>=v).all()
def test_generation_deterministic():
    for f in CFG['families']:assert_allclose(generate(4,f)[0],generate(4,f)[0])
def test_entropy_no_correction_inside_band():
    r=np.random.default_rng(5);A=r.normal(size=(50,3));p=np.ones(50)/50;B=A.T@p+np.array([.3,-.4,.2]);out,ok=entropy_solve(A,B,p,band=1)
    assert ok;assert_allclose(out,p,atol=1e-7)
def test_entropy_simplex():
    r=np.random.default_rng(5);A=r.normal(size=(50,3));p=np.ones(50)/50
    for b in [0,1]:
        out,ok=entropy_solve(A,np.array([.5,-.8,1.7]),p,band=b);assert ok;assert np.all(out>0);assert_allclose(out.sum(),1)
def test_entropy_moment_fit_improves():
    A=np.linspace(-1,1,100)[:,None];p=np.ones(100)/100;B=np.array([.7]);out,ok=entropy_solve(A,B,p,band=0);assert abs((A.T@out-B)[0])<abs((A.T@p-B)[0])
def test_filter_no_future_in_prefix():
    x=np.random.default_rng(3).normal(size=(120,8));y=x.copy();y[100:]+=100
    a,va=filter_returns(x);b,vb=filter_returns(y);assert_allclose(a[:50],b[:50]);assert not np.allclose(va,vb)
def test_filter_zero_finite():
    r,v=filter_returns(np.zeros((100,8)));assert np.isfinite(r).all();assert np.isfinite(v).all()
def test_population_parameters_separate_from_training():
    import inspect,research
    src=inspect.getsource(research.one);before=src.split('tv,te=truth')[0]
    assert 'pars[' not in before and 'truth(' not in before
