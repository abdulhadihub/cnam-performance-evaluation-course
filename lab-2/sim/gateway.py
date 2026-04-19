from dataclasses import dataclass, field
from typing import Callable

from .event import Event, EventType
from .message import Message
from .queue_model import SimQueue
from .server import Server


@dataclass
class Gateway:
    gateway_id: int
    num_servers: int
    mu_rate: float
    rng: object
    system_capacity: int | None = None
    queue: SimQueue = field(default_factory=SimQueue)
    servers: list[Server] = field(default_factory=list)
    n_system: int = 0
    dropped_messages: int = 0

    def __post_init__(self) -> None:
        if not self.servers:
            self.servers = [
                Server(server_id=i, mu_rate=self.mu_rate, rng=self.rng)
                for i in range(self.num_servers)
            ]

    def in_service_count(self) -> int:
        return sum(1 for server in self.servers if server.busy)

    def queue_count(self) -> int:
        return len(self.queue)

    def _find_idle_server(self) -> Server | None:
        for server in self.servers:
            if not server.busy:
                return server
        return None

    def _can_admit(self) -> bool:
        if self.system_capacity is None:
            return True
        return self.n_system < self.system_capacity

    def _schedule_departure(
        self,
        *,
        now: float,
        message: Message,
        queue_arrival_time: float,
        server: Server,
        next_event_id: Callable[[], int],
    ) -> Event:
        queue_wait = now - queue_arrival_time
        completion_time = server.start_service(message, now, queue_wait)
        return Event(
            event_id=next_event_id(),
            event_time=completion_time,
            event_type=EventType.MSG_DEPT,
            message=message,
            node=self.gateway_id,
            source=message.source,
            destination=message.destination,
            server_id=server.server_id,
        )

    def handle_receive(
        self,
        *,
        now: float,
        message: Message,
        next_event_id: Callable[[], int],
    ) -> tuple[list[Event], bool]:
        if not self._can_admit():
            self.dropped_messages += 1
            return [], True

        self.n_system += 1
        idle_server = self._find_idle_server()
        if idle_server is not None:
            dept = self._schedule_departure(
                now=now,
                message=message,
                queue_arrival_time=now,
                server=idle_server,
                next_event_id=next_event_id,
            )
            return [dept], False

        self.queue.push(message, now)
        return [], False

    def handle_departure(
        self,
        *,
        now: float,
        server_id: int,
        next_event_id: Callable[[], int],
    ) -> tuple[list[Event], Message, float, float]:
        server = self.servers[server_id]
        message, _, queue_wait = server.complete_service()
        self.n_system -= 1
        response_time = now - message.created_at

        follow_up_events: list[Event] = []
        if not self.queue.is_empty():
            next_message, queue_arrival_time = self.queue.pop()
            next_departure = self._schedule_departure(
                now=now,
                message=next_message,
                queue_arrival_time=queue_arrival_time,
                server=server,
                next_event_id=next_event_id,
            )
            follow_up_events.append(next_departure)

        return follow_up_events, message, queue_wait, response_time

    def print_gateway(self) -> str:
        return (
            f"Gateway(id={self.gateway_id}, servers={self.num_servers}, "
            f"in_system={self.n_system}, in_queue={self.queue_count()}, dropped={self.dropped_messages})"
        )
