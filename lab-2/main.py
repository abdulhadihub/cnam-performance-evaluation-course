from __future__ import annotations

import argparse
from pathlib import Path

from sim import Engine, EngineConfig, run_experiment_set


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Discrete-event simulator for queueing scenarios")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("test", help="Run class-level smoke tests")

    run = sub.add_parser("run", help="Run one simulation with custom parameters")
    run.add_argument("--lambda-rate", type=float, default=6.0)
    run.add_argument("--mu-rate", type=float, default=8.0)
    run.add_argument("--servers", type=int, default=1)
    run.add_argument("--capacity", type=int, default=-1, help="-1 means infinite capacity")
    run.add_argument("--sim-time", type=float, default=20_000.0)
    run.add_argument("--warmup-fraction", type=float, default=0.1)
    run.add_argument("--seed", type=int, default=1)
    run.add_argument("--trace", type=str, default="", help="Optional trace CSV output path")

    exp = sub.add_parser("experiments", help="Run all required scenarios and generate CI plots")
    exp.add_argument("--sim-time", type=float, default=20_000.0)
    exp.add_argument("--warmup-fraction", type=float, default=0.1)
    exp.add_argument("--replications", type=int, default=30)
    exp.add_argument("--seed", type=int, default=100)
    exp.add_argument("--output", type=str, default="outputs")
    exp.add_argument("--write-traces", action="store_true")
    return parser


def run_tests() -> int:
    for line in Engine.run_class_tests():
        print(line)
    print("Class tests completed.")
    return 0


def run_single(args: argparse.Namespace) -> int:
    capacity = None if args.capacity < 0 else args.capacity
    engine = Engine(
        EngineConfig(
            lambda_rate=args.lambda_rate,
            mu_rate=args.mu_rate,
            num_servers=args.servers,
            system_capacity=capacity,
            simulation_time=args.sim_time,
            warmup_fraction=args.warmup_fraction,
            seed=args.seed,
        )
    )
    trace_path = Path(args.trace) if args.trace else None
    metrics = engine.run(trace_path=trace_path)
    for key, value in metrics.items():
        print(f"{key}: {value}")
    return 0


def run_experiments(args: argparse.Namespace) -> int:
    _, summary = run_experiment_set(
        simulation_time=args.sim_time,
        warmup_fraction=args.warmup_fraction,
        replications=args.replications,
        base_seed=args.seed,
        output_root=args.output,
        write_traces=args.write_traces,
    )
    print(f"Completed {len(summary)} aggregated configurations.")
    print(f"Results: {Path(args.output) / 'results' / 'summary.csv'}")
    print(f"Plots:   {Path(args.output) / 'plots'}")
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "test":
        return run_tests()
    if args.command == "run":
        return run_single(args)
    if args.command == "experiments":
        return run_experiments(args)

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
