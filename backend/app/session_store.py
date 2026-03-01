# backend/app/session_store.py
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import threading


@dataclass
class Session:
    stream_sid: str
    call_sid: Optional[str] = None
    status: str = "active"  # active|ended
    created_at: float = field(default_factory=lambda: time.time())
    last_seen: float = field(default_factory=lambda: time.time())

    transcript: List[str] = field(default_factory=list)
    final_segments: int = 0

    time_to_first_transcript_s: Optional[float] = None
    last_final_utterance_latency_s: Optional[float] = None

    report: Optional[Dict[str, Any]] = None

    def touch(self) -> None:
        self.last_seen = time.time()

    def to_dict(self, summary: bool = True) -> Dict[str, Any]:
        base = {
            "stream_sid": self.stream_sid,
            "call_sid": self.call_sid,
            "status": self.status,
            "created_at": self.created_at,
            "last_seen": self.last_seen,
            "final_segments": self.final_segments,
            "time_to_first_transcript_s": self.time_to_first_transcript_s,
            "last_final_utterance_latency_s": self.last_final_utterance_latency_s,
        }
        if summary:
            return base

        base.update(
            {
                "transcript": self.transcript,
                "report": self.report,
            }
        )
        return base


_lock = threading.Lock()
_sessions: Dict[str, Session] = {}


def upsert_session(stream_sid: str, call_sid: Optional[str] = None) -> Session:
    with _lock:
        s = _sessions.get(stream_sid)
        if s is None:
            s = Session(stream_sid=stream_sid, call_sid=call_sid)
            _sessions[stream_sid] = s
        else:
            if call_sid and not s.call_sid:
                s.call_sid = call_sid
            s.status = "active"
            s.touch()
        return s


def get_session(stream_sid: str) -> Optional[Session]:
    with _lock:
        return _sessions.get(stream_sid)


def list_sessions(limit: int = 50) -> List[Session]:
    with _lock:
        items = list(_sessions.values())
    items.sort(key=lambda x: x.created_at, reverse=True)
    return items[:limit]


def append_transcript(stream_sid: str, text: str) -> None:
    with _lock:
        s = _sessions.get(stream_sid)
        if not s:
            s = Session(stream_sid=stream_sid)
            _sessions[stream_sid] = s
        s.transcript.append(text)
        s.final_segments += 1
        s.touch()


def set_time_to_first_transcript(stream_sid: str, seconds: float) -> None:
    with _lock:
        s = _sessions.get(stream_sid)
        if not s:
            return
        if s.time_to_first_transcript_s is None:
            s.time_to_first_transcript_s = float(seconds)
        s.touch()


def set_last_final_latency(stream_sid: str, seconds: float) -> None:
    with _lock:
        s = _sessions.get(stream_sid)
        if not s:
            return
        s.last_final_utterance_latency_s = float(seconds)
        s.touch()


def set_report(stream_sid: str, report: Dict[str, Any]) -> None:
    with _lock:
        s = _sessions.get(stream_sid)
        if not s:
            return
        s.report = report
        s.touch()


def end_session(stream_sid: str) -> None:
    with _lock:
        s = _sessions.get(stream_sid)
        if not s:
            return
        s.status = "ended"
        s.touch()