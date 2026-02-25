from dataclasses import dataclass, field
from typing import Dict, Optional
import time

@dataclass
class CallSession:
    stream_sid: str
    created_at: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    status: str = "active"

_sessions: Dict[str, CallSession] = {}

def upsert_session(stream_sid: str):
    s = _sessions.get(stream_sid)
    if not s:
        s = CallSession(stream_sid=stream_sid)
        _sessions[stream_sid] = s
    s.last_seen = time.time()
    return s

def list_sessions():
    return list(_sessions.values())
