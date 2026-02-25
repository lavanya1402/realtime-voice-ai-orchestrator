from fastapi import APIRouter
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse, Connect
from .config import PUBLIC_BASE_URL

router = APIRouter()

@router.post("/voice")
async def voice():
    vr = VoiceResponse()
    connect = Connect()
    ws_url = PUBLIC_BASE_URL.replace("https://", "wss://") + "/media"
    connect.stream(url=ws_url)
    vr.append(connect)
    vr.say("Hello. You are connected to AI assistant.")
    return Response(str(vr), media_type="application/xml")
