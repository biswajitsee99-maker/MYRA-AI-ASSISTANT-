"""Optional offline speech recognition and speech synthesis for MYRA."""

from __future__ import annotations

from threading import Event
from typing import Callable


VOICE_INSTALL_HINT = (
    "Voice support is not installed. Run "
    "'python -m pip install -e .[voice]' from the project directory."
)


def listen_offline(stop_event: Event, publish: Callable[[str, str], None]) -> None:
    """Continuously recognize local speech and publish transcripts or errors."""
    try:
        import speech_recognition as sr
    except ImportError:
        publish("error", VOICE_INSTALL_HINT)
        return

    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            publish("status", "Microphone ready — listening offline")
            while not stop_event.is_set():
                try:
                    audio = recognizer.listen(source, timeout=1, phrase_time_limit=8)
                except sr.WaitTimeoutError:
                    continue

                try:
                    transcript = recognizer.recognize_sphinx(audio)
                except sr.UnknownValueError:
                    publish("status", "Didn't catch that — still listening")
                    continue
                except sr.RequestError as exc:
                    publish("error", f"Offline speech recognition unavailable: {exc}")
                    return

                if transcript.strip():
                    publish("transcript", transcript.strip())
    except AttributeError:
        publish("error", VOICE_INSTALL_HINT)
    except OSError as exc:
        publish(
            "error",
            f"Could not open the microphone: {exc}. Check microphone access and device availability.",
        )


def speak_offline(text: str) -> None:
    """Speak text using the local system voice."""
    try:
        import pyttsx3
    except ImportError as exc:
        raise RuntimeError(VOICE_INSTALL_HINT) from exc

    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
