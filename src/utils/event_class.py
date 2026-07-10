from typing import Literal
from datetime import datetime, timedelta

class Event():
    def __init__(self):
        self.event_name: str | None = None
        self.description: str | None = None
        self.mode: Literal["99", "classic"] | None = None
        self.scoring: Literal["points", "placement"] | None = None
        self.machine_required: bool = False
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None
        self.divisions: list[Division] | None = None
        self.teams: list[Team] | None = None

    @property
    def duration(self) -> int | None:
        if self.start_time and self.end_time:
            return int(round(timedelta(self.start_time - self.end_time).total_seconds() / 3600, 0))
        else:
            return None
        
class Division():
    def __init__(self):
        self.id: int | None = None
        self.name: str | None = None
        self.alt_name: str | None = None
        self.capacity: int | None = None
        self.emote: str | None = None


class Team():
    def __init__(self):
        self.id: int | None = None
        self.name: str | None = None
        self.alt_name: str | None = None
        self.capacity: int | None = None
        self.emote: str | None = None