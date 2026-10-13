"""Integration test: change one source crowd in isolation; both pages must change."""
import tempfile,pathlib,shutil,subprocess,sys,csv,json,re
root=pathlib.Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='ewf-weekly-') as tmp:
 dest=pathlib.Path(tmp)
 for name in ['study-tools','2026-27','downloads']:
  shutil.copytree(root/name,dest/name,ignore=shutil.ignore_patterns('__pycache__','reproducible-study.zip'))
 for name in ['index.html','atlas.html','CNAME','analytics.js','site-navigation.css','site-navigation.js']:
  shutil.copyfile(root/name,dest/name)
 path=dest/'2026-27/data/new-matches.csv';rows=list(csv.DictReader(path.open()));fields=list(rows[0])
 target=next(r for r in rows if r['home']=='Penybont FC' and r['date']=='2026-10-09')
 target['attendance']=str(int(target['attendance'])+7)
 with path.open('w') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 result=subprocess.run([sys.executable,'study-tools/build_site.py'],cwd=dest,capture_output=True,text=True)
 assert result.returncode==0,result.stdout+result.stderr
 D=json.loads((dest/'downloads/data.json').read_text());S=json.loads((dest/'2026-27/data.json').read_text())
 baseline=json.loads((root/'downloads/data.json').read_text())
 assert D['meta']['total']==baseline['meta']['total']+7
 p=next(r for r in D['expansion'] if r['k']=='Penybont FC')
 current=[r for r in S['matches'] if r['season']=='2026-2027'];original=json.loads((root/'2026-27/data.json').read_text());before=[r for r in original['matches'] if r['season']=='2026-2027'];assert sum(r['attendance'] for r in current)==sum(r['attendance'] for r in before)+7
 bont=[r for r in current if r['home']=='Penybont FC'];assert p['now']==round(sum(r['attendance'] for r in bont)/len(bont))
 embedded=json.loads(re.search(r'<script id="D" type="application/json">(.*?)</script>',(dest/'index.html').read_text(),re.S)[1])
 assert embedded==D
 assert (dest/'index.html').read_bytes()==(dest/'atlas.html').read_bytes()
 print('PASS: one isolated source correction automatically updates study, dashboard, percentages, downloads and both page copies.')
