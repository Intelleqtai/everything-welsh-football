import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {average,total,pct,filterRows,previousHomeChange,csv,conditionRows,seasonBaseline} from '../model.mjs';
const data=JSON.parse(readFileSync(new URL('../data.json',import.meta.url)));
const state={teams:[],from:1,to:13,day:'all',weather:'all',slot:'all'};
const current=filterRows(data.matches,state);
test('published results reconcile across every complete fixture round',()=>{
 assert.equal(current.length,104);assert.equal(current.filter(r=>r.attendance!==null).length,104);
 assert.equal(total(current),64789);
 const sums=[6084,5612,5153,4101,3953,7946,3820,4926,3913,4739,6492,3359,4691];
 sums.forEach((sum,i)=>{const round=current.filter(r=>r.round===i+1);assert.equal(round.length,8);assert.equal(total(round),sum);});
 assert.equal(new Set(data.matches.map(r=>r.id)).size,data.matches.length);
});
test('Bash stays in actual gates and club growth but leaves every conditions denominator',()=>{
 const bont=current.filter(r=>r.home==='Penybont FC');
 assert.equal(total(bont),7056);assert.equal(average(bont),1008);
 assert.equal(conditionRows(bont).length,6);assert.equal(total(conditionRows(bont)),4390);
 const saturday=current.filter(r=>r.day==='Saturday');assert.equal(saturday.length,26);
 assert.equal(conditionRows(saturday).length,25);assert.equal(average(conditionRows(saturday)),550.92);
 assert.equal(conditionRows(current).length,103);
 assert.equal(current.find(r=>r.specialEvent).attendance,2666);
 assert.equal(average(bont)/seasonBaseline(data,'Penybont FC',{...state,baseline:'full'}).value>2,true);
});
test('missing weather remains unknown, not dry; routes have explicit provenance',()=>{
 for(const r of current){assert.equal(r.weather==='Unknown',r.rain===null);assert.ok(Number.isFinite(r.roadKm));assert.ok(Number.isFinite(r.driveMinutes));assert.ok(r.travelSource.includes('estimate'));}
 assert.equal(current.filter(r=>r.date>'2026-09-19').every(r=>r.weather==='Unknown'),true);
 assert.ok(current.filter(r=>r.home==="Connah's Quay Nomads").every(r=>r.venue==='Essity Stadium'));
});
test('combined filters and baseline seasons stay independent',()=>{
 const friday=filterRows(data.matches,{...state,day:'Friday'});assert.equal(friday.length,60);assert.equal(total(friday),35013);
 assert.equal(filterRows(data.matches,{...state,teams:['Penybont FC']}).length,7);
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
