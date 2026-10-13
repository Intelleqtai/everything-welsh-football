"""Build the independent dashboard data from the frozen extract + verified additions."""
import csv,json,pathlib,datetime,hashlib,collections
ROOT=pathlib.Path(__file__).resolve().parents[1]
audit=json.loads((ROOT/'data/update-audit.json').read_text())
reviewed=audit['reviewed']
datetime.date.fromisoformat(reviewed)
seed=json.loads((ROOT/'data/study-snapshot.json').read_text())
weather=json.loads((ROOT/'data/weather-cache.json').read_text()) if (ROOT/'data/weather-cache.json').exists() else {}
short={'Airbus UK Broughton':'Airbus','Ammanford AFC':'Ammanford','Barry Town United':'Barry','Briton Ferry Llansawel':'Briton Ferry','Caernarfon Town':'Caernarfon','Cardiff Metropolitan University':'Cardiff Met','Connah\'s Quay Nomads':"Connah’s Quay",'Flint Town United':'Flint','Haverfordwest County':'Haverfordwest','Holywell Town':'Holywell','Llandudno FC':'Llandudno','Penybont FC':'Penybont','The New Saints':'TNS','Trefelin Boys & Girls Club':'Trefelin','Cambrian United':'Cambrian'}
def num(v):return float(v) if v not in ['',None] else None
def convert(r):
 return dict(id=r['season']+'-'+r['date']+'-'+r['home'],season=r['season'],date=r['date'],round=int(r['matchday']),home=r['home'],away=r['away'],attendance=num(r['attendance']),kickoff=r['kick_off'],homeScore=num(r['home_score']),awayScore=num(r['away_score']),temp=num(r['wx_temp']),rain=num(r['wx_precip_3h']),wind=num(r['wx_wind']),source='https://everythingwelshfootball.club/downloads/matches.csv',provenance='Frozen study extract · Football Web Pages / Transfermarkt',weatherSource='Frozen study extract · Open-Meteo',reviewed='2026-09-09')
rows=[convert(r) for r in seed['matches']]
for r in csv.DictReader((ROOT/'data/new-matches.csv').open()):
 c=dict(id='fwp-'+r['source'].split('/')[-1],season='2026-2027',date=r['date'],round=int(r['round']),home=r['home'],away=r['away'],attendance=num(r['attendance']),kickoff=r['kickoff'],homeScore=num(r['homeScore']),awayScore=num(r['awayScore']),temp=None,rain=None,wind=None,source='https://www.footballwebpages.co.uk/match/2026-2027/cymru-premier/'+r['source'],provenance='Football Web Pages',weatherSource=None,reviewed=reviewed)
 w=weather.get(r['home'],{}); h=w.get('data',{}).get('hourly',{}); key=r['date']+'T'+r['kickoff'][:2]+':00'
 if key in h.get('time',[]):
  i=h['time'].index(key); c['temp']=h['temperature_2m'][i];c['wind']=h['wind_speed_10m'][i]
  rain=h['precipitation'][i-2:i+1];c['rain']=round(sum(rain),2) if len(rain)==3 and all(v is not None for v in rain) else None
  c['weatherSource']=w['source']
 rows.append(c)
# Season audit: refresh every current-season weather record at the verified ground.
clubmap={c['club']:c for c in seed['clubs']}
travel={(r['from_club'],r['to_club']):r for r in csv.DictReader((ROOT.parent/'downloads/travel_matrix.csv').open())}
for r in rows:
 r['specialEvent']='Big Bont Bash · free entry' if r['date']=='2026-09-26' and r['home']=='Penybont FC' else ''
 r['excludeFromConditions']=bool(r['specialEvent'])
 origin='Flint Town United' if r['away']=="Connah's Quay Nomads" else r['away']
 destination='Flint Town United' if r['home']=="Connah's Quay Nomads" else r['home']
 route=travel.get((origin,destination),{})
 r['roadKm']=0 if origin==destination else num(route.get('road_km'))
 r['driveMinutes']=0 if origin==destination else num(route.get('drive_min'))
 r['travelSource']='Frozen routing matrix · ground-to-ground estimate'
 t=r['driveMinutes'];r['travelBand']='Unknown' if t is None else 'Under 45m' if t<45 else '45–60m' if t<60 else '1–2h' if t<120 else '2–3h' if t<180 else '3h+'
 r['venue']='Essity Stadium' if r['home']=="Connah's Quay Nomads" else clubmap[r['home']]['ground']
 if r['season']!='2026-2027': continue
 r['reviewed']=reviewed
 w=weather.get('Flint Town United' if r['home']=="Connah's Quay Nomads" else r['home'],{});h=w.get('data',{}).get('hourly',{});key=r['date']+'T'+r['kickoff'][:2]+':00'
 if r['home']=="Connah's Quay Nomads":
  r['temp']=r['rain']=r['wind']=None
  r['weatherSource']=None
 if key in h.get('time',[]):
  i=h['time'].index(key);r['temp']=h['temperature_2m'][i];r['wind']=h['wind_speed_10m'][i]
  rain=h['precipitation'][max(0,i-2):i+1];r['rain']=round(sum(rain),2) if len(rain)==3 and all(v is not None for v in rain) else None
  r['weatherSource']=w['source']

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
assert max(r['date'] for r in cur)<=audit['through'], 'Verify new fixtures and update data/update-audit.json before publishing'
assert audit['through']<=reviewed, 'Review cannot precede the verified fixture cutoff'
clubs=[dict(name=c['club'],short=short.get(c['club'],c['club']),region=c['region'],ground='Essity Stadium' if c['club']=="Connah's Quay Nomads" else c['ground']) for c in seed['clubs'] if c['club'] in {r['home'] for r in cur}]
meta=dict(season='2026-2027',reviewed=reviewed,through=max(r['date'] for r in cur),rounds=max(r['round'] for r in cur),played=len(cur),recorded=sum(r['attendance'] is not None for r in cur),roundFixtureCount=8,fixtureSource='https://www.footballwebpages.co.uk/cymru-premier/fixtures-results',roundSource='https://faw.cymru/cymru-leagues/news/2026-27-novira-cymru-premier-phase-one-fixtures-released/',pendingFixture='',seedCommit='f43c26f')
(ROOT/'data.json').write_text(json.dumps(dict(meta=meta,clubs=clubs,matches=rows,promotedBaselines=json.loads((ROOT/"data/promoted-baselines.json").read_text()),publishedBaselines=json.loads((ROOT/'data/published-baselines.json').read_text())),ensure_ascii=False,separators=(',',':')))
with (ROOT/'matches.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(cur[0]),lineterminator="\n");w.writeheader();w.writerows(cur)
print(json.dumps(meta,indent=2));print('Weather coverage',sum(r['rain'] is not None for r in cur),'/',len(cur))
