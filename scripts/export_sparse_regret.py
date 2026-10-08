"""Export all fixed computational cells and reproducible manuscript figures."""
import csv
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import platform

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'runs/sparse_regret_audit/20261008'


def main():
    rows = [json.loads(gzip.decompress(p.read_bytes()))['body']['result']
            for p in sorted((OUT/'frozen/cases').glob('*.json.gz'))]
    cells = []
    for row in rows:
        task, times = row['task'], row['timings']
        paired = np.array(times['union'])/times['local']
        cells.append(dict(**task, local_seconds=float(np.median(times['local'])),
                          union_seconds=float(np.median(times['union'])),
                          paired_ratio_median=float(np.median(paired)),
                          paired_ratio_min=float(min(paired)), paired_ratio_max=float(max(paired)),
                          lp_seconds=times.get('lp', ['NOT_RUN'])[0],
                          max_error=max(row['max_errors'].values()),
                          max_witness_error=max(row['witness_errors'].values()),
                          argmin_disagrees=row['argmin_disagrees']))
    with (OUT/'computational_cells.csv').open('w') as f:
        writer = csv.DictWriter(f, fieldnames=cells[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(cells)
    groups = []
    for kind in ('lp', 'scale'):
        for alpha in (.05, .2, 1.):
            for r in (3, 6, 12):
                selected = [c for c in cells if c['kind'] == kind and c['alpha'] == alpha and c['r'] == r]
                ratio = [c['paired_ratio_median'] for c in selected]
                groups.append(dict(kind=kind, alpha=alpha, r=r, cases=len(selected),
                                   median_paired_ratio=float(np.median(ratio)),
                                   ratio_min=min(ratio), ratio_max=max(ratio),
                                   local_faster=sum(v > 1 for v in ratio)))
    with (OUT/'timing_groups.csv').open('w') as f:
        writer = csv.DictWriter(f, fieldnames=groups[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(groups)
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.9), layout='constrained')
    colors = {0.05: '#0072B2', .2: '#D55E00', 1.: '#555555'}
    markers = {.05: 'o', .2: '^', 1.: 's'}
    for alpha in (.05, .2, 1.):
        for r in (3, 6, 12):
            selected = [c for c in cells if c['kind'] == 'scale' and c['alpha'] == alpha and c['r'] == r]
            jitter = np.linspace(-.14, .14, len(selected))
            xx = (3, 6, 12).index(r)+(.05, .2, 1.).index(alpha)*.22-.22
            axes[0].scatter(xx+jitter*.45, [c['paired_ratio_median'] for c in selected],
                            s=24, color=colors[alpha], marker=markers[alpha], alpha=.7,
                            label=f'tail mass {alpha:g}' if r == 3 else None)
        selected = [c for c in cells if c['kind'] == 'scale' and c['alpha'] == alpha and c['m'] == 256 and c['s'] == 128]
        if alpha != 1:
            for method, linestyle in [('local', '-'), ('union', '--')]:
                med = [np.median([c[method+'_seconds'] for c in selected if c['r'] == r]) for r in (3, 6, 12)]
                axes[1].plot([3, 6, 12], med, linestyle, marker=markers[alpha], color=colors[alpha],
                             label=f'{method}, tail {alpha:g}')
    axes[0].axhline(1, color='black', linestyle=':', linewidth=1)
    axes[0].set(xticks=[0, 1, 2], xticklabels=['3', '6', '12'], xlabel='Number of component laws',
                ylabel='Union / local elapsed time', title='All 72 scaling inputs; three timing pairs each')
    axes[0].legend(fontsize=8)
    axes[1].set(xlabel='Number of component laws', ylabel='Seconds per solve (median)',
                title='256 actions, 128 scenarios; two inputs per point', yscale='log')
    axes[1].legend(fontsize=8)
    fig.savefig(OUT/'timing.png', dpi=180)
    fig.savefig(OUT/'timing.pdf')
    plt.close(fig)
    fixture_path = OUT/'reviews/j2_sharpness_check.py'
    spec = importlib.util.spec_from_file_location('fixture', fixture_path)
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    values, components = fixture.component_masses()
    values, components = np.array(values), np.array(components, float)
    qlist = [np.array([a/60, b/60, 1-(a+b)/60]) for a in range(61) for b in range(61-a)]
    qarray = np.array(qlist)
    p = qarray @ components[:, ::-1]
    before = np.column_stack([np.zeros(len(p)), np.cumsum(p, axis=1)[:, :-1]])
    risks = sum(.5*np.minimum(p, np.maximum(0, alpha-before)) @ values[::-1]/alpha for alpha in (.2, .6))
    coordinates = qarray @ np.array([[0, 0], [1, 0], [.5, np.sqrt(3)/2]])
    exact = json.loads((OUT/'extensions.json').read_text())['spectral_sharpness']
    from fractions import Fraction
    qstar = np.array([float(Fraction(v)) for v in exact['q']])
    star = qstar @ np.array([[0, 0], [1, 0], [.5, np.sqrt(3)/2]])
    fig, ax = plt.subplots(figsize=(6, 4.9), layout='constrained')
    fill = ax.tricontourf(coordinates[:, 0], coordinates[:, 1], risks, levels=16, cmap='cividis')
    ax.plot([0, 1, .5, 0], [0, 0, np.sqrt(3)/2, 0], color='black', linewidth=1)
    ax.scatter(*star, s=120, marker='*', color='#D55E00', edgecolors='black', label='Exact unique interior maximum')
    ax.annotate('P1', (0, 0), xytext=(-12, -14), textcoords='offset points')
    ax.annotate('P2', (1, 0), xytext=(2, -14), textcoords='offset points')
    ax.annotate('P3', (.5, np.sqrt(3)/2), xytext=(-8, 7), textcoords='offset points')
    ax.set(aspect='equal', xlim=(-.04, 1.04), ylim=(-.025, .94))
    ax.set_title('Two ES levels can require three component laws', pad=12)
    ax.axis('off')
    ax.legend(loc='lower center', bbox_to_anchor=(.5, -.18), fontsize=8)
    fig.colorbar(fill, ax=ax, label='(ES at tail .2 + ES at tail .6) / 2; loss units', shrink=.8)
    fig.savefig(OUT/'spectral_sharpness.png', dpi=180, bbox_inches='tight')
    fig.savefig(OUT/'spectral_sharpness.pdf', bbox_inches='tight')
    plt.close(fig)
    info = dict(source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                matplotlib=matplotlib.__version__, numpy=np.__version__, python=platform.python_version(),
                rows=len(rows), figure_scope='Computed figures, no image synthesis or smoothing; spectral grid is visual only, optimum is exact rational enumeration.',
                files={name: hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in
                       ['computational_cells.csv', 'timing_groups.csv', 'timing.png', 'timing.pdf',
                        'spectral_sharpness.png', 'spectral_sharpness.pdf']})
    (OUT/'export_receipt.json').write_text(json.dumps(info, indent=2)+'\n')
    print(json.dumps(info, indent=2))


if __name__ == '__main__':
    main()
