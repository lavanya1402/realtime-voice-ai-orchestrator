```mermaid
flowchart LR
  A[Caller] -->|Phone call| B[Twilio Voice]
  B -->|Webhook /voice| C[FastAPI Backend (Render)]
  C -->|TwiML: <Stream>| B
  B -->|Media Streams (WSS)| D[/media WebSocket]
  D -->|mulaw 8k frames| E[Deepgram Live STT]
  E -->|Final transcripts| C
  C -->|Store session + transcript| F[(In-memory Session Store)]
  G[Streamlit UI (Cloud)] -->|Poll /sessions| C
  G -->|Poll /sessions/{id}| C
  G -->|POST /sessions/{id}/analyze| C
  C -->|Async call| H[OpenAI Chat Completions]
  H -->|JSON report| C
  C -->|report| F
  G -->|Display transcript + report| I[Dashboard]