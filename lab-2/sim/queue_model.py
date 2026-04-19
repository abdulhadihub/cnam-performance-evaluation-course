from collections import deque
from dataclasses import dataclass, field

from .message import Message


@dataclass
class SimQueue:
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
