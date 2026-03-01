# ui/dashboard.py
import os
import time
import requests
import streamlit as st
from urllib.parse import urlparse

st.set_page_config(page_title="Realtime Voice Dashboard", layout="wide")

DEFAULT_REFRESH = 1.0
DEFAULT_LOCAL = "http://localhost:8000"

def normalize_base(url: str) -> str:
    return (url or "").strip().rstrip("/")

def is_valid_http_url(url: str) -> bool:
    if not url:
        return False
    try:
        p = urlparse(url)
        return p.scheme in ("http", "https") and bool(p.netloc)
    except Exception:
        return False

def get_api_base_default() -> str:
    api_base = ""
    try:
        api_base = st.secrets["API_BASE"] if "API_BASE" in st.secrets else ""
    except Exception:
        api_base = ""

    if not api_base:
        api_base = os.getenv("API_BASE", "")

    api_base = normalize_base(api_base)
    return api_base or DEFAULT_LOCAL

@st.cache_data(ttl=2)
def safe_get_json(url: str, timeout: int = 10):
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.json()

def safe_post_json(url: str, payload: dict | None = None, timeout: int = 30):
    r = requests.post(url, json=payload or {}, timeout=timeout)
    r.raise_for_status()
    return r.json()

st.title("Realtime Voice Dashboard (Twilio + Deepgram + LLM Report)")

with st.sidebar:
    st.header("Controls")

    if "api_base" not in st.session_state:
        st.session_state["api_base"] = get_api_base_default()

    api_base = st.text_input(
        "Backend API Base:",
        value=st.session_state["api_base"],
        placeholder="https://your-backend.onrender.com",
        help="Render backend: https://xyz.onrender.com",
    )
    api_base = normalize_base(api_base)
    st.session_state["api_base"] = api_base

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Reset localhost"):
            st.session_state["api_base"] = DEFAULT_LOCAL
            st.cache_data.clear()
            st.rerun()

    with c2:
        if st.button("Use ENV/Secrets"):
            st.session_state["api_base"] = get_api_base_default()
            st.cache_data.clear()
            st.rerun()

    st.divider()

    st.subheader("📞 Call Controls")
    to_number = st.text_input("To (your phone):", value="+91XXXXXXXXXX")
    from_number = st.text_input("From (Twilio number):", value="")  # optional

    if st.button("🚀 Start Call"):
        if not is_valid_http_url(api_base):
            st.error("Backend API Base invalid")
        elif not to_number.strip():
            st.error("To number required")
        else:
            try:
                payload = {
                    "to": to_number.strip(),
                    "from_number": (from_number.strip() or None),
                    "voice_path": "/voice",
                }
                out = safe_post_json(f"{api_base}/call", payload=payload, timeout=30)
                st.success(f"Call started ✅ Call SID: {out.get('call_sid')}")
                st.json(out)
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Call failed: {e}")

    st.divider()

    auto = st.checkbox("Auto refresh (sessions + transcript)", value=True)
    refresh = st.slider("Refresh interval (seconds)", 0.5, 5.0, DEFAULT_REFRESH, 0.1)

    st.caption("Streamlit Cloud: Secrets me `API_BASE` set karo. File commit mat karna.")

col1, col2 = st.columns([2, 1])

with col2:
    st.subheader("Service Status")
    if not is_valid_http_url(api_base):
        st.warning("API_BASE missing/invalid. Sidebar me backend URL paste karo.")
    else:
        try:
            data = safe_get_json(f"{api_base}/health", timeout=10)
            st.json(data)
        except Exception as e:
            st.error(f"Backend not reachable: {e}")

with col1:
    st.subheader("Active / Recent Sessions")

    if not is_valid_http_url(api_base):
        st.info("Backend URL set karo, phir sessions dikhenge.")
    else:
        try:
            sessions = safe_get_json(f"{api_base}/sessions", timeout=10)
        except Exception as e:
            st.error(f"/sessions failed: {e}")
            sessions = []

        if not sessions:
            st.info("No sessions found yet.")
            st.caption("Call start hote hi Twilio /voice -> /media hit karega.")
        else:
            for s in sessions:
                stream_sid = s.get("stream_sid", "unknown")
                status = s.get("status", "unknown")
                finals = s.get("final_segments", 0)

                with st.expander(f"{stream_sid} | {status} | finals={finals}", expanded=False):
                    st.write(s)

                    detail = safe_get_json(f"{api_base}/sessions/{stream_sid}", timeout=10)
                    transcript = detail.get("transcript", [])
                    report = detail.get("report")

                    st.markdown("### Transcript (final)")
                    if transcript:
                        st.text("\n".join(transcript))
                    else:
                        st.caption("No final transcript yet (Deepgram key check karo).")

                    a, b = st.columns(2)
                    with a:
                        st.markdown("### Metrics")
                        st.write({
                            "time_to_first_transcript_s": detail.get("time_to_first_transcript_s"),
                            "last_final_utterance_latency_s": detail.get("last_final_utterance_latency_s"),
                        })

                    with b:
                        st.markdown("### LLM Report")
                        if report:
                            st.json(report)
                        else:
                            if st.button("Generate report", key=f"analyze-{stream_sid}"):
                                try:
                                    out = safe_post_json(f"{api_base}/sessions/{stream_sid}/analyze", timeout=45)
                                    st.success("Report generated ✅")
                                    st.json(out)
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Analyze failed: {e}")

if auto and is_valid_http_url(api_base):
    time.sleep(refresh)
    st.cache_data.clear()
    st.rerun()