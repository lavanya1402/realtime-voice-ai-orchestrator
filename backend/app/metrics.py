import time
from dataclasses import dataclass, field

@dataclass
class Metrics:
    calls_started: int = 0
    calls_ended: int = 0
    ws_disconnects: int = 0
    openai_errors: int = 0
    started_at: float = field(default_factory=time.time)

M = Metrics()
