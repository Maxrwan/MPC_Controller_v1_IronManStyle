import { ReplayClock, snapshot } from './clock.mjs';

const $ = id => document.getElementById(id);
const send = (type, extra = {}) => parent.postMessage({isStreamlitMessage:true, type, ...extra}, '*');
const report = value => send('streamlit:setComponentValue', {value, dataType:'json'});
const fmt = (v, digits=4) => typeof v === 'number' && Number.isFinite(v) ? v.toFixed(digits) : 'unavailable';
const colors = {center:'#8799ae',left:'#526f97',right:'#526f97',plant:'#efba82',prediction:'#7cdaec',reference:'#cebded'};
let data = null, epoch = null, clock = null, verified = 0, raf = 0, lastPaint = -Infinity;
let lastReadout = -Infinity, lastPlot = -Infinity, base = null, charts = [], segment = null, frames = 0;
let lastFrame = null, maxGap = 0, received = 0;

function height() { send('streamlit:setFrameHeight', {height:Math.ceil(document.body.getBoundingClientRect().height + 16)}); }
function stopSegment(now) {
  if (segment && clock) {
    const seconds = (now - segment.wall) / 1000, advance = clock.time - segment.time;
    $('coverage').textContent = `${data.coverage.samples} native samples; ${data.coverage.stop_reason || 'partial coverage'}. ` +
      `Last playback segment: ${fmt(advance,4)} simulated s / ${fmt(seconds,4)} wall s at ${segment.speed}×; ` +
      `pacing difference ${fmt(advance - seconds * segment.speed,4)} s; ${frames} rendered frames; ` +
      `maximum painted-frame gap ${fmt(maxGap,1)} ms. Display timing only.`;
    $('coverage').dataset.segment = JSON.stringify({simulated_s:advance,wall_s:seconds,speed:segment.speed,frames,max_gap_ms:maxGap});
  }
  segment = null;
}
function pause(now = performance.now()) { if (clock) clock.pause(now); cancelAnimationFrame(raf); stopSegment(now); if (data) render(now,true); }
function invalidate(message) {
  pause(); data = null; clock = null; base = null; charts = [];
  $('notice').textContent = message; $('notice').className = 'invalid'; document.querySelector('main').hidden = true;
  $('readout').replaceChildren(); $('diagnostics').textContent = ''; $('authority').textContent = '';
  for (const canvas of document.querySelectorAll('canvas')) canvas.getContext('2d').clearRect(0,0,canvas.width,canvas.height);
  height();
}
function canvasSize(canvas) {
  const box = canvas.getBoundingClientRect(), dpr = Math.min(2, devicePixelRatio || 1);
  canvas.width = Math.round(box.width * dpr); canvas.height = Math.round(box.height * dpr);
  const ctx = canvas.getContext('2d'); ctx.scale(dpr,dpr);
  return {ctx,w:box.width,h:box.height};
}
function path(ctx, points, map, color, width=1.5) {
  if (!points.length) return;
  ctx.beginPath(); points.forEach((p,i) => {const [x,y] = map(p); if(i) ctx.lineTo(x,y); else ctx.moveTo(x,y);});
  ctx.strokeStyle = color; ctx.lineWidth = width; ctx.stroke();
}
function background() {
  if (!data) return;
  const canvas = $('track'), {w,h} = canvasSize(canvas);
  const points = $('view').value === 'track' ? data.track.center : data.states.map(s=>[s.x,s.y]);
  const xs=points.map(p=>p[0]), ys=points.map(p=>p[1]);
  const loX=Math.min(...xs)-2, hiX=Math.max(...xs)+2, loY=Math.min(...ys)-2, hiY=Math.max(...ys)+2;
  const scale=Math.min((w-50)/(hiX-loX),(h-70)/(hiY-loY)), cx=(loX+hiX)/2, cy=(loY+hiY)/2;
  const map=p=>[w/2+(p[0]-cx)*scale,h/2-(p[1]-cy)*scale];
  const buffer=document.createElement('canvas'); buffer.width=canvas.width; buffer.height=canvas.height;
  const ctx=buffer.getContext('2d'); ctx.scale(canvas.width/w,canvas.height/h);
  ctx.fillStyle='#121922'; ctx.fillRect(0,0,w,h);
  for (const side of ['left','right','center']) path(ctx,data.track[side],map,colors[side]);
  path(ctx,data.states.map(s=>[s.x,s.y]),map,colors.plant,2);
  ctx.fillStyle='#c5d0e0'; ctx.font='12px system-ui'; ctx.fillText('Canonical track · native trajectory · cyan prediction · violet reference',14,20);
  ctx.fillText(`Global x / y [m] · ${fmt(w/scale,1)} m visible width · position marker has no physical dimensions`,14,h-12);
  base={buffer,map,w,h}; charts=[];
}
function drawChart(id, rows, series, yLabel, time) {
  const canvas=$(id), {ctx,w,h}=canvasSize(canvas);
  const points=series.map(s=>rows.filter(r=>Number.isFinite(r[s.x])&&Number.isFinite(r[s.y])).map(r=>[r[s.x],r[s.y]]));
  const ys=points.flat().map(p=>p[1]); if(!ys.length)return;
  const low=Math.min(...ys), high=Math.max(...ys), pad=Math.max(0.001,(high-low)*.12);
  const start=data.states[0].time, end=data.states.at(-1).time;
  const map=p=>[52+(p[0]-start)/(end-start||1)*(w-70),h-30-(p[1]-low+pad)/(high-low+2*pad)*(h-55)];
  ctx.fillStyle='#121922'; ctx.fillRect(0,0,w,h);
  ctx.strokeStyle='#354052'; ctx.beginPath();ctx.moveTo(52,25);ctx.lineTo(52,h-30);ctx.lineTo(w-18,h-30);ctx.stroke();
  points.forEach((p,i)=>{
    const shown=series[i].step?p.flatMap((v,k)=>k?[[v[0],p[k-1][1]],v]:[v]):p;
    path(ctx,shown,map,series[i].color,1.5);
  });
  ctx.fillStyle='#c5d0e0';ctx.font='12px system-ui';ctx.fillText(yLabel,12,15);ctx.fillText(`${fmt(start,2)} → ${fmt(end,3)} simulated s`,w/2-60,h-8);
  ctx.fillText(fmt(high,3),2,35);ctx.fillText(fmt(low,3),2,h-33);
  const x=map([time,0])[0];ctx.strokeStyle='#fff';ctx.setLineDash([3,4]);ctx.beginPath();ctx.moveTo(x,25);ctx.lineTo(x,h-30);ctx.stroke();ctx.setLineDash([]);
}
function selected(s) { return $('packet').value === 'active' ? s.active : data.packets.find(p=>String(p.id)===$('packet').value) || null; }
function details(s,p) {
  const node=Math.min(Number($('node').value),p ? p.states.length-1 : 0); $('node').max=p ? p.states.length-1 : 0;
  const u=p && node<p.controls.length ? p.controls[node] : null;
  $('diagnostics').textContent=JSON.stringify({
    plant_native_sample_time_s:s.native.time,active_packet_at_native_sample:s.active?.id ?? null,
    inspected_packet:p?.id ?? null,inspection_mode:$('packet').value==='active'?'Follow active packet':'Manual historical inspection',
    recorded_completion_time_s:p?.completion ?? null,completion_reached: p && Number.isFinite(p.completion)?p.completion<=clock.time:null,
    recorded_valid:p?.valid ?? null,recorded_reason:p?.reason ?? null,recorded_handoffs:p?.handoffs ?? [],
    native_solver_diagnostics:p?.diagnostics ?? null,
    prediction_node:node,prediction_time_s:p?.times[node] ?? null,
    solver_state_order:['vx','vy','r','e_psi','s_abs','e_y'],solver_state_SI:p?.states[node] ?? null,
    nominal_command_order:['delta_rad','a_cmd_Fx_per_m_mps2'],nominal_command:u,terminal_state_without_command:!!p&&!u,
    recorded_request:s.requested,recorded_application:s.applied,
    note:'Completion, validity and actual native active identity are distinct. Historical inspection does not confer authority. Predictions are solver values; no control or packet event is interpolated.'
  },null,2);
}
function render(now,force=false) {
  if(!data||!clock)return;
  const s=snapshot(data,clock.time),p=selected(s);
  if(!base)background();
  const canvas=$('track'),ctx=canvas.getContext('2d');ctx.setTransform(1,0,0,1,0,0);ctx.drawImage(base.buffer,0,0);
  ctx.scale(canvas.width/base.w,canvas.height/base.h);
  if(p){path(ctx,p.reference,base.map,colors.reference,2);path(ctx,p.xy,base.map,colors.prediction,2.5);}
  const pos=base.map(s.position);ctx.fillStyle='#87edb1';ctx.beginPath();ctx.arc(...pos,7,0,2*Math.PI);ctx.fill();ctx.strokeStyle='#fff';ctx.lineWidth=1.5;ctx.stroke();
  $('timeline').value=s.index; $('timeline').setAttribute('aria-valuetext',`${fmt(s.native.time,6)} seconds, native sample ${s.index}`);
  $('time').textContent=`${fmt(clock.time,3)} / ${fmt(clock.end,3)} s · ${clock.playing?'Playing':'Paused'}`;
  $('time').dataset.replayTime=String(clock.time);$('time').dataset.playing=String(clock.playing);
  $('play').textContent=clock.playing?'Pause':'Play';$('play').disabled=!clock.playing&&clock.time>=clock.end;
  $('back').disabled=s.index===0;$('next').disabled=s.index===data.states.length-1;
  if(force||now-lastReadout>=100){
    const a=s.applied, r=s.requested;
    const values=[`Native t ${fmt(s.native.time,6)} s`,`vx ${fmt(s.native.vx)} m/s`,`vy ${fmt(s.native.vy)} m/s`,`r ${fmt(s.native.r)} rad/s`,
      `Held δ ${fmt(s.native.delta)} rad`,`Held a_cmd ${fmt(s.native.a_cmd)} m/s²`,`Racing error ${fmt(s.native.error_y)} m`,
      `Latest application t ${fmt(a?.application_time,6)} s`,`Requested δ ${fmt(r?.requested_delta)} rad`];
    $('readout').replaceChildren(...values.map(text=>{const node=document.createElement('span');node.textContent=text;return node;}));
    $('authority').textContent=`Active at held native sample: ${s.active ? 'packet '+s.active.id : 'no available valid trajectory'}. `+
      ($('packet').value==='active'?'Following active horizon.':`Inspecting historical packet ${p?.id ?? 'unavailable'}; this selection does not change active authority.`);
    if($('details').open)details(s,p);lastReadout=now;
  }
  if((force||now-lastPlot>=200)&&document.querySelector('details').open){
    drawChart('error',data.states,[{x:'time',y:'error_y',color:colors.plant}],'Native racing-reference error [m]',clock.time);
    drawChart('command',data.controls,[{x:'time',y:'requested_delta',color:colors.reference,step:true},{x:'application_time',y:'delta',color:colors.prediction,step:true}],'Recorded request / application events, ZOH display · steering [rad]',clock.time);lastPlot=now;
  }
}
function loop(now) {
  if(!data||!clock?.playing)return;
  clock.advance(now);
  if(now-lastPaint>=1000/30){if(lastFrame!==null)maxGap=Math.max(maxGap,now-lastFrame);lastFrame=now;frames++;render(now);lastPaint=now;}
  if(clock.playing)raf=requestAnimationFrame(loop);else{stopSegment(now);render(now,true);}
}
function seek(index) { pause(); clock.seek(data.states[Math.max(0,Math.min(data.states.length-1,index))].time);render(performance.now(),true); }
$('play').onclick=()=>{if(clock.playing)pause();else{const now=performance.now();clock.play(now);segment={wall:now,time:clock.time,speed:clock.speed};frames=0;maxGap=0;lastFrame=null;raf=requestAnimationFrame(loop);render(now,true);}};
$('restart').onclick=()=>seek(0);
$('back').onclick=()=>seek(snapshot(data,clock.time).index-1);
$('next').onclick=()=>seek(snapshot(data,clock.time).index+1);
$('timeline').oninput=()=>seek(Number($('timeline').value));
$('speed').onchange=()=>{const now=performance.now();clock.advance(now);stopSegment(now);clock.rate(Number($('speed').value),now);if(clock.playing){segment={wall:now,time:clock.time,speed:clock.speed};frames=0;maxGap=0;lastFrame=null;}render(now,true);};
$('view').onchange=()=>{background();render(performance.now(),true);};
$('packet').onchange=()=>{pause();$('node').value=0;render(performance.now(),true);};
$('node').oninput=()=>{pause();render(performance.now(),true);};
document.querySelectorAll('details').forEach(d=>d.ontoggle=()=>{render(performance.now(),true);height();});
document.addEventListener('visibilitychange',()=>{if(document.hidden)pause();});
window.addEventListener('pagehide',()=>pause());
window.addEventListener('resize',()=>{if(data){background();render(performance.now(),true);}height();});
setInterval(()=>{if(data&&performance.now()-verified>4500){invalidate('Evidence recheck unavailable — replay cleared. Reopen the recording.');report({epoch,loaded:false});}},250);
window.addEventListener('message',event=>{
  if(event.source!==parent||event.data?.type!=='streamlit:render')return;
  const args=event.data.args;
  if(args?.valid!==true){invalidate(args?.error||'Evidence unavailable; replay cleared');return;}
  verified=performance.now();
  if(args.payload&&(!data||args.epoch!==epoch)){
    pause();data=args.payload;epoch=args.epoch;clock=new ReplayClock(data.states[0].time,data.states.at(-1).time);base=null;
    $('speed').value='1';$('timeline').max=data.states.length-1;$('timeline').value=0;$('packet').replaceChildren(new Option('Follow active packet','active'),...data.packets.map(p=>new Option('Historical packet '+p.id,String(p.id))));
    $('node').value=0;document.querySelector('main').hidden=false;$('notice').className='';
    received++;$('notice').textContent=`Verified native replay · ${data.run_id} · payload load ${received}`;
    $('notice').dataset.epoch=epoch;$('coverage').textContent=`${data.coverage.samples} retained native samples; end state is not extrapolated to the requested duration.`;
    $('coverage').removeAttribute('data-segment');background();render(performance.now(),true);report({epoch,loaded:true});height();
  }else if(!data){report({epoch:args.epoch,loaded:false});}
});
new ResizeObserver(height).observe(document.body);
send('streamlit:componentReady',{apiVersion:1});height();
