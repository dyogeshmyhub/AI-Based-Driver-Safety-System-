from __future__ import annotations

import os
import threading
import time
from pathlib import Path

try:
    import winsound
except ImportError:  # pragma: no cover
    winsound = None


class Alarm:
    """Simple laptop-compatible alarm with safe cooldowns and fallback beeps."""

    def __init__(self, warning_file: str | None = None, critical_file: str | None = None) -> None:
        root = Path(__file__).resolve().parent.parent
        self.warning_file = warning_file or str(root / "sounds" / "warning.wav")
        self.critical_file = critical_file or str(root / "sounds" / "critical.wav")
        self._thread_lock = threading.Lock()
        self._active = False
        self._last_played = 0.0
        self._cooldown = 1.0
        self._audio_enabled = True

    def _play_windows_beep(self, frequency: int = 1000, duration_ms: int = 250) -> None:
        if winsound is None:
            return
        try:
            winsound.Beep(frequency, duration_ms)
        except Exception:
            pass

    def play_warning(self, cooldown: float = 1.0) -> None:
        self._cooldown = cooldown
        self._play_alarm(self.warning_file, 1000, 220)

    def play_danger(self, cooldown: float = 1.0) -> None:
        self._cooldown = cooldown
        self._play_alarm(self.warning_file, 900, 260)

    def play_critical(self, cooldown: float = 1.0) -> None:
        self._cooldown = cooldown
        self._play_alarm(self.critical_file, 1400, 500)

    def _play_alarm(self, audio_path: str, frequency: int, duration_ms: int) -> None:
        if not self._audio_enabled:
            return
        with self._thread_lock:
            now = time.monotonic()
            if (now - self._last_played) < self._cooldown:
                return
            self._last_played = now
            self._active = True

        threading.Thread(
            target=self._play_audio,
            args=(audio_path, frequency, duration_ms),
            daemon=True,
        ).start()

    def _play_audio(self, audio_path: str, frequency: int, duration_ms: int) -> None:
        if os.path.exists(audio_path) and winsound is not None:
            try:
                winsound.PlaySound(audio_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                return
            except Exception:
                pass
        self._play_windows_beep(frequency, duration_ms)

    def stop_alarm(self) -> None:
        self._active = False
        self._last_played = 0.0

    def is_active(self) -> bool:
        return self._active
