"""Independent matrix-algebra verification of all stored regression coefficients and clustered intervals."""
import json,pandas as pd,numpy as np,patsy
from scipy.stats import t
D=json.load(open('output/data.json'));m=pd.read_csv('output/matches.csv');d=m[m.excluded.fillna('').eq('')&m.attendance.gt(0)].copy(); ncheck=0
flags=d.get("exclude_from_conditions",pd.Series(False,index=d.index)).fillna(False).astype(str).str.lower().isin(["true","1","1.0"])
d=d[~flags].copy()
for model in D['review']['models']:
 r=d.loc[model['rows']].copy();formula=model['formula']
 assert len(r)==model['n']
 assert not r.index.duplicated().any()
 r['trip']=pd.Categorical(np.where(r.derby.eq(1),'Derby',r.travel_band),['Derby','<1h','1-2h','2-3h','>3h'])
 r['kob']=pd.Categorical(r.kick_off_band,['Sat afternoon']+sorted(set(r.kick_off_band.dropna())-{'Sat afternoon'}))
 r['mo']=pd.Categorical(r.month, [v for v in ['Jul','Aug','Sep','Oct','Nov','Dec','Jan','Feb','Mar','Apr','May','Jun'] if v in set(r.month)]) if 'C(kob)' in formula or 'fri*ns' in formula else pd.Categorical(r.month)
 r['sea']=pd.Categorical(r.season,['2024-2025']+sorted(set(r.season)-{'2024-2025'})) if 'C(kob)' in formula else pd.Categorical(r.season)
 r['bh']=pd.Categorical(r.bank_holiday.fillna('Ordinary'),['Ordinary']+sorted(set(r.bank_holiday.dropna())))
 if 'C(sh)' not in formula and 'C(kob)' in formula:r['bh']=pd.Categorical(r.bank_holiday.fillna('Ordinary fixture'),['Ordinary fixture']+sorted(set(r.bank_holiday.dropna())))
 r['sh']=pd.Categorical(r.school_holiday.fillna('Term time'),['Term time']+sorted(set(r.school_holiday.dropna())))
 if 'fri*ns' in formula:r['bh']=pd.Categorical(r.bank_holiday.fillna('Ordinary'));r['sh']=pd.Categorical(r.school_holiday.fillna('Term'))
 r['fri']=r.kick_off_band.eq('Fri evening').astype(int);r['ns']=r.fixture_type.eq('North-South').astype(int)
 r['day']=pd.Categorical(np.where(r.day_of_week.isin(['Friday','Saturday','Sunday']),r.day_of_week,'Other'),['Saturday','Friday','Sunday','Other'])
 if '+C(travel_band)' in formula or ('C(day)' in formula and model['n'] in [D['day_model']['within']['n'],D['day_model']['cross']['n']]):r['day']=pd.Categorical(r.day_of_week,['Saturday','Friday','Sunday'])
 r['wet']=r.wx_precip_3h.ge(1).astype(float).where(r.wx_precip_3h.notna());r['heavy']=r.wx_precip_3h.ge(4).astype(float).where(r.wx_precip_3h.notna());r['gale']=r.wx_gust.ge(55).astype(float).where(r.wx_gust.notna());r['cold']=r.wx_feels.lt(5).astype(float).where(r.wx_feels.notna());r['log_att']=np.log(r.attendance)
 for col,levels in model["categories"].items():r[col]=pd.Categorical(r[col],levels)
 y,X=patsy.dmatrices(formula,r,return_type='dataframe');a=X.to_numpy();b=np.linalg.lstsq(a,y.to_numpy().ravel(),rcond=None)[0];res=y.to_numpy().ravel()-a@b;bread=np.linalg.pinv(a)@np.linalg.pinv(a).T;groups=r.loc[X.index,'home'].to_numpy();G=np.unique(groups);rank=np.linalg.matrix_rank(a);scores=np.array([a[groups==g].T@res[groups==g] for g in G]);cov=bread@scores.T@scores@bread*len(G)/(len(G)-1)*(len(a)-1)/(len(a)-len(model["terms"]))
 assert len(a)==model['n'],(formula,len(a),model['n'])
 for name,v in model['terms'].items():
  j=X.columns.get_loc(name);se=np.sqrt(cov[j,j]);delta=t.ppf(.975,len(G)-1)*se
  for got,expected in [(b[j],v['beta']),(np.expm1(b[j]-delta)*100,v['lo']),(np.expm1(b[j]+delta)*100,v['hi'])]:assert np.isclose(got,expected,rtol=1e-6,atol=1e-6),(formula,name,got,expected)
  ncheck+=3
print(ncheck,'independent coefficient/interval checks passed across',len(D['review']['models']),'models')
