# Lab 2: Discrete-Event Simulator for Queueing Systems

### The big picture

You were asked to build a **discrete-event simulator** for queueing systems. Specifically, you had to implement and analyze **four queueing models** from queueing theory:

| Model | Meaning | Servers | Capacity (max entities in system) |
|-------|---------|---------|-----------------------------------|
| M/M/1 | Single server, infinite queue | 1 | ∞ |
| M/M/1/4 | Single server, limited to 4 | 1 | 4 |
| M/M/1/8 | Single server, limited to 8 | 1 | 8 |
| M/M/3/8 | Three servers, limited to 8 | 3 | 8 |

In Kendall's notation, **M/M/c/K** means:
- **M** (first): Markovian (exponential) inter-arrival times — arrivals are random
- **M** (second): Markovian (exponential) service times — service duration is random
- **c**: number of parallel servers
- **K**: maximum number of entities allowed in the system (queue + in service). If omitted, K = ∞.

### The simulation scenario

Imagine an **IoT gateway** system:
- A **client** (mobile device) sends messages to a gateway
- The **gateway** has a queue and one or more servers
- Messages arrive randomly (exponential inter-arrival times with mean 1/λ)
- Each server processes messages with random service times (exponential with mean 1/μ)
- Service rate μ is fixed at **8 messages/second** for all scenarios
- Arrival rates λ tested: **4, 6, 8, 12** messages/second
- It takes **1 second** for a message to propagate from client to gateway

### Required deliverables

1. **Object-oriented simulator** with these classes:
   - `Message` — what's being sent
   - `Event` — something that happens at a specific time
   - `Scheduler` — maintains events in chronological order
   - `Client` — generates arrivals
   - `Queue` — FIFO waiting line
   - `Server` — processes messages
   - `Gateway` — orchestrates queue + servers
   - `Engine` — main simulation loop

2. **Class tests** — a test method for each class that prints its state

3. **Trace generation** — CSV output showing every event (time, node, event type, source, destination, message ID)

4. **Performance metrics** for each configuration:
   - Average number of messages in system (`avg_n_system`)
   - Average number of messages in queue (`avg_n_queue`)
   - Average queue waiting time (`avg_wait_queue`)
   - Average response time (total time in system) (`avg_response_time`)
   - Throughput (completed messages/second)
   - Server utilization (fraction of time servers are busy)
   - Drop probability (for capacity-limited systems)

5. **Confidence intervals** — all metrics reported with 95% confidence intervals from 30 independent replications

6. **Plots** — error-bar plots showing each metric vs. arrival rate λ

### What "capacity K" means

Capacity K = **total entities allowed in the entire system** (in-service + in-queue). If the system is full when a new message arrives, that message is **dropped** (lost forever). This is the standard M/M/c/K convention.

For M/M/1 (no capacity limit), messages are never dropped, but the queue can grow infinitely.

---

## 2. Queueing Theory — The Concepts You Need to Know

### What is a queueing model?

A queueing model describes a system where:
- **Customers** (messages, in our case) arrive over time
- They wait in a **queue** if all **servers** are busy
- They receive **service** and then leave

Queueing theory answers questions like: "How long will customers wait?", "How many servers do I need?", "What happens when the system gets overloaded?"

### Key parameters

- **λ (lambda)** — arrival rate (messages per second)
- **μ (mu)** — service rate per server (messages per second)
- **c** — number of servers
- **ρ (rho) = λ / (c × μ)** — utilization / traffic intensity

### Stability condition

A queueing system is **stable** only if λ < c × μ. Otherwise, the queue grows without bound over time.

| Scenario | Max stable λ |
|----------|-------------|
| M/M/1 (1 server × 8) | λ < 8 |
| M/M/1/4 (1 server × 8) | Always stable (buffer limits queue) |
| M/M/1/8 (1 server × 8) | Always stable (buffer limits queue) |
| M/M/3/8 (3 servers × 8 = 24) | λ < 24 |

### Exponential distribution — why it matters

Exponential distribution has a special property called **memorylessness**: the probability of an event occurring in the next second is the same regardless of how long you've already waited. This makes the math tractable and is why M/M/c models can be analyzed theoretically.

### What "discrete-event simulation" means

Instead of simulating every millisecond (continuous time), we jump from event to event. The simulator:
1. Looks at the next scheduled event (earliest by time)
2. Advances the clock to that event's time
3. Processes the event (which may schedule new events)
4. Repeats until the simulation end time

This is far more efficient than time-stepping.

---

## 3. How Your Code Works

### Project structure

```
lab-2/
├── main.py              # CLI entry point (test, run, experiments)
├── pyproject.toml       # Python dependencies (numpy, matplotlib)
├── .python-version      # Python 3.14
└── sim/
    ├── __init__.py      # Exports Engine, EngineConfig, run_experiment_set
    ├── message.py       # Message dataclass
    ├── event.py         # Event dataclass + EventType enum
    ├── scheduler.py     # Min-heap event scheduler
    ├── client.py        # Generates exponential arrivals
    ├── queue_model.py   # FIFO queue (deque-based)
    ├── server.py        # Single server (busy/idle, exp service times)
    ├── gateway.py       # Orchestrates queue + multiple servers
    ├── engine.py        # Main simulation loop + metrics + tests
    └── experiments.py   # Batch runner + CI computation + plotting
```

### Component walkthrough

**Message** (`message.py`)
- Just a data container: message_id, source, destination, created_at
- Created when a client sends a message

**Event** (`event.py`)
- Represents something happening at a specific time
- Three event types (EventType enum):
  - `SEND_MSG` — Client sends a message
  - `RECV_MSG` — Gateway receives a message (after 1-second propagation delay)
  - `MSG_DEPT` — Service completes and message departs

**Scheduler** (`scheduler.py`)
- Stores events in a **min-heap** (priority queue) ordered by event time
- `add_event(event)` — inserts in O(log n) using heapq
- `get_event()` — pops the earliest event, returns None if empty
- This is the key data structure — it ensures events are processed in correct chronological order

**Client** (`client.py`)
- One client (client_id=1) generates all arrivals
- `next_interarrival()` — returns an exponential random value with mean 1/λ
- This means: if λ=6, the average time between messages is 1/6 ≈ 0.167 seconds

**Queue** (`sim/queue_model.py`)
- Standard FIFO queue using Python's `deque`
- Stores (message, arrival_time) tuples
- `push()`, `pop()`, `is_empty()`

**Server** (`server.py`)
- Has `busy`, `current_message`, `service_start_time` state
- `start_service(message, start_time, queue_wait_time)` — marks server busy, generates exponential service time with mean 1/μ, returns completion time
- `complete_service()` — marks server idle, returns the completed message + timing info

**Gateway** (`gateway.py`)
- Owns the queue and a list of servers
- `handle_receive()` — called on RECV_MSG:
  1. If system is full (capacity reached), drop the message, increment dropped counter
  2. If a server is idle, start service immediately
  3. Otherwise, push to queue
- `handle_departure()` — called on MSG_DEPT:
  1. Complete service on the specified server
  2. If queue is not empty, dequeue next message and start service on the freed server
  3. Return queue_wait and response_time for metrics

**Engine** (`engine.py`)
- The main simulator loop
- **Initialization**: Creates client, gateway, scheduler. Sets up metrics accumulators.
- **Event types**:
  - `SEND_MSG` → schedule RECV_MSG after 1-second propagation delay, schedule next SEND_MSG
  - `RECV_MSG` → gateway.handle_receive(), may schedule immediate MSG_DEPT
  - `MSG_DEPT` → gateway.handle_departure(), may schedule next MSG_DEPT from queue
- **Warmup**: First 10% of simulation time is excluded from metrics to let the system reach steady state
- **Metrics**: Time-weighted averages (area under curve / time) for occupancy metrics; count-based averages for wait/response times
- **Trace**: Every event is recorded in `self.trace_rows` and optionally written to CSV

**Experiments** (`experiments.py`)
- Defines 4 scenarios × 4 lambda values = 16 configurations
- Runs 30 replications per configuration = **480 total simulation runs**
- Each replication uses a different seed: `base_seed + scenario_idx × 10000 + λ × 100 + rep`
- Computes 95% confidence intervals using t-distribution table (for df=29, t=2.045)
- Generates summary CSV and error-bar plots for 4 key metrics:
  - avg_n_system, avg_wait_queue, throughput, drop_probability

### CLI usage

```bash
# Install dependencies
uv sync

# Run class tests (validates all components)
uv run python main.py test

# Run a single simulation
uv run python main.py run --lambda-rate 6 --mu-rate 8 --servers 1 --capacity -1 --sim-time 20000

# Run all experiments (16 configs × 30 reps = 480 runs)
uv run python main.py experiments --replications 30 --output outputs --write-traces
```

### Simulation parameters

| Parameter | Value | Meaning |
|-----------|-------|---------|
| Simulation time | 20,000 seconds | Total simulated time per run |
| Warmup | 10% (2,000s) | Excluded from metrics |
| Propagation delay | 1 second | Time between SEND and RECV |
| Replications | 30 per config | For confidence intervals |
| μ (service rate) | 8 msg/s | Same for all scenarios |

---

## 4. Verification — Is Your Code Correct?

### What the code does right

1. **Event processing is correct**: SEND → RECV (after 1s delay) → immediate DEPT if server idle, or queue → DEPT when server frees. This matches the assignment's event model exactly.

2. **Capacity semantics are correct**: `system_capacity` checks total entities (in-service + in-queue). Messages are dropped when `n_system >= capacity`. This is the standard M/M/c/K convention.

3. **Metrics computation is sound**:
   - Time-weighted averages use area-under-curve integration (the standard way)
   - Warmup period is properly excluded from all metrics
   - Queue wait = time from arrival to service start
   - Response time = time from arrival to departure

4. **Statistical methodology is correct**:
   - 95% CI uses t-distribution with n-1 degrees of freedom
   - Independent seeds per replication ensure valid statistics
   - 30 replications is standard practice

5. **Scheduler ordering**: Uses heapq with a tie-breaking sequence counter, ensuring correct chronological order even with events at the same time.

6. **Class tests exist** and validate each component individually.

### Potential concerns to be aware of

1. **M/M/1 with λ=8 and λ=12**: These are unstable (ρ ≥ 1). The queue grows without bound. The simulation results for these cases reflect transient behavior over 20,000 seconds, not steady state. The report acknowledges this — it's expected. For λ=12, the average system occupancy after 20,000 seconds is ~44,000 entities, which clearly shows instability.

2. **Single client model**: The code uses one client that schedules the next arrival when the current one is sent. This is correct for a Poisson process (memoryless property of exponential means the time until next arrival is independent of when we schedule it).

3. **Prof. Pedro's expected class structure**: The task.md described specific method names like `Print_Message()`, `Test_Message()`, etc. Your code uses more Pythonic names (`print_message()`, `test_message()`) but also provides the assignment-style aliases (e.g., `Print_Event()` calls `print_event()`). This hybrid approach should be acceptable.

---

## 5. What the Results Show

Your simulation produced 16 plots (4 scenarios × 4 metrics). Here's what each scenario tells us:

### M/M/1 (infinite capacity, 1 server)

- **λ=4 (ρ=0.5)**: System is lightly loaded. ~1 entity in system, minimal waiting (~0.12s). Throughput ≈ 4 msg/s (matches arrival rate).
- **λ=6 (ρ=0.75)**: Moderate load. ~3 entities in system, noticeable waiting (~0.37s). Throughput ≈ 6 msg/s.
- **λ=8 (ρ=1.0)**: **Critical.** System is at saturation. Queue grows very large over time. Results show ~347 entities in system on average, with ~43s wait time. This is the system being overwhelmed.
- **λ=12 (ρ=1.5)**: **Unstable.** Queue explodes. ~44,006 entities in system. Wait time ~3,668s (over an hour!). The system cannot keep up — arrivals come faster than the server can process them.
- **Drop probability**: Always 0 (no capacity limit, so nothing is dropped).
- **Throughput**: Maxes out at ~8 msg/s (the service rate) regardless of how high λ goes. This demonstrates the fundamental limit of a single server.

### M/M/1/4 (capacity 4, 1 server)

- **λ=4, 6**: System behaves similarly to M/M/1 since capacity (4) is rarely full.
- **λ=8, 12**: Drop probability becomes significant (~0.47 at λ=12). This caps the system occupancy at 4 and limits throughput. Half of arriving messages are rejected at λ=12.
- **Key insight**: Capacity limits protect the system from unbounded queues but cause message loss.

### M/M/1/8 (capacity 8, 1 server)

- Similar pattern to M/M/1/4 but with lower drop probability at each λ (because there's more buffer space).
- **Trade-off**: Larger buffer → lower loss but potentially longer wait times for messages that enter.

### M/M/3/8 (3 servers, capacity 8)

- **Best performer by far.** Three servers can handle up to 24 msg/s aggregate.
- Even at λ=12, the system is stable (ρ = 12/(3×8) = 0.5).
- Queue waits are minimal, system occupancy stays low.
- Drop probability is near zero for all tested λ values.
- **Key insight**: Parallelism dramatically improves performance. Adding servers is more effective than adding buffer space.

### Confidence interval behavior

- Narrow CIs at low load (system is stable and predictable)
- Wider CIs at high load (system is more variable/chaotic)
- This is expected — high-load systems have larger variance

---

## 6. How to Talk About This in Your Presentation

### Key talking points

1. **What you built**: A discrete-event simulator using object-oriented design that models M/M/c/K queueing systems. It processes events chronologically and computes standard queueing metrics.

2. **Architecture highlights**:
   - Min-heap scheduler for O(log n) event insertion
   - Clean separation of concerns (each component is its own class)
   - Deterministic seeding for reproducibility
   - 95% confidence intervals from 30 independent replications

3. **Key findings**:
   - Systems become unstable when arrival rate exceeds service capacity
   - Capacity limits prevent queue explosion at the cost of message loss
   - Multi-server systems dramatically outperform single-server systems
   - There's a fundamental trade-off: larger buffers → lower loss but longer waits

4. **If asked about theory**:
   - Know that ρ = λ/(c×μ) must be < 1 for stability (in infinite-capacity systems)
   - Know that exponential distribution is "memoryless"
   - Know that M/M/c models can be solved analytically, but simulation lets us study transient behavior and finite-capacity variants

5. **If asked about the code**:
   - The engine runs a simple event loop: pop event → accumulate state → process event → repeat
   - Time-weighted metrics use area-under-curve integration
   - Each replication uses a deterministic seed for reproducibility

### Possible questions and answers

**Q: Why does M/M/1 with λ=12 have 44,000 messages in the system?**
A: Because λ > μ (12 > 8), the system is unstable. The queue grows roughly linearly over time at rate (λ - μ) = 4 messages/second. Over 18,000 seconds of measured time (after warmup), the average queue length reflects this constant growth. In reality, you'd need admission control or more servers.

**Q: Why use discrete-event simulation instead of analytical formulas?**
A: Analytical formulas exist for steady-state M/M/c/K models, but simulation lets us study transient behavior, verify analytical results, and extend to more complex scenarios (non-exponential distributions, priority queues, etc.) that can't be solved analytically.

**Q: What does the 1-second propagation delay represent?**
A: It models network latency — the time it takes for a message to travel from the client to the gateway. In real IoT systems, this could be transmission time over a wireless network.

**Q: How do you know the simulation is correct?**
A: We have class-level tests for each component. We also verify that measured utilization matches theoretical values (e.g., at λ=6, μ=8, measured utilization ≈ 0.75, matching ρ = λ/μ = 6/8 = 0.75). Trace files can be inspected to verify event ordering.

---

## 7. Key Terminology Cheat Sheet

| Term | Meaning |
|------|---------|
| λ (lambda) | Arrival rate (messages per second) |
| μ (mu) | Service rate per server (messages per second) |
| ρ (rho) | Utilization = λ/(c×μ). Must be < 1 for stability |
| M/M/c/K | Kendall notation for queueing models |
| Inter-arrival time | Time between consecutive arrivals |
| Service time | Time to process one message |
| Warmup period | Initial simulation time excluded from metrics |
| Replication | One complete simulation run |
| CI (Confidence Interval) | Range that contains the true mean with specified probability |
| Throughput | Rate of completed messages (departures / time) |
| Drop probability | Fraction of arrivals that are rejected due to full system |

---

## 8. Commands to Re-run Everything

```bash
cd lab-2

# Install dependencies
uv sync

# Run tests to verify everything works
uv run python main.py test

# Run all experiments (this will take several minutes for 480 runs)
uv run python main.py experiments --replications 30 --output outputs --write-traces

# Run a quick single simulation
uv run python main.py run --lambda-rate 6 --mu-rate 8 --servers 1 --sim-time 20000
```
