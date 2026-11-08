# Real-time Voice AI Orchestrator

**A backend and monitoring dashboard for AI on live phone calls: Twilio streams call audio, Deepgram transcribes it in real time, and an LLM turns the transcript into a structured call report.**

Each call is tracked as a session with its transcript, time to first transcript and per-utterance latency.

## How it works

```mermaid
flowchart LR
  A[Caller] -->|Phone call| B[Twilio Voice]
  B -->|Webhook /voice| C[FastAPI backend]
  C -->|TwiML Stream| B
  B -->|Media Streams over WebSocket| D[/media endpoint]
  D -->|audio frames| E[Deepgram live STT]
  E -->|final transcripts + latency| F[(Session store)]
  G[Streamlit dashboard] -->|poll /sessions| C
  G -->|POST /sessions/id/analyze| C
  C -->|transcript| H[OpenAI]
  H -->|JSON report| F
```

1. A call reaches Twilio, which calls the `/voice` webhook. The backend replies with TwiML that opens a media stream.
2. Twilio streams the call audio to the `/media` WebSocket. The backend creates a session and forwards each audio frame to Deepgram's live API.
3. Deepgram returns transcripts while the caller speaks. Final transcripts are stored with the time to first transcript and the latency of each utterance.
4. The Streamlit dashboard lists sessions, shows transcripts and latency fields, and can request an analysis.
5. `/sessions/{id}/analyze` sends the call transcript to OpenAI and stores a JSON report for the dashboard.

## Project structure

```
backend/
  app/routes_twilio.py     /voice webhook (TwiML) and session endpoints
  app/ws_twilio_media.py   /media WebSocket: Twilio audio -> Deepgram live STT
  app/openai_realtime.py   /sessions/{id}/analyze: LLM call report
  app/session_store.py     In-memory sessions, transcripts, latency fields
  app/metrics.py           Call and packet counters
  app/make_call.py         Start an outbound call through Twilio
  server.py                FastAPI app (entry point)
  render.yaml              Render deployment (free plan)
  tests/                   Unit tests for transcript and latency logic
ui/dashboard.py            Streamlit monitoring dashboard
```

## Run locally

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env        # add Deepgram, Twilio and OpenAI keys
uvicorn server:app --reload --port 8000

# in another terminal
streamlit run ui/dashboard.py
```

Expose port 8000 with a tunnel (for example `ngrok http 8000`) and set your Twilio number's voice webhook to `https://<your-tunnel>/voice`.

## Deploy

`backend/render.yaml` deploys the backend to Render; the health check is `/health`. Set the environment variables from `.env.example` in Render, not in the repository.

## Tests

```bash
cd backend
pip install pytest
python -m pytest -q tests
```

## Roadmap

- [x] Forward call audio to Deepgram live STT
- [x] Record time to first transcript and per-utterance latency for every call
- [ ] Persist sessions beyond memory (currently in-memory)
- [ ] Human handoff when the caller asks for a person

## License

MIT, see [LICENSE](LICENSE).

## Author

Built by [Lavanya Srivastava](https://github.com/lavanya1402), Lavanya AI Consultancy.
