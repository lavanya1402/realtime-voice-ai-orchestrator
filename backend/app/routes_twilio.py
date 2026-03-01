# backend/app/routes_twilio.py
from fastapi import APIRouter, Response
from twilio.twiml.voice_response import VoiceResponse, Connect
from app.utils import ws_base_url
from app.session_store import list_sessions, get_session

router = APIRouter()


@router.post("/voice")
@router.get("/voice")
def voice():
    ws_base = ws_base_url()
    vr = VoiceResponse()

    if not ws_base:
        vr.say("Public base URL is missing. Please set PUBLIC_BASE_URL.")
        return Response(str(vr), media_type="application/xml")

    stream_url = f"{ws_base}/media"

    connect = Connect()
    connect.stream(url=stream_url)
    vr.append(connect)

    return Response(str(vr), media_type="application/xml")


@router.get("/sessions")
def sessions():
    return list_sessions()


@router.get("/sessions/{stream_sid}")
def session_detail(stream_sid: str):
    s = get_session(stream_sid)
    return s or {"error": "not_found", "stream_sid": stream_sid}