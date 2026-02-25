import json
from fastapi import WebSocket
from .config import OPENAI_API_KEY
from .openai_realtime import OpenAIRealtime
from .session_store import upsert_session
from .metrics import M

async def media_ws_handler(ws: WebSocket):
    await ws.accept()
    rt = OpenAIRealtime(OPENAI_API_KEY)
    await rt.connect()

    stream_sid = None

    while True:
        msg = json.loads(await ws.receive_text())

        if msg["event"] == "start":
            stream_sid = msg["start"]["streamSid"]
            upsert_session(stream_sid)
            M.calls_started += 1

        if msg["event"] == "media":
            payload = msg["media"]["payload"]
            await rt.append_audio(payload)

        async for event in rt.events():
            if event.get("type") == "response.output_audio.delta":
                await ws.send_text(json.dumps({
                    "event": "media",
                    "streamSid": stream_sid,
                    "media": {"payload": event["delta"]}
                }))
