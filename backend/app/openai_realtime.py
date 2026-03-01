# backend/app/openai_realtime.py
import os
from fastapi import APIRouter, HTTPException
from openai import OpenAI
from app.session_store import get_session, set_report

router = APIRouter()


def client():
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        return None
    return OpenAI(api_key=key)


@router.post("/sessions/{stream_sid}/analyze")
def analyze(stream_sid: str):
    s = get_session(stream_sid)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")

    transcript = s.get("transcript", [])
    if not transcript:
        raise HTTPException(status_code=400, detail="No transcript available")

    c = client()
    if not c:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY missing")

    text = "\n".join(transcript)

    prompt = f"""
Return JSON only with:
summary, key_points, action_items, sentiment, risks.

Transcript:
{text}
""".strip()

    resp = c.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )

    content = resp.choices[0].message.content
    report = {"raw": content}

    set_report(stream_sid, report)
    return report