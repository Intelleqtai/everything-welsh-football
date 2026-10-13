import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {average,total,pct,filterRows,previousHomeChange,csv,conditionRows,seasonBaseline} from '../model.mjs';
const data=JSON.parse(readFileSync(new URL('../data.json',import.meta.url)));
const state={teams:[],from:1,to:data.meta.rounds,day:'all',weather:'all',slot:'all'};
const current=filterRows(data.matches,state);
test('published records reconcile with metadata and every club',()=>{
 assert.equal(current.length,data.meta.played);
 assert.equal(current.filter(r=>r.attendance!==null).length,data.meta.recorded);
 assert.equal(current.map(r=>r.date).sort().at(-1),data.meta.through);
 assert.equal(Math.max(...current.map(r=>r.round)),data.meta.rounds);
 assert.equal(data.clubs.reduce((sum,c)=>sum+(total(current.filter(r=>r.home===c.name))??0),0),total(current));
 assert.equal(new Set(data.matches.map(r=>r.id)).size,data.matches.length);
 for(const r of current){assert.ok(r.source);assert.ok(r.reviewed);assert.ok(r.date<=data.meta.through);}
 for(let i=1;i<=data.meta.rounds;i++)assert.ok(current.filter(r=>r.round===i).length<=data.meta.roundFixtureCount);
});
test('Bash stays in actual gates and club growth but leaves every conditions denominator',()=>{
 const bash=current.find(r=>r.date==='2026-09-26'&&r.home==='Penybont FC');
 assert.equal(bash.attendance,2666);assert.equal(bash.excludeFromConditions,true);
 const bont=current.filter(r=>r.home==='Penybont FC');
 assert.equal(total(bont)-total(conditionRows(bont)),2666);
 assert.equal(bont.length-conditionRows(bont).length,1);
 assert.equal(current.length-conditionRows(current).length,1);
 for(const key of ['day','weather','slot','travelBand']){
  const bucket=current.filter(r=>r[key]===bash[key]);
  assert.equal(total(bucket)-total(conditionRows(bucket)),2666);
 }
});
test('weather categories and route provenance stay consistent without inventing missing values',()=>{
 for(const r of current){
  assert.equal(r.weather,r.rain===null?'Unknown':r.rain>=4?'Heavy rain':r.rain>=1?'Wet':'Dry');
  for(const key of ['temp','rain','wind','roadKm','driveMinutes'])assert.ok(r[key]===null||Number.isFinite(r[key]),`${r.id} ${key}`);
  assert.ok(r.travelSource.includes('estimate'));
  if(r.rain!==null)assert.ok(r.weatherSource);
 }
 assert.ok(current.filter(r=>r.home==="Connah's Quay Nomads").every(r=>r.venue==='Essity Stadium'));
});
test('combined filters and baseline seasons stay independent',()=>{
 const friday=filterRows(data.matches,{...state,day:'Friday'});assert.deepEqual(friday,current.filter(r=>r.day==='Friday'));
 assert.deepEqual(filterRows(data.matches,{...state,teams:['Penybont FC']}),current.filter(r=>r.home==='Penybont FC'));
 assert.equal(filterRows(data.matches,state,{season:'2025-2026'}).every(r=>r.season==='2025-2026'),true);
 for(const r of current)assert.equal(new Date(r.week+'T12:00:00Z').getUTCDay(),1);
});
test('missing and zero attendances, latest-match changes and exports are honest',()=>{
 assert.equal(average([{attendance:null}]),null);assert.equal(total([]),null);
 assert.equal(average([{attendance:0},{attendance:null},{attendance:100}]),50);
 assert.equal(pct(5,0),null);assert.equal(pct(null,100),null);
 assert.equal(previousHomeChange([{date:'2026-10-01',kickoff:'14:30',attendance:100},{date:'2026-10-02',kickoff:'14:30',attendance:null}]).value,null);
 const out=csv([{attendance:null,home:'Club "A"',specialEvent:'Event',excludeFromConditions:true}]);assert.ok(out.includes('"Club ""A"""'));assert.ok(!out.includes('null'));assert.ok(out.includes('excludeFromConditions'));
});
test('all clubs have baselines; promoted clubs cannot invent matched-round history',()=>{
 for(const c of data.clubs)assert.ok(seasonBaseline(data,c.name,{...state,baseline:'full'}).value>0,c.name);
 assert.equal(data.promotedBaselines.length,6);
 assert.equal(seasonBaseline(data,'Cambrian United',{...state,baseline:'full'}).value,227);
 assert.equal(seasonBaseline(data,'Cambrian United',{...state,baseline:'matched'}).value,null);
});

test('published full-season baseline reconciles and replaces incomplete frozen aggregates',()=>{
 assert.equal(data.publishedBaselines.reduce((s,r)=>s+r.total,0),87608);
 assert.equal(seasonBaseline(data,'Penybont FC',{...state,baseline:'full'}).value,6353/16);
 assert.equal(seasonBaseline(data,'Caernarfon Town',{...state,baseline:'full'}).value,7455/16);
});
