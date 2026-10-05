import csv,hashlib,json,time,sys
from pathlib import Path
import numpy as np
from numpy.testing import assert_allclose
from research import ROOT,CFG,generate,truth,bank,Risk,gmm,calibrate

def main():
    start=time.perf_counter();freeze=json.loads((ROOT/'results/selection_freeze.json').read_text())
    assert hashlib.sha256((ROOT/'src/research.py').read_bytes()).hexdigest()==freeze['source_sha256']
    assert hashlib.sha256((ROOT/'results/validation.csv').read_bytes()).hexdigest()==freeze['validation_sha256']
    seen=set();scalar_checks=0;repro=0;warnings=[];gnonc=0;cnonc=0
    for stage,expected in [('validation',1440),('test',5760)]:
        rows=list(csv.DictReader((ROOT/'results'/f'{stage}.csv').open()));assert len(rows)==expected
        grouped={}
        for r in rows:grouped.setdefault((r['family'],int(r['seed'])),[]).append(r)
        for (fam,seed),rr in grouped.items():
            assert len(rr)==18;assert (fam,seed) not in seen;seen.add((fam,seed))
            pp=ROOT/'results'/stage/f'{fam}_{seed}.npz';zz=np.load(pp);x,pars=generate(seed,fam);w=bank(seed)
            assert_allclose(zz['returns'],x,atol=0,rtol=0);assert_allclose(zz['weights'],w,atol=0,rtol=0)
            v,e=truth(w,pars);assert_allclose(zz['true_es'],e);assert_allclose(zz['true_var'],v)
            diag=json.loads(pp.with_suffix('.json').read_text())
            assert hashlib.sha256(x.tobytes()).hexdigest()==diag['x_sha256']
            for key,val in diag.items():
                if isinstance(val,dict) and 'converged' in val and not val['converged']:
                    if 'gmm' in key:gnonc+=1
                    else:cnonc+=1
                    warnings.append({'stage':stage,'family':fam,'seed':seed,'component':key,'detail':val})
            eh=zz['historical_es'];vh=zz['historical_var'];se=(np.maximum(-x@w.T-vh,0)/.05).std(0,ddof=1)/np.sqrt(len(x))
            special={'equal_weight':0,'historical_se_penalty':int(np.argmin(eh+se)),'historical_concentration_penalty':int(np.argmin(eh+.2*np.median(eh)*(w*w).sum(1)))}
            for r in rr:
                meth=r['method'];est=zz[meth+'_es'];j=special.get(meth,int(np.argmin(est)));assert j==int(r['portfolio_id'])
                expected_values={'predicted_es':est[j],'true_es':e[j],'absolute_error':abs(est[j]-e[j]),'relative_error':abs(est[j]-e[j])/e[j], 'regret':e[j]-e.min(),'relative_regret':e[j]/e.min()-1,'underestimation':e[j]-est[j],'equal_predicted_es':est[0],'equal_true_es':e[0],'all_portfolio_mae':np.mean(abs(est-e)),'hhi':w[j]@w[j]}
                for k,value in expected_values.items():assert_allclose(float(r[k]),value,rtol=1e-11,atol=1e-11);scalar_checks+=1
            # Refit selected method on first held-out seed of each family; not a new evaluation.
            if stage=='test' and seed==CFG['test_seeds'][0]:
                z,_=gmm(x[:256],seed);pred,dd=calibrate(z,x[256:],w,beta=.5,band=1,seed=seed)
                assert_allclose(pred[1],zz['support_band50_es'],rtol=1e-9,atol=1e-9);repro+=1
    # Monte Carlo check of analytic population tails, independent of fitting.
    mc=[];rng=np.random.default_rng(89919);n=200000
    for fam in CFG['families']:
        _,p=generate(5091,fam);w=bank(5091)[:1];_,target=truth(w,p)
        if p['kind']=='t':z=rng.multivariate_normal(np.zeros(8),p['shape'],n)/np.sqrt(rng.chisquare(p['df'],n)/p['df'])[:,None]
        else:
            kk=rng.choice(len(p['p']),n,p=p['p']);z=np.zeros((n,8))
            for k in range(len(p['p'])):
                ii=np.flatnonzero(kk==k);z[ii]=rng.multivariate_normal(p['mu'][k],p['cov'][k],len(ii))
        sim=Risk(z,w).eval()[1][0];rel=abs(sim-target[0])/target[0];assert rel<.04
        mc.append({'family':fam,'n':n,'formula_es':target[0],'mc_es':sim,'relative_difference':rel})
    receipt={'status':'PASS','market_instances_checked':len(seen),'aggregate_rows_checked':7200,'scalar_values_checked':scalar_checks,'selected_model_refits':repro,'population_mc_checks':mc,'gmm_nonconverged_components':gnonc,'calibration_nonconverged_components':cnonc,'warnings':warnings,'source_hash':freeze['source_sha256'],'audit_seconds':time.perf_counter()-start,'scope':'Software/numerical verification, not independent reviewer or market validation'}
    (ROOT/'results/audit_receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
