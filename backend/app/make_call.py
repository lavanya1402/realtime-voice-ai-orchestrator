# backend/app/make_call.py
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from twilio.rest import Client
from app.utils import public_base_url

router = APIRouter()


class CallRequest(BaseModel):
    to: str
    from_number: str | None = None
    voice_path: str = "/voice"


@router.post("/call")
def start_call(payload: CallRequest):

    # 🔹 Required Twilio credentials
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    api_key = os.getenv("TWILIO_API_KEY")
    api_secret = os.getenv("TWILIO_API_SECRET")

    if not account_sid or not api_key or not api_secret:
        raise HTTPException(
            status_code=500,
            detail="Twilio credentials missing in environment variables."
        )

    # 🔹 PUBLIC_BASE_URL (Render URL)
    pub = public_base_url()
    if not pub:
        raise HTTPException(
            status_code=500,
            detail="PUBLIC_BASE_URL missing."
        )

    # 🔹 From number (Twilio number)
    from_number = (
        payload.from_number
        or os.getenv("TWILIO_FROM_NUMBER", "")
    ).strip()

    if not from_number:
        raise HTTPException(
            status_code=400,
            detail="from_number missing."
        )

    # 🔹 Construct Twilio voice webhook URL
    voice_url = f"{pub.rstrip('/')}{payload.voice_path}"

    # 🔹 Initialize Twilio client
    client = Client(api_key, api_secret, account_sid)

    try:
        call = client.calls.create(
            url=voice_url,
            method="POST",
            to=payload.to.strip(),
            from_=from_number,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Twilio call failed: {str(e)}"
        )

    return {
        "ok": True,
        "call_sid": call.sid,
        "voice_url": voice_url
    }