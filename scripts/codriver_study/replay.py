"""Saved planner packets with frozen availability; no optimization or new planning."""

import json
from dataclasses import fields

from apex.control.trajectory.packet import TrajectoryPacket


class PacketReplay:
    def __init__(self, folder):
        names = {f.name for f in fields(TrajectoryPacket)}
        self.packets = {
            p["plan_id"]: TrajectoryPacket(**{k: v for k, v in p.items() if k in names})
            for p in json.loads((folder / "trajectory_packets.json").read_text())
        }
        self.events = {
            p["plan_id"]: p for p in json.loads((folder / "events.json").read_text())["plans"]
        }

    def prepare(self, plan_id, state, time, estimate, buffer, tracker, *, startup=False):
        if plan_id not in self.events:
            return None, dict(
                plan_id=plan_id,
                release_time=time,
                estimated_delay=0,
                predicted_state=list(state),
                success=False,
                status="replay_finished",
                planner_total_time=0,
                planner_cpu_time=0,
                solver_attempted=False,
                preparation="replay_finished",
            )
        original = self.events[plan_id]
        if abs(time - original["release_time"]) > 1e-8:
            raise ValueError("Replay release differs from frozen packet chronology")
        event = dict(original)
        event.update(
            planner_total_time=0 if startup else original["completion_time"] - time,
            planner_cpu_time=0,
            solve_time=0,
            preview_time=0,
            prediction_time=0,
            gain_time=0,
            replay=True,
        )
        return self.packets.get(plan_id), event
