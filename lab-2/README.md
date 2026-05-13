# Lab 2 - Discrete Event Simulator

This project implements a discrete-event simulator for the scenarios:

- `M/M/1`
- `M/M/1/4`
- `M/M/1/8`
- `M/M/3/8`

Implementation choices:

- Capacity `K` means total system capacity (in service + queue), i.e. `M/M/1/K` semantics.
- 95% confidence intervals are computed from independent replications.
- Exponential inter-arrival and service-time generators use `numpy` RNG.

## Project Structure

- `main.py`: CLI entry point
- `sim/message.py`: Message class
- `sim/event.py`: Event and EventType
- `sim/scheduler.py`: event scheduler
- `sim/client.py`: client arrivals
- `sim/queue_model.py`: FIFO queue
- `sim/server.py`: server process
- `sim/gateway.py`: queue+server orchestration
- `sim/engine.py`: simulator engine, trace, metrics, class tests
- `sim/experiments.py`: batch experiments, CSV outputs, plots with CI

## Install

```bash
uv sync
```

## Run

Run class smoke tests:

```bash
uv run python main.py test
```

Run one simulation:

```bash
uv run python main.py run --lambda-rates 6 --mu-rate 8 --servers 1 --capacity -1 --sim-time 5000 --warmup-fraction 0.1 --seed 1 --trace outputs/traces/single.csv
```

Run full experiment set with plots:

```bash
uv run python main.py experiments --replications 100 --sim-time 5000 --warmup-fraction 0.1 --output outputs --write-traces
```

## Output Files

- `outputs/results/raw_replications.csv`
- `outputs/results/summary.csv`
- `outputs/plots/*.png`
- `outputs/traces/*.csv` (optional)
