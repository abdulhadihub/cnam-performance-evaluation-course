from collections import deque
from dataclasses import dataclass, field

from .message import Message


@dataclass
class SimQueue:
    """
    FIFO queue storing (message, arrival_time) pairs.
    - arrival_time is the time the message entered the queue
      (used at departure to compute queue_wait = departure_time - queue_arrival_time)
    - implemented with deque for O(1) push/pop
    """
    _items: deque[tuple[Message, float]] = field(default_factory=deque)

    def push(self, message: Message, arrival_time: float) -> None:
        self._items.append((message, arrival_time))

    def pop(self) -> tuple[Message, float]:
        return self._items.popleft()

    def __len__(self) -> int:
        return len(self._items)

    def is_empty(self) -> bool:
        return not self._items

    def print_queue(self) -> str:
        ids = [str(message.message_id) for message, _ in self._items]
        return "Queue[" + ", ".join(ids) + "]"
