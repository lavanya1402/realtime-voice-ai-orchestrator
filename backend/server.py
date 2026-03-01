# backend/server.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes_twilio import router as twilio_router
from app.ws_twilio_media import router as media_router
from app.make_call import router as call_router
from app.openai_realtime import router as ai_router

app = FastAPI(
    title="Realtime Voice Orchestrator",
    version="1.0.0"
)

# Allow Streamlit Cloud frontend to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Later you can restrict to your Streamlit domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include feature routers
app.include_router(twilio_router)
app.include_router(media_router)
app.include_router(call_router)
app.include_router(ai_router)


@app.get("/")
def root():
    return {
        "ok": True,
        "service": "realtime-voice-orchestrator"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}