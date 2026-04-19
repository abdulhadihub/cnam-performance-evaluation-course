import heapq
from dataclasses import dataclass, field
from itertools import count

from .event import Event


@dataclass
class Scheduler:
    _events: list[tuple[float, int, Event]] = field(default_factory=list)
    _seq: object = field(default_factory=count)
    _current_time: float = 0.0

    def add_event(self, event: Event) -> None:
        heapq.heappush(self._events, (event.event_time, next(self._seq), event))

    def get_event(self) -> Event | None:
        if not self._events:
            return None
        event_time, _, event = heapq.heappop(self._events)
        self._current_time = event_time
        return event

    def get_current_time(self) -> float:
        return self._current_time

    def __len__(self) -> int:
        return len(self._events)

    def print_scheduler(self) -> str:
        ordered = sorted(self._events, key=lambda item: (item[0], item[1]))
        payload = [f"(t={time:.6f}, id={event.event_id}, type={event.event_type})" for time, _, event in ordered]
        return "Scheduler[" + ", ".join(payload) + "]"

    # Assignment-style aliases
    def AddEvent(self, event: Event) -> None:
        self.add_event(event)

    def GetEvent(self) -> Event | None:
        return self.get_event()

    def GetCurrentTime(self) -> float:
        return self.get_current_time()
