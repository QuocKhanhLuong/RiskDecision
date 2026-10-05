"""Recompute the reported quantities without refitting or changing decisions."""
from pathlib import Path
import json,hashlib,sys
import numpy as np
import pandas as pd
from scipy.stats import norm
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'results'
sys.path.insert(0,str(ROOT/'src'))
from run_pilot import population_var_es,create_population,draw_population,sanity_tests

def main():
    d=pd.read_csv(R/'all_results.csv')
    assert len(d)==480
    checked=0;maximum_error=0.
    for family in d.family.unique():
        for seed in sorted(d.seed.unique()):
            part=d[(d.family==family)&(d.seed==seed)]
            with np.load(R/f'{family}_{seed}_surfaces.npz') as a:
                W=a['weights']; p=create_population(int(seed),W.shape[1],family)
                _,truth=population_var_es(W,p,.95)
                assert np.allclose(truth,a['population_ES'],atol=1e-11)
                for _,row in part.iterrows():
                    w=row[[f'w_{j}' for j in range(W.shape[1])]].to_numpy(float)
                    _,actual=population_var_es(w[None],p,.95)
                    err=abs(actual[0]-row.true_ES);maximum_error=max(maximum_error,err)
                    assert err<1e-10
                    assert abs(actual[0]-row.predicted_ES-row.signed_underestimate)<1e-10
                    assert abs(abs(row.signed_underestimate)-row.absolute_risk_error)<1e-10
                    if row.method not in ['nominal_half_equal']:
                        ix=int(row.portfolio_index)
                        assert np.allclose(w,W[ix])
                        assert abs(row.predicted_ES-a[row.method+'_ES'][ix])<1e-10
                        if row.method!='equal_weight':assert ix==int(np.argmin(a[row.method+'_ES']))
                    checked+=1
    # Independent large-sample Monte Carlo check on the exact mixture formula.
    p=create_population(999,8,'asymmetric_crash_mixture')
    rng=np.random.default_rng(987654)
    x=draw_population(300000,rng,p)
    w=np.full((1,8),.125)
    _,es=population_var_es(w,p,.95)
    losses=-x@w[0]
    # Fractional quantile formula used directly, without RiskBank.
    v=np.quantile(losses,.95);emp=v+np.maximum(losses-v,0).mean()/.05
    assert abs(emp-es[0])<.06
    metadata={}
    for f in ['diagnostics_100_104.json','diagnostics_105_129.json']:
        metadata.update(json.loads((R/f).read_text()))
    flagged=[]
    for tag,m in metadata.items():
        assert m['gmm_base']['converged'] and m['gmm_pooled']['converged']
        for method in ['random_tail_calibration','adaptive_tail_calibration']:
            assert m[method]['dual_runs'][-1]['success']
            for step,s in enumerate(m[method]['dual_runs']):
                if not s['success']:flagged.append({'run':tag,'method':method,'step_zero_based':step,**s})
    receipt={'records_recomputed':checked,'max_population_ES_recompute_error':maximum_error,
             'exact_ES_validation':{'oracle_ES':float(es[0]),'independent_MC_ES':float(emp),'n_MC':300000},
             'all_final_dual_solves_report_convergence':True,'intermediate_solver_flags':flagged,
             'all_GMM_fits_converged':True,'sanity':sanity_tests(),
             'note':'Internal code/arithmetic audit, not independent scientific peer review.',
             'files':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(R.glob('*.csv'))}}
    (R/'audit_receipt.json').write_text(json.dumps(receipt,indent=2))
    print(json.dumps({k:v for k,v in receipt.items() if k!='files'},indent=2))
if __name__=='__main__':main()
