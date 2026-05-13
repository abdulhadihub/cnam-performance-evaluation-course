=== Performance Evaluation - Discrete Event Simulator ===
            CNAM - USEEJ7 - Lab 2

=== Overview ===

This simulator implements four queueing scenarios:
  - M/M/1    : Single server, infinite capacity
  - M/M/1/4  : Single server, capacity 4
  - M/M/1/8  : Single server, capacity 8
  - M/M/3/8  : Three servers, capacity 8

=== Requirements ===

  - Python 3.14+
  - uv (package manager)
  - numpy, matplotlib

Install dependencies:  uv sync

=== Command-line Usage ===

Run class-level smoke tests:
  uv run python main.py test

Run a single simulation with custom parameters:
  uv run python main.py run \
      --lambda-rates 6 \
      --mu-rate 8 \
      --servers 1 \
      --capacity -1 \
      --sim-time 20000 \
      --warmup-fraction 0.1 \
      --seed 1 \
      --trace trace.csv

Parameters:
  --lambda-rates   Arrival rate(s) in msg/s (default: 6.0). Pass multiple values
                   to create multiple clients, e.g. --lambda-rates 4 6 runs two
                   clients at 4 msg/s and 6 msg/s.
  --mu-rate        Service rate per server in msg/s (default: 8.0)
  --servers        Number of servers (default: 1)
  --capacity       System capacity (-1 = infinite) (default: -1)
  --sim-time       Total simulation time in seconds (default: 5000)
  --warmup-fraction Fraction of sim-time discarded as warmup (default: 0.1)
  --seed           RNG seed (default: 1)
  --trace          Path to write trace CSV (optional)
  --replications   Number of independent replications (default: 1)

Run the full experiment set (all 4 scenarios x 4 lambda values x 100 reps):
  uv run python main.py experiments \
      --replications 100 \
      --sim-time 5000 \
      --warmup-fraction 0.1 \
      --output outputs \
      --write-traces

Experiment output:
  outputs/results/summary.csv        -- Aggregated metrics with 95% CI
  outputs/results/raw_replications.csv -- Per-replication raw data
  outputs/plots/*.png                -- 32 plots (8 metrics x 4 scenarios)
  outputs/traces/*.csv               -- Event traces (optional)

=== Simulator Architecture ===

  sim/message.py      Message dataclass (ID, source, destination, timestamp)
  sim/event.py        Event dataclass + EventType enum
  sim/scheduler.py    Min-heap priority queue for chronological events
  sim/client.py       Client generating exponential inter-arrival times
  sim/queue_model.py  FIFO queue
  sim/server.py       Server with exponential service times
  sim/gateway.py      Gateway: orchestrates queue + server pool
  sim/engine.py       Main event loop, metrics, traces, class tests
  sim/experiments.py  Batch runner, CI aggregation, plotting
  main.py             CLI entry point
