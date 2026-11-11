import {ReplayClock,snapshot} from './clock.mjs';
import {instruments,progressIndex} from './instruments.mjs';
import {SmoothCamera,fit,target,mapper,wheel,nodeView} from './camera.mjs';

const $=id=>document.getElementById(id);
const send=(type,extra={})=>parent.postMessage({isStreamlitMessage:true,type,...extra},'*');
const report=value=>send('streamlit:setComponentValue',{value,dataType:'json'});
const fmt=(v,d=3)=>typeof v==='number'&&Number.isFinite(v)?v.toFixed(d):'unavailable';
const css=getComputedStyle(document.documentElement),token=n=>css.getPropertyValue('--apex-'+n).trim();
const colors={plant:token('copper'),prediction:token('mint'),reference:token('lime'),center:token('line'),left:token('dim'),right:token('dim')};
let data=null,epoch=null,clock=null,verified=0,raf=0,lastPaint=-Infinity,lastReadout=-Infinity,lastPlot=-Infinity;
let camera=new SmoothCamera(),microCamera=new SmoothCamera(),moving=false,tableKey='',ratio=12,received=0;
let segment=null,frames=0,lastFrame=null,maxGap=0,pending=null,waiting=false,historyXY=[];
const height=()=>send('streamlit:setFrameHeight',{height:Math.ceil(document.body.getBoundingClientRect().height+16)});
function size(canvas){
  const b=canvas.getBoundingClientRect(),dpr=Math.min(2,devicePixelRatio||1),w=Math.round(b.width*dpr),h=Math.round(b.height*dpr);
  if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;}
  const ctx=canvas.getContext('2d');ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,b.width,b.height);
  return {ctx,w:b.width,h:b.height};
}
function path(ctx,points,map,color,width=1.5,end=points.length){
  if(!end)return;ctx.beginPath();for(let i=0;i<end;i++){const p=map(points[i]);i?ctx.lineTo(...p):ctx.moveTo(...p);}ctx.strokeStyle=color;ctx.lineWidth=width;ctx.stroke();
}
function cameraMoving(a,b){return !!a&&!!b&&(Math.hypot(a.x-b.x,a.y-b.y)*b.scale>.1||Math.abs(Math.log(a.scale/b.scale))>.001);}
function stopSegment(now){
  if(segment&&clock){const wall=(now-segment.wall)/1000,sim=clock.time-segment.time;
    const result={simulated_s:sim,wall_s:wall,speed:segment.speed,frames,max_gap_ms:maxGap};
    $('coverage').dataset.segment=JSON.stringify(result);
    $('coverage').textContent=`${data.coverage.samples} native samples; ${data.coverage.stop_reason||'partial coverage'}. Last playback segment: ${fmt(sim,4)} simulated s / ${fmt(wall,4)} wall s at ${segment.speed}×; ${frames} rendered frames; maximum painted-frame gap ${fmt(maxGap,1)} ms. Display timing only.`;
  }segment=null;
}
function startSegment(now){segment={wall:now,time:clock.time,speed:clock.speed};frames=0;lastFrame=null;maxGap=0;}
function pause(now=performance.now()){if(clock)clock.pause(now);stopSegment(now);}
function invalidate(message){
  pause();cancelAnimationFrame(raf);raf=0;data=null;clock=null;pending=null;waiting=false;historyXY=[];
  $('notice').textContent=message;$('notice').className='invalid';document.querySelector('main').hidden=true;
  $('nodes').replaceChildren();$('diagnostics').textContent='';$('readout').replaceChildren();
  for(const c of document.querySelectorAll('canvas'))c.getContext('2d').clearRect(0,0,c.width,c.height);height();
}
function packet(s){return $('packet').value==='active'?s.active:data.packets.find(p=>String(p.id)===$('packet').value)||null;}
function drawHorizon(ctx,p,map,allLabels,selected){
  if(!p)return;
  const refs=p.microscope?.map(n=>n.reference_xy)??[];
  path(ctx,refs,map,colors.reference,1.5);path(ctx,p.xy,map,colors.prediction,2.2);
  p.xy.forEach((point,i)=>{
    const pos=map(point),n=p.microscope?.[i];
    if(n){path(ctx,[point,n.reference_xy],map,colors.plant,1);}
    ctx.beginPath();ctx.arc(...pos,i===selected?5:3,0,Math.PI*2);ctx.fillStyle=colors.prediction;ctx.fill();
    if(allLabels||i===selected){ctx.font='11px '+token('mono');ctx.fillStyle=token('text');ctx.fillText(String(i),pos[0]+7,pos[1]-7);}
  });
}
function drawTrack(s,p,now){
  const {ctx,w,h}=size($('track')),goal=target(data,s,$('view').value,w,h),frame=camera.update(goal,now);
  const map=mapper(frame,w,h);moving=cameraMoving(frame,goal);
  ctx.fillStyle=token('surface');ctx.fillRect(0,0,w,h);
  for(const side of ['left','right','center'])path(ctx,data.track[side],map,colors[side],side==='center'?1:1.2);
  path(ctx,data.planning_reference,map,colors.reference,1);
  path(ctx,historyXY,map,colors.plant,2.4,s.index+1);
  drawHorizon(ctx,p,map,$('all-labels').checked,Number($('node').value));
  const xy=map(s.position);ctx.fillStyle=colors.plant;ctx.beginPath();ctx.arc(...xy,6,0,Math.PI*2);ctx.fill();ctx.strokeStyle=token('text');ctx.lineWidth=1.3;ctx.stroke();
  ctx.fillStyle=token('muted');ctx.font='10px '+token('font');ctx.fillText(`GLOBAL XY [m] · ${fmt(w/frame.scale,1)} m visible width · schematic position marker`,14,h-14);
  $('track').dataset.camera=JSON.stringify(frame);$('track').dataset.position=JSON.stringify(s.position);
}
function drawWheel(d){
  const v=wheel(d.angle,d.nominal,ratio),canvas=$('steering'),{ctx,w,h}=size(canvas);
  Object.assign(canvas.dataset,{appliedRad:String(v.appliedRad),appliedDeg:String(v.appliedDeg),nominalRad:String(d.nominal),visualRatio:String(ratio),visualAngleRad:String(v.visualRad),nativeTime:String(d.nativeTime),applicationTime:String(d.applicationTime),requestTime:String(d.requestTime)});
  const draw=(angle,color,dash=false)=>{
    if(!Number.isFinite(angle))return;
    ctx.save();ctx.translate(w/2,h/2);ctx.rotate(-angle);ctx.strokeStyle=color;ctx.lineWidth=dash?1.4:2.5;ctx.setLineDash(dash?[3,3]:[]);
    ctx.beginPath();ctx.arc(0,0,32,0,Math.PI*2);ctx.stroke();
    ctx.beginPath();ctx.moveTo(-30,0);ctx.lineTo(-7,3);ctx.lineTo(0,27);ctx.lineTo(7,3);ctx.lineTo(30,0);ctx.stroke();
    ctx.beginPath();ctx.arc(0,0,7,0,Math.PI*2);ctx.stroke();ctx.beginPath();ctx.moveTo(0,-32);ctx.lineTo(0,-24);ctx.stroke();ctx.restore();
  };
  if($('nominal').checked)draw(v.nominalVisualRad,colors.prediction,true);
  draw(v.visualRad,colors.plant);
  $('steering-value').textContent=fmt(d.angle,4)+' rad';$('steering-degrees').textContent=fmt(v.appliedDeg,2)+'° front steering';
}
function updateInstruments(s){
  const d=instruments(s,clock.time,data.meta);drawWheel(d);
  $('speed-value').textContent=fmt(s.native.vx,2);$('error-value').textContent=fmt(s.native.error_y,3);$('accel-value').textContent=fmt(s.applied?s.applied.a_cmd:s.native.a_cmd,2);
  for(const side of ['front','rear']){const v=s.native[side+'_utilization'];$(side+'-value').textContent=Number.isFinite(v)?fmt(v):'—';$(side+'-meter').hidden=!Number.isFinite(v);$(side+'-meter').value=Number.isFinite(v)?Math.max(0,Math.min(1,v)):0;}
  $('packet-value').textContent=s.active?'TVLQR · packet '+s.active.id:'No available valid trajectory';$('authority').textContent='Native mode: '+s.native.mode+' · t '+fmt(s.native.time)+' s';
  $('progress-value').textContent=d.fraction===null?'Unavailable':fmt(d.fraction*100,1)+'%';$('progress').value=d.fraction??0;$('lap-value').textContent=String(d.laps);
  $('lap-time').textContent=d.lapTime===null?'Partial launch crossing excluded':fmt(d.lapTime)+' s · last complete native lap';
  $('sector-value').textContent=d.sectors.length?d.sectors.map(c=>'S'+c.sector+' '+fmt(c.time_s)+' s').join(' / '):'Not yet complete';
  $('progress-seek').min=data.states[0].s_abs;$('progress-seek').max=data.states.at(-1).s_abs;
}
function drawMicroscope(p,now,force){
  if(!$('prediction-details').open)return;
  const {ctx,w,h}=size($('microscope'));ctx.fillStyle=token('surface');ctx.fillRect(0,0,w,h);
  if(p){
    const goal=fit([...p.xy,...(p.microscope??[]).map(n=>n.reference_xy)],w,h,.4,1.2),frame=microCamera.update(goal,now),map=mapper(frame,w,h);
    moving=moving||cameraMoving(frame,goal);drawHorizon(ctx,p,map,$('all-labels').checked,Number($('node').value));
    const n=nodeView(p,Number($('node').value)),point=map(p.xy[n.index]);
    if(n.reference){
      for(const [heading,color] of [[n.reference.reference_heading_rad,colors.reference],[n.reference.predicted_heading_rad,colors.prediction]]){
        const end=[point[0]+25*Math.cos(heading),point[1]-25*Math.sin(heading)];ctx.strokeStyle=color;ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(...point);ctx.lineTo(...end);ctx.stroke();
      }
      ctx.strokeStyle=colors.plant;ctx.lineWidth=1.5;ctx.beginPath();ctx.arc(...point,17,-n.reference.reference_heading_rad,-n.reference.reference_heading_rad-n.reference.heading_error_rad,n.reference.heading_error_rad>0);ctx.stroke();
    }
    ctx.fillStyle=token('muted');ctx.font='10px '+token('font');ctx.fillText('World XY [m] · connectors: lateral tracking error · heading glyph lengths schematic',12,h-12);
  }else{ctx.fillStyle=token('muted');ctx.font='13px '+token('font');ctx.fillText('No active available horizon at this replay time',16,32);}
  const key=[epoch,p?.id,$('node').value,$('show-radians').checked].join('/');
  if(!force&&key===tableKey)return;tableKey=key;
  $('node').max=p?p.states.length-1:0;
  const n=nodeView(p,Number($('node').value));
  $('node-title').textContent=n?`Node ${n.index} / ${p.states.length-1} · native target ${fmt(n.time)} s`:'Selected predicted node unavailable';
  $('node-lateral').textContent=fmt(n?.reference?.lateral_error_m,4)+' m';
  $('node-heading').textContent=fmt(n?.reference?.heading_error_rad*180/Math.PI,2)+'°'+($('show-radians').checked?' / '+fmt(n?.reference?.heading_error_rad,5)+' rad':'');
  $('node-control').textContent=n?.control?`Nominal u[${n.index}]: δ ${fmt(n.control[0],4)} rad; Fx/m ${fmt(n.control[1])} m/s² over [${fmt(n.interval[0])}, ${fmt(n.interval[1])}) s. Not an applied command.`:n?'Terminal predicted state · no terminal control interval.':'No recorded control interval';
  $('node-state').textContent=n?`[vx, vy, r, eψ, s_abs, e_y] = [${n.state.map(v=>fmt(v,4)).join(', ')}] in SI units.`:'';
  $('reference-status').textContent=data.meta.microscope_status+' · Racing-reference tracking errors, not actual-future prediction residuals. Native NMPC preview is not reconstructed. Heading glyphs are schematic.';
  $('nodes').replaceChildren(...(p?p.states.map((_,i)=>{const v=nodeView(p,i),row=document.createElement('tr');for(const text of [i,fmt(v.time),fmt(v.reference?.lateral_error_m,4),fmt(v.reference?.heading_error_rad*180/Math.PI,2),v.control?fmt(v.control[0],4):'— terminal',v.control?fmt(v.control[1]):'—']){const cell=document.createElement('td');cell.textContent=String(text);row.appendChild(cell);}if(i===n.index)row.className='selected';return row;}):[]));
}
function diagnostics(s,p){
  const n=nodeView(p,Number($('node').value));
  $('diagnostics').textContent=JSON.stringify({plant_native_sample_time_s:s.native.time,active_packet:s.active?.id??null,inspected_packet:p?.id??null,inspection:$('packet').value==='active'?'Follow active packet':'Manual historical inspection',completion_time_s:p?.completion??null,recorded_valid:p?.valid??null,validation_reason:p?.reason??null,node:n,recorded_request:s.requested,recorded_application:s.applied,native_solver_diagnostics:p?.diagnostics??null,recorded_handoffs:p?.handoffs??null},null,2);
}
function chart(id,rows,series,label){
  const {ctx,w,h}=size($(id)),values=rows.flatMap(r=>series.map(s=>r[s.y]).filter(Number.isFinite));if(!values.length)return;
  const low=Math.min(...values),high=Math.max(...values),pad=Math.max(.001,(high-low)*.12),start=clock.start,end=clock.end;
  const map=p=>[48+(p[0]-start)/(end-start||1)*(w-64),h-28-(p[1]-low+pad)/(high-low+2*pad)*(h-50)];
  ctx.fillStyle=token('surface');ctx.fillRect(0,0,w,h);
  series.forEach(series=>{let prior=null;ctx.strokeStyle=series.color;ctx.lineWidth=1.5;ctx.beginPath();for(const row of rows){const x=row[series.x],y=row[series.y];if(!Number.isFinite(x)||!Number.isFinite(y)){prior=null;continue;}const p=map([x,y]);if(!prior)ctx.moveTo(...p);else{if(series.step)ctx.lineTo(p[0],prior[1]);ctx.lineTo(...p);}prior=p;}ctx.stroke();});
  ctx.fillStyle=token('muted');ctx.font='11px '+token('font');ctx.fillText(label,12,15);ctx.fillText(`${fmt(start)} → ${fmt(end)} simulated s`,48,h-7);ctx.fillText(fmt(high),0,34);ctx.fillText(fmt(low),0,h-28);
  const x=map([clock.time,0])[0];ctx.strokeStyle=token('text');ctx.setLineDash([3,4]);ctx.beginPath();ctx.moveTo(x,22);ctx.lineTo(x,h-28);ctx.stroke();ctx.setLineDash([]);
}
function render(now,force=false){
  if(!data||!clock)return;const s=snapshot(data,clock.time),p=packet(s);drawTrack(s,p,now);updateInstruments(s);drawMicroscope(p,now,force);
  const inspection=$('packet').value==='active'?(p?'Following available active packet '+p.id:'No active horizon available at this clock'):`Historical inspection · packet ${p?.id??'unavailable'} · ${p?.valid!==true?'not valid':!Number.isFinite(p.completion)||p.completion>clock.time?'not available at this replay time':'recorded completion reached'} · selection does not confer authority`;
  $('horizon-status').textContent=inspection;$('inspection-note').textContent=inspection;
  $('timeline').value=s.index;$('timeline').setAttribute('aria-valuetext',fmt(s.native.time,6)+' seconds, native sample '+s.index);
  $('time').textContent=`${fmt(clock.time)} / ${fmt(clock.end)} s · ${clock.playing?'Playing':'Paused'}`;Object.assign($('time').dataset,{replayTime:String(clock.time),playing:String(clock.playing)});
  $('play').textContent=clock.playing?'Pause':'Play';$('play').disabled=waiting||!clock.playing&&clock.time>=clock.end;$('back').disabled=s.index===0;$('next').disabled=s.index===data.states.length-1;
  if(force||now-lastReadout>=100){
    $('readout').replaceChildren(...[`Native t ${fmt(s.native.time,6)} s`,`vy ${fmt(s.native.vy)} m/s`,`r ${fmt(s.native.r)} rad/s`,`Latest application ${fmt(s.applied?.application_time,6)} s`,`Requested δ ${fmt(s.requested?.requested_delta,4)} rad`].map(text=>{const e=document.createElement('span');e.textContent=text;return e;}));
    if($('details').open)diagnostics(s,p);lastReadout=now;
  }
  if($('traces').open&&(force||now-lastPlot>=200)){chart('error',data.states,[{x:'time',y:'error_y',color:colors.plant}],'Native racing-reference lateral error [m]');chart('command',data.controls,[{x:'time',y:'requested_delta',color:colors.reference,step:true},{x:'application_time',y:'delta',color:colors.prediction,step:true}],'Recorded request / applied steering [rad] · ZOH');lastPlot=now;}
}
function requestContinuation(){
  if(waiting||!data?.meta.next_window||!$('continue').checked)return;
  pending={epoch,end:clock.end,speed:clock.speed};waiting=true;$('transition-status').textContent='Verifying next native window… playback pauses at the boundary.';
  report({epoch,loaded:true,advance:true,speed:clock.speed});
}
function loop(now){
  raf=0;if(!data||!clock)return;const wasPlaying=clock.playing;clock.advance(now);
  if(now-lastPaint>=1000/30){if(segment){if(lastFrame!==null)maxGap=Math.max(maxGap,now-lastFrame);lastFrame=now;frames++;}render(now);lastPaint=now;}
  if(wasPlaying&&!clock.playing){stopSegment(now);render(now,true);requestContinuation();}
  if(clock.playing||moving)raf=requestAnimationFrame(loop);
}
function animate(){if(!raf)raf=requestAnimationFrame(loop);}
function seek(index){pause();waiting=false;pending=null;$('transition-status').textContent='';clock.seek(data.states[Math.max(0,Math.min(data.states.length-1,index))].time);camera.wall=performance.now();microCamera.wall=camera.wall;render(performance.now(),true);animate();}
$('play').onclick=()=>{if(clock.playing)pause();else{const now=performance.now();clock.play(now);startSegment(now);}render(performance.now(),true);animate();};
$('restart').onclick=()=>seek(0);$('back').onclick=()=>seek(snapshot(data,clock.time).index-1);$('next').onclick=()=>seek(snapshot(data,clock.time).index+1);$('timeline').oninput=()=>seek(Number($('timeline').value));
$('speed').onchange=()=>{const now=performance.now();clock.advance(now);stopSegment(now);clock.rate(Number($('speed').value),now);if(clock.playing)startSegment(now);render(now,true);animate();};
$('view').onchange=()=>{camera.wall=performance.now();render(performance.now(),true);animate();};
$('packet').onchange=()=>{pause();$('node').value=0;tableKey='';render(performance.now(),true);animate();};
for(const id of ['node','all-labels','show-radians','nominal'])$(id).oninput=()=>{render(performance.now(),true);animate();};
$('ratio').oninput=()=>{const v=Number($('ratio').value);try{wheel(0,0,v);ratio=v;$('ratio-error').textContent='';render(performance.now(),true);animate();}catch(e){$('ratio-error').textContent=e.message;}};
$('seek-progress').onclick=()=>{if($('progress-seek').value==='')return;const i=progressIndex(data.states,Number($('progress-seek').value),snapshot(data,clock.time).index);if(i===null)$('inspection-note').textContent='Progress seek unavailable: native progress is not monotone.';else seek(i);};
document.querySelectorAll('details').forEach(d=>d.ontoggle=()=>{if(data){render(performance.now(),true);animate();}height();});
document.addEventListener('visibilitychange',()=>{if(document.hidden)pause();});window.addEventListener('pagehide',()=>pause());window.addEventListener('resize',()=>{if(data){render(performance.now(),true);animate();}height();});
setInterval(()=>{if(data&&performance.now()-verified>4500){invalidate('Evidence recheck unavailable — replay cleared. Reopen the recording.');report({epoch,loaded:false});}},250);
window.addEventListener('message',event=>{
  if(event.source!==parent||event.data?.type!=='streamlit:render')return;const args=event.data.args;
  if(args?.valid!==true){invalidate(args?.error||'Evidence unavailable; replay cleared');return;}verified=performance.now();
  if(args.payload&&(!data||args.epoch!==epoch)){
    const resume=!!pending&&args.resume?.from_epoch===pending.epoch&&args.payload.states[0].time===pending.end&&$('continue').checked;
    const rate=pending?.speed??1;pause();data=args.payload;epoch=args.epoch;clock=new ReplayClock(data.states[0].time,data.states.at(-1).time);clock.rate(rate,performance.now());
    historyXY=data.states.map(s=>[s.x,s.y]);waiting=false;pending=null;tableKey='';$('transition-status').textContent=resume?'Continued after source verification; no simulated time added during the boundary pause.':'';
    $('speed').value=String(rate);$('timeline').max=data.states.length-1;$('timeline').value=0;$('packet').replaceChildren(new Option('Follow active packet','active'),...data.packets.map(p=>new Option('Historical packet '+p.id,String(p.id))));$('node').value=0;
    document.querySelector('main').hidden=false;$('notice').className='';received++;
    $('notice').textContent=`${data.meta.software_fixture?'SOFTWARE TRANSPORT FIXTURE — NO SCIENTIFIC EVIDENCE':'VERIFIED RECORDING'} · ${data.run_id} · ${data.coverage.samples.toLocaleString()} / ${data.meta.native_samples_total.toLocaleString()} native samples in this window`;
    Object.assign($('notice').dataset,{epoch,payloadLoads:String(received)});$('coverage').removeAttribute('data-segment');$('coverage').textContent=`${data.coverage.samples} retained native samples; no endpoint extrapolation.`;
    if(resume){clock.play(performance.now());startSegment(performance.now());}render(performance.now(),true);report({epoch,loaded:true});animate();height();
  }else if(!data)report({epoch:args.epoch,loaded:false});
});
new ResizeObserver(height).observe(document.body);send('streamlit:componentReady',{apiVersion:1});height();
