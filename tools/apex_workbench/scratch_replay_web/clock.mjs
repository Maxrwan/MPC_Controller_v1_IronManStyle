// Display time and native-record lookup only. No model, controller or event reconstruction.
export function lastAt(rows, time, field = 'time') {
  let lo = 0, hi = rows.length;
  while (lo < hi) { const mid = (lo + hi) >>> 1; if (rows[mid][field] <= time) lo = mid + 1; else hi = mid; }
  return lo - 1;
}
export class ReplayClock {
  constructor(start, end) { this.start = start; this.end = end; this.time = start; this.speed = 1; this.playing = false; this.lastWall = null; }
  advance(now) {
    if (this.playing) {
      if (this.lastWall !== null) this.time = Math.min(this.end, this.time + Math.max(0, now - this.lastWall) / 1000 * this.speed);
      this.lastWall = Math.max(now, this.lastWall ?? now);
      if (this.time >= this.end) this.pause();
    }
    return this.time;
  }
  play(now) { if (this.time < this.end) { this.lastWall = now; this.playing = true; } }
  pause(now) { if (now !== undefined) this.advance(now); this.playing = false; this.lastWall = null; }
  seek(time) { this.pause(); this.time = Math.max(this.start, Math.min(this.end, time)); }
  rate(value, now) { if (![0.25, 0.5, 1, 2].includes(value)) throw Error('Unsupported playback speed'); this.advance(now); this.speed = value; }
}
export function snapshot(data, time) {
  const index = Math.max(0, lastAt(data.states, time));
  const native = data.states[index], next = data.states[Math.min(index + 1, data.states.length - 1)];
  // Only the displayed XY marker interpolates. Hold across a documented instantaneous state kick.
  const jump = data.jumps.includes(next.time);
  const f = !jump && next.time > native.time ? Math.max(0, Math.min(1, (time - native.time) / (next.time - native.time))) : 0;
  const position = [native.x + (next.x - native.x) * f, native.y + (next.y - native.y) * f];
  const candidate = data.packets.find(p => p.id === native.plan_id);
  const active = native.mode === 'trajectory' && candidate?.valid === true &&
    Number.isFinite(candidate.completion) && candidate.completion <= time &&
    time >= candidate.times[0] && time < candidate.times.at(-1) ? candidate : null;
  const ai = lastAt(data.controls, time, 'application_time'), ri = lastAt(data.controls, time);
  return { index, native, position, interpolated: f > 0, active,
    applied: ai >= 0 ? data.controls[ai] : null, requested: ri >= 0 ? data.controls[ri] : null };
}
