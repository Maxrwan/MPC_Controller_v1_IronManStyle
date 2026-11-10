// Readouts from the accepted clock snapshot. No model, event or physical ratio reconstruction.
export function instruments(s, time, meta) {
  const applied = s.applied;
  const angle = applied ? applied.delta : s.native.delta;
  const nominal = applied?.nominal_delta;
  const length = meta.track_length_m;
  const phase = Number.isFinite(s.native.s_abs) && length > 0 ? ((s.native.s_abs % length) + length) % length : null;
  const crossings = meta.lap_crossings.filter(c => c.time_s <= s.native.time);
  const sectors = meta.sectors.filter(c => c.coverage === 'complete' && c.end_time_s <= s.native.time);
  return {angle: Number.isFinite(angle) ? angle : null,
    nominal: Number.isFinite(nominal) ? nominal : null,
    applicationTime: applied?.application_time ?? null, requestTime: applied?.time ?? null,
    phase, fraction: phase === null ? null : phase / length,
    laps: crossings.filter(c => c.complete_circuit).length,
    lapTime: crossings.filter(c => c.complete_circuit).at(-1)?.interval_s ?? null,
    sectors, nativeTime:s.native.time, replayTime:time};
}

export function progressIndex(states, progress, index) {
  // Seek within this native window only, nearest genuine progress observation.
  // Nonmonotone trajectories have no unambiguous progress seek.
  if (states.some((s,i) => !Number.isFinite(s.s_abs) || i && s.s_abs < states[i-1].s_abs)) return null;
  let best = index;
  states.forEach((s,i) => {if(Math.abs(s.s_abs-progress) < Math.abs(states[best].s_abs-progress)) best=i;});
  return best;
}
