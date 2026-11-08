from app.ws_twilio_media import SILENCE_RESET_S, TranscriptTracker


def result(text, final=False):
    return {"channel": {"alternatives": [{"transcript": text}]}, "is_final": final}


def test_first_transcript_time_is_reported_once():
    t = TranscriptTracker(call_start=100.0)
    assert t.on_result(result("hello"), 101.5) == {"time_to_first_transcript_s": 1.5}
    assert t.on_result(result("hello there"), 101.8) is None


def test_final_transcript_reports_utterance_latency():
    t = TranscriptTracker(call_start=0.0)
    t.on_result(result("my order"), 1.0)
    event = t.on_result(result("my order is late", final=True), 1.6)
    assert event == {"text": "my order is late", "latency_s": 0.6}
    assert t.finals == ["my order is late"]


def test_silence_starts_a_new_utterance():
    t = TranscriptTracker(call_start=0.0)
    t.on_result(result("first"), 1.0)
    later = 1.0 + SILENCE_RESET_S + 0.5
    t.on_result(result("second"), later)
    event = t.on_result(result("second part", final=True), later + 0.4)
    assert event["latency_s"] == 0.4


def test_empty_results_are_ignored():
    t = TranscriptTracker(call_start=0.0)
    assert t.on_result(result("   "), 1.0) is None
    assert t.on_result({"type": "Metadata"}, 1.0) is None
    assert t.first_transcript_at is None
