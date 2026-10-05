from pathlib import Path
import json
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parents[1]/'results'
df=pd.concat([pd.read_csv(R/'raw_100_104.csv'),pd.read_csv(R/'raw_105_129.csv')],ignore_index=True)
assert len(df)==30*2*8
assert not df.duplicated(['family','seed','method']).any()
df.to_csv(R/'all_results.csv',index=False)
metrics=['predicted_ES','true_ES','signed_underestimate','absolute_risk_error','relative_underestimate_pct','regret_vs_candidate_oracle','fixed_equal_signed_error','selection_excess_error','hhi']
s=df.groupby(['family','method'])[metrics].agg(['mean','std'])
s.to_csv(R/'summary.csv')
print(s[[('predicted_ES','mean'),('true_ES','mean'),('signed_underestimate','mean'),('absolute_risk_error','mean'),('selection_excess_error','mean'),('hhi','mean')]].round(4).to_string())
rng=np.random.default_rng(98765);B=10000;res=[]
for fam in df.family.unique():
 z=df[df.family==fam]
 for control in ['GMM_base','GMM_pooled','historical_CVaR','LedoitWolf_Gaussian','random_tail_calibration','nominal_half_equal']:
  a=z[z.method=='adaptive_tail_calibration'].set_index('seed').sort_index()
  b=z[z.method==control].set_index('seed').sort_index()
  for metric in ['true_ES','absolute_risk_error','signed_underestimate','hhi']:
   d=(a[metric]-b[metric]).values
   boot=d[rng.integers(0,len(d),(B,len(d)))].mean(axis=1)
   res.append({'family':fam,'reference':control,'metric':metric,'paired_difference':float(d.mean()),'CI_low':float(np.quantile(boot,.025)),'CI_high':float(np.quantile(boot,.975)),'n':len(d)})
pd.DataFrame(res).to_csv(R/'paired_CI.csv',index=False)
print('\nPAIRED candidate minus baseline\n',pd.DataFrame(res).round(4).to_string(index=False))
meta={}
for f in [R/'diagnostics_100_104.json',R/'diagnostics_105_129.json']:meta.update(json.loads(f.read_text()))
print('FIT CONVERGENCE',sum(not m[k]['converged'] for m in meta.values() for k in ['gmm_base','gmm_pooled']))
print('DUAL FAILS',sum(not s['success'] for m in meta.values() for k in ['random_tail_calibration','adaptive_tail_calibration'] for s in m[k]['dual_runs']))
print('TOTAL SEED WALL',sum(m['wall_seconds'] for m in meta.values()))
print('ESS means',[(k,np.mean([m[k]['ess'] for m in meta.values()])) for k in ['random_tail_calibration','adaptive_tail_calibration']])
