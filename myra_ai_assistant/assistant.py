"""Core assistant behaviors for the MYRA scaffold."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .windows_control import WindowsController


@dataclass
class AssistantEngine:
    name: str = "MYRA"
    model: str = "default"
    windows: WindowsController | None = None

    def __post_init__(self) -> None:
        if self.windows is None:
            self.windows = WindowsController()

    def listen(self, text: str | None = None) -> str:
        if text:
            return f"Listening to: {text}"
        return "Listening for your next command..."

    def respond(self, prompt: str) -> str:
        prompt = prompt.strip()
        if not prompt:
            return "I’m ready. Ask me to research, automate, or create something."
        if self.windows is not None:
            result = self.windows.handle_command(prompt)
            if result is not None:
                return result
        return (
            f"Processing request: '{prompt}'\n"
            "I can currently open Notepad, Calculator, File Explorer, or Paint; "
            "report system status; and control system volume."
        )

    def status(self) -> dict[str, Any]:
        return {
            "assistant": self.name,
            "model": self.model,
            "voice": "optional offline voice support",
            "automation": "allowlisted Windows controls",
            "screen_reading": "not implemented",
            "status": "ready",
        }
