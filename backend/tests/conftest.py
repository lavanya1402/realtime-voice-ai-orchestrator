"""Stub web frameworks so the transcript logic can be tested without them."""
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _stub(name, **attrs):
    if name not in sys.modules:
        mod = types.ModuleType(name)
        mod.__dict__.update(attrs)
        sys.modules[name] = mod


class _Router:
    def websocket(self, *a, **k):
        return lambda fn: fn


_stub("fastapi", APIRouter=_Router, WebSocket=object, WebSocketDisconnect=type("WebSocketDisconnect", (Exception,), {}))
_stub("websockets", connect=None)
