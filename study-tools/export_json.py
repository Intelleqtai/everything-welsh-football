"""Everything the visual report needs, as one JSON bundle."""
import json, pathlib, warnings
import pandas as pd, numpy as np, statsmodels.formula.api as smf
from scipy import stats as st
warnings.filterwarnings("ignore")
MODEL_AUDIT=[]
def fit_reviewed(model):
    eligible=len(model.data.frame)
    frame=model.data.frame.loc[model.data.row_labels].copy()
    for col in frame.select_dtypes(include="category"):
        frame[col]=frame[col].cat.remove_unused_categories()
    frame["home"]=pd.Categorical(frame.home)
    model=smf.ols(model.formula,data=frame)
    plain=model.fit()
    result=model.fit(cov_type="cluster",cov_kwds={"groups":frame["home"],"use_correction":True,"df_correction":True},use_t=True)
    MODEL_AUDIT.append({"formula":model.formula,"n":int(result.nobs),"clusters":int(frame.home.nunique()),"rows":[int(i) for i in frame.index],"first":str(frame.date.min().date()),"last":str(frame.date.max().date()),"current_n":int(frame.season.eq(max(all_d.season)).sum()),"eligible":int(eligible),"omitted":int(eligible-result.nobs),"categories":{c:list(frame[c].cat.categories) for c in frame.select_dtypes(include="category")},
      "terms":{k:{"beta":float(result.params[k]),"pct":float(np.expm1(result.params[k])*100),
       "lo":float(np.expm1(result.conf_int().loc[k,0])*100),"hi":float(np.expm1(result.conf_int().loc[k,1])*100),
       "p":float(result.pvalues[k]),"ordinary_lo":float(np.expm1(plain.conf_int().loc[k,0])*100),"ordinary_hi":float(np.expm1(plain.conf_int().loc[k,1])*100)} for k in result.params.index}})
    if "wet" in result.params and "heavy" in result.params:
        test=result.t_test("wet + heavy = 0")
        lo,hi=test.conf_int()[0]
        MODEL_AUDIT[-1]["heavy_vs_dry"]={"pct":float(np.expm1(float(test.effect[0]))*100),"lo":float(np.expm1(lo)*100),"hi":float(np.expm1(hi)*100),"p":float(test.pvalue)}
    return result


m=pd.read_csv("output/matches.csv",parse_dates=["date"]); m["excluded"]=m.excluded.fillna("")
d=m[(m.excluded=="")&m.attendance.notna()].copy()
all_d=d.copy()
flag=m.get("exclude_from_conditions",pd.Series(False,index=m.index)).fillna(False).astype(str).str.lower().isin(["true","1","1.0"])
d=d.loc[~flag.loc[d.index]].copy()
d["attendance_index"]=d.attendance/d.groupby(["season","home"]).attendance.transform("mean")
d["sy"]=d.season.str[:4].astype(int)
context=d.get("context_verified",pd.Series(True,index=d.index)).fillna(False).astype(str).str.lower().isin(["true","1","1.0"])
BANDS=["<1h","1-2h","2-3h",">3h"]
DAYS=[x for x in ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"] if x in set(d.day_of_week)]
MO=[x for x in ["Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar","Apr","May","Jun"] if x in set(d.month)]
def ci95(s):
    s=pd.Series(s).dropna()
    if len(s)<2: return 0.0
    return float(st.t.ppf(.975,len(s)-1)*s.std(ddof=1)/np.sqrt(len(s)))
def block(g,key):
    return [dict(k=str(k), idx=round(float(v.attendance_index.mean()),3),
                 ci=round(ci95(v.attendance_index),3), raw=round(float(v.attendance.mean())),
                 n=int(len(v))) for k,v in g]
B={}
B["meta"]=dict(fixtures=int(len(all_d)), clubs=int(all_d.home.nunique()), seasons=sorted(all_d.season.unique()),
    first=str(all_d.date.min().date()), last=str(all_d.date.max().date()),
    total=int(all_d.attendance.sum()), mean=round(float(all_d.attendance.mean())),
    median=int(all_d.attendance.median()), max=int(all_d.attendance.max()),
    min=int(all_d.attendance.min()), far_pct=round(float((d.travel_band==">3h").mean()*100)),
    derby_pct=round(float(d.derby.mean()*100)), excluded_bcd=int((m.excluded=="behind closed doors").sum()),
    conditions_fixtures=int(len(d)), conditions_excluded=int(len(all_d)-len(d)), missing=int(((m.excluded=="")&m.attendance.isna()).sum()))

# day: raw vs travel-standardised
mix=d.travel_band.value_counts(normalize=True)
cell=d.pivot_table(index="day_of_week",columns="travel_band",values="attendance_index",aggfunc="mean")
wts=(cell.notna()*mix); adj=(cell.fillna(0)*mix).sum(axis=1)/wts.sum(axis=1)
B["day"]=[dict(k=day, raw=round(float(d[d.day_of_week==day].attendance_index.mean()),3),
    adj=round(float(adj[day]),3), ci=round(ci95(d[d.day_of_week==day].attendance_index),3),
    rawatt=round(float(d[d.day_of_week==day].attendance.mean())),
    far=round(float((d[d.day_of_week==day].travel_band==">3h").mean()*100)),
    n=int((d.day_of_week==day).sum())) for day in DAYS]
B["kickoff"]=sorted(block(d.groupby("kick_off_band"),"k"),key=lambda r:-r["idx"])
B["travel"]=[r for k in BANDS for r in block(d[d.travel_band==k].groupby("travel_band"),"k")]
B["region"]=sorted(block(d.groupby("fixture_type"),"k"),key=lambda r:-r["idx"])
B["month"]=[r for k in MO for r in block(d[d.month==k].groupby("month"),"k")]
d["bh_lbl"]=d.bank_holiday.fillna("Ordinary fixture").where(context)
B["bh"]=sorted(block(d.groupby("bh_lbl"),"k"),key=lambda r:-r["idx"])
d["derby_lbl"]=np.where(d.derby==1,"Derby (under 45 min)","Everything else")
B["derby"]=block(d.groupby("derby_lbl"),"k")

# day x travel grid
grid=[]
for day in DAYS:
    for b in BANDS:
        s=d[(d.day_of_week==day)&(d.travel_band==b)]
        grid.append(dict(day=day,band=b,idx=round(float(s.attendance_index.mean()),3) if len(s) else None,n=int(len(s))))
B["grid"]=grid

# derby pairs
dp=(d[d.derby==1].groupby(["home","away"]).agg(idx=("attendance_index","mean"),
    n=("attendance_index","size"),raw=("attendance","mean")).query("n>=4").sort_values("idx",ascending=False))
B["derby_pairs"]=[dict(home=h,away=a,idx=round(r.idx,2),raw=round(r.raw),n=int(r.n)) for (h,a),r in dp.iterrows()]

# opponent pull
pl=(d.groupby("away").agg(idx=("attendance_index","mean"),n=("attendance_index","size"),
    raw=("attendance","mean"),drive=("drive_min","mean")).query("n>=10").sort_values("idx",ascending=False))
B["pull"]=[dict(k=k,idx=round(r.idx,3),raw=round(r.raw),n=int(r.n),drive=round(r.drive)) for k,r in pl.iterrows()]

# season trend + modelled effect
sea=all_d.groupby("season").agg(mean=("attendance","mean"),median=("attendance","median"),
    n=("attendance","size"),total=("attendance","sum"))
r=d[d.attendance>0].copy()
r["trip"]=pd.Categorical(np.where(r.derby==1,"Derby",r.travel_band),["Derby"]+BANDS)
r["kob"]=pd.Categorical(r.kick_off_band,["Sat afternoon"]+[c for c in r.kick_off_band.dropna().unique() if c!="Sat afternoon"])
r["bh"]=pd.Categorical(r.bh_lbl,["Ordinary fixture"]+sorted(set(r.bh_lbl.dropna())-{"Ordinary fixture"}))
r["mo"]=pd.Categorical(r.month,MO)
r["sea"]=pd.Categorical(r.season,["2024-2025"]+[s for s in sorted(r.season.unique()) if s!="2024-2025"])
r["log_att"]=np.log(r.attendance)
mod=fit_reviewed(smf.ols("log_att ~ C(sea)+C(kob)+C(trip)+C(mo)+C(bh)+home_form_5+C(home)",data=r))
co=pd.DataFrame({"pct":(np.exp(mod.params)-1)*100,"lo":(np.exp(mod.conf_int()[0])-1)*100,
                 "hi":(np.exp(mod.conf_int()[1])-1)*100,"p":mod.pvalues})
se={i.split("T.")[1].rstrip("]"):row for i,row in co[co.index.str.contains(r"C\(sea\)")].iterrows()}
B["trend"]=[dict(k=s, mean=round(float(sea.loc[s,"mean"])), median=int(sea.loc[s,"median"]),
    n=int(sea.loc[s,"n"]), total=int(sea.loc[s,"total"]),
    eff=0.0 if s=="2024-2025" else round(float(se[s].pct),1),
    lo=0.0 if s=="2024-2025" else round(float(se[s].lo),1),
    hi=0.0 if s=="2024-2025" else round(float(se[s].hi),1),
    sig=bool(s!="2024-2025" and se[s].p<0.05)) for s in sorted(sea.index)]
B["model"]=dict(n=int(mod.nobs),r2=round(float(mod.rsquared),3))

def lab(i):
    return (i.replace("C(kob)[T.","").replace("C(trip)[T.","").replace("C(mo)[T.","")
             .replace("C(bh)[T.","").rstrip("]").replace("home_form_5","Form: +1 point per game"))
keep=co[co.index.str.contains("kob|trip|mo\\(|C\\(mo|bh|form")]
B["coef"]=[dict(k=lab(i), pct=round(float(r.pct),1), lo=round(float(r.lo),1),
    hi=round(float(r.hi),1), sig=bool(r.p<0.05),
    grp=("Kick-off slot" if "kob" in i else "Away journey" if "trip" in i
         else "Month" if "mo" in i.lower() and "C(mo" in i else "Bank holiday" if "bh" in i else "Form"))
    for i,r in keep.iterrows()]

# Current season-to-date against published previous full-season home averages.
latest=sorted(all_d.season.unique())[-1]
base=json.loads(pathlib.Path("output/current-baselines.json").read_text())
lookup={x["club"]:x for x in base}
league_base=[x for x in base if x.get("division")=="Cymru Premier" and x.get("total") is not None]
previous_total=sum(x["total"] for x in league_base);previous_n=sum(x["matches"] for x in league_base)
current_crowds=all_d[all_d.season.eq(latest)].attendance
B["league_growth"]={"previous_total":previous_total,"previous_n":previous_n,"previous_average":previous_total/previous_n,"current_total":int(current_crowds.sum()),"current_n":len(current_crowds),"current_average":float(current_crowds.mean()),"pct":float((current_crowds.mean()/(previous_total/previous_n)-1)*100),"source":league_base[0]["source"],"basis":"Current season to date versus published full previous season"}

exp=[]
for club,g in all_d[all_d.season.eq(latest)].groupby("home"):
    if club not in lookup: raise ValueError("Missing published baseline: "+club)
    prior=lookup[club]; prev=float(prior["average"]); now=float(g.attendance.mean())
    exp.append(dict(k=club,prev=round(prev),now=round(now),chg=round((now/prev-1)*100),
      previous_exact=prev,current_exact=now,n=len(g),division=prior.get("division"),
      approximate=bool(prior.get("rounded",False)),source=prior.get("source")))
B["expansion"]=sorted(exp,key=lambda x:x["chg"])
changes=[(x["current_exact"]/x["previous_exact"]-1)*100 for x in exp]
B["expansion_stats"]=dict(median=round(float(np.median(changes))),mean=round(float(np.mean(changes))),n=len(exp),
  current_season=latest,through=str(all_d.date.max().date()),comparison="Current season to date versus previous full-season published average")

# club x season matrix + club summary
cs=all_d.pivot_table(index="home",columns="season",values="attendance",aggfunc="mean").round(0)
B["club_season"]=[dict(club=c,**{s:(None if pd.isna(v) else int(v)) for s,v in row.items()}) for c,row in cs.iterrows()]
cl=(all_d.groupby("home").agg(avg=("attendance","mean"),n=("attendance","size"),best=("attendance","max"),
    region=("home_region","first"),drive=("drive_min","mean")).sort_values("avg",ascending=False))
B["clubs"]=[dict(k=k,avg=round(r.avg),n=int(r.n),best=int(r.best),region=r.region,drive=round(r.drive)) for k,r in cl.iterrows()]

# first/last home game
d2=d[d.season.ne(latest)].sort_values("date").copy()
d2["gm"]=d2.groupby(["season","home"]).cumcount()+1
d2["tot"]=d2.groupby(["season","home"]).home.transform("size")
d2["slot"]=np.where(d2.gm==1,"First home game",np.where(d2.gm==d2.tot,"Last home game","Everything else"))
B["firstlast"]=block(d2.groupby("slot"),"k")

# form & position bins
dd=d.dropna(subset=["home_position","home_form_5"])
pb=pd.cut(dd.home_position,[0,4,8,12,16],labels=["1st-4th","5th-8th","9th-12th","13th-16th"])
B["position"]=[dict(k=str(k),idx=round(float(v.attendance_index.mean()),3),ci=round(ci95(v.attendance_index),3),n=int(len(v))) for k,v in dd.groupby(pb,observed=True)]
fb=pd.cut(dd.home_form_5,[-0.01,1,1.6,2.2,3],labels=["0-1.0","1.0-1.6","1.6-2.2","2.2-3.0"])
B["form"]=[dict(k=str(k),idx=round(float(v.attendance_index.mean()),3),ci=round(ci95(v.attendance_index),3),n=int(len(v))) for k,v in dd.groupby(fb,observed=True)]
B["corr"]=dict(pos_r=round(float(st.pearsonr(dd.home_position,dd.attendance_index)[0]),3),
               pos_p=float(st.pearsonr(dd.home_position,dd.attendance_index)[1]),
               form_r=round(float(st.pearsonr(dd.home_form_5,dd.attendance_index)[0]),3),
               form_p=float(st.pearsonr(dd.home_form_5,dd.attendance_index)[1]))

# fri vs sat within band
fs=[]
for bd in BANDS:
    row=dict(band=bd)
    for day in ["Friday","Saturday"]:
        s=d[(d.day_of_week==day)&(d.travel_band==bd)]
        row[day.lower()]=round(float(s.attendance_index.mean()),3) if len(s) else None
        row[day.lower()+"_n"]=int(len(s))
    fs.append(row)
B["frisat"]=fs

# scatter: every fixture, drive time vs index
B["scatter"]=[dict(x=int(r.drive_min),y=round(float(r.attendance_index),3),a=int(r.attendance),
    s=r.season[2:4]+"/"+r.season[-2:], h=r.home, aw=r.away, d=r.day_of_week[:3])
    for r in d.itertuples() if pd.notna(r.drive_min) and pd.notna(r.attendance_index)]
# distribution
B["dist"]=[int(x) for x in all_d.attendance]
# day mix by season (scheduling shift)
mix2=(pd.crosstab(d.season,d.day_of_week,normalize="index")*100).round(1)
B["daymix"]=[dict(season=s,**{c:float(mix2.loc[s,c]) for c in mix2.columns}) for s in mix2.index]
tb=(pd.crosstab(d.season,d.travel_band,normalize="index")*100)[BANDS].round(1)
B["travelmix"]=[dict(season=s,**{c:float(tb.loc[s,c]) for c in BANDS}) for s in tb.index]
# biggest crowds
B["top"]=[dict(season=r.season,date=str(r.date.date()),home=r.home,away=r.away,att=int(r.attendance),
    day=r.day_of_week,ko=r.kick_off) for r in all_d.nlargest(12,"attendance").itertuples()]


# ---------------- weather ----------------
import statsmodels.formula.api as _smf
wd=d[d.wx_cond.notna()].copy()
def wblock(g):
    return [dict(k=str(k),idx=round(float(v.attendance_index.mean()),3),ci=round(ci95(v.attendance_index),3),
                 raw=round(float(v.attendance.mean())),n=int(len(v))) for k,v in g if len(v)>0]
CONDS=["Clear","Dry, overcast","Drizzle","Rain","Heavy rain","Snow"]
B["wx_cond"]=[r for c in CONDS for r in wblock(wd[wd.wx_cond==c].groupby("wx_cond"))]
TB=["Under 2°C","2-7°C","7-12°C","12-17°C","Over 17°C"]
B["wx_temp"]=[r for c in TB for r in wblock(wd[wd.wx_temp_band==c].groupby("wx_temp_band"))]
WB=["Calm (<25 km/h gusts)","Breezy (25-40)","Windy (40-55)","Gale (55+)"]
B["wx_wind"]=[r for c in WB for r in wblock(wd[wd.wx_wind_band==c].groupby("wx_wind_band"))]
wd["wet"]=(wd.wx_precip_3h>=1).astype(float).where(wd.wx_precip_3h.notna())
rx=[]
for b in BANDS:
    for lab,val in [("Dry",0),("Wet",1)]:
        s_=wd[(wd.travel_band==b)&(wd.wet==val)]
        rx.append(dict(band=b,wet=lab,idx=round(float(s_.attendance_index.mean()),3) if len(s_) else None,
                       raw=round(float(s_.attendance.mean())) if len(s_) else None,n=int(len(s_))))
B["wx_raindist"]=rx
# model with weather
wm=wd[wd.attendance>0].copy()
wm["trip"]=pd.Categorical(np.where(wm.derby==1,"Derby",wm.travel_band),["Derby"]+BANDS)
wm["kob"]=pd.Categorical(wm.kick_off_band,["Sat afternoon"]+[c for c in wm.kick_off_band.dropna().unique() if c!="Sat afternoon"])
wm["bh"]=pd.Categorical(wm.bh_lbl,["Ordinary fixture"]+sorted(set(wm.bh_lbl.dropna())-{"Ordinary fixture"}))
wm["mo"]=pd.Categorical(wm.month,MO)
wm["sea"]=pd.Categorical(wm.season,["2024-2025"]+[x for x in sorted(wm.season.unique()) if x!="2024-2025"])
wm["log_att"]=np.log(wm.attendance)
wm["wet"]=(wm.wx_precip_3h>=1).astype(float).where(wm.wx_precip_3h.notna()); wm["heavy"]=(wm.wx_precip_3h>=4).astype(float).where(wm.wx_precip_3h.notna())
wm["gale"]=(wm.wx_gust>=55).astype(float).where(wm.wx_gust.notna()); wm["cold"]=(wm.wx_feels<5).astype(float).where(wm.wx_feels.notna())
wmod=fit_reviewed(_smf.ols("log_att ~ C(sea)+C(kob)+C(trip)+C(mo)+C(bh)+home_form_5+C(home)+wet+heavy+gale+cold",data=wm))
wco=pd.DataFrame({"pct":(np.exp(wmod.params)-1)*100,"lo":(np.exp(wmod.conf_int()[0])-1)*100,
                  "hi":(np.exp(wmod.conf_int()[1])-1)*100,"p":wmod.pvalues})
NAMES={"wet":"Rain (1mm+ before kick-off)","heavy":"Additional heavy (4mm+ beyond wet)",
       "gale":"Gales (55+ km/h gusts)","cold":"Cold (feels under 5°C)"}
B["wx_coef"]=[dict(k=NAMES[i],pct=round(float(wco.loc[i,"pct"]),1),lo=round(float(wco.loc[i,"lo"]),1),
    hi=round(float(wco.loc[i,"hi"]),1),sig=bool(wco.loc[i,"p"]<0.05),
    n=int(wm[i].sum())) for i in ["heavy","wet","cold","gale"]]
B["wx_meta"]=dict(n=int(wmod.nobs),r2=round(float(wmod.rsquared),3),
                  wettest=int(wd.wx_precip_3h.max()*10)/10,
                  coldest=round(float(wd.wx_feels.min()),1),windiest=round(float(wd.wx_gust.max())))


# ---------------- clashes + school holidays + FULL model ----------------
fd=d[d.wx_cond.notna()&(d.attendance>0)&context].copy()
fd["trip"]=pd.Categorical(np.where(fd.derby==1,"Derby",fd.travel_band),["Derby"]+BANDS)
fd["kob"]=pd.Categorical(fd.kick_off_band,["Sat afternoon"]+[c for c in fd.kick_off_band.dropna().unique() if c!="Sat afternoon"])
fd["bh"]=pd.Categorical(fd.bank_holiday.fillna("Ordinary"),["Ordinary"]+sorted(set(fd.bank_holiday.dropna())))
fd["mo"]=pd.Categorical(fd.month,MO)
fd["sea"]=pd.Categorical(fd.season,["2024-2025"]+[x for x in sorted(fd.season.unique()) if x!="2024-2025"])
fd["sh"]=pd.Categorical(fd.school_holiday.fillna("Term time"),["Term time"]+sorted(set(fd.school_holiday.dropna())))
fd["wet"]=(fd.wx_precip_3h>=1).astype(float).where(fd.wx_precip_3h.notna()); fd["heavy"]=(fd.wx_precip_3h>=4).astype(float).where(fd.wx_precip_3h.notna())
fd["cold"]=(fd.wx_feels<5).astype(float).where(fd.wx_feels.notna()); fd["log_att"]=np.log(fd.attendance)
fmod=fit_reviewed(_smf.ols("log_att ~ C(sea)+C(kob)+C(trip)+C(mo)+C(bh)+C(sh)+home_form_5+C(home)+wet+heavy+cold+clash",data=fd))
fco=pd.DataFrame({"pct":(np.exp(fmod.params)-1)*100,"lo":(np.exp(fmod.conf_int()[0])-1)*100,
                  "hi":(np.exp(fmod.conf_int()[1])-1)*100,"p":fmod.pvalues})
PRETTY={"clash":"Big Welsh club at home same day","heavy":"Additional heavy precipitation (beyond wet)",
        "wet":"Rain before kick-off","cold":"Cold (feels under 5\u00b0C)",
        "home_form_5":"Form: +1 point per game"}
def flab(i):
    if i in PRETTY: return PRETTY[i]
    t=(i.replace("C(kob)[T.","").replace("C(trip)[T.","").replace("C(mo)[T.","")
        .replace("C(bh)[T.","").replace("C(sh)[T.","").rstrip("]"))
    if "C(trip)" in i: return t+" away trip"
    if "C(sh)" in i: return t+" school holiday"
    if "C(bh)" in i: return t+" fixture"
    if "C(mo)" in i: return "Month: "+t
    return t
fkeep=fco[fco.index.str.contains(r"kob|trip|C\(mo|C\(bh|C\(sh|clash|heavy|^wet$|^cold$|home_form_5")]
B["coef"]=[dict(k=flab(i),pct=round(float(r.pct),1),lo=round(float(r.lo),1),hi=round(float(r.hi),1),
    sig=bool(r.p<0.05),
    grp=("Away journey" if "trip" in i else "Weather" if i in ("wet","heavy","cold")
         else "Clash" if i=="clash" else "School holiday" if "C(sh)" in i
         else "Kick-off slot" if "kob" in i else "Bank holiday" if "C(bh)" in i
         else "Form" if "form" in i else "Month"))
    for i,r in fkeep.iterrows()]
B["model"]=dict(n=int(fmod.nobs),r2=round(float(fmod.rsquared),3))
B["clash"]=[dict(k=str(k),idx=round(float(v.attendance_index.mean()),3),ci=round(ci95(v.attendance_index),3),
    raw=round(float(v.attendance.mean())),n=int(len(v)))
    for k,v in d.groupby(d.clash.map({0:"No clash",1:"Big club at home"}))]
sat=d[d.day_of_week=="Saturday"]
B["clash_sat"]=[dict(k=str(k),idx=round(float(v.attendance_index.mean()),3),
    raw=round(float(v.attendance.mean())),n=int(len(v)))
    for k,v in sat.groupby(sat.clash.map({0:"No clash",1:"Big club at home"}))]
cb=(d[d.clash==1].groupby("clash_club").agg(idx=("attendance_index","mean"),
    n=("attendance_index","size"),raw=("attendance","mean")).query("n>=20").sort_values("idx"))
B["clash_by_club"]=[dict(k=k,idx=round(r.idx,3),n=int(r.n),raw=round(r.raw)) for k,r in cb.iterrows()]
SH=["Christmas","Summer","Easter","February half-term","October half-term","Term time"]
shg=d[context].groupby(d.loc[context,"school_holiday"].fillna("Term time"))
B["school"]=[dict(k=str(k),idx=round(float(v.attendance_index.mean()),3),ci=round(ci95(v.attendance_index),3),
    raw=round(float(v.attendance.mean())),n=int(len(v))) for k,v in shg if str(k) in SH]
B["school"].sort(key=lambda r:-r["idx"])
B["clash_mix"]=dict(sat_pct=round(float((d[d.clash==1].day_of_week=="Saturday").mean()*100)),
                    far_pct=round(float((d[d.clash==1].travel_band==">3h").mean()*100)),
                    far_pct_no=round(float((d[d.clash==0].travel_band==">3h").mean()*100)))


# ---------------- cross-country vs within-region, and Friday inside each ----------------
from scipy import stats as _st
d["cross"]=np.where(d.fixture_type=="North-South","North v South","Within region")
B["cross"]=[dict(k=str(k),idx=round(float(v.attendance_index.mean()),3),ci=round(ci95(v.attendance_index),3),
    raw=round(float(v.attendance.mean())),n=int(len(v))) for k,v in d.groupby("cross")]
fs2=[]
for grp in ["Within region","North v South"]:
    g=d[(d.cross==grp)&d.day_of_week.isin(["Friday","Saturday"])]
    f=g[g.day_of_week=="Friday"].attendance_index; sa=g[g.day_of_week=="Saturday"].attendance_index
    tt=_st.ttest_ind(f,sa,equal_var=False)
    fs2.append(dict(k=grp,fri=round(float(f.mean()),3),fri_n=int(len(f)),
                    sat=round(float(sa.mean()),3),sat_n=int(len(sa)),
                    gap=round(float((f.mean()/sa.mean()-1)*100),1),
                    p=float(tt.pvalue),sig=bool(tt.pvalue<0.05)))
B["cross_friday"]=fs2
rr=d[(d.attendance>0)&context].copy()
rr["trip"]=pd.Categorical(np.where(rr.derby==1,"Derby",rr.travel_band),["Derby"]+BANDS)
rr["mo"]=pd.Categorical(rr.month,MO); rr["sea"]=pd.Categorical(rr.season)
rr["bh"]=pd.Categorical(rr.bank_holiday.fillna("Ordinary"))
rr["sh"]=pd.Categorical(rr.school_holiday.fillna("Term"))
rr["fri"]=(rr.kick_off_band=="Fri evening").astype(int)
rr["ns"]=(rr.fixture_type=="North-South").astype(int)
rr["log_att"]=np.log(rr.attendance)
im=fit_reviewed(_smf.ols("log_att ~ fri*ns + C(trip)+C(mo)+C(sea)+C(bh)+C(sh)+home_form_5+C(home)",data=rr))
ic=pd.DataFrame({"pct":(np.exp(im.params)-1)*100,"lo":(np.exp(im.conf_int()[0])-1)*100,
                 "hi":(np.exp(im.conf_int()[1])-1)*100,"p":im.pvalues})
B["friday_split"]=dict(
    within=dict(pct=round(float(ic.loc["fri","pct"]),1),lo=round(float(ic.loc["fri","lo"]),1),
                hi=round(float(ic.loc["fri","hi"]),1),sig=bool(ic.loc["fri","p"]<0.05)),
    cross=dict(pct=round(float((np.exp(im.params["fri"]+im.params["fri:ns"])-1)*100),1)),
    interaction=dict(pct=round(float(ic.loc["fri:ns","pct"]),1),lo=round(float(ic.loc["fri:ns","lo"]),1),
                     hi=round(float(ic.loc["fri:ns","hi"]),1),sig=bool(ic.loc["fri:ns","p"]<0.05)),
    n=int(im.nobs))


# ---------------- North v South, day by day (the decisive table) ----------------
_ns=d[d.fixture_type=="North-South"]; _wr=d[d.fixture_type!="North-South"]
def _blk(g):
    x=g.attendance_index.dropna()
    return dict(n=int(len(x)),idx=round(float(x.mean()),3) if len(x) else None,
                ci=round(ci95(x),3) if len(x)>1 else None,
                raw=round(float(g.attendance.mean())) if len(g) else None)
B["ns_by_day"]=[dict(k=day, cross=_blk(_ns[_ns.day_of_week==day]), within=_blk(_wr[_wr.day_of_week==day]))
                for day in ["Friday","Saturday","Sunday"]]
_t=[]
for a,b_ in [("Friday","Saturday"),("Sunday","Saturday"),("Sunday","Friday")]:
    x=_ns[_ns.day_of_week==a].attendance_index.dropna(); y=_ns[_ns.day_of_week==b_].attendance_index.dropna()
    tt=_st.ttest_ind(x,y,equal_var=False)
    _t.append(dict(a=a,b=b_,gap=round(float((x.mean()/y.mean()-1)*100),1),p=float(tt.pvalue),
                   sig=bool(tt.pvalue<0.05),na=int(len(x)),nb=int(len(y))))
B["ns_tests"]=_t
_an=_ns.attendance_index.dropna(); _aw=_wr.attendance_index.dropna()
_tt=_st.ttest_ind(_an,_aw,equal_var=False)
B["ns_overall"]=dict(cross=round(float(_an.mean()),3),within=round(float(_aw.mean()),3),
    n_cross=int(len(_an)),n_within=int(len(_aw)),
    gap=round(float((_an.mean()/_aw.mean()-1)*100),1),p=float(_tt.pvalue))


# ---------------- cross-country: day effect with club, month and season held constant ----------------
_r=_ns[_ns.attendance>0].copy()
_r["day"]=pd.Categorical(np.where(_r.day_of_week.isin(["Friday","Saturday","Sunday"]),_r.day_of_week,"Other"),
                         ["Saturday","Friday","Sunday","Other"])
_r["mo"]=pd.Categorical(_r.month); _r["sea"]=pd.Categorical(_r.season)
_r["log_att"]=np.log(_r.attendance)
_mm=fit_reviewed(_smf.ols("log_att ~ C(day)+C(mo)+C(sea)+C(home)+home_form_5",data=_r))
_cc=pd.DataFrame({"pct":(np.exp(_mm.params)-1)*100,"lo":(np.exp(_mm.conf_int()[0])-1)*100,
                  "hi":(np.exp(_mm.conf_int()[1])-1)*100,"p":_mm.pvalues})
B["ns_day_model"]={}
for dd in ["Friday","Sunday"]:
    k=f"C(day)[T.{dd}]"
    if k in _cc.index:
        B["ns_day_model"][dd]=dict(pct=round(float(_cc.loc[k,"pct"]),1),lo=round(float(_cc.loc[k,"lo"]),1),
                                   hi=round(float(_cc.loc[k,"hi"]),1),sig=bool(_cc.loc[k,"p"]<0.05),
                                   p=round(float(_cc.loc[k,"p"]),3))
B["ns_day_model"]["n"]=int(_mm.nobs)
# how the Sunday sample is composed (the confound)
_sun=_ns[_ns.day_of_week=="Sunday"]
B["ns_sunday_mix"]=dict(n=int(len(_sun)),
    aug_apr=int(_sun.month.isin(["Aug","Apr"]).sum()),
    pct=round(float(_sun.month.isin(["Aug","Apr"]).mean()*100)))


# ---------------- THE day-of-week question, answered directly ----------------
# Friday v Saturday v Sunday, whole days (not kick-off slots), club/month/season/form held constant.
_dd=d[d.day_of_week.isin(["Friday","Saturday","Sunday"])&(d.attendance>0)].copy()
def _daymod(df, extra=""):
    df=df.copy()
    df["day"]=pd.Categorical(df.day_of_week,["Saturday","Friday","Sunday"])
    df["mo"]=pd.Categorical(df.month); df["sea"]=pd.Categorical(df.season)
    df["log_att"]=np.log(df.attendance)
    mod=fit_reviewed(_smf.ols("log_att ~ C(day)+C(mo)+C(sea)+C(home)+home_form_5"+extra,data=df))
    co=pd.DataFrame({"pct":(np.exp(mod.params)-1)*100,"lo":(np.exp(mod.conf_int()[0])-1)*100,
                     "hi":(np.exp(mod.conf_int()[1])-1)*100,"p":mod.pvalues})
    out={"n":int(mod.nobs)}
    for day in ["Friday","Sunday"]:
        k=f"C(day)[T.{day}]"
        if k in co.index:
            out[day]=dict(pct=round(float(co.loc[k,"pct"]),1),lo=round(float(co.loc[k,"lo"]),1),
                          hi=round(float(co.loc[k,"hi"]),1),p=round(float(co.loc[k,"p"]),3),
                          sig=bool(co.loc[k,"p"]<0.05))
    for day in ["Friday","Saturday","Sunday"]:
        g=df[df.day_of_week==day]
        out.setdefault("raw",{})[day]=dict(n=int(len(g)),idx=round(float(g.attendance_index.mean()),3),
                                           att=round(float(g.attendance.mean())))
    return out
B["day_model"]=dict(
    all=_daymod(_dd,"+C(travel_band)"),
    within=_daymod(_dd[_dd.fixture_type!="North-South"]),
    cross=_daymod(_dd[_dd.fixture_type=="North-South"]))

B["review"]={"date":json.loads(pathlib.Path("output/update-meta.json").read_text())["reviewed"],"condition_normalisation":"Home club-season mean excluding flagged special events; totals and growth include all crowds","firstlast_scope":"Completed seasons only; first and last recorded home fixtures","context_known":int(context.sum()),"context_unknown":int((~context).sum()),"full_model_current_n":int(fd.loc[fmod.model.data.row_labels,"season"].eq(latest).sum()),"full_model_current_eligible":int(d.season.eq(latest).sum()),"uncertainty":"95% intervals clustered by home club; t reference with clusters minus one degrees of freedom", "rain_window":"Three complete hourly precipitation totals ending at the kick-off hour rounded down; London local time", "models":MODEL_AUDIT}
pathlib.Path("output/data.json").write_text(json.dumps(B,separators=(",",":"),allow_nan=False))
print("written output/data.json", round(pathlib.Path("output/data.json").stat().st_size/1024),"KB")
print("keys:", ", ".join(B.keys()))
