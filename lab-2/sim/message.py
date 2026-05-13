from dataclasses import dataclass


@dataclass(slots=True)
class Message:
    """
    Represents a message traveling through the system.
    - created_at: timestamp when the message was created (used to compute
      response time = departure_time - created_at)
    - messages are created by Client, delivered to the Gateway, and
      depart when service completes
    """
    message_id: int
    source: int
    destination: int
    created_at: float

    def get_message_id(self) -> int:
        return self.message_id

    def get_source(self) -> int:
        return self.source

    def get_destination(self) -> int:
        return self.destination

    def set_destination(self, destination: int) -> None:
        self.destination = destination

    def print_message(self) -> str:
        return (
            f"Message(id={self.message_id}, source={self.source}, "
            f"destination={self.destination}, created_at={self.created_at:.6f})"
        )

    # Assignment-style alias
    def Print_Message(self) -> str:
        return self.print_message()
