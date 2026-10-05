from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import requests, json, hashlib, time
root=Path('/mnt/data/quant_research_v2/data')
urls={
 'ecb_fx':'https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.zip',
 'boc_fx':'https://www.bankofcanada.ca/valet/observations/group/FX_RATES_DAILY/json?start_date=2017-01-01&end_date=2025-12-31',
 'boc_yield':'https://www.bankofcanada.ca/valet/observations/BD.CDN.2YR.DQ.YLD,BD.CDN.3YR.DQ.YLD,BD.CDN.5YR.DQ.YLD,BD.CDN.7YR.DQ.YLD,BD.CDN.10YR.DQ.YLD,BD.CDN.LONG.DQ.YLD/json?start_date=1995-01-01&end_date=2025-12-31',
 'ecb_yield':'https://data-api.ecb.europa.eu/service/data/YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_1Y+SR_2Y+SR_3Y+SR_5Y+SR_7Y+SR_10Y+SR_15Y+SR_20Y?startPeriod=2004-01-01&endPeriod=2025-12-31&format=csvdata',
}
def f(item):
 n,u=item;t=time.time()
 try:
  r=requests.get(u,timeout=35,headers={'User-Agent':'AcademicResearch/1.0'})
  ext='.zip' if n=='ecb_fx' else ('.csv' if n=='ecb_yield' else '.json')
  if r.status_code==200:(root/(n+ext)).write_bytes(r.content)
  return {'name':n,'url':u,'status':r.status_code,'bytes':len(r.content),'hash':hashlib.sha256(r.content).hexdigest(),'seconds':time.time()-t,'head':r.text[:100] if ext!='.zip' else str(r.content[:20])}
 except Exception as e:return {'name':n,'url':u,'error':str(e),'seconds':time.time()-t}
if __name__=='__main__':
 out=list(ThreadPoolExecutor(4).map(f,urls.items()))
 (root/'downloads.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
