from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
import os
import json
import time
import base64
import asyncio
import websockets

app = FastAPI()

# ====== CONFIG ======
NGROK_DOMAIN = "ea42-2401-4900-1cd7-4005-b138-273c-c2c5-854e.ngrok-free.app"

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "").strip()

def get_media_wss_url():
    return f"wss://{NGROK_DOMAIN}/media"

DEEPGRAM_WSS = (
    "wss://api.deepgram.com/v1/listen"
    "?encoding=mulaw"
    "&sample_rate=8000"
    "&channels=1"
    "&smart_format=true"
    "&interim_results=true"
    "&punctuate=true"
)

# ====== HEALTH ======
@app.get("/")
def health():
    return {"status": "ok"}

@app.get("/voice")
def voice_get():
    return Response(content="VOICE GET OK", media_type="text/plain")

@app.post("/voice")
async def voice_post(request: Request):
    print("✅ /voice POST hit from Twilio")

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say>Connecting you to the AI assistant.</Say>
  <Connect>
    <Stream url="{get_media_wss_url()}" track="inbound_track" />
  </Connect>
</Response>"""

    print("✅ Sending TwiML:\n", twiml)
    return Response(content=twiml, media_type="application/xml")

@app.get("/media")
def media_help():
    return {"message": "This is a WebSocket endpoint."}

# ====== MEDIA WEBSOCKET ======
@app.websocket("/media")
async def media(ws: WebSocket):
    await ws.accept()
    print("✅ Twilio Media Stream connected")

    if not DEEPGRAM_API_KEY:
        print("❌ Missing DEEPGRAM_API_KEY")
        await ws.close(code=1011)
        return

    dg_headers = {"Authorization": f"Token {DEEPGRAM_API_KEY}"}

    frames = 0
    start_ts = time.time()

    try:
        async with websockets.connect(DEEPGRAM_WSS, extra_headers=dg_headers) as dg_ws:
            print("✅ Deepgram WS connected")

            async def twilio_to_deepgram():
                nonlocal frames
                while True:
                    msg = await ws.receive_text()
                    data = json.loads(msg)

                    event = data.get("event")

                    if event == "media":
                        frames += 1
                        payload_b64 = data["media"]["payload"]
                        audio_bytes = base64.b64decode(payload_b64)
                        await dg_ws.send(audio_bytes)

                        if frames % 50 == 0:
                            print(f"🎧 frames={frames} elapsed={time.time()-start_ts:.1f}s")

                    elif event == "stop":
                        print("⏹️ stop from Twilio")
                        break

            async def deepgram_listener():
                while True:
                    dg_msg = await dg_ws.recv()
                    if isinstance(dg_msg, (bytes, bytearray)):
                        continue

                    dg_data = json.loads(dg_msg)
                    channel = dg_data.get("channel", {})
                    alts = channel.get("alternatives", []) or []
                    if not alts:
                        continue

                    transcript = (alts[0].get("transcript") or "").strip()
                    if not transcript:
                        continue

                    if dg_data.get("is_final"):
                        print(f"📝 FINAL: {transcript}")
                    else:
                        print(f"… {transcript}")

            await asyncio.gather(twilio_to_deepgram(), deepgram_listener())

    except WebSocketDisconnect:
        print("❌ Twilio disconnected")
    except Exception as e:
        print("❌ Error:", repr(e))
    finally:
        print("✅ session ended")