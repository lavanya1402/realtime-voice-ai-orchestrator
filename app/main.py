from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from .routes_twilio import router
from .ws_twilio_media import media_ws_handler
from .metrics import M
from .session_store import list_sessions

app = FastAPI(title="RealtimeVoiceOrchestrator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.websocket("/media")
async def media(ws: WebSocket):
    await media_ws_handler(ws)

@app.get("/health")
def health():
    return {
        "status": "ok",
        "calls_started": M.calls_started
    }

@app.get("/sessions")
def sessions():
    return [s.__dict__ for s in list_sessions()]
