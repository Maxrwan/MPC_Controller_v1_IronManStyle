// Independently specified display fixtures, not scientific simulation or qualification.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {ReplayClock,snapshot} from '../lap/ui_web/clock.mjs';
import {instruments,progressIndex} from '../lap/ui_web/instruments.mjs';
let checks=0;
function check(fn){fn();checks++;}
const meta={track_length_m:100,lap_crossings:[{time_s:1,complete_circuit:false,interval_s:1},{time_s:3,complete_circuit:true,interval_s:2}],sectors:[{coverage:'complete',end_time_s:2,time_s:1,sector:1}]};
const data={states:[{time:0,x:0,y:0,delta:-.1,s_abs:1,mode:'trajectory',plan_id:1},{time:1,x:5,y:2,delta:.2,s_abs:101,mode:'trajectory',plan_id:2},{time:3,x:8,y:0,delta:.3,s_abs:201,mode:'fallback'}],controls:[{time:0,application_time:.005,delta:.2,nominal_delta:.15},{time:.5,application_time:.505,delta:-.3,nominal_delta:-.25}],packets:[{id:1,valid:true,completion:0,times:[0,.5]},{id:2,valid:true,completion:1.1,times:[1,2]}],jumps:[]};
check(()=>{const d=instruments(snapshot(data,0),0,meta);assert.equal(d.angle,-.1);assert.equal(d.nominal,null);assert.equal(d.applicationTime,null);assert.equal(d.laps,0);assert.deepEqual(d.sectors,[]);});
check(()=>{assert.equal(instruments(snapshot(data,.004),.004,meta).angle,-.1);assert.equal(instruments(snapshot(data,.005),.005,meta).angle,.2);const d=instruments(snapshot(data,.502),.502,meta);assert.equal(d.angle,.2);assert.equal(d.nominal,.15);assert.equal(d.requestTime,0);assert.equal(d.applicationTime,.005);assert.equal(snapshot(data,.502).requested.delta,-.3);assert.equal(instruments(snapshot(data,.505),.505,meta).angle,-.3);});
check(()=>{assert.equal(snapshot(data,1.05).active,null);assert.equal(snapshot(data,1.1).active.id,2);const d=instruments(snapshot(data,3),3,meta);assert.equal(d.laps,1);assert.equal(d.lapTime,2);assert.equal(d.sectors.length,1);assert.equal(d.fraction,.01);});
check(()=>{const clone=structuredClone(data);delete clone.controls[0].nominal_delta;assert.equal(instruments(snapshot(clone,.4),.4,meta).nominal,null);clone.controls[0].delta=null;assert.equal(instruments(snapshot(clone,.4),.4,meta).angle,null);});
check(()=>{assert.equal(progressIndex(data.states,100,0),1);const a=structuredClone(data.states);a[1].s_abs=0;assert.equal(progressIndex(a,1,0),null);});
check(()=>{const a=structuredClone(data);a.jumps=[1];assert.deepEqual(snapshot(a,.999).position,[0,0]);assert.equal(instruments(snapshot(a,.999),.999,meta).angle,-.3);});
for(const rate of [.25,.5,1,2])check(()=>{const c=new ReplayClock(0,80);c.rate(rate,0);c.play(100);c.advance(1100);assert.equal(c.time,rate);c.pause(1100);c.advance(10000);assert.equal(c.time,rate);});
export async function genuineCheck(path){
  const p=JSON.parse(await readFile(path,'utf8'));
  for(const row of p.controls){
    for(const t of [row.application_time-1e-10,row.application_time]){
      if(t<p.states[0].time||t>p.states.at(-1).time)continue;
      const expected=p.controls.filter(c=>c.application_time<=t).at(-1);
      const native=p.states.filter(c=>c.time<=t).at(-1);
      const d=instruments(snapshot(p,t),t,p.meta);
      assert.equal(d.angle,expected?expected.delta:native.delta);
      assert.equal(d.nominal,Number.isFinite(expected?.nominal_delta)?expected.nominal_delta:null);
      checks++;
    }
  }
  return {outcome:'PASS',checks,scope:'Pure display plus genuine retained pilot application-edge assertions',scientific_runs:0};
}
export const result={outcome:'PASS',checks,scientific_runs:0};
