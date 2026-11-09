"""Opt-in fixed commitments and urgent latency accounting; no solve cancellation."""

TOL = 1e-10
GRID = 0.01


def on_grid(time):
    return abs(time - round(time / GRID) * GRID) <= TOL


class FixedHandoffs:
    """Released commitments may wait concurrently; computations remain single-pending.

    This retains every early completed packet until its own deadline, including an urgent
    release while another packet is waiting. It is not a queue of solver launches.
    """

    def __init__(self, offset):
        self.offset = offset
        self.cycles = []
        self.ready = {}
        self.demands = []
        self.latched = None
        self.consecutive_misses = 0

    def trigger(self, time, busy):
        if self.latched is not None:
            # The runtime latch coalesces repeated demand; preserve the earliest wait.
            self.latched["coalesced_trigger_times"].append(time)
            return
        row = dict(
            trigger_time=time,
            coalesced_trigger_times=[],
            eligible_time=None if busy else time,
            release_time=None,
            planner_busy_wait=None,
            grid_alignment_wait=None,
            fixed_offset=self.offset,
            serviced_by_plan_id=None,
            coalesced_nominal=None,
            accepted_plan_id=None,
            accepted_time=None,
            trigger_to_authority=None,
            status="latched",
        )
        self.demands.append(row)
        self.latched = row

    def idle(self, time):
        if self.latched is not None and self.latched["eligible_time"] is None:
            self.latched["eligible_time"] = time

    def release(self, plan_id, time, urgent, packet):
        if not on_grid(time):
            raise ValueError("Fixed planner release is not on the global 10 ms grid")
        row = dict(
            plan_id=plan_id,
            t_release=time,
            t_ready=None,
            valid_from=time + self.offset,
            t_accept=None,
            first_TVLQR_use=None,
            expiry=None if packet is None else packet.horizon_end_time,
            preparation_duration=None,
            wait_duration=None,
            deadline_margin=None,
            status="pending",
            miss_time=None,
            late_discard_time=None,
            packet_age=None,
            reserve_at_acceptance=None,
            consecutive_misses=None,
        )
        self.cycles.append(row)
        if self.latched is not None:
            demand = self.latched
            self.idle(time)
            demand.update(
                release_time=time,
                serviced_by_plan_id=plan_id,
                coalesced_nominal=not urgent,
                planner_busy_wait=demand["eligible_time"] - demand["trigger_time"],
                grid_alignment_wait=max(0.0, time - demand["eligible_time"]),
                status="released",
            )
            self.latched = None

    def cycle(self, plan_id):
        return next(row for row in self.cycles if row["plan_id"] == plan_id)

    def complete(self, plan_id, time, packet):
        row = self.cycle(plan_id)
        row.update(
            t_ready=time,
            preparation_duration=time - row["t_release"],
            deadline_margin=row["valid_from"] - time,
            wait_duration=max(0.0, row["valid_from"] - time),
        )
        if row["status"] == "missed":
            row["late_discard_time"] = time
        else:
            self.ready[plan_id] = packet
        self.idle(time)

    def due(self, time):
        return [
            row
            for row in self.cycles
            if row["status"] == "pending" and row["valid_from"] <= time + TOL
        ]

    def resolve(self, row, time, status):
        row["status"] = status
        self.consecutive_misses = self.consecutive_misses + 1 if status == "missed" else 0
        row["consecutive_misses"] = self.consecutive_misses
        if status == "missed":
            row["miss_time"] = time
        elif status == "accepted":
            row.update(t_accept=time, packet_age=time - row["t_release"])
            for demand in self.demands:
                if (
                    demand["release_time"] is not None
                    and demand["accepted_time"] is None
                    and row["plan_id"] >= demand["serviced_by_plan_id"]
                ):
                    demand.update(
                        accepted_plan_id=row["plan_id"],
                        accepted_time=time,
                        trigger_to_authority=time - demand["trigger_time"],
                        status="accepted",
                    )

    def sample(self, plan_id, time):
        if plan_id:
            row = self.cycle(plan_id)
            if row["first_TVLQR_use"] is None:
                row["first_TVLQR_use"] = time

    def next_deadlines(self):
        return [row["valid_from"] for row in self.cycles if row["status"] == "pending"]
