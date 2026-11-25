"""On macOS, WAV replies are played with afplay instead of PortAudio."""

import io
import subprocess
import sys
import wave

from openjarvis.speech import voice_io


def _wav() -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(22050)
        w.writeframes(b"\x00\x00" * 10)
    return buf.getvalue()


def test_uses_afplay_on_macos(monkeypatch):
    calls = []
    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/afplay")
    monkeypatch.setattr(
        subprocess, "run", lambda cmd, **kw: calls.append(cmd) or None
    )
    voice_io.play_wav(_wav())
    assert calls and calls[0][0] == "/usr/bin/afplay"


def test_not_used_off_macos_or_for_raw_pcm(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    assert voice_io._play_with_afplay(_wav()) is False
    monkeypatch.setattr(sys, "platform", "darwin")
    assert voice_io._play_with_afplay(b"\x00\x01" * 50) is False
