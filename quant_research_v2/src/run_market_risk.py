"""Prepared rolling risk-factor experiment. Only smoke-tested on artificial fixtures.
NOT a trading backtest: reference price moves exclude spread, funding and carry.
No test selection: synthetic-validation model configuration remains frozen.
"""
import argparse,csv,json,time
from pathlib import Path
import numpy as np
from research import bank,Risk,gaussian,student_fit,gmm,calibrate,filter_returns
from market_data import returns_pp,past_window

def forecast(x,w,seed):
    r={};r['historical']=Risk(x,w).eval();r['gaussian_LW']=gaussian(x,w);r['student_t_LW']=student_fit(x,w)[0]
    z,diag=gmm(x[:256],seed);zp,diagp=gmm(x,seed)
    r['gmm_base']=Risk(z,w).eval();r['gmm_pooled']=Risk(zp,w).eval()
    r['support_band50']=calibrate(z,x[256:],w,beta=.5,band=1,seed=seed)[0]
    r['aptc_v1']=calibrate(z,x[256:],w,beta=0,band=0,old=True,seed=seed)[0]
    res,vol=filter_returns(x);r['filtered_historical']=Risk(res*vol,w).eval()
    vh,eh=r['historical'];se=(np.maximum(-x@w.T-vh,0)/.05).std(0,ddof=1)/np.sqrt(len(x))
    jse=int(np.argmin(eh+se));r['historical_se_penalty']=r['historical'];r['equal_weight']=r['historical']
    return r,{'historical_se_penalty':jse,'equal_weight':0}

def evaluate_window(x,y,w,seed=7):
    risks,chosen=forecast(x,w,seed);out=[]
    for method,(v,e) in risks.items():
        j=chosen.get(method,int(np.argmin(e)));loss=float(-y@w[j]);vv=float(v[j]);ee=float(e[j])
        pin=(.95-float(loss<vv))*(loss-vv)
        # Upper-loss form of FZ0, valid only on positive ES domain.
        fz=(max(loss-vv,0)/.05+vv)/ee+np.log(ee)-1 if ee>0 else None
        out.append({'method':method,'portfolio_id':j,'var95':vv,'es95':ee,'realized_loss':loss,'var_breach':int(loss>vv),'pinball95':pin,'fz0':fz,'weights':json.dumps(w[j].tolist())})
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument('--levels',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--from-date',default='2010-01-01');p.add_argument('--to-date',default='2025-12-31');p.add_argument('--stride',type=int,default=5);p.add_argument('--limit',type=int,default=0);a=p.parse_args()
    rows=list(csv.DictReader(a.levels.open()));cols=[c for c in rows[0] if c!='date'];dates=[r['date'] for r in rows];levels=np.array([[float(r[c]) for c in cols] for r in rows]);rr=returns_pp(levels);rdates=dates[1:]
    if len(cols)!=8:raise ValueError('Frozen protocol requires eight declared risk factors')
    if dates!=sorted(dates) or len(set(dates))!=len(dates):raise ValueError('Dates must be unique and sorted')
    inds=[i for i in range(513,len(rr)) if a.from_date<=rdates[i]<=a.to_date][::a.stride]
    if a.limit:inds=inds[:a.limit]
    if not inds:raise ValueError('No eligible forecast dates')
    a.out.mkdir(parents=True,exist_ok=True);w=bank(2026);allrows=[];start=time.perf_counter()
    for k,i in enumerate(inds):
        batch=evaluate_window(past_window(rr,i,gap=1),rr[i],w,seed=7000+i)
        for r in batch:r.update({'date':rdates[i],'training_last_date':rdates[i-2],'gap_observations':1})
        allrows+=batch
        if k%10==0:print(k+1,len(inds),'elapsed',round(time.perf_counter()-start,1),flush=True)
    with (a.out/'risk_forecasts.csv').open('w',newline='') as f:
        ww=csv.DictWriter(f,fieldnames=list(allrows[0]));ww.writeheader();ww.writerows(allrows)
    (a.out/'run_manifest.json').write_text(json.dumps({'dates':len(inds),'rows':len(allrows),'seconds':time.perf_counter()-start,'first':rdates[inds[0]],'last':rdates[inds[-1]],'limits':'Reference-factor risk only; not executed trading. Latest downloaded vintage; release timing approximated by one-observation gap. No population ES ground truth. Sparse sampled dates are not full daily VaR backtesting.'},indent=2))
if __name__=='__main__':main()
