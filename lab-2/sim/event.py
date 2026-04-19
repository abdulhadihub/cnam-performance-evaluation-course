from dataclasses import dataclass
from enum import Enum

from .message import Message


class EventType(str, Enum):
    SEND_MSG = "SEND_MSG"
    RECV_MSG = "RECV_MSG"
    MSG_DEPT = "MSG_DEPT"


@dataclass(slots=True)
class Event:
    event_id: int
    event_time: float
    event_type: EventType
    message: Message
    node: int
    source: int
    destination: int
    server_id: int | None = None

    def set_event_time(self, event_time: float) -> None:
        self.event_time = event_time

    def get_event_time(self) -> float:
        return self.event_time

    def set_event_type(self, event_type: EventType) -> None:
        self.event_type = event_type

    def get_event_type(self) -> EventType:
        return self.event_type

    def print_event(self) -> str:
        return (
            f"Event(id={self.event_id}, time={self.event_time:.6f}, type={self.event_type}, "
            f"msg={self.message.message_id}, node={self.node}, src={self.source}, "
            f"dst={self.destination}, server_id={self.server_id})"
        )

    # Assignment-style alias
    def Print_Event(self) -> str:
        return self.print_event()
