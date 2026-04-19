from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .engine import Engine, EngineConfig


@dataclass(frozen=True)
class Scenario:
    name: str
    num_servers: int
    system_capacity: int | None


def _t_critical_95(df: int) -> float:
    # Two-sided 95% t critical values for 1..30 df, then normal approximation.
    table = {
        1: 12.706,
        2: 4.303,
        3: 3.182,
        4: 2.776,
        5: 2.571,
        6: 2.447,
        7: 2.365,
        8: 2.306,
        9: 2.262,
        10: 2.228,
        11: 2.201,
        12: 2.179,
        13: 2.160,
        14: 2.145,
        15: 2.131,
        16: 2.120,
        17: 2.110,
        18: 2.101,
        19: 2.093,
        20: 2.086,
        21: 2.080,
        22: 2.074,
        23: 2.069,
        24: 2.064,
        25: 2.060,
        26: 2.056,
        27: 2.052,
        28: 2.048,
        29: 2.045,
        30: 2.042,
    }
    if df <= 0:
        return 0.0
    if df in table:
        return table[df]
    return 1.96


def mean_ci95(values: list[float]) -> tuple[float, float, float, float]:
    n = len(values)
    if n == 0:
        return 0.0, 0.0, 0.0, 0.0
    mean_val = sum(values) / n
    if n == 1:
        return mean_val, mean_val, mean_val, 0.0

    variance = sum((x - mean_val) ** 2 for x in values) / (n - 1)
    std = math.sqrt(variance)
    tcrit = _t_critical_95(n - 1)
    half_width = tcrit * std / math.sqrt(n)
    return mean_val, mean_val - half_width, mean_val + half_width, half_width


def _write_csv(path: Path, rows: list[dict[str, float | int | str]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _plot_metric(
    output_dir: Path,
    scenario_name: str,
    lambdas: list[float],
    means: list[float],
    errors: list[float],
    metric: str,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(8, 5))
    plt.errorbar(lambdas, means, yerr=errors, fmt="o-", capsize=4)
    plt.xlabel("Arrival rate lambda (msg/s)")
    plt.ylabel(metric)
    plt.title(f"{scenario_name} - {metric} (95% CI)")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / f"{scenario_name}-{metric}.png", dpi=150)
    plt.close()


def run_experiment_set(
    *,
    lambdas: list[float] | None = None,
    mu_rate: float = 8.0,
    simulation_time: float = 20_000.0,
    warmup_fraction: float = 0.1,
    replications: int = 30,
    base_seed: int = 100,
    output_root: str = "outputs",
    write_traces: bool = False,
) -> tuple[list[dict[str, float | int | str]], list[dict[str, float | int | str]]]:
    lambdas = lambdas or [4.0, 6.0, 8.0, 12.0]
    scenarios = [
        Scenario(name="MM1", num_servers=1, system_capacity=None),
        Scenario(name="MM1K4", num_servers=1, system_capacity=4),
        Scenario(name="MM1K8", num_servers=1, system_capacity=8),
        Scenario(name="MM3K8", num_servers=3, system_capacity=8),
    ]

    output_dir = Path(output_root)
    raw_rows: list[dict[str, float | int | str]] = []
    summary_rows: list[dict[str, float | int | str]] = []

    for scenario_idx, scenario in enumerate(scenarios):
        for lambda_rate in lambdas:
            per_rep: list[dict[str, float | int]] = []
            for rep in range(replications):
                seed = base_seed + scenario_idx * 10_000 + int(lambda_rate * 100) + rep
                engine = Engine(
                    EngineConfig(
                        lambda_rate=lambda_rate,
                        mu_rate=mu_rate,
                        num_servers=scenario.num_servers,
                        system_capacity=scenario.system_capacity,
                        simulation_time=simulation_time,
                        warmup_fraction=warmup_fraction,
                        seed=seed,
                    )
                )
                trace_path = None
                if write_traces and rep == 0:
                    trace_path = output_dir / "traces" / f"{scenario.name}-lambda{lambda_rate:.0f}.csv"
                metrics = engine.run(trace_path=trace_path)
                metrics["scenario"] = scenario.name
                metrics["replication"] = rep
                per_rep.append(metrics)
                raw_rows.append(metrics)

            numeric_metrics = [
                "avg_n_system",
                "avg_n_queue",
                "avg_wait_queue",
                "avg_response_time",
                "throughput",
                "utilization",
                "drop_probability",
            ]
            summary_row: dict[str, float | int | str] = {
                "scenario": scenario.name,
                "lambda": lambda_rate,
                "mu": mu_rate,
                "servers": scenario.num_servers,
                "capacity": -1 if scenario.system_capacity is None else scenario.system_capacity,
                "replications": replications,
            }
            for metric in numeric_metrics:
                values = [float(row[metric]) for row in per_rep]
                mean_val, ci_low, ci_high, ci_half = mean_ci95(values)
                summary_row[f"{metric}_mean"] = mean_val
                summary_row[f"{metric}_ci_low"] = ci_low
                summary_row[f"{metric}_ci_high"] = ci_high
                summary_row[f"{metric}_ci_half"] = ci_half
            summary_rows.append(summary_row)

    _write_csv(output_dir / "results" / "raw_replications.csv", raw_rows)
    _write_csv(output_dir / "results" / "summary.csv", summary_rows)

    for scenario in scenarios:
        rows = [row for row in summary_rows if row["scenario"] == scenario.name]
        rows.sort(key=lambda row: float(row["lambda"]))
        for metric in ["avg_n_system", "avg_wait_queue", "throughput", "drop_probability"]:
            _plot_metric(
                output_dir=output_dir / "plots",
                scenario_name=scenario.name,
                lambdas=[float(row["lambda"]) for row in rows],
                means=[float(row[f"{metric}_mean"]) for row in rows],
                errors=[float(row[f"{metric}_ci_half"]) for row in rows],
                metric=metric,
            )

    return raw_rows, summary_rows
