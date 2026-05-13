from dataclasses import dataclass

from numpy.random import Generator

from .message import Message


@dataclass
class Client:
    """
    Generates messages at exponentially distributed inter-arrival times.
    - lambda_rate: average arrival rate in msg/s
    - inter-arrival times are drawn from Exponential(1/lambda_rate)
      so the mean inter-arrival time = 1/lambda_rate seconds
    """
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
