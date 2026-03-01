# backend/app/utils.py
import os


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def public_base_url() -> str:
    """
    Returns PUBLIC_BASE_URL without trailing slash.
    Required on Render.
    Example:
      https://your-service.onrender.com
    """
    return env("PUBLIC_BASE_URL").rstrip("/")


def ws_base_url() -> str:
    """
    Convert PUBLIC_BASE_URL to WebSocket base URL.
    Example:
      https://abc.onrender.com -> wss://abc.onrender.com
    """
    base = public_base_url()
    if not base:
        return ""

    if base.startswith("https://"):
        return "wss://" + base[len("https://"):]
    if base.startswith("http://"):
        return "ws://" + base[len("http://"):]

    return base