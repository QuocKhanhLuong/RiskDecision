import numpy as np
import pytest
from scipy.integrate import quad
from scipy.stats import norm
from tail_band_audit.core import normal_hinge_moments, radii, dkw_es, weighted_es_sorted, clipped_normal_es
from coverage_audit.core import multiplier
from tail_band_audit.analyze import group_summary


@pytest.mark.parametrize("eta", [-2., 0., 1.644853626951, 4.])
def test_analytic_moments_against_quadrature(eta):
    sd = 1.3
    mean,var = normal_hinge_moments(np.array([eta]), np.array([sd]))
    m = quad(lambda x:(x-eta)*norm.pdf(x,scale=sd),eta,np.inf,epsabs=1e-12)[0]
    second = quad(lambda x:(x-eta)**2*norm.pdf(x,scale=sd),eta,np.inf,epsabs=1e-12)[0]
    np.testing.assert_allclose(mean,m,atol=1e-11,rtol=1e-10)
    np.testing.assert_allclose(var,second-m*m,atol=1e-11,rtol=1e-10)


def test_plugin_matches_frozen_multiplier_and_oracle_changes_only_width():
    h = np.maximum(np.random.default_rng(22).normal(size=(256,9))-1,0)
    exact = np.linspace(.01,.1,9); scale = np.linspace(.5,2,9)
    g = np.random.default_rng(27).normal(size=(499,256))
    rr,se,c = radii(h,exact,scale,g)
    old,cc,_ = multiplier(h,1,499,27)
    np.testing.assert_allclose(rr['plugin_max_t'],old,atol=1e-12,rtol=0)
    assert c == pytest.approx(cc)
    np.testing.assert_allclose(rr['oracle_width_swap'],c*exact)
    changed,_,_ = radii(h,exact*2,scale,g)
    np.testing.assert_array_equal(rr['fixed_scale_max'],changed['fixed_scale_max'])
    np.testing.assert_array_equal(rr['plugin_max_t'],changed['plugin_max_t'])


def test_zero_plugin_feature_retained_but_fixed_scale_can_expand():
    h = np.column_stack([np.zeros(32),np.arange(32.)])
    rr,se,_ = radii(h,np.ones(2),np.ones(2),np.random.default_rng(4).normal(size=(99,32)))
    assert se[0] == 0 and rr['plugin_max_t'][0] == 0
    assert rr['oracle_width_swap'][0] > 0 and rr['fixed_scale_max'][0] > 0


def test_weighted_es_partial_atom_and_invalid_weights():
    es = weighted_es_sorted(np.array([0,1,3,11]),np.array([.99,0,0,.01]))
    assert es[0] == pytest.approx(2.2)
    with pytest.raises(ValueError):
        weighted_es_sorted(np.array([0,1]),np.array([.5,.3]))


def test_dkw_known_support_saturation_and_mass_transfer():
    x = np.full((256,285),.2); low=np.zeros(285); high=np.ones(285)
    lo,hi,eps=dkw_es(x,low,high)
    assert eps > .05
    np.testing.assert_allclose(hi,1,atol=1e-12)
    np.testing.assert_allclose(lo,.2,atol=1e-12)
    lo,hi,eps=dkw_es(np.full((4096,2),.2),np.zeros(2),np.ones(2))
    assert eps < .05
    np.testing.assert_allclose(hi,.2+eps/.05*.8,atol=1e-12)
    np.testing.assert_allclose(lo,.2,atol=1e-12)
    with pytest.raises(ValueError,match='bounds'):
        dkw_es(np.ones((16,2))*2,np.zeros(2),np.ones(2))


def test_clipped_es_population_integral():
    sd=np.array([.8,1.2]); eta=norm.ppf(.95)
    target=(quad(lambda z:z*norm.pdf(z),eta,3)[0]+3*norm.sf(3))/.05
    np.testing.assert_allclose(clipped_normal_es(sd),sd*target,atol=1e-12)


def test_duplicate_seed_aggregation_rejected():
    r={'n':256,'seed':1}
    with pytest.raises(ValueError,match='duplicated'):
        group_summary([r,r],['n'],[],[],2)
