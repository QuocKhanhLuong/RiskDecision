import csv,json,hashlib,datetime,collections
from pathlib import Path
from research import ROOT,CANDIDATES
rows=list(csv.DictReader((ROOT/'results/validation.csv').open()))
d=collections.defaultdict(list)
for r in rows:d[r['method']].append(float(r['relative_error']))
score={m:sum(v)/len(v) for m,v in d.items()}
base=['historical','historical_se_penalty','historical_concentration_penalty','gaussian_LW','student_t_LW','gmm_pooled','filtered_historical','filtered_gaussian']
freeze={'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'selected_candidate':min(CANDIDATES,key=lambda m:score[m]),'selected_equal_information_baseline':min(base,key=lambda m:score[m]),'criterion':'equal-family mean relative absolute ES error at the selected portfolio; validation only','validation_scores':score,'eligible_candidates':CANDIDATES,'eligible_baselines':base,'validation_sha256':hashlib.sha256((ROOT/'results/validation.csv').read_bytes()).hexdigest(),'source_sha256':hashlib.sha256((ROOT/'src/research.py').read_bytes()).hexdigest(),'test_started':False}
p=ROOT/'results/selection_freeze.json'
if p.exists():raise RuntimeError('Freeze already exists: will not overwrite')
p.write_text(json.dumps(freeze,indent=2));print(json.dumps(freeze,indent=2))
