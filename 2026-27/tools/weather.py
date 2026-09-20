"""Refresh only this dashboard's weather cache. Never writes the locked study."""
import csv,json,pathlib,urllib.request,urllib.parse,concurrent.futures
ROOT=pathlib.Path(__file__).resolve().parents[1]
seed=json.loads((ROOT/'data/study-snapshot.json').read_text())
rows=list(csv.DictReader((ROOT/'data/new-matches.csv').open()))
clubs={x['club']:x for x in seed['clubs']}
def get(name):
 c=clubs[name]; q=urllib.parse.urlencode(dict(latitude=c['lat'],longitude=c['lng'],start_date=min(x['date'] for x in rows),end_date=max(x['date'] for x in rows),hourly='temperature_2m,precipitation,wind_speed_10m',timezone='Europe/London'))
 url='https://archive-api.open-meteo.com/v1/archive?'+q
 try:
  with urllib.request.urlopen(url,timeout=30) as f:data=json.load(f)
  return name,dict(source=url,data=data)
 except Exception as e:return name,dict(source=url,error=str(e))
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
 result=dict(pool.map(get,sorted({r['home'] for r in rows})))
(ROOT/'data/weather-cache.json').write_text(json.dumps(result,indent=2))
print('Weather responses:',len(result),'errors:',{k:v['error'] for k,v in result.items() if 'error' in v})
