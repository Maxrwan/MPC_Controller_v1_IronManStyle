"""Independent literal nominal reference; only the future explicit qualification worker uses it."""

from tools.apex_workbench import lab_configuration as config


def execute(values, output, *, resolved, qualification=False):
    config.execution_context(values, qualification=qualification, reference=True)
    resolved = config.validate_resolved(
        values, resolved, vehicle_yaml=resolved["base_source"]["yaml"]
    )
    from apex.models.tire.linear import LinearAxleTire
    from apex.models.vehicle.dynamic_bicycle import DynamicBicycle
    from apex.models.vehicle.load_transfer import QuasiStaticLongitudinalLoadTransfer
    from apex.models.vehicle.parameters import VehicleParameters
    from apex.simulation.runner import RunConfig, SimulationRunner
    from apex.track import ClosedTrack
    from apex.track.synthetic import circle_waypoints
    from tools.apex_workbench.dynamic_lab import export_result
    from tools.apex_workbench.storage import write_json

    class LiteralInputs:
        def __init__(self):
            self.commands = [[0.0, 0.0] for _ in range(20)] + [[0.020, 0.0] for _ in range(80)]
            self.tick = 0

        def compute_control(self, state, context):
            if context != {"time": self.tick * 0.005, "dt": 0.005}:
                raise ValueError("Independent reference clock mismatch")
            action = self.commands[self.tick].copy()
            self.tick += 1
            return action

    parameters = VehicleParameters(
        name="synthetic_dynamic_test_vehicle",
        mass=2.0,
        yaw_inertia=0.025,
        wheelbase=0.30,
        lf=0.15,
        lr=0.15,
        cg_height=0.04,
        front_cornering_stiffness=45.0,
        rear_cornering_stiffness=45.0,
        tire_road_friction_coefficient=1.0,
        maximum_steering_angle=0.4,
        maximum_acceleration=2.0,
        maximum_braking_deceleration=3.0,
        maximum_speed=6.0,
    )
    track = ClosedTrack.from_waypoints(
        circle_waypoints(5.0, count=128), left_width=0.6, right_width=0.9
    )
    model = DynamicBicycle(
        parameters,
        track,
        default_dt=0.005,
        v_dynamic_min=0.5,
        tire_model=LinearAxleTire(),
        load_model=QuasiStaticLongitudinalLoadTransfer(),
    )
    output.mkdir(exist_ok=False)
    write_json(output / "resolved_lab.json", resolved, exclusive=True)
    result = SimulationRunner(
        model,
        LiteralInputs(),
        track,
        RunConfig(
            duration=0.500,
            dt_plant=0.005,
            dt_control=0.005,
            target_laps=None,
            stop_on_boundary=False,
            latency=None,
        ),
    ).run([2.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    return export_result(model, result, resolved, output)
