"""Plot a synthetic circle or CSV track; use --save for noninteractive validation."""

import argparse
from pathlib import Path

import numpy as np

from apex.track import ClosedTrack, load_track_csv
from apex.track.synthetic import circle_waypoints


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path)
    parser.add_argument("--left-width", type=float)
    parser.add_argument("--right-width", type=float)
    parser.add_argument("--save", type=Path)
    args = parser.parse_args()
    if args.csv and (args.left_width is None or args.right_width is None):
        parser.error("CSV tracks require explicit --left-width and --right-width")
    if args.save:
        import matplotlib

        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if args.csv:
        track = load_track_csv(args.csv, left_width=args.left_width, right_width=args.right_width)
        title = f"Track geometry: {args.csv.name}"
    else:
        # Synthetic plotting dimensions only, not physical project defaults.
        track = ClosedTrack.from_waypoints(
            circle_waypoints(5.0),
            left_width=0.6 if args.left_width is None else args.left_width,
            right_width=0.9 if args.right_width is None else args.right_width,
        )
        title = "Synthetic CCW circle: radius 5 m"
    samples = [track.sample(s) for s in np.linspace(0, track.length, 401)]
    xy = np.array([(p.x, p.y) for p in samples])
    normals = np.array([(-np.sin(p.heading), np.cos(p.heading)) for p in samples])
    left = xy + np.array([p.left_width for p in samples])[:, None] * normals
    right = xy - np.array([p.right_width for p in samples])[:, None] * normals
    fig, ax = plt.subplots(figsize=(8, 8), layout="constrained")
    ax.plot(*xy.T, label="Centerline", color="black")
    ax.plot(*left.T, label="Left boundary", color="tab:blue")
    ax.plot(*right.T, label="Right boundary", color="tab:orange")
    selected = np.arange(0, 400, 25)
    ax.quiver(
        *xy[selected].T,
        *normals[selected].T,
        angles="xy",
        scale_units="xy",
        scale=2,
        color="tab:blue",
        label="Left unit-normal direction (0.5 m arrows)",
    )
    ax.scatter([xy[0, 0]], [xy[0, 1]], color="red", label="Start/finish")
    ax.set(xlabel="Global X [m]", ylabel="Global Y [m]", title=title, aspect="equal")
    ax.grid(alpha=0.25)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.09), ncols=2, fontsize=8)
    if args.save:
        args.save.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(args.save, dpi=160)
        print(f"Saved {args.save.resolve()}")
    else:
        plt.show()
    plt.close(fig)


if __name__ == "__main__":
    main()
