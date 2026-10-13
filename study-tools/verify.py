"""Independent verification: recompute every published statistic straight from matches.csv
by a separate code path and compare with output/data.json. Any mismatch is a failure."""
import json, numpy as np, pandas as pd
from scipy.stats import t
D=json.load(open("output/data.json"))
m=pd.read_csv("output/matches.csv",parse_dates=["date"])
m["excluded"]=m.excluded.fillna("")
d=m[(m.excluded=="")&m.attendance.notna()].copy()
all_d=d.copy()
flag=d.get("exclude_from_conditions",pd.Series(False,index=d.index)).fillna(False).astype(str).str.lower().isin(["true","1","1.0"])
d=d[~flag].copy()
d["attendance_index"]=d.attendance/d.groupby(["season","home"]).attendance.transform("mean")
context=d.get("context_verified",pd.Series(True,index=d.index)).fillna(False).astype(str).str.lower().isin(["true","1","1.0"])
fails=[];checks=0
def chk(name,got,exp,tol=0.005):
    global checks; checks+=1
    ok = (abs(got-exp)<=tol*max(1,abs(exp))) if isinstance(exp,(int,float)) and not isinstance(exp,bool) else got==exp
    if not ok: fails.append(f"{name}: page={exp} recomputed={got}")
    return ok

# --- headline counts ---
chk("fixtures",len(all_d),D["meta"]["fixtures"],0)
chk("total attendance",int(all_d.attendance.sum()),D["meta"]["total"],0)
chk("mean",round(all_d.attendance.mean()),D["meta"]["mean"],0)
chk("median",int(all_d.attendance.median()),D["meta"]["median"],0)
chk("max",int(all_d.attendance.max()),D["meta"]["max"],0)
chk("clubs",all_d.home.nunique(),D["meta"]["clubs"],0)
chk("missing",int(((m.excluded=="")&m.attendance.isna()).sum()),D["meta"]["missing"],0)

chk("conditions count",len(d),D["meta"]["conditions_fixtures"],0)
chk("special event exclusion",len(all_d)-len(d),D["meta"]["conditions_excluded"],0)
rec_all=all_d.groupby(["season","home"]).attendance.transform("mean")
chk("saved all-match index",float((all_d.attendance/rec_all-all_d.attendance_index).abs().max()),0.0,1e-9)
# --- index is truly attendance / own season home average ---
rec=d.groupby(["season","home"]).attendance.transform("mean")
chk("attendance_index definition",float((d.attendance/rec-d.attendance_index).abs().max()),0.0,1e-9)

# --- every block: index, raw, n ---
def block(col,rows,label,filt=None):
    src=d if filt is None else filt
    for r in rows:
        g=src[src[col].astype(str)==r["k"]]
        chk(f"{label}[{r['k']}].n",len(g),r["n"],0)
        chk(f"{label}[{r['k']}].idx",round(float(g.attendance_index.mean()),3),r["idx"],0)
        if "ci" in r:
            vals=g.attendance_index.dropna(); ci=t.ppf(.975,len(vals)-1)*vals.std(ddof=1)/np.sqrt(len(vals)) if len(vals)>1 else 0
            chk(f"{label}[{r['k']}].ci",round(float(ci),3),r["ci"],0)
        if "raw" in r and r["raw"] is not None:
            chk(f"{label}[{r['k']}].raw",round(float(g.attendance.mean())),r["raw"],0)
block("travel_band",D["travel"],"travel")
block("kick_off_band",D["kickoff"],"kickoff")
block("fixture_type",D["region"],"region")
block("month",D["month"],"month")
d["bh_lbl"]=d.bank_holiday.fillna("Ordinary fixture").where(context); block("bh_lbl",D["bh"],"bh")
d["derby_lbl"]=np.where(d.derby==1,"Derby (under 45 min)","Everything else"); block("derby_lbl",D["derby"],"derby")
d["sh"]=d.school_holiday.fillna("Term time").where(context); block("sh",D["school"],"school")
d["cl"]=d.clash.map({0:"No clash",1:"Big club at home"}); block("cl",D["clash"],"clash")
block("wx_cond",D["wx_cond"],"weather")
block("wx_temp_band",D["wx_temp"],"temperature")
block("wx_wind_band",D["wx_wind"],"wind")

# --- day of week: raw, adjusted, long-haul share ---
mix=d.travel_band.value_counts(normalize=True)
cell=d.pivot_table(index="day_of_week",columns="travel_band",values="attendance_index",aggfunc="mean")
wts=(cell.notna()*mix); adj=(cell.fillna(0)*mix).sum(axis=1)/wts.sum(axis=1)
for r in D["day"]:
    g=d[d.day_of_week==r["k"]]
    chk(f"day[{r['k']}].n",len(g),r["n"],0)
    chk(f"day[{r['k']}].raw",round(float(g.attendance_index.mean()),3),r["raw"],0.002)
    chk(f"day[{r['k']}].adj",round(float(adj[r['k']]),3),r["adj"],0.002)
    chk(f"day[{r['k']}].far",round(float((g.travel_band==">3h").mean()*100)),r["far"],0.01)

# --- season trend ---
for r in D["trend"]:
    g=all_d[all_d.season==r["k"]]
    chk(f"trend[{r['k']}].n",len(g),r["n"],0)
    chk(f"trend[{r['k']}].mean",round(float(g.attendance.mean())),r["mean"],0.01)
    chk(f"trend[{r['k']}].total",int(g.attendance.sum()),r["total"],0)

# --- first / last home game ---
d2=d[d.season.ne(max(d.season))].sort_values("date").copy()
d2["gm"]=d2.groupby(["season","home"]).cumcount()+1
d2["tot"]=d2.groupby(["season","home"]).home.transform("size")
d2["slot"]=np.where(d2.gm==1,"First home game",np.where(d2.gm==d2.tot,"Last home game","Everything else"))
block("slot",D["firstlast"],"firstlast",d2)

# --- Friday vs Saturday within band ---
for r in D["frisat"]:
    for day in ["friday","saturday"]:
        g=d[(d.day_of_week==day.capitalize())&(d.travel_band==r["band"])]
        chk(f"frisat[{r['band']}].{day}_n",len(g),r[day+"_n"],0)
        if r[day] is not None:
            chk(f"frisat[{r['band']}].{day}",round(float(g.attendance_index.mean()),3),r[day],0.002)

# --- clash confound percentages ---
c1=d[d.clash==1]
chk("clash sat_pct",round(float((c1.day_of_week=="Saturday").mean()*100)),D["clash_mix"]["sat_pct"],0.01)
chk("clash far_pct",round(float((c1.travel_band==">3h").mean()*100)),D["clash_mix"]["far_pct"],0.01)

# --- every full-season baseline comparison ---
base={x["club"]:x for x in json.load(open("output/current-baselines.json"))}
cur=all_d[all_d.season.eq(max(all_d.season))]
for row in D["expansion"]:
 g=cur[cur.home.eq(row["k"])]; prev=float(base[row["k"]]["average"]); now=float(g.attendance.mean())
 chk("expansion current "+row["k"],round(now),row["now"],0)
 chk("expansion previous "+row["k"],round(prev),row["prev"],0)
 chk("expansion growth "+row["k"],round((now/prev-1)*100),row["chg"],0)
 chk("expansion count "+row["k"],len(g),row["n"],0)
chk("expansion complete clubs",len(D["expansion"]),cur.home.nunique(),0)

# --- opponent pull + club table spot checks ---
for r in D["pull"]:
    g=d[d.away==r["k"]]; chk(f"pull[{r['k']}].n",len(g),r["n"],0)
    chk(f"pull[{r['k']}].idx",round(float(g.attendance_index.mean()),3),r["idx"],0)
for r in D["clubs"]:
    g=all_d[all_d.home==r["k"]]; chk(f"club[{r['k']}].avg",round(float(g.attendance.mean())),r["avg"],0.01)
    chk(f"club[{r['k']}].n",len(g),r["n"],0)

# --- biggest crowds ---
top=all_d.nlargest(len(D["top"]),"attendance")
for i,r in enumerate(D["top"]):
    chk(f"top[{i}].att",int(top.iloc[i].attendance),r["att"],0)
    chk(f"top[{i}].home",top.iloc[i].home,r["home"])

# Exhaustive data points in grids/scatter and saved club-season matrix.
for row in D["grid"]:
 g=d[d.day_of_week.eq(row["day"])&d.travel_band.eq(row["band"])]
 chk("grid count",len(g),row["n"],0)
 if len(g):chk("grid index",round(float(g.attendance_index.mean()),3),row["idx"],0)
for row in D["club_season"]:
 for season,avg in row.items():
  if season=="club" or avg is None:continue
  g=all_d[all_d.home.eq(row["club"])&all_d.season.eq(season)]
  chk("club-season average",round(float(g.attendance.mean())),avg,0)
sc=d[d.drive_min.notna()&d.attendance_index.notna()]
chk("scatter records",len(sc),len(D["scatter"]),0)
for (_,row),point in zip(sc.iterrows(),D["scatter"]):
 chk("scatter attendance",int(row.attendance),point["a"],0)
 chk("scatter index",round(float(row.attendance_index),3),point["y"],0)
 chk("scatter trip",int(row.drive_min),point["x"],0)
chk("distribution total",sum(D["dist"]),int(all_d.attendance.sum()),0)
chk("unique fixtures",int(m.duplicated(["season","date","home","away"]).sum()),0,0)
assert "NaN" not in open("output/data.json").read(), "Nonfinite published JSON"
# League headline uses published complete previous season, never mean club growth.
base=json.load(open("output/current-baselines.json"))
prior=[r for r in base if r.get("division")=="Cymru Premier" and r.get("total") is not None]
prior_mean=sum(r["total"] for r in prior)/sum(r["matches"] for r in prior)
current=all_d[all_d.season.eq(sorted(all_d.season.unique())[-1])]
chk("league baseline average",prior_mean,D["league_growth"]["previous_average"],1e-10)
chk("league current average",float(current.attendance.mean()),D["league_growth"]["current_average"],1e-10)
chk("league growth exact",(float(current.attendance.mean())/prior_mean-1)*100,D["league_growth"]["pct"],1e-10)
print(f"{checks} checks run")
if fails:
    print(f"\n{len(fails)} MISMATCHES:")
    for f in fails[:40]: print("  ",f)
else:
    print("ALL AGGREGATE CHECKS PASSED - regression verification is separate")

if fails: raise SystemExit(1)
