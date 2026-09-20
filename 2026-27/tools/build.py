"""Build the independent dashboard data from the frozen extract + verified additions."""
import csv,json,pathlib,datetime,hashlib,collections
ROOT=pathlib.Path(__file__).resolve().parents[1]
seed=json.loads((ROOT/'data/study-snapshot.json').read_text())
weather=json.loads((ROOT/'data/weather-cache.json').read_text()) if (ROOT/'data/weather-cache.json').exists() else {}
short={'Airbus UK Broughton':'Airbus','Ammanford AFC':'Ammanford','Barry Town United':'Barry','Briton Ferry Llansawel':'Briton Ferry','Caernarfon Town':'Caernarfon','Cardiff Metropolitan University':'Cardiff Met','Connah\'s Quay Nomads':"Connah’s Quay",'Flint Town United':'Flint','Haverfordwest County':'Haverfordwest','Holywell Town':'Holywell','Llandudno FC':'Llandudno','Penybont FC':'Penybont','The New Saints':'TNS','Trefelin Boys & Girls Club':'Trefelin','Cambrian United':'Cambrian'}
def num(v):return float(v) if v not in ['',None] else None
def convert(r):
 return dict(id=r['season']+'-'+r['date']+'-'+r['home'],season=r['season'],date=r['date'],round=int(r['matchday']),home=r['home'],away=r['away'],attendance=num(r['attendance']),kickoff=r['kick_off'],homeScore=num(r['home_score']),awayScore=num(r['away_score']),temp=num(r['wx_temp']),rain=num(r['wx_precip_3h']),wind=num(r['wx_wind']),source='https://everythingwelshfootball.club/downloads/matches.csv',provenance='Frozen study extract · Football Web Pages / Transfermarkt',weatherSource='Frozen study extract · Open-Meteo',reviewed='2026-09-09')
rows=[convert(r) for r in seed['matches']]
for r in csv.DictReader((ROOT/'data/new-matches.csv').open()):
 c=dict(id='fwp-'+r['source'].split('/')[-1],season='2026-2027',date=r['date'],round=int(r['round']),home=r['home'],away=r['away'],attendance=num(r['attendance']),kickoff=r['kickoff'],homeScore=num(r['homeScore']),awayScore=num(r['awayScore']),temp=None,rain=None,wind=None,source='https://www.footballwebpages.co.uk/match/2026-2027/cymru-premier/'+r['source'],provenance='Football Web Pages',weatherSource=None,reviewed='2026-09-20')
 w=weather.get(r['home'],{}); h=w.get('data',{}).get('hourly',{}); key=r['date']+'T'+r['kickoff'][:2]+':00'
 if key in h.get('time',[]):
  i=h['time'].index(key); c['temp']=h['temperature_2m'][i];c['wind']=h['wind_speed_10m'][i]
  rain=h['precipitation'][i-2:i+1];c['rain']=round(sum(rain),2) if len(rain)==3 and all(v is not None for v in rain) else None
  c['weatherSource']=w['source']
 rows.append(c)
rows.sort(key=lambda x:(x['date'],x['kickoff'],x['home']))
seen=set()
for r in rows:
 key=(r['date'],r['home'],r['away']);assert key not in seen,key;seen.add(key)
 assert r['attendance'] is None or r['attendance']>=0
 assert 1<=r['round']<=40
 r['day']=datetime.date.fromisoformat(r['date']).strftime('%A')
 date=datetime.date.fromisoformat(r['date']);r['week']=(date-datetime.timedelta(days=date.weekday())).isoformat()
 r['weather']='Unknown' if r['rain'] is None else 'Heavy rain' if r['rain']>=4 else 'Wet' if r['rain']>=1 else 'Dry'
 r['slot']='Evening' if r['kickoff']>='17:00' else 'Afternoon' if r['kickoff']>='14:00' else 'Lunchtime'
cur=[r for r in rows if r['season']=='2026-2027']
clubs=[dict(name=c['club'],short=short.get(c['club'],c['club']),region=c['region'],ground=c['ground']) for c in seed['clubs'] if c['club'] in {r['home'] for r in cur}]
meta=dict(season='2026-2027',reviewed='2026-09-20',through=max(r['date'] for r in cur),rounds=10,played=len(cur),recorded=sum(r['attendance'] is not None for r in cur),roundFixtureCount=8,fixtureSource='https://www.footballwebpages.co.uk/cymru-premier/fixtures-results',roundSource='https://faw.cymru/cymru-leagues/news/2026-27-novira-cymru-premier-phase-one-fixtures-released/',pendingFixture='Matchday 9: Cardiff Met v Haverfordwest is scheduled for 29 September.',seedCommit='f43c26f')
(ROOT/'data.json').write_text(json.dumps(dict(meta=meta,clubs=clubs,matches=rows,promotedBaselines=json.loads((ROOT/"data/promoted-baselines.json").read_text())),ensure_ascii=False,separators=(',',':')))
with (ROOT/'matches.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(cur[0]),lineterminator="\n");w.writeheader();w.writerows(cur)
print(json.dumps(meta,indent=2));print('Weather coverage',sum(r['rain'] is not None for r in cur),'/',len(cur))
