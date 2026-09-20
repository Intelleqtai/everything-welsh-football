import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {average,total,pct,filterRows,previousHomeChange,csv} from '../model.mjs';
const data=JSON.parse(readFileSync(new URL('../data.json',import.meta.url)));
const state={teams:[],from:1,to:10,day:'all',weather:'all',slot:'all'};
const current=filterRows(data.matches,state);
test('missing figures remain missing; actual zero is recorded',()=>{
 assert.equal(average([{attendance:null}]),null);assert.equal(total([]),null);
 assert.equal(average([{attendance:0},{attendance:null},{attendance:100}]),50);
 assert.equal(pct(5,0),null);assert.equal(pct(null,100),null);
});
test('published season and latest round totals reconcile',()=>{
 assert.equal(current.length,79);assert.equal(current.filter(r=>r.attendance!==null).length,78);
 assert.equal(total(current),49314);
 for(const [round,sum] of [[8,4926],[9,3476],[10,4243]])assert.equal(total(current.filter(r=>r.round===round)),sum);
 assert.equal(new Set(data.matches.map(r=>r.id)).size,data.matches.length);
 assert.equal(current.filter(r=>r.attendance===null)[0].home,'The New Saints');
});
test('combined filters and baseline seasons stay independent',()=>{
 const friday=filterRows(data.matches,{...state,day:'Friday'});assert.equal(friday.length,53);assert.equal(total(friday),30862);
 const filtered=filterRows(data.matches,{...state,teams:['Caernarfon Town'],from:8,to:10,weather:'Heavy rain'});
 assert.equal(filtered.length,1);assert.equal(filtered[0].attendance,1010);
 assert.equal(filterRows(data.matches,state,{season:'2025-2026'}).every(r=>r.season==='2025-2026'),true);
});
test('latest missing attendance does not silently compare older matches',()=>{
 assert.equal(previousHomeChange(current.filter(r=>r.home==='The New Saints')).value,null);
 assert.ok(Math.abs(previousHomeChange(current.filter(r=>r.home==='Airbus UK Broughton')).value-16.470588235294116)<1e-9);
});
test('calendar weeks are Mondays and missing attendance exports blank',()=>{
 for(const r of current){assert.equal(new Date(r.week+'T12:00:00Z').getUTCDay(),1);assert.ok(r.date>=r.week);}
 const out=csv([{attendance:null,home:'Club "A"'}]);assert.ok(out.includes('"Club ""A"""'));assert.ok(!out.includes('null'));
});

test('all sixteen clubs have a full-season baseline including promoted clubs',async()=>{
 const {seasonBaseline}=await import('../model.mjs');
 for(const c of data.clubs)assert.ok(seasonBaseline(data,c.name,{...state,baseline:'full'}).value>0,c.name);
 assert.equal(data.promotedBaselines.length,6);
 const base=seasonBaseline(data,'Cambrian United',{...state,baseline:'full'});
 assert.equal(base.value,227);assert.equal(base.aggregate.division,'Cymru South');assert.equal(base.rows.length,0);
 assert.ok(Math.abs(pct(average(current.filter(r=>r.home==='Cambrian United')),base.value)-260.0220264317181)<1e-8);
});
test('aggregate baselines cannot masquerade as filtered or matched-round records',async()=>{
 const {seasonBaseline}=await import('../model.mjs');
 assert.equal(seasonBaseline(data,'Cambrian United',{...state,baseline:'matched'}).value,null);
 assert.equal(seasonBaseline(data,'Cambrian United',{...state,baseline:'full',weather:'Wet',day:'Friday'}).value,227);
 assert.equal(data.matches.filter(r=>r.season==='2025-2026'&&r.home==='Cambrian United').length,0);
});
