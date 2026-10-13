"""Merge the immutable historical study with the verified current-season feed.
Unknown contextual fields stay unknown; no attendance or covariate is invented.
"""
import csv,json,pathlib,datetime,collections,statistics
ROOT=pathlib.Path(__file__).resolve().parents[1]
out=ROOT/'output';out.mkdir(exist_ok=True)
original=list(csv.DictReader((ROOT/'study-tools/source/original-matches.csv').open()))
D=json.loads((ROOT/'2026-27/data.json').read_text())
current=[r for r in D['matches'] if r['season']==D['meta']['season']]
context=json.loads((ROOT/'study-tools/source/current-context.json').read_text())
weather=json.loads((ROOT/'2026-27/data/weather-cache.json').read_text())
clubs={r['club']:r for r in csv.DictReader((ROOT/'downloads/clubs.csv').open())}
old={(r['date'],r['home'],r['away']):r for r in original if r['season']==D['meta']['season']}
extra=['special_event','exclude_from_conditions','context_verified','source_url','weather_source','reviewed','venue']
fields=list(original[0])+extra
rows=[dict(r,special_event='',exclude_from_conditions=False,context_verified=True) for r in original if r['season']!=D['meta']['season']]
new=[]
for r in current:
 key=(r['date'],r['home'],r['away']);p=old.get(key);v={k:'' for k in fields}
 if p:v.update(p)
 day=datetime.date.fromisoformat(r['date']).strftime('%A');hour=int(r['kickoff'][:2]);slot='evening' if hour>=17 else 'afternoon' if hour>=14 else 'lunch'
 ko=day[:3]+' '+slot if day in ['Friday','Saturday','Sunday'] else 'Midweek'
 hr=clubs[r['home']]['region'];ar=clubs[r['away']]['region'];ft='-'.join(sorted([hr,ar]));t=r['driveMinutes']
 v.update(season=r['season'],date=r['date'],day_of_week=day,kick_off=r['kickoff'],kick_off_band=ko,home=r['home'],away=r['away'],home_region=hr,away_region=ar,fixture_type=ft,attendance=r['attendance'],attendance_source=r['provenance'],home_score=r['homeScore'],away_score=r['awayScore'],month=datetime.date.fromisoformat(r['date']).strftime('%b'),road_km=r['roadKm'],drive_min=t,travel_band='<1h' if t<60 else '1-2h' if t<120 else '2-3h' if t<180 else '>3h',derby=int(t<45),matchday=r['round'],excluded='',special_event=r['specialEvent'],exclude_from_conditions=r['excludeFromConditions'],context_verified=bool(p),source_url=r['source'],weather_source=r['weatherSource'],reviewed=r['reviewed'],venue=r['venue'])
 # Only source-reviewed calendar intervals can establish no clash / term time.
 if context['from']<=r['date']<=context['through']:
  regional={'Wrexham'} if hr=='North' else {'Cardiff City','Swansea City','Newport County'}
  same=[x for x in context['home_fixtures'] if x['date']==r['date']]
  relevant=[x['club'] for x in same if x['club'] in regional]
  v.update(clash=int(bool(relevant)),clash_any=int(bool(same)),clash_club=' + '.join(relevant),bank_holiday='')
  term=context['school_term']
  if term['from']<=r['date']<=term['through']:
   v.update(school_holiday='',in_school_holiday=term['in_school_holiday'],context_verified=True)
 # A blank clash/holiday is NOT a verified absence outside reviewed intervals.
 w=weather['Flint Town United' if r['home']=="Connah's Quay Nomads" else r['home']]['data']['hourly'];stamp=r['date']+'T'+r['kickoff'][:2]+':00';i=w['time'].index(stamp)
 mapping={'wx_temp':'temperature_2m','wx_feels':'apparent_temperature','wx_precipitation':'precipitation','wx_rain':'rain','wx_snowfall':'snowfall','wx_wind':'wind_speed_10m','wx_gust':'wind_gusts_10m','wx_cloud':'cloud_cover','wx_code':'weather_code'}
 for dest,src in mapping.items():v[dest]=w[src][i]
 assert all(v[k] is not None for k in mapping),key
 rain=sum(w['precipitation'][i-2:i+1]);v['wx_precip_3h']=round(rain,2);v['wx_wet']=int(rain>=1)
 v['wx_cond']='Snow' if v['wx_snowfall']>0 else 'Heavy rain' if rain>=4 else 'Rain' if rain>=1 else 'Drizzle' if rain>0 else 'Clear' if v['wx_cloud']<50 else 'Dry, overcast'
 # Original study bins are apparent temperature and gusts, not air temp and wind speed.
 temp=v['wx_feels'];gust=v['wx_gust']
 v['wx_temp_band']='Under 2°C' if temp<2 else '2-7°C' if temp<7 else '7-12°C' if temp<12 else '12-17°C' if temp<17 else 'Over 17°C'
 v['wx_wind_band']='Calm (<25 km/h gusts)' if gust<25 else 'Breezy (25-40)' if gust<40 else 'Windy (40-55)' if gust<55 else 'Gale (55+)'
 new.append(v)
# Pre-match form and table position: only results completed before that fixture.
points=collections.defaultdict(int);gd=collections.defaultdict(int);gf=collections.defaultdict(int);history=collections.defaultdict(list)
teams=sorted({r['home'] for r in new}|{r['away'] for r in new})
for stamp,g in __import__('itertools').groupby(sorted(new,key=lambda r:(r['date'],r['kick_off'])),key=lambda r:(r['date'],r['kick_off'])):
 batch=list(g);table=sorted(teams,key=lambda c:(-points[c],-gd[c],-gf[c],c))
 for r in batch:
  r['home_position']=1+sum((points[c],gd[c],gf[c])>(points[r['home']],gd[r['home']],gf[r['home']]) for c in teams) if any(history.values()) else ''
  r['home_form_5']=statistics.mean(history[r['home']][-5:]) if len(history[r['home']])>=3 else ''
 for r in batch:
  h,a=r['home'],r['away'];hs,aws=r['home_score'],r['away_score']
  if hs is None or aws is None:continue
  hp=3 if hs>aws else 1 if hs==aws else 0;ap=3 if aws>hs else 1 if hs==aws else 0
  for c,p in [(h,hp),(a,ap)]:points[c]+=p;history[c].append(p)
  gd[h]+=hs-aws;gd[a]+=aws-hs;gf[h]+=hs;gf[a]+=aws
rows+=new
# Historical rows stay byte-equivalent in their values. Recompute current indices.
means={c:statistics.mean([r['attendance'] for r in new if r['home']==c and r['attendance'] is not None]) for c in teams}
for r in new:
 r['home_season_avg']=means[r['home']];r['away_season_avg']=means[r['away']]
 r['attendance_index']=r['attendance']/means[r['home']] if r['attendance'] is not None else ''
rows.sort(key=lambda r:(r['date'],r['kick_off'],r['home']))
with (out/'matches.csv').open('w') as f:
 writer=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(rows)
(out/'current-baselines.json').write_text(json.dumps(D['publishedBaselines']+D['promotedBaselines']))
(out/'update-meta.json').write_text(json.dumps(D['meta']))
print('Merged',len(rows),'rows; current season',len(new),'recorded',sum(r['attendance'] is not None for r in new),'unknown contextual metadata',sum(not r['context_verified'] for r in new))
