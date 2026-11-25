"""macOS `say` TTS backend — exercised with a fake `say` executable."""

import io
import os
import stat
import sys
import wave

import pytest

from openjarvis.speech.macos_say import MacOSSayBackend

FAKE_SAY = r'''#!/usr/bin/env python3
import sys, wave, json
args = sys.argv[1:]
if args[:2] == ["-v", "?"]:
    print("Thomas              fr_FR    # Bonjour, je m'appelle Thomas.")
    print("Amélie              fr_CA    # Bonjour, je m'appelle Amélie.")
    sys.exit(0)
out = args[args.index("-o") + 1]
text = sys.stdin.read()
with wave.open(out, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(22050)
    w.writeframes(b"\x00\x00" * 100)
open(out + ".args", "w").write(json.dumps({"args": args, "text": text}))
'''


@pytest.fixture
def fake_say(tmp_path):
    p = tmp_path / "say"
    p.write_text(FAKE_SAY)
    p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return str(p)


def test_synthesize_returns_playable_wav(fake_say):
    result = MacOSSayBackend(say_path=fake_say).synthesize(
        "-- Bonjour Damien", voice_id="Thomas", speed=1.5
    )
    assert result.format == "wav"
    with wave.open(io.BytesIO(result.audio)) as w:
        assert w.getframerate() == 22050
    assert result.metadata["rate_wpm"] == 270


def test_text_is_sent_on_stdin_not_argv(fake_say, tmp_path, monkeypatch):
    import json, subprocess

    seen = {}
    real_run = subprocess.run

    def spy(cmd, **kw):
        seen["cmd"], seen["input"] = cmd, kw.get("input")
        return real_run(cmd, **kw)

    monkeypatch.setattr(subprocess, "run", spy)
    MacOSSayBackend(say_path=fake_say).synthesize("-v pirate", voice_id="Amélie")
    assert "-v pirate" not in seen["cmd"]
    assert seen["input"] == "-v pirate".encode()
    assert seen["cmd"][1:3] == ["-v", "Amélie"]


def test_available_voices(fake_say):
    assert MacOSSayBackend(say_path=fake_say).available_voices() == ["Thomas", "Amélie"]


def test_health_requires_macos(fake_say, monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    assert MacOSSayBackend(say_path=fake_say).health() is False
    monkeypatch.setattr(sys, "platform", "darwin")
    assert MacOSSayBackend(say_path=fake_say).health() is True


def test_listed_as_local_backend_with_french_default():
    from openjarvis.speech._tts_discovery import TTS_BACKEND_ORDER, default_voice_for

    assert TTS_BACKEND_ORDER.index("macos_say") < TTS_BACKEND_ORDER.index("openai_tts")
    assert default_voice_for("macos_say") == "Thomas"

