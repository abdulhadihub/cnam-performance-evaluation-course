from dataclasses import dataclass

from numpy.random import Generator

from .message import Message


@dataclass
class Client:
    client_id: int
    lambda_rate: float
    destination: int
    rng: Generator

    def next_interarrival(self) -> float:
        return float(self.rng.exponential(1.0 / self.lambda_rate))

    def build_message(self, message_id: int, created_at: float) -> Message:
        return Message(
            message_id=message_id,
            source=self.client_id,
            destination=self.destination,
            created_at=created_at,
        )

    def print_client(self) -> str:
        return f"Client(id={self.client_id}, lambda={self.lambda_rate}, destination={self.destination})"
