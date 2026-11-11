// Display-only fixtures and retained packet checks; no physical simulation.
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {SmoothCamera,target,mapper,wheel,nodeView} from '../lap/ui_web/camera.mjs';
import {snapshot,ReplayClock} from '../lap/ui_web/clock.mjs';
let checks=0;const check=fn=>{fn();checks++;};
const data={states:[{time:0,x:1,y:2,delta:.1,plan_id:0,mode:'trajectory'},{time:.5,x:2,y:3,plan_id:1,mode:'trajectory'},{time:1,x:3,y:5,plan_id:1,mode:'trajectory'}],track:{center:[[0,0],[10,10]]},controls:[{time:0,application_time:.005,delta:.1,nominal_delta:.15}],packets:[{id:0,valid:true,completion:0,times:[0,.4],xy:[[1,2],[2,2]]},{id:1,valid:true,completion:.7,times:[.5,1.5],xy:[[2,3],[3,5]]}],jumps:[]};
check(()=>{const v=wheel(.1,.15,12);assert.equal(v.appliedRad,.1);assert.ok(Math.abs(v.visualRad-1.2)<1e-14);assert.ok(Math.abs(v.appliedDeg-5.729577951308232)<1e-14);assert.ok(Math.abs(v.nominalVisualRad-1.8)<1e-14);assert.equal(wheel(.1,null,2).nominalVisualRad,null);assert.equal(wheel(null,null,12).visualRad,null);});
for(const r of [0,-1,NaN,Infinity,101])check(()=>assert.throws(()=>wheel(.1,.2,r)));
check(()=>{const c=new SmoothCamera();c.update({x:0,y:0,scale:1},0);let previous=0;for(let now=33;now<=990;now+=33){const f=c.update({x:10,y:20,scale:5},now);assert.ok(f.x>previous&&f.x<10);assert.ok(f.scale>0&&f.scale<5);previous=f.x;}assert.ok(previous>9.9);});
check(()=>{const before=JSON.stringify(data),s=snapshot(data,.25);const v=target(data,s,'vehicle',800,400);assert.deepEqual([v.x,v.y],s.position);const active=target(data,s,'prediction',800,400);assert.deepEqual([active.x,active.y],[1.5,2]);const unavailable=target(data,snapshot(data,.6),'prediction',800,400);assert.deepEqual([unavailable.x,unavailable.y],snapshot(data,.6).position);assert.equal(JSON.stringify(data),before);});
check(()=>{const c=new ReplayClock(0,1),camera=new SmoothCamera();c.play(0);c.advance(250);const t=c.time;c.pause(250);for(let n=0;n<10;n++)camera.update({x:n,y:n,scale:2},n*33);assert.equal(c.time,t);assert.equal(c.playing,false);});
check(()=>{const map=mapper({x:2,y:3,scale:10},100,80);assert.deepEqual(map([2,3]),[50,40]);assert.deepEqual(map([3,4]),[60,30]);});
const packet={times:Array.from({length:9},(_,i)=>i*.1),states:Array.from({length:9},(_,i)=>[1,2,3,4,5,i]),controls:Array.from({length:8},(_,i)=>[i*.01,i]),microscope:null};
for(let i=0;i<9;i++)check(()=>{const n=nodeView(packet,i);assert.deepEqual(n.state,packet.states[i]);assert.equal(n.reference,null);assert.deepEqual(n.control,i<8?packet.controls[i]:null);assert.deepEqual(n.interval,i<8?[packet.times[i],packet.times[i+1]]:null);});
export async function genuine(path){
 const p=JSON.parse(await readFile(path,'utf8')),before=JSON.stringify(p);
 for(const packet of p.packets){assert.equal(packet.states.length,9);assert.equal(packet.controls.length,8);for(let i=0;i<9;i++)check(()=>{const n=nodeView(packet,i);assert.equal(n.reference.lateral_error_m,packet.states[i][5]-n.reference.reference_e_y_m);assert.ok(n.reference.heading_error_rad>-Math.PI&&n.reference.heading_error_rad<=Math.PI);assert.deepEqual(n.reference.predicted_xy,packet.xy[i]);assert.equal(n.control===null,i===8);});}
 for(const state of p.states){const s=snapshot(p,state.time);if(!s.active)continue;const frame=target(p,s,'prediction',800,400);assert.ok(frame.scale>0&&Number.isFinite(frame.x));checks++;}
 assert.equal(JSON.stringify(p),before);return {outcome:'PASS',checks,scientific_runs:0};
}
export const result={outcome:'PASS',checks,scientific_runs:0};
