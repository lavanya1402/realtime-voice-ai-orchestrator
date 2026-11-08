# Real-time Voice AI Orchestrator

**A backend and monitoring dashboard for AI on live phone calls: Twilio streams call audio, the backend tracks each call session, and an LLM turns the call transcript into a structured report.**

> **Status:** the telephony, session and dashboard pipeline is in this repository. Live speech-to-text with Deepgram is implemented in the companion repository [Twilio-Deepgram-Realtime-STT](https://github.com/lavanya1402/Twilio-Deepgram-Realtime-STT) and is being merged into this backend.

## How it works

```mermaid
flowchart LR
  A[Caller] -->|Phone call| B[Twilio Voice]
  B -->|Webhook /voice| C[FastAPI backend]
  C -->|TwiML Stream| B
  B -->|Media Streams over WebSocket| D[/media endpoint]
  D --> F[(Session store)]
  E[Deepgram live STT<br/>companion repo] -.->|transcripts| F
  G[Streamlit dashboard] -->|poll /sessions| C
  G -->|POST /sessions/id/analyze| C
  C -->|transcript| H[OpenAI]
  H -->|JSON report| F
```

1. A call reaches Twilio, which calls the `/voice` webhook. The backend replies with TwiML that opens a media stream.
2. Twilio streams the call audio to the `/media` WebSocket. The backend creates a session for each stream and counts calls and media packets.
3. The Streamlit dashboard lists sessions, shows transcripts and latency fields, and can request an analysis.
4. `/sessions/{id}/analyze` sends the call transcript to OpenAI and stores a JSON report for the dashboard.

## Project structure

```
backend/
  app/main.py              FastAPI app, /health and /sessions
  app/routes_twilio.py     /voice webhook (TwiML) and session endpoints
  app/ws_twilio_media.py   /media WebSocket for Twilio Media Streams
  app/openai_realtime.py   /sessions/{id}/analyze: LLM call report
  app/session_store.py     In-memory sessions, transcripts, latency fields
  app/metrics.py           Call and packet counters
  app/make_call.py         Start an outbound call through Twilio
  render.yaml              Render deployment (free plan)
ui/dashboard.py            Streamlit monitoring dashboard
```

## Run locally

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env        # add Twilio and OpenAI keys
uvicorn server:app --reload --port 8000

# in another terminal
streamlit run ui/dashboard.py
```

Expose port 8000 with a tunnel (for example `ngrok http 8000`) and set your Twilio number's voice webhook to `https://<your-tunnel>/voice`.

## Deploy

`backend/render.yaml` deploys the backend to Render; the health check is `/health`. Set the environment variables from `.env.example` in Render, not in the repository.

## Roadmap

- [ ] Forward media frames from `/media` to Deepgram live STT (from the companion repo)
- [ ] Record time-to-first-transcript and per-utterance latency for every call
- [ ] Persist sessions beyond memory
- [ ] Human handoff when the caller asks for a person

## Author

Built by [Lavanya Srivastava](https://github.com/lavanya1402), Lavanya AI Consultancy.
