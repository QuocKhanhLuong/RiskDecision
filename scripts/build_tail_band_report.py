"""Render the frozen mechanism experiment directly from audited CSVs."""
from pathlib import Path
import csv
import json
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from local_market.data import sha256,atomic_json

out=ROOT/"results/tail_band_v1"
def read(name):
    with (out/name).open() as f:return list(csv.DictReader(f))
rows,bounded,paired=read("coverage.csv"),read("bounded.csv"),read("paired.csv")
audit=json.loads((out/"audit.json").read_text())
receipt=json.loads((out/"provenance.json").read_text())
assert audit["status"]=="PASS"
for name,digest in audit["aggregate_sha256"].items():assert sha256(out/name)==digest
index={(int(r['n']),r['anchor'],r['recipe']):r for r in rows}
assert len(index)==27 and len(bounded)==3 and len(paired)==18
anchors=['population_quantiles_oracle','base_only','reused_mixture']
recipes=['plugin_max_t','oracle_width_swap','fixed_scale_max']
lines=['# Tail-band mechanism: executed results','',
       'Freeze commit `296457e`. [Protocol](TAIL_BAND_PROTOCOL.md), [Vietnamese decision](TAIL_BAND_DECISION.md), '
       '[coverage CSV](../results/tail_band_v1/coverage.csv), [paired CSV](../results/tail_band_v1/paired.csv).', '',
       f"Completed {receipt['cases']} Gaussian IID series, {receipt['rows']:,} mechanism rows and {receipt['bounded_rows']} bounded-target rows. "
       f"First completed invocation computed {receipt['computed_this_invocation']} cases in {receipt['wall_seconds']:.2f}s with 2 numerical processes, one thread each. "
       f"All {audit['inputs_regenerated']} generated inputs were verified; {audit['metrics_recomputed']:,} metrics recomputed from arrays. "
       f"GMM nonconvergence {receipt['gmm_nonconverged']}, warnings {receipt['gmm_warnings']}. Tests: 80 passed before execution.",'',
       '## Simultaneous coverage of all 855 means','',
       'Cells are covered seeds / 200, with pointwise Wilson 95% Monte Carlo intervals in percent. '
       'Oracle width swaps and population quantiles are diagnostics, not deployable methods. For reused-mixture anchors, the oracle scale is the population variance of a fixed feature evaluated at the realized threshold divided by n; it is not the exact sampling variance conditional on that data-dependent threshold. '
       'A confidence interval containing 95% does not establish a 95% guarantee.','',
       '| n / anchor | Plug-in max-t | Oracle width swap | Fixed-scale max |',
       '|---|---:|---:|---:|']
cells=0
for n in [256,1024,4096]:
    for anchor in anchors:
        values=[]
        for recipe in recipes:
            r=index[n,anchor,recipe]
            values.append(f"{int(r['all_covered_count'])}/200 [{100*float(r['all_covered_lo']):.1f}, {100*float(r['all_covered_hi']):.1f}]")
            cells+=3
        lines.append(f'| {n} / {anchor} | '+' | '.join(values)+' |')
lines += ['', '## Paired coverage changes', '',
          'Same 200 seeds within each contrast; 5,000 paired bootstrap draws. Differences and intervals are percentage points, pointwise and unadjusted. '
          'Rescued/lost counts record changed simultaneous-coverage events. No recipe was selected or promoted after this comparison.','',
          '| n / anchor | Contrast | Difference [95% interval] | Rescued / lost |','|---|---|---:|---:|']
for r in paired:
    lines.append(f"| {r['n']} / {r['anchor']} | {r['contrast']} | {100*float(r['coverage_difference']):.1f} [{100*float(r['lo']):.1f}, {100*float(r['hi']):.1f}] | {r['rescued']} / {r['lost']} |")
    cells+=5
lines += ['', '## Standard errors and width', '',
          'SE ratios are sample SE / exact Gaussian hinge SE. Worst-error feature maximizes absolute mean error / exact SE, so its ratio is descriptive and selected using the evaluator. '
          'Widths are mean-over-seeds of median-over-features radius/(0.05 × unbounded Gaussian ES95). These are hinge widths, not ES confidence intervals.','',
          '| n / anchor | Mean minimum SE ratio | Mean median SE ratio | Mean SE ratio at worst error | Plug-in width | Oracle width | Fixed-scale width |','|---|---:|---:|---:|---:|---:|---:|']
for n in [256,1024,4096]:
    for anchor in anchors:
        r=index[n,anchor,'plugin_max_t']
        values=[float(r[k+'_mean']) for k in ['se_ratio_min','se_ratio_median','se_ratio_at_worst_error']]
        values += [float(index[n,anchor,p]['width_ratio_median_mean']) for p in recipes]
        lines.append(f'| {n} / {anchor} | '+' | '.join(f'{v:.3f}' for v in values)+' |');cells+=6
lines += ['', '## Known-bounded-target DKW positive control', '',
          'Target: ES95 of each portfolio loss clipped at ±3 population SD, under IID sampling. '
          'This is a different target from unbounded ES. DKW + a union bound over the fixed portfolio bank controls every threshold. '
          'Widths below are actual ES interval widths divided by population clipped ES95, not the hinge-width proxy above.','',
          '| n | All 285 ES covered [Wilson interval %] | epsilon | Mean relative interval width | Upper endpoint at support (%) | Clipping change in true ES (%) |',
          '|---|---:|---:|---:|---:|---:|']
for r in bounded:
    lines.append(f"| {r['n']} | {int(r['all_covered_count'])}/200 [{100*float(r['all_covered_lo']):.1f}, {100*float(r['all_covered_hi']):.1f}] | {float(r['epsilon_mean']):.6f} | {float(r['width_relative_median_mean']):.3f} | {100*float(r['upper_at_support_fraction_mean']):.1f} | {100*float(r['clipping_es_relative_change_mean']):.3f} |")
    cells+=7
lines += ['', '## Reproduction and limits', '',
          'Gaussian IID only; the same covariance family that motivated the experiment. New seeds are independent simulation draws, '
          'not independent validation of a proposed market algorithm. No conclusions about heavy-tailed or dependent calibration follow. '
          'The oracle scale intervention changes widths without replacing the plug-in critical value. Fixed scaling reallocates width across quantiles. '
          'The clipped DKW control uses known support and is not an unbounded or next-period market risk certificate.','',
          'All original historical, market and earlier diagnostic artifacts remain unchanged. No market test, new dataset, neural model or candidate v3 was run. '
          'Independent review remains NOT RUN: the Orca Codex launch hit its updater then exited; a retry failed readiness before task delivery. '
          'The updater changed the CLI to 0.160.1; the coordinator did not change global agent preferences. The second terminal was released, '
          'and Orca retained the first shell with identity_unproven.','',
          '```bash','rtk proxy bash scripts/reproduce_tail_band.sh','```','',
          'Aggregate tables are generated from CSV. The analyzer checks source/protocol hashes, regenerates inputs and recomputes per-case metrics. '
          'Supplementary verification re-fits the first and last case and independently parses each table number. '
          'Local arrays remain under ignored runs/; first-execution timing is preserved across resumes.','']
report=ROOT/'docs/TAIL_BAND_RESULTS.md';report.write_text('\n'.join(lines))
atomic_json(out/'table_receipt.json',{'report_sha256':sha256(report),'builder_sha256':sha256(Path(__file__)),
            'aggregate_sha256':audit['aggregate_sha256'],'numeric_table_values_from_csv':cells})
print('Rendered',cells,'numeric table values')
