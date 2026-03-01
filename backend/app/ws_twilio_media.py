# backend/app/ws_twilio_media.py
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .session_store import upsert_session
from .metrics import M

router = APIRouter()

@router.websocket("/media")
async def media(ws: WebSocket):
    await ws.accept()
    stream_sid = None

    try:
        while True:
            msg = json.loads(await ws.receive_text())
            event = msg.get("event")

            if event == "start":
                stream_sid = msg["start"]["streamSid"]
                upsert_session(stream_sid)
                M.calls_started += 1

            elif event == "media":
                if stream_sid:
                    M.media_packets += 1

            elif event == "stop":
                if stream_sid:
                    M.calls_ended += 1

    except WebSocketDisconnect:
        pass
    except Exception:
        # keep server alive in demo
        pass