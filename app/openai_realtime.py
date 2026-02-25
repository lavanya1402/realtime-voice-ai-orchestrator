import websockets
import json

class OpenAIRealtime:

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.ws = None

    async def connect(self):
        url = "wss://api.openai.com/v1/realtime?model=gpt-realtime"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "OpenAI-Beta": "realtime=v1"
        }
        self.ws = await websockets.connect(url, extra_headers=headers)

    async def append_audio(self, audio_b64: str):
        await self.ws.send(json.dumps({
            "type": "input_audio_buffer.append",
            "audio": audio_b64
        }))

    async def events(self):
        while True:
            yield json.loads(await self.ws.recv())
