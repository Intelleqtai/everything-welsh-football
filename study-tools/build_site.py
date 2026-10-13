"""Single build: verified match inputs -> both pages, all downloads, regression audit.
Any validation failure stops publication. Run from any working directory.
"""
import pathlib,sys,subprocess,json,re,shutil,zipfile,hashlib,csv
ROOT=pathlib.Path(__file__).resolve().parents[1]
def run(*args):subprocess.run(args,cwd=ROOT,check=True)
run(sys.executable,'2026-27/tools/build.py')
run(sys.executable,'study-tools/merge_matches.py')
# Historical values must stay unchanged; only current-season records are replaced.
original=list(csv.DictReader((ROOT/'study-tools/source/original-matches.csv').open()))
merged=list(csv.DictReader((ROOT/'output/matches.csv').open()))
old={(r['season'],r['date'],r['home'],r['away']):r for r in original if r['season']!='2026-2027'}
now={(r['season'],r['date'],r['home'],r['away']):r for r in merged if r['season']!='2026-2027'}
assert old.keys()==now.keys(),'Historical fixture membership changed'
for k,row in old.items():
 assert all(now[k][field]==value for field,value in row.items()),('Historical value changed',k)
assert len({(r['season'],r['date'],r['home'],r['away']) for r in merged})==len(merged),'Duplicate match'
run(sys.executable,'study-tools/export_json.py')
run(sys.executable,'study-tools/verify.py')
run(sys.executable,'study-tools/verify_models.py')
run('node','--test','2026-27/tools/model.test.mjs')
D=json.loads((ROOT/'output/data.json').read_text())
S=json.loads((ROOT/'2026-27/data.json').read_text())
current=[r for r in S['matches'] if r['season']==S['meta']['season']]
assert next(r for r in D['trend'] if r['k']==S['meta']['season'])['n']==S['meta']['recorded']
for name in ['matches.csv','data.json']:shutil.copyfile(ROOT/'output'/name,ROOT/'downloads'/name)
html=(ROOT/'index.html').read_text()
html,n=re.subn(r'(<script id="D" type="application/json">).*?(</script>)',lambda m:m[1]+json.dumps(D,separators=(',',':')).replace('</','<\\/')+m[2],html,flags=re.S)
assert n==1,'Missing unique study data block'
(ROOT/'index.html').write_text(html)
(ROOT/'atlas.html').write_text(html)
manifest={'reviewed':S['meta']['reviewed'],'through':S['meta']['through'],'currentSeasonMatches':len(current),'currentSeasonRecorded':sum(r['attendance'] is not None for r in current),'currentSeasonTotal':sum(r['attendance'] or 0 for r in current),'studyRecorded':D['meta']['fixtures'],'hashes':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['downloads/matches.csv','downloads/data.json','2026-27/data.json','2026-27/matches.csv']}}
(ROOT/'downloads/build-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
with zipfile.ZipFile(ROOT/'downloads/reproducible-study.zip','w',zipfile.ZIP_DEFLATED) as z:
 for path in ['study-tools','2026-27']:
  for p in sorted((ROOT/path).rglob('*')):
   if p.is_file() and '__pycache__' not in p.parts:z.write(p,p.relative_to(ROOT))
 for path in ['downloads/matches.csv','downloads/data.json','downloads/clubs.csv','downloads/travel_matrix.csv','index.html','atlas.html','CNAME','analytics.js','site-navigation.css','site-navigation.js']:
  z.write(ROOT/path,path)
site=ROOT/'_site'
if site.exists():shutil.rmtree(site)
site.mkdir()
for name in ['index.html','atlas.html','CNAME','analytics.js','site-navigation.css','site-navigation.js']:shutil.copyfile(ROOT/name,site/name)
for name in ['downloads','2026-27']:shutil.copytree(ROOT/name,site/name,ignore=shutil.ignore_patterns('__pycache__'))
print('VALIDATED SITE READY:',json.dumps(manifest))
