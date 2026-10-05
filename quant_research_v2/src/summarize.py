import csv, json, collections
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]

def write(path, rows):
    with path.open('w',newline='') as fp:
        w=csv.DictWriter(fp,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    rows=list(csv.DictReader((ROOT/'results/test.csv').open()))
    freeze=json.loads((ROOT/'results/selection_freeze.json').read_text())
    metrics=['relative_error','absolute_error','true_es','predicted_es','relative_regret','underestimation','all_portfolio_mae','hhi']
    groups=collections.defaultdict(list)
    for r in rows: groups[(r['family'],r['method'])].append(r)
    tab=[]
    for (family,method),rr in groups.items():
        row={'family':family,'method':method,'n':len(rr)}
        for m in metrics:
            a=np.array([float(r[m]) for r in rr]);row[m+'_mean']=a.mean();row[m+'_sd']=a.std(ddof=1)
        tab.append(row)
    write(ROOT/'results/test_summary_by_family.csv',tab)
    # Cluster on seed: preserve the shared seed across all four DGPs, then bootstrap.
    methods=sorted(set(r['method'] for r in rows));families=sorted(set(r['family'] for r in rows));seeds=sorted(set(int(r['seed']) for r in rows))
    lookup={(r['family'],int(r['seed']),r['method']):r for r in rows}
    overall=[]
    for method in methods:
        line={'method':method,'n_seed_clusters':len(seeds),'n_market_instances':len(seeds)*len(families)}
        for metric in metrics:
            x=np.array([[float(lookup[(f,s,method)][metric]) for s in seeds] for f in families]).mean(0)
            line[metric+'_mean']=x.mean();line[metric+'_sd_seed_mean']=x.std(ddof=1)
        overall.append(line)
    write(ROOT/'results/test_summary_overall.csv',overall)
    selected=freeze['selected_candidate'];baselines=['gmm_base','gmm_pooled','aptc_v1','historical',freeze['selected_equal_information_baseline'],'support_mix50','support_point50','filtered_support_band50']
    comparisons=[];rng=np.random.default_rng(7331);ind=rng.integers(len(seeds),size=(5000,len(seeds)))
    for fam in families+['equal_family_mean']:
        ff=families if fam=='equal_family_mean' else [fam]
        for ref in baselines:
            for metric in ['relative_error','absolute_error','true_es','relative_regret']:
                a=np.array([[float(lookup[(f,s,selected)][metric])-float(lookup[(f,s,ref)][metric]) for s in seeds] for f in ff]).mean(0)
                bs=a[ind].mean(1);low,hi=np.quantile(bs,[.025,.975])
                comparisons.append({'family':fam,'candidate':selected,'reference':ref,'metric':metric,'difference':a.mean(),'ci_low':low,'ci_high':hi,'bootstrap_seed':7331,'bootstrap_replicates':5000,'note':'pointwise interval, paired by seed; no multiple-testing claim'})
    write(ROOT/'results/paired_differences.csv',comparisons)
    print('FROZEN',selected,'REFERENCE',freeze['selected_equal_information_baseline'])
    for r in sorted(overall,key=lambda a:a['relative_error_mean']): print(r['method'],round(r['relative_error_mean'],5),round(r['relative_regret_mean'],5))
    print('\nMain paired comparisons:')
    for r in comparisons:
        if r['family']=='equal_family_mean' and r['metric']=='relative_error':print(r)
if __name__=='__main__':main()
