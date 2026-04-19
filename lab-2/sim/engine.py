from __future__ import annotations

import csv
from dataclasses import dataclass
from itertools import count
from pathlib import Path

import numpy as np

from .client import Client
from .event import Event, EventType
from .gateway import Gateway
from .scheduler import Scheduler


@dataclass(slots=True)
class EngineConfig:
    lambda_rate: float
    mu_rate: float = 8.0
    num_servers: int = 1
    system_capacity: int | None = None
    simulation_time: float = 20_000.0
    warmup_fraction: float = 0.1
    propagation_delay: float = 1.0
    seed: int = 1


class Engine:
    def __init__(self, config: EngineConfig) -> None:
        self.config = config
        self.rng = np.random.default_rng(config.seed)
        self.scheduler = Scheduler()
        self.client = Client(client_id=1, lambda_rate=config.lambda_rate, destination=0, rng=self.rng)
        self.gateway = Gateway(
            gateway_id=0,
            num_servers=config.num_servers,
            mu_rate=config.mu_rate,
            rng=self.rng,
            system_capacity=config.system_capacity,
        )

        self._event_id = count(1)
        self._message_id = count(1)
        self._last_time = 0.0
        self._warmup_time = self.config.simulation_time * self.config.warmup_fraction

        self.area_n_system = 0.0
        self.area_n_queue = 0.0
        self.area_busy_servers = 0.0

        self.arrivals_after_warmup = 0
        self.departures_after_warmup = 0
        self.drops_after_warmup = 0
        self.total_queue_wait = 0.0
        self.total_response_time = 0.0

        self.trace_rows: list[dict[str, float | int | str]] = []

    def _next_event_id(self) -> int:
        return next(self._event_id)

    def _next_message_id(self) -> int:
        return next(self._message_id)

    def _accumulate_state(self, new_time: float) -> None:
        start = max(self._last_time, self._warmup_time)
        end = min(new_time, self.config.simulation_time)
        if end > start:
            dt = end - start
            self.area_n_system += self.gateway.n_system * dt
            self.area_n_queue += self.gateway.queue_count() * dt
            self.area_busy_servers += self.gateway.in_service_count() * dt
        self._last_time = new_time

    def _append_trace(self, event: Event) -> None:
        self.trace_rows.append(
            {
                "time": round(event.event_time, 6),
                "node": event.node,
                "event": event.event_type.value,
                "source": event.source,
                "destination": event.destination,
                "msgID": event.message.message_id,
            }
        )

    def _schedule_initial_send(self) -> None:
        send_time = self.client.next_interarrival()
        if send_time > self.config.simulation_time:
            return
        msg = self.client.build_message(self._next_message_id(), created_at=send_time)
        self.scheduler.add_event(
            Event(
                event_id=self._next_event_id(),
                event_time=send_time,
                event_type=EventType.SEND_MSG,
                message=msg,
                node=self.client.client_id,
                source=msg.source,
                destination=msg.destination,
            )
        )

    def _process_send(self, event: Event) -> None:
        recv_time = event.event_time + self.config.propagation_delay
        if recv_time <= self.config.simulation_time:
            self.scheduler.add_event(
                Event(
                    event_id=self._next_event_id(),
                    event_time=recv_time,
                    event_type=EventType.RECV_MSG,
                    message=event.message,
                    node=self.gateway.gateway_id,
                    source=event.source,
                    destination=event.destination,
                )
            )

        next_send_time = event.event_time + self.client.next_interarrival()
        if next_send_time <= self.config.simulation_time:
            msg = self.client.build_message(self._next_message_id(), created_at=next_send_time)
            self.scheduler.add_event(
                Event(
                    event_id=self._next_event_id(),
                    event_time=next_send_time,
                    event_type=EventType.SEND_MSG,
                    message=msg,
                    node=self.client.client_id,
                    source=msg.source,
                    destination=msg.destination,
                )
            )

    def _process_recv(self, event: Event) -> None:
        if event.event_time >= self._warmup_time:
            self.arrivals_after_warmup += 1

        followups, dropped = self.gateway.handle_receive(
            now=event.event_time,
            message=event.message,
            next_event_id=self._next_event_id,
        )
        if dropped and event.event_time >= self._warmup_time:
            self.drops_after_warmup += 1

        for next_event in followups:
            self.scheduler.add_event(next_event)

    def _process_departure(self, event: Event) -> None:
        if event.server_id is None:
            raise RuntimeError("Departure event without server id")

        followups, _, queue_wait, response_time = self.gateway.handle_departure(
            now=event.event_time,
            server_id=event.server_id,
            next_event_id=self._next_event_id,
        )
        if event.event_time >= self._warmup_time:
            self.departures_after_warmup += 1
            self.total_queue_wait += queue_wait
            self.total_response_time += response_time

        for next_event in followups:
            self.scheduler.add_event(next_event)

    def run(self, trace_path: Path | None = None) -> dict[str, float | int]:
        self._schedule_initial_send()

        while True:
            event = self.scheduler.get_event()
            if event is None:
                break
            if event.event_time > self.config.simulation_time:
                break

            self._accumulate_state(event.event_time)
            self._append_trace(event)

            if event.event_type == EventType.SEND_MSG:
                self._process_send(event)
            elif event.event_type == EventType.RECV_MSG:
                self._process_recv(event)
            elif event.event_type == EventType.MSG_DEPT:
                self._process_departure(event)
            else:
                raise RuntimeError(f"Unknown event type: {event.event_type}")

        self._accumulate_state(self.config.simulation_time)

        if trace_path is not None:
            trace_path.parent.mkdir(parents=True, exist_ok=True)
            with trace_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=["time", "node", "event", "source", "destination", "msgID"],
                )
                writer.writeheader()
                writer.writerows(self.trace_rows)

        measured_time = max(self.config.simulation_time - self._warmup_time, 1e-9)
        avg_n_system = self.area_n_system / measured_time
        avg_n_queue = self.area_n_queue / measured_time
        utilization = self.area_busy_servers / (self.config.num_servers * measured_time)
        avg_wait_queue = (
            self.total_queue_wait / self.departures_after_warmup
            if self.departures_after_warmup
            else 0.0
        )
        avg_response = (
            self.total_response_time / self.departures_after_warmup
            if self.departures_after_warmup
            else 0.0
        )
        throughput = self.departures_after_warmup / measured_time
        drop_prob = (
            self.drops_after_warmup / self.arrivals_after_warmup
            if self.arrivals_after_warmup
            else 0.0
        )

        return {
            "lambda": self.config.lambda_rate,
            "mu": self.config.mu_rate,
            "servers": self.config.num_servers,
            "capacity": -1 if self.config.system_capacity is None else self.config.system_capacity,
            "simulation_time": self.config.simulation_time,
            "warmup_time": self._warmup_time,
            "arrivals": self.arrivals_after_warmup,
            "departures": self.departures_after_warmup,
            "dropped": self.drops_after_warmup,
            "avg_n_system": avg_n_system,
            "avg_n_queue": avg_n_queue,
            "avg_wait_queue": avg_wait_queue,
            "avg_response_time": avg_response,
            "throughput": throughput,
            "utilization": utilization,
            "drop_probability": drop_prob,
        }

    @staticmethod
    def test_message() -> str:
        from .message import Message

        msg = Message(message_id=1, source=1, destination=0, created_at=0.5)
        return msg.print_message()

    @staticmethod
    def test_event() -> str:
        from .event import Event, EventType
        from .message import Message

        msg = Message(message_id=2, source=1, destination=0, created_at=1.0)
        event = Event(
            event_id=10,
            event_time=2.0,
            event_type=EventType.SEND_MSG,
            message=msg,
            node=1,
            source=1,
            destination=0,
        )
        return event.print_event()

    @staticmethod
    def test_scheduler() -> str:
        from .event import Event, EventType
        from .message import Message

        scheduler = Scheduler()
        for idx, t in enumerate([3.0, 1.0, 2.0], start=1):
            msg = Message(message_id=idx, source=1, destination=0, created_at=t)
            scheduler.add_event(
                Event(
                    event_id=idx,
                    event_time=t,
                    event_type=EventType.SEND_MSG,
                    message=msg,
                    node=1,
                    source=1,
                    destination=0,
                )
            )
        popped = [scheduler.get_event().event_time for _ in range(3)]
        if popped != [1.0, 2.0, 3.0]:
            raise AssertionError(f"Scheduler ordering failed: {popped}")
        return "Scheduler ordering OK"

    @staticmethod
    def test_client() -> str:
        rng = np.random.default_rng(7)
        client = Client(client_id=1, lambda_rate=4.0, destination=0, rng=rng)
        return client.print_client()

    @staticmethod
    def test_queue_server_gateway() -> str:
        rng = np.random.default_rng(11)
        gateway = Gateway(gateway_id=0, num_servers=1, mu_rate=8.0, rng=rng, system_capacity=4)
        return gateway.print_gateway()

    @classmethod
    def run_class_tests(cls) -> list[str]:
        return [
            cls.test_message(),
            cls.test_event(),
            cls.test_scheduler(),
            cls.test_client(),
            cls.test_queue_server_gateway(),
        ]
