"""speech.initial_prompt reaches faster-whisper (vocabulary hint)."""

from openjarvis.core import registry
from openjarvis.core.config import JarvisConfig
from openjarvis.speech import _discovery


def test_faster_whisper_receives_initial_prompt(monkeypatch):
    captured = {}

    class Fake:
        def __init__(self, **kw):
            captured.update(kw)

    monkeypatch.setattr(registry.SpeechRegistry, "contains", lambda key: True)
    monkeypatch.setattr(registry.SpeechRegistry, "get", lambda key: Fake)
    cfg = JarvisConfig()
    cfg.speech.initial_prompt = "email, Gmail"
    _discovery._create_backend("faster-whisper", cfg)
    assert captured["initial_prompt"] == "email, Gmail"


def test_backend_forwards_prompt_to_transcribe(monkeypatch):
    from openjarvis.speech import faster_whisper as fw

    seen = {}

    class Model:
        def transcribe(self, path, **kw):
            seen.update(kw)
            return iter([]), type("I", (), {"language": "fr", "language_probability": 1.0})()

    b = fw.FasterWhisperBackend(initial_prompt="email, Gmail")
    monkeypatch.setattr(b, "_ensure_model", lambda: Model())
    b.transcribe(b"RIFF....WAVE", language="fr")
    assert seen == {"language": "fr", "initial_prompt": "email, Gmail"}
