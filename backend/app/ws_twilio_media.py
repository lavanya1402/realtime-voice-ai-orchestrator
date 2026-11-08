# backend/app/ws_twilio_media.py
"""Twilio Media Streams -> Deepgram live speech-to-text bridge.

Twilio sends the caller's audio (mu-law, 8 kHz, mono) to /media as JSON
events. Each audio frame is forwarded to Deepgram over a second WebSocket.
Final transcripts are stored in the session store together with two
latency measures: time to first transcript, and per-utterance latency.

If DEEPGRAM_API_KEY is not set, calls are still tracked, but no transcript
is produced.
"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Optional

import websockets
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .metrics import M
from .session_store import (
    append_transcript,
    end_session,
    set_last_final_latency,
    set_time_to_first_transcript,
    upsert_session,
)

log = logging.getLogger("voice.media")
router = APIRouter()

DEEPGRAM_URL = (
    "wss://api.deepgram.com/v1/listen"
    "?encoding=mulaw&sample_rate=8000&channels=1"
    "&interim_results=true&punctuate=true&smart_format=true"
)
SILENCE_RESET_S = 1.2  # a gap longer than this starts a new utterance


@dataclass
class TranscriptTracker:
    """Turns a stream of Deepgram results into final transcripts and latencies.

    Kept free of I/O so it can be unit-tested.
    """

    call_start: float
    first_transcript_at: Optional[float] = None
    utterance_start: Optional[float] = None
    last_event_at: Optional[float] = None
    finals: list = field(default_factory=list)

    def on_result(self, result: dict, now: float) -> Optional[dict]:
        """Process one Deepgram message. Returns a dict for a final transcript."""
        alts = result.get("channel", {}).get("alternatives", [])
        text = (alts[0].get("transcript") or "").strip() if alts else ""
        if not text:
            return None

        event = {}
        if self.first_transcript_at is None:
            self.first_transcript_at = now
            event["time_to_first_transcript_s"] = round(now - self.call_start, 3)

        if self.last_event_at is not None and now - self.last_event_at > SILENCE_RESET_S:
            self.utterance_start = None
        self.last_event_at = now
        if self.utterance_start is None:
            self.utterance_start = now

        if not (result.get("is_final") or result.get("speech_final")):
            return event or None

        event["text"] = text
        event["latency_s"] = round(now - self.utterance_start, 3)
        self.utterance_start = None
        self.finals.append(text)
        return event


def _deepgram_key() -> str:
    return os.getenv("DEEPGRAM_API_KEY", "").strip()


async def _connect_deepgram(key: str):
    headers = {"Authorization": f"Token {key}"}
    try:  # websockets >= 14
        return await websockets.connect(DEEPGRAM_URL, additional_headers=headers)
    except TypeError:  # websockets <= 13
        return await websockets.connect(DEEPGRAM_URL, extra_headers=headers)


@router.websocket("/media")
async def media(ws: WebSocket):
    await ws.accept()
    stream_sid: Optional[str] = None
    tracker = TranscriptTracker(call_start=time.time())
    key = _deepgram_key()
    dg = None
    listener: Optional[asyncio.Task] = None

    if not key:
        log.warning("DEEPGRAM_API_KEY not set: calls are tracked without transcripts")

    async def listen():
        async for message in dg:
            if isinstance(message, (bytes, bytearray)):
                continue
            event = tracker.on_result(json.loads(message), time.time())
            if not event or not stream_sid:
                continue
            if "time_to_first_transcript_s" in event:
                set_time_to_first_transcript(stream_sid, event["time_to_first_transcript_s"])
            if "text" in event:
                append_transcript(stream_sid, event["text"])
                set_last_final_latency(stream_sid, event["latency_s"])

    try:
        while True:
            msg = json.loads(await ws.receive_text())
            kind = msg.get("event")

            if kind == "start":
                start = msg.get("start", {})
                stream_sid = start.get("streamSid")
                upsert_session(stream_sid, start.get("callSid"))
                M.calls_started += 1
                tracker.call_start = time.time()
                if key:
                    dg = await _connect_deepgram(key)
                    listener = asyncio.create_task(listen())

            elif kind == "media" and dg is not None:
                await dg.send(base64.b64decode(msg["media"]["payload"]))

            elif kind == "stop":
                break

    except WebSocketDisconnect:
        M.ws_disconnects += 1
    except Exception:  # keep the server alive; record the failure
        log.exception("media stream failed")
    finally:
        if dg is not None:
            try:
                await dg.send(json.dumps({"type": "CloseStream"}))
                if listener:
                    await asyncio.wait_for(listener, timeout=3)
            except Exception:
                pass
            await dg.close()
        if stream_sid:
            end_session(stream_sid)
            M.calls_ended += 1
