"""Official FX loaders. Online download NOT successful in the ChatGPT run.
No community mirror, automatic repair, or fabricated observations are used.
Derived levels are base-currency units per foreign-currency unit.
"""
import argparse,csv,datetime,hashlib,io,json,zipfile
from pathlib import Path
import urllib.request
import numpy as np

ECB_COLS=['USD','JPY','GBP','CHF','SEK','NOK','CAD','AUD']
BOC_COLS=['USD','EUR','GBP','JPY','CHF','AUD','NZD','CNY']

def parse_ecb_csv(raw,cutoff='2025-12-31'):
    rows=csv.DictReader(io.StringIO(raw.decode('utf-8-sig')),skipinitialspace=True)
    points=[]
    for row in rows:
        r={k.strip():v.strip() if isinstance(v,str) else v for k,v in row.items() if k}
        date=r.get('Date','');datetime.date.fromisoformat(date)
        if date>cutoff:continue
        try:x=np.array([float(r[k]) for k in ECB_COLS])
        except (ValueError,KeyError,TypeError):continue
        if np.isfinite(x).all() and (x>0).all():points.append((date,1/x))
    return validate_points(points,ECB_COLS)

def parse_boc_json(raw,cutoff='2025-12-31'):
    obj=json.loads(raw);points=[]
    if 'observations' not in obj:raise ValueError('Valet JSON contains no observations')
    for r in obj['observations']:
        date=r['d'];datetime.date.fromisoformat(date)
        if date>cutoff:continue
        try:x=np.array([float(r['FX'+k+'CAD']['v']) for k in BOC_COLS])
        except (ValueError,KeyError,TypeError):continue
        if np.isfinite(x).all() and (x>0).all():points.append((date,x))
    return validate_points(points,BOC_COLS)

def validate_points(points,cols):
    points=sorted(points,key=lambda x:x[0]);dates=[r[0] for r in points]
    if not points:raise ValueError('No complete positive eight-currency observations')
    if len(set(dates))!=len(dates):raise ValueError('Duplicate dates: will not silently aggregate')
    return dates,np.stack([r[1] for r in points]),cols

def returns_pp(levels):
    a=np.asarray(levels)
    if a.ndim!=2 or len(a)<2 or not np.isfinite(a).all() or (a<=0).any():raise ValueError('Invalid level panel')
    # Simple percentage-point changes, NOT total returns including interest/carry/costs.
    return 100*(a[1:]/a[:-1]-1)

def past_window(r,index,window=512,gap=1):
    end=index-gap
    if end<window or index>=len(r):raise ValueError('Insufficient history or invalid index')
    return r[end-window:end].copy()

def get_source(source):
    if source=='ecb':return 'https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.zip'
    series=','.join('FX'+c+'CAD' for c in BOC_COLS)
    return 'https://www.bankofcanada.ca/valet/observations/'+series+'/json?start_date=2017-01-01&end_date=2025-12-31'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',choices=['ecb','boc'],required=True);ap.add_argument('--raw-file',type=Path);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--cutoff',default='2025-12-31');args=ap.parse_args()
    url=get_source(args.source);args.out.mkdir(parents=True,exist_ok=True)
    try:
        if args.raw_file:raw=args.raw_file.read_bytes()
        else:
            req=urllib.request.Request(url,headers={'User-Agent':'Academic risk-research reproducibility script'})
            with urllib.request.urlopen(req,timeout=45) as response:raw=response.read()
    except Exception as err:
        (args.out/'download_failure.json').write_text(json.dumps({'url':url,'error':repr(err),'status':'NOT DOWNLOADED; NO MARKET RESULTS'},indent=2))
        raise SystemExit(f'Official download failed: {err}\nUse --raw-file with an original official download. No fallback data generated.')
    rawpath=args.out/('official_ecb.zip' if args.source=='ecb' and raw[:2]==b'PK' else 'official_response.dat');rawpath.write_bytes(raw)
    if args.source=='ecb':
        if raw[:2]==b'PK':
            with zipfile.ZipFile(io.BytesIO(raw)) as zz:
                names=[n for n in zz.namelist() if n.lower().endswith('.csv')]
                if len(names)!=1:raise ValueError('Unexpected ECB archive structure')
                data=zz.read(names[0])
        else:data=raw
        dates,levels,cols=parse_ecb_csv(data,args.cutoff);base='EUR'
    else:dates,levels,cols=parse_boc_json(raw,args.cutoff);base='CAD'
    with (args.out/'levels.csv').open('w',newline='') as f:
        ww=csv.writer(f);ww.writerow(['date']+cols);ww.writerows([[d]+list(a) for d,a in zip(dates,levels)])
    manifest={'source':args.source,'url':url,'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'raw_sha256':hashlib.sha256(raw).hexdigest(),'rows':len(dates),'first':dates[0],'last':dates[-1],'cutoff':args.cutoff,'columns':cols,'base':base,'transformation':'ECB reciprocal; BoC original quote; complete common dates only; no fill','warning':'Reference-price risk factors, not executable total-return assets; no archived vintages'}
    (args.out/'manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
