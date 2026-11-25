"""macOS ``say`` TTS backend — the system voices built into every Mac.

Fully local, free, no Python ML stack. Useful where Kokoro cannot be
installed (Intel Macs: PyTorch no longer ships macOS x86_64 wheels) and for
non-English users: macOS ships good French voices ("Thomas", "Amélie",
"Audrey"...). More voices can be downloaded in System Settings →
Accessibility → Spoken Content → System Voice → Manage Voices.

Output is 16-bit little-endian PCM WAV, which ``voice_io.play_wav`` and
``play_audio_file`` can play directly.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List

from openjarvis.core.registry import TTSRegistry
from openjarvis.speech.tts import TTSBackend, TTSResult

DEFAULT_VOICE = "Thomas"  # French (France), male; present on stock macOS
_BASE_RATE_WPM = 180  # macOS default speaking rate is ~175-200 words/minute
_SAMPLE_RATE = 22050


@TTSRegistry.register("macos_say")
class MacOSSayBackend(TTSBackend):
    """Text-to-speech through the macOS ``say`` command."""

    backend_id = "macos_say"

    def __init__(self, *, say_path: str = "") -> None:
        self._say = say_path or shutil.which("say") or ""

    def health(self) -> bool:
        return sys.platform == "darwin" and bool(self._say)

    def synthesize(
        self,
        text: str,
        *,
        voice_id: str = DEFAULT_VOICE,
        speed: float = 1.0,
        output_format: str = "wav",
    ) -> TTSResult:
        if not self._say:
            raise RuntimeError("the macOS 'say' command is not available")
        rate = max(80, int(_BASE_RATE_WPM * (speed or 1.0)))
        fd, tmp = tempfile.mkstemp(suffix=".wav", prefix="jarvis-say-")
        os.close(fd)
        try:
            cmd = [
                self._say,
                "-r",
                str(rate),
                "-o",
                tmp,
                "--file-format=WAVE",
                f"--data-format=LEI16@{_SAMPLE_RATE}",
            ]
            if voice_id:
                cmd[1:1] = ["-v", voice_id]
            # Text goes through stdin so leading dashes are never parsed as
            # options and long replies do not hit argv limits.
            subprocess.run(
                cmd, input=text.encode("utf-8"), check=True, capture_output=True
            )
            audio = Path(tmp).read_bytes()
        finally:
            Path(tmp).unlink(missing_ok=True)
        return TTSResult(
            audio=audio,
            format="wav",
            voice_id=voice_id,
            sample_rate=_SAMPLE_RATE,
            metadata={"backend": self.backend_id, "rate_wpm": rate},
        )

    def available_voices(self) -> List[str]:
        if not self._say:
            return []
        out = subprocess.run(
            [self._say, "-v", "?"], capture_output=True, text=True, check=False
        ).stdout
        # Lines look like: "Thomas              fr_FR    # Bonjour, je m'appelle Thomas."
        voices = []
        for line in out.splitlines():
            head = line.split("#", 1)[0].rstrip()
            parts = head.rsplit(None, 1)
            if len(parts) == 2:
                voices.append(parts[0].strip())
        return voices


__all__ = ["DEFAULT_VOICE", "MacOSSayBackend"]
