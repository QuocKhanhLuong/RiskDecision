import time,json
import numpy as np
from research import ROOT,generate,bank,Risk,gmm,calibrate
x,_=generate(4000,'asymmetric_crash');w=bank(4000)
def baseline():
    v,e=Risk(x,w).eval();se=(np.maximum(-x@w.T-v,0)/.05).std(0,ddof=1)/np.sqrt(len(x));j=np.argmin(e+se)
    return float(e[j])
def candidate():
    z,d=gmm(x[:256],4000);p,d=calibrate(z,x[256:],w,beta=.5,band=1,seed=4000);return float(p[1].min())
out={}
for name,fun in [('historical_se_penalty',baseline),('support_band50',candidate)]:
    fun();tt=[]
    for _ in range(5):
        t=time.perf_counter();fun();tt.append(time.perf_counter()-t)
    out[name]={'seconds':tt,'mean_seconds':float(np.mean(tt)),'sd_seconds':float(np.std(tt,ddof=1))}
out['scope']='One synthetic 512x8 window,285 candidates, includes fit/risk optimization,5 warm CPU timings; NOT market performance or Mac timing'
(ROOT/'results/latency.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
