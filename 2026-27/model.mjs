export const recorded = rows => rows.filter(r => Number.isFinite(r.attendance));
export const average = rows => {const a=recorded(rows); return a.length ? a.reduce((s,r)=>s+r.attendance,0)/a.length : null;};
export const total = rows => {const a=recorded(rows); return a.length ? a.reduce((s,r)=>s+r.attendance,0) : null;};
export const pct = (now,before) => Number.isFinite(now)&&Number.isFinite(before)&&before>0 ? (now/before-1)*100 : null;
export function filterRows(rows,s,{range=true,season='2026-2027'}={}) {return rows.filter(r=>r.season===season&&(!s.teams.length||s.teams.includes(r.home))&&(!range||(r.round>=s.from&&r.round<=s.to))&&(s.day==='all'||r.day===s.day)&&(s.weather==='all'||r.weather===s.weather)&&(s.slot==='all'||r.slot===s.slot));}
export function groups(rows,key,keys){return keys.map(k=>({key:k,rows:rows.filter(r=>r[key]===k)}));}
export function previousHomeChange(rows){const sorted=[...rows].sort((a,b)=>a.date.localeCompare(b.date)||a.kickoff.localeCompare(b.kickoff));const last=sorted.at(-1),prev=sorted.at(-2);return {last,prev,value:pct(last?.attendance,prev?.attendance)};}
export function csv(rows){const fields=['date','round','home','away','attendance','kickoff','day','temp','rain','weather','source'];const cell=v=>'"'+String(v??'').replaceAll('"','""')+'"';return [fields.join(','),...rows.map(r=>fields.map(f=>cell(r[f])).join(','))].join('\r\n');}

export function seasonBaseline(data,club,state){
 const aggregate=data.promotedBaselines?.find(r=>r.club===club);
 if(aggregate)return {value:state.baseline==='full'?aggregate.average:null,aggregate,rows:[]};
 const rows=filterRows(data.matches,state,{season:'2025-2026',range:state.baseline==='matched'}).filter(r=>r.home===club);
 return {value:average(rows),aggregate:null,rows};
}
