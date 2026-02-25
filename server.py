import os
import json
import time
import base64
import asyncio

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response, PlainTextResponse
import websockets

app = FastAPI()

# =========================
# CONFIG
# =========================
NGROK_DOMAIN = os.getenv("NGROK_DOMAIN", "").strip()
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "").strip()


def get_media_wss_url() -> str:
    # Twilio expects wss://<ngrok-domain>/media
    return f"wss://{NGROK_DOMAIN}/media"


# Deepgram Live Streaming STT (Twilio = mulaw 8kHz, mono)
# ✅ Keyword boosts help proper nouns in phone audio
DEEPGRAM_WSS = (
    "wss://api.deepgram.com/v1/listen"
    "?encoding=mulaw"
    "&sample_rate=8000"
    "&channels=1"
    "&interim_results=true"
    "&punctuate=true"
    "&smart_format=true"
    "&keywords=Lavanya:3.0"
    "&keywords=Deepgram:2.5"
    "&keywords=Twilio:2.5"
)

# =========================
# HEALTH
# =========================
@app.get("/")
def health():
    return {"status": "ok", "service": "Twilio-Deepgram-Realtime-STT"}


# =========================
# TWILIO VOICE WEBHOOK
# =========================
@app.api_route("/voice", methods=["GET", "POST"])
async def voice(request: Request):
    if request.method == "GET":
        return PlainTextResponse("VOICE GET OK")

    print("✅ /voice POST received from Twilio")
    print("🔗 Streaming to:", get_media_wss_url())

    # ✅ Stable TwiML: short pause + stream
    # (track removed to avoid any track-related quirks)
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say>Connecting you to the AI assistant.</Say>
  <Pause length="1"/>
  <Connect>
    <Stream url="{get_media_wss_url()}" />
  </Connect>
</Response>"""

    return Response(content=twiml, media_type="application/xml")


# =========================
# MEDIA WEBSOCKET
# =========================
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
    stop_event = asyncio.Event()
    last_logged = 0
    call_sid = None
    stream_sid = None

    # ✅ Utterance-based latency tracking (with silence reset)
    utterance_start_ts = None
    last_transcript_ts = None
    SILENCE_RESET_S = 1.2  # reset utterance if transcript gap > 1.2s

    # ✅ Strong recruiter metric: Time-to-first-transcript (per call)
    first_transcript_ts = None

    try:
        async with websockets.connect(DEEPGRAM_WSS, extra_headers=dg_headers) as dg_ws:
            print("✅ Deepgram WS connected")

            async def twilio_to_deepgram():
                nonlocal frames, last_logged, call_sid, stream_sid

                while True:
                    msg_text = await ws.receive_text()
                    data = json.loads(msg_text)
                    event = data.get("event")

                    if event == "start":
                        start = data.get("start", {})
                        call_sid = start.get("callSid")
                        stream_sid = start.get("streamSid")
                        print(f"▶️ start callSid={call_sid} streamSid={stream_sid}")

                    elif event == "media":
                        frames += 1
                        payload_b64 = data["media"]["payload"]
                        audio_bytes = base64.b64decode(payload_b64)
                        await dg_ws.send(audio_bytes)

                        if frames % 50 == 0 and frames != last_logged:
                            last_logged = frames
                            print(f"🎧 frames={frames} elapsed={time.time()-start_ts:.1f}s")

                    elif event == "stop":
                        print("⏹️ stop from Twilio")
                        stop_event.set()

                        # Flush Deepgram
                        try:
                            await dg_ws.send(json.dumps({"type": "CloseStream"}))
                        except Exception:
                            pass

                        try:
                            await dg_ws.close()
                        except Exception:
                            pass

                        break

            async def deepgram_listener():
                nonlocal utterance_start_ts, last_transcript_ts, first_transcript_ts

                while not stop_event.is_set():
                    try:
                        dg_msg = await dg_ws.recv()
                    except Exception:
                        break

                    if not dg_msg or isinstance(dg_msg, (bytes, bytearray)):
                        continue

                    dg_data = json.loads(dg_msg)
                    alts = dg_data.get("channel", {}).get("alternatives", [])
                    if not alts:
                        continue

                    transcript = (alts[0].get("transcript") or "").strip()
                    if not transcript:
                        continue

                    now = time.time()

                    # ✅ Time-to-first-transcript (prints once per call)
                    if first_transcript_ts is None:
                        first_transcript_ts = now
                        print(f"⚡ Time-to-first-transcript: {first_transcript_ts - start_ts:.2f}s")

                    # ✅ Reset utterance if long silence gap between transcript events
                    if last_transcript_ts and (now - last_transcript_ts) > SILENCE_RESET_S:
                        utterance_start_ts = None

                    last_transcript_ts = now

                    # ✅ Start new utterance timing at first transcript event
                    if utterance_start_ts is None:
                        utterance_start_ts = now

                    is_final = bool(dg_data.get("is_final")) or bool(dg_data.get("speech_final"))

                    if is_final:
                        lat = now - utterance_start_ts
                        lat_s = f"{lat:.2f}s" if lat >= 0.05 else "<0.05s"
                        print(f"📝 FINAL: {transcript}")
                        print(f"🧠 Transcript latency: {lat_s}")
                        utterance_start_ts = None  # reset for next utterance
                    else:
                        print(f"… {transcript}")

            await asyncio.gather(twilio_to_deepgram(), deepgram_listener())

    except WebSocketDisconnect:
        print("❌ Twilio disconnected")
    except Exception as e:
        print("❌ Error:", repr(e))
    finally:
        stop_event.set()
        try:
            await ws.close()
        except Exception:
            pass
        print("✅ session ended")