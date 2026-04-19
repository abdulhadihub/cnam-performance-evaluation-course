from dataclasses import dataclass

from numpy.random import Generator

from .message import Message


@dataclass
class Server:
    server_id: int
    mu_rate: float
    rng: Generator
    busy: bool = False
    current_message: Message | None = None
    service_start_time: float = 0.0
    queue_wait_time: float = 0.0

    def start_service(self, message: Message, start_time: float, queue_wait_time: float) -> float:
        self.busy = True
        self.current_message = message
        self.service_start_time = start_time
        self.queue_wait_time = queue_wait_time
        service_time = float(self.rng.exponential(1.0 / self.mu_rate))
        return start_time + service_time

    def complete_service(self) -> tuple[Message, float, float]:
        if self.current_message is None:
            raise RuntimeError("Server has no message in service")
        message = self.current_message
        start_time = self.service_start_time
        queue_wait = self.queue_wait_time
        self.busy = False
        self.current_message = None
        self.service_start_time = 0.0
        self.queue_wait_time = 0.0
        return message, start_time, queue_wait

    def print_server(self) -> str:
        msg_id = self.current_message.message_id if self.current_message else None
        return f"Server(id={self.server_id}, busy={self.busy}, message={msg_id})"
