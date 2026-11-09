// Independent display fixtures only; no scientific/controller code is imported.
import assert from 'node:assert/strict';
import { ReplayClock, snapshot, lastAt } from '../scratch_replay_web/clock.mjs';
let checks=0;
function check(fn){fn();checks++;}
for(const speed of [.25,.5,1,2])check(()=>{
  const c=new ReplayClock(0,10);c.rate(speed,0);c.play(1000);
  for(const t of [1030,1113,1462,2000])c.advance(t);
  assert.equal(c.time,speed);c.pause(2000);c.advance(9000);assert.equal(c.time,speed);
});
check(()=>{const c=new ReplayClock(0,2);c.play(0);c.advance(500);c.rate(2,1000);c.advance(1250);assert.equal(c.time,1.5);c.advance(1700);assert.equal(c.time,2);assert.equal(c.playing,false);c.seek(0);assert.equal(c.time,0);assert.equal(c.playing,false);c.seek(-4);assert.equal(c.time,0);c.seek(8);assert.equal(c.time,2);assert.throws(()=>c.rate(5,0));});
const data={states:[
  {time:0,x:0,y:0,plan_id:0,mode:'trajectory'},
  {time:.5,x:5,y:2,plan_id:1,mode:'trajectory'},
  {time:1,x:10,y:4,plan_id:1,mode:'trajectory'}],
  packets:[{id:0,times:[0,.4],completion:0,valid:true},{id:1,times:[.5,1.5],completion:.7,valid:true}],
  controls:[{time:0,application_time:.005,delta:.1},{time:.5,application_time:.505,delta:.2}],jumps:[]};
const before=JSON.stringify(data);
check(()=>{const c=new ReplayClock(0,10);c.play(100);c.advance(90);c.advance(110);assert.equal(c.time,.01);});
check(()=>{const s=snapshot(data,.25);assert.deepEqual(s.position,[2.5,1]);assert.equal(s.index,0);assert.equal(s.native.time,0);assert.equal(s.active.id,0);assert.equal(s.interpolated,true);});
check(()=>{assert.equal(snapshot(data,.45).active,null);assert.equal(snapshot(data,.5).active,null);assert.equal(snapshot(data,.7).active.id,1);assert.equal(snapshot(data,.8).active.id,1);});
check(()=>{assert.equal(snapshot(data,0).applied,null);assert.equal(snapshot(data,.004).applied,null);assert.equal(snapshot(data,.005).applied.delta,.1);assert.equal(snapshot(data,.502).applied.delta,.1);assert.equal(snapshot(data,.502).requested.delta,.2);assert.equal(snapshot(data,.505).applied.delta,.2);});
check(()=>{assert.equal(lastAt(data.states,.5),1);assert.equal(lastAt(data.states,.4999999999999),0);assert.equal(snapshot(data,1).index,2);assert.equal(snapshot(data,1).interpolated,false);assert.equal(JSON.stringify(data),before);});
check(()=>{const d=structuredClone(data);d.jumps=[.5];assert.deepEqual(snapshot(d,.499).position,[0,0]);assert.deepEqual(snapshot(d,.5).position,[5,2]);d.packets[1].valid=false;assert.equal(snapshot(d,.8).active,null);d.packets[1].valid=true;d.states[1].mode='fallback';assert.equal(snapshot(d,.8).active,null);});
export const result={outcome:'PASS',checks,scope:'Deterministic display-clock/native authority fixture checks only',scientific_runs:0};
