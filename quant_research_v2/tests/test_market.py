import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
from numpy.testing import assert_allclose
import pytest
from market_data import *

def test_ecb_inversion_fixture_only():
    raw=('Date,'+','.join(ECB_COLS)+'\n2020-01-01,'+','.join(['2']*8)+'\n2020-01-02,'+','.join(['4']*8)+'\n').encode()
    dates,x,cols=parse_ecb_csv(raw);assert_allclose(x[0],.5);assert_allclose(x[1],.25);assert_allclose(returns_pp(x),-50)
def test_boc_units_fixture_only():
    obj={'observations':[{'d':'2020-01-01',**{'FX'+c+'CAD':{'v':'1.2'} for c in BOC_COLS}}]}
    dates,x,cols=parse_boc_json(json.dumps(obj).encode());assert_allclose(x,1.2)
def test_duplicate_rejected():
    with pytest.raises(ValueError):validate_points([('2020-01-01',np.ones(8)),('2020-01-01',np.ones(8))],ECB_COLS)
def test_missing_not_filled():
    raw=('Date,'+','.join(ECB_COLS)+'\n2020-01-01,NA,'+','.join(['2']*7)+'\n').encode()
    with pytest.raises(ValueError):parse_ecb_csv(raw)
def test_cutoff():
    raw=('Date,'+','.join(ECB_COLS)+'\n2020-01-01,'+','.join(['2']*8)+'\n2026-01-02,'+','.join(['4']*8)+'\n').encode()
    dates,x,c=parse_ecb_csv(raw);assert len(dates)==1
def test_forecast_window_excludes_future_and_gap():
    a=np.arange(600*8).reshape(600,8);b=a.copy();b[550:]=-999
    assert_allclose(past_window(a,551),past_window(b,551));assert_allclose(past_window(a,551)[-1],a[549])
def test_invalid_prices():
    with pytest.raises(ValueError):returns_pp(np.array([[1.,0.],[1.,1.]]))
def test_market_forecast_fixture_no_truth():
    from run_market_risk import evaluate_window
    from research import bank
    x=np.random.default_rng(900).normal(0,1,(512,8));y=np.zeros(8)
    out=evaluate_window(x,y,bank(900),901);assert len(out)==10
    assert all(r['realized_loss']==0 for r in out);assert all(np.isfinite(r['es95']) for r in out)
