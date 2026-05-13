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
    """Describes one of the four queueing scenarios to simulate."""
    name: str
    num_servers: int
    system_capacity: int | None


def _t_critical_95(df: int) -> float:
    """
    Two-sided 95% t critical values for 1..30 df, then normal approximation.
    Used to compute confidence intervals via:
      CI = mean ± t_crit * std / sqrt(n)
    The t-table covers df=1..30; beyond that the t-distribution converges to
    the standard normal (z_0.975 ≈ 1.96).
    """
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
    """Compute sample mean and two-sided 95% CI using t-distribution.
    Returns (mean, ci_low, ci_high, half_width)."""
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


def _fmt_val(v: float) -> str:
    """Format a metric value with appropriate precision."""
    if abs(v) < 0.01:
        return f"{v:.4f}"
    elif abs(v) < 10:
        return f"{v:.3f}"
    elif abs(v) < 1000:
        return f"{v:.2f}"
    else:
        return f"{v:.1f}"


def _plot_metric(
    output_dir: Path,
    scenario_name: str,
    lambdas: list[float],
    means: list[float],
    errors: list[float],
    metric: str,
    ylabel: str = "",
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 6.5))
    ax.errorbar(
        lambdas, means, yerr=errors,
        fmt="o-", capsize=8, capthick=3, linewidth=2.5,
        markersize=10, color="#1f77b4", ecolor="#d62728",
        elinewidth=3, markerfacecolor="#1f77b4",
    )
    ax.set_xlabel("Arrival rate λ (msg/s)", fontsize=15, labelpad=10)
    ax.set_ylabel(ylabel or metric, fontsize=15, labelpad=10)
    ax.set_title(f"{scenario_name} - {ylabel or metric} (95% CI)", fontsize=16, fontweight="bold", pad=15)
    ax.grid(True, alpha=0.3)
    ax.tick_params(labelsize=14)

    # Expand y-limits so annotations stay within the frame
    y_min = min(m - e for m, e in zip(means, errors))
    y_max = max(m + e for m, e in zip(means, errors))
    y_range = y_max - y_min if y_max > y_min else 1.0
    ax.set_ylim(y_min - y_range * 0.20, y_max + y_range * 0.20)

    # Recalculate offset from expanded limits
    y_min2, y_max2 = ax.get_ylim()
    offset = (y_max2 - y_min2) * 0.04

    # Annotate each point with mean above upper CI cap and ±CI below lower cap
    for x, y, e in zip(lambdas, means, errors):
        ax.annotate(_fmt_val(y), (x, y + e + offset),
                    ha="center", va="bottom", fontsize=10,
                    fontweight="bold", color="#1f4f7a")
        ax.annotate(f"±{_fmt_val(e)}", (x, y - e - offset),
                    ha="center", va="top", fontsize=9,
                    color="#d62728", fontstyle="italic")

    fig.tight_layout()
    fig.savefig(output_dir / f"{scenario_name}-{metric}.png", dpi=150)
    plt.close(fig)


def run_experiment_set(
    *,
    lambdas: list[float] | None = None,
    mu_rate: float = 8.0,
    simulation_time: float = 5_000.0,
    warmup_fraction: float = 0.1,
    replications: int = 100,
    base_seed: int = 100,
    output_root: str = "outputs",
    write_traces: bool = False,
) -> tuple[list[dict[str, float | int | str]], list[dict[str, float | int | str]]]:
    """Run the full experiment battery: 4 scenarios x 4 arrival rates x N reps."""
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
            print(f"  [experiments] {scenario.name} λ={lambda_rate}: ", end="", flush=True)
            per_rep: list[dict[str, float | int]] = []
            for rep in range(replications):
                seed = base_seed + scenario_idx * 10_000 + int(lambda_rate * 100) + rep
                engine = Engine(
                    EngineConfig(
                        lambda_rates=[lambda_rate],
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
                metrics["avg_time_in_servers"] = metrics["avg_response_time"] - metrics["avg_wait_queue"]
                metrics["scenario"] = scenario.name
                metrics["replication"] = rep
                per_rep.append(metrics)
                raw_rows.append(metrics)

            numeric_metrics = [
                "avg_n_system",
                "avg_n_queue",
                "avg_wait_queue",
                "avg_response_time",
                "avg_time_in_servers",
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
            print(f"done ({replications} reps)", flush=True)

    _write_csv(output_dir / "results" / "raw_replications.csv", raw_rows)
    _write_csv(output_dir / "results" / "summary.csv", summary_rows)

    # All 6 required metrics × 4 scenarios = 24 plots
    # Each entry: (plot_name, csv_data_key, ylabel)
    all_metrics = [
        ("avg_n_system",       "avg_n_system",       "Average messages in the gateway"),
        ("avg_n_queue",        "avg_n_queue",        "Average messages in queue"),
        ("avg_response_time",  "avg_response_time",   "Average time in the gateway"),
        ("avg_wait_queue",     "avg_wait_queue",      "Average time in queue"),
        ("avg_time_in_servers","avg_time_in_servers", "Average time in the servers"),
        ("drop_probability",   "drop_probability",    "Drop probability"),
        ("throughput",         "throughput",          "Throughput (msg/s)"),
        ("utilization",        "utilization",         "Server utilization"),
    ]
    for scenario in scenarios:
        rows = [row for row in summary_rows if row["scenario"] == scenario.name]
        rows.sort(key=lambda row: float(row["lambda"]))
        for plot_name, data_key, ylabel in all_metrics:
            _plot_metric(
                output_dir=output_dir / "plots",
                scenario_name=scenario.name,
                lambdas=[float(row["lambda"]) for row in rows],
                means=[float(row[f"{data_key}_mean"]) for row in rows],
                errors=[float(row[f"{data_key}_ci_half"]) for row in rows],
                metric=plot_name,
                ylabel=ylabel,
            )

    return raw_rows, summary_rows
