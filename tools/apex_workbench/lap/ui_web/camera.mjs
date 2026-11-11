// Display camera only: coordinates, telemetry, packet authority and replay time are never changed.
export function fit(points,w,h,pad=2,minSpan=.5){
  const values=points.filter(p=>p?.length===2&&p.every(Number.isFinite));
  if(!values.length)return null;
  const xs=values.map(p=>p[0]),ys=values.map(p=>p[1]);
  const loX=Math.min(...xs),hiX=Math.max(...xs),loY=Math.min(...ys),hiY=Math.max(...ys);
  return {x:(loX+hiX)/2,y:(loY+hiY)/2,scale:Math.min(Math.max(1,w-40)/Math.max(minSpan,hiX-loX+2*pad),Math.max(1,h-50)/Math.max(minSpan,hiY-loY+2*pad))};
}
export function target(data,s,mode,w,h){
  if(mode==='track')return fit(data.track.center,w,h);
  if(mode==='window')return fit(data.states.map(r=>[r.x,r.y]),w,h);
  // Follow Prediction always uses the physically available active packet, never a manual selection.
  if(mode==='prediction'&&s.active)return fit([...s.active.xy,...(s.active.microscope??[]).map(n=>n.reference_xy)],w,h,.7,2);
  return {x:s.position[0],y:s.position[1],scale:Math.min(Math.max(1,w-40)/12,Math.max(1,h-50)/9)};
}
export class SmoothCamera {
  constructor(){this.frame=null;this.wall=null;}
  update(goal,now,snap=false){
    if(!goal)return this.frame;
    if(!this.frame||snap){this.frame={...goal};this.wall=now;return this.frame;}
    const dt=Math.max(0,Math.min(.25,(now-this.wall)/1000)),a=1-Math.exp(-dt/.18);
    this.frame={x:this.frame.x+(goal.x-this.frame.x)*a,y:this.frame.y+(goal.y-this.frame.y)*a,scale:Math.exp(Math.log(this.frame.scale)+(Math.log(goal.scale)-Math.log(this.frame.scale))*a)};
    this.wall=Math.max(now,this.wall);return this.frame;
  }
}
export function mapper(frame,w,h){return p=>[w/2+(p[0]-frame.x)*frame.scale,h/2-(p[1]-frame.y)*frame.scale];}
export function wheel(angle,nominal,ratio){
  if(!Number.isFinite(ratio)||ratio<=0||ratio>100)throw Error('Visual ratio must be greater than 0 and at most 100');
  return {ratio,appliedRad:Number.isFinite(angle)?angle:null,appliedDeg:Number.isFinite(angle)?angle*180/Math.PI:null,
    visualRad:Number.isFinite(angle)?ratio*angle:null,nominalVisualRad:Number.isFinite(nominal)?ratio*nominal:null};
}
export function nodeView(packet,index){
  if(!packet)return null;
  const i=Math.max(0,Math.min(packet.states.length-1,index));
  return {index:i,state:packet.states[i],time:packet.times[i],reference:packet.microscope?.[i]??null,
    control:i<packet.controls.length?packet.controls[i]:null,
    interval:i<packet.controls.length?[packet.times[i],packet.times[i+1]]:null};
}
