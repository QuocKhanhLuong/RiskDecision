"""Exact boundary refits, bounded-row recalculation, independent Markdown parse."""
from pathlib import Path
import sys,csv,json,re
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tail_band_audit.core import *
from tail_band_audit.run import contract
from local_market.data import sha256,atomic_json

p,identity=contract(); out=ROOT/'results/tail_band_v1'; run=ROOT/'runs/tail_band_v1'
for seed in [71000,71199]:
    with np.load(run/'cases'/f'{seed}.npz') as a:
        x,_,_=generate(seed,'gaussian',n=4352);w=bank(2026)
        np.testing.assert_array_equal(x,a['returns'])
        z,_=gmm_fit(x[:256],seed);np.testing.assert_array_equal(z,a['scenarios'])
        for n in p['sizes']:
            g=np.random.default_rng(np.random.SeedSequence([seed,n,920000])).standard_normal((499,n))
            for anchor in ANCHORS:
                key=f'n{n}_{anchor}'
                if anchor=='population_quantiles_oracle':
                    eta=(a['sd'][:,None]*norm.ppf(QUANTILES)).ravel()
                    h=np.maximum(np.repeat(-x[256:256+n]@w.T,3,axis=1)-eta,0)
                else:eta,h,_,_=features(z,x[256:256+n],w,anchor)
                np.testing.assert_array_equal(eta,a[key+'_eta'])
                rr,_,_=radii(h,a[key+'_exact_se'],a['base_scale'],g)
                for recipe,radius in rr.items():np.testing.assert_array_equal(radius,a[key+'_'+recipe])

with (run/'bounded.csv').open() as f:bounded_cases=list(csv.DictReader(f))
for r in bounded_cases:
    with np.load(run/'cases'/f"{r['seed']}.npz") as a:
        n=int(r['n']);key=f'n{n}_dkw';lo,hi,true=a[key+'_lo'],a[key+'_hi'],a[key+'_truth']
        values={'all_covered':int(((lo<=true+1e-12)&(true<=hi+1e-12)).all()),
                'equal_covered':int(lo[0]<=true[0]+1e-12 and true[0]<=hi[0]+1e-12),
                'epsilon':min(float(np.sqrt(np.log(2*285/.05)/(2*n))),1.),
                'width_relative_median':float(np.median((hi-lo)/true)),
                'upper_at_support_fraction':float(np.isclose(hi,3*a['sd'],atol=1e-10,rtol=0).mean()),
                'clipping_es_relative_change':float(np.median((a['es']-true)/a['es']))}
        for key,val in values.items():np.testing.assert_allclose(float(r[key]),val,atol=1e-12,rtol=0)

def read(name):
    with (out/name).open() as f:return list(csv.DictReader(f))
index={(int(r['n']),r['anchor'],r['recipe']):r for r in read('coverage.csv')}
pp={(int(r['n']),r['anchor'],r['contrast']):r for r in read('paired.csv')}
bb={int(r['n']):r for r in read('bounded.csv')}
mode=None;count=0
for line in (ROOT/'docs/TAIL_BAND_RESULTS.md').read_text().splitlines():
    if line=='## Simultaneous coverage of all 855 means':mode='coverage'
    elif line=='## Paired coverage changes':mode='paired'
    elif line=='## Standard errors and width':mode='width'
    elif line=='## Known-bounded-target DKW positive control':mode='bounded'
    elif line=='## Reproduction and limits':mode=None
    if not line.startswith('| ') or line.startswith('| n'):continue
    parts=[v.strip() for v in line.strip('|').split('|')]
    if mode in ['coverage','paired','width']:
        ns,anchor=parts[0].split(' / ');n=int(ns)
    nums=lambda s:[float(x) for x in re.findall(r'-?\d+(?:\.\d+)?',s)]
    if mode=='coverage':
        for recipe,text in zip(RECIPES,parts[1:]):
            r=index[n,anchor,recipe]
            assert nums(text)==[int(r['all_covered_count']),200,round(100*float(r['all_covered_lo']),1),round(100*float(r['all_covered_hi']),1)];count+=3
    elif mode=='paired':
        r=pp[n,anchor,parts[1]]
        assert nums(parts[2])==[round(100*float(r[k]),1) for k in ['coverage_difference','lo','hi']]
        assert nums(parts[3])==[int(r['rescued']),int(r['lost'])];count+=5
    elif mode=='width':
        r=index[n,anchor,'plugin_max_t']
        expected=[float(r[k+'_mean']) for k in ['se_ratio_min','se_ratio_median','se_ratio_at_worst_error']]
        expected += [float(index[n,anchor,recipe]['width_ratio_median_mean']) for recipe in RECIPES]
        assert list(map(float,parts[1:]))==[round(v,3) for v in expected];count+=6
    elif mode=='bounded':
        r=bb[int(parts[0])]
        assert nums(parts[1])==[int(r['all_covered_count']),200,round(100*float(r['all_covered_lo']),1),round(100*float(r['all_covered_hi']),1)]
        expected=[round(float(r['epsilon_mean']),6),round(float(r['width_relative_median_mean']),3),round(100*float(r['upper_at_support_fraction_mean']),1),round(100*float(r['clipping_es_relative_change_mean']),3)]
        assert list(map(float,parts[2:]))==expected;count+=7
table=json.loads((out/'table_receipt.json').read_text())
assert table['report_sha256']==sha256(ROOT/'docs/TAIL_BAND_RESULTS.md')
assert count==table['numeric_table_values_from_csv']
atomic_json(out/'supplementary_audit.json',{'status':'PASS','identity':identity,'exact_refit_seeds':[71000,71199],
            'bounded_rows_independently_recomputed':600,'numeric_table_values_independently_parsed':count,
            'performed_by':'coordinator; not independent agent review'})
print('PASS: two exact refits; 600 bounded rows;',count,'table numbers independently parsed')
