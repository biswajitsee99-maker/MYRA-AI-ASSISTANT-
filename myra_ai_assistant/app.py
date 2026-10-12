"""Main application facade for the MYRA AI assistant."""

from __future__ import annotations

from .assistant import AssistantEngine
from .config import AppConfig, load_config


class MYRAApp:
    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or load_config()
        self.assistant = AssistantEngine(name=self.config.name, model=self.config.model)

    def render_banner(self) -> str:
        return "\n".join(
            [
                "+--------------------------------------------------+",
                "|                 MYRA AI ASSISTANT               |",
                "|      Voice • Automation • Screen Reading        |",
                "+--------------------------------------------------+",
            ]
        )

    def status(self) -> dict[str, object]:
        data = self.assistant.status()
        data["theme"] = self.config.theme
        data["wake_word"] = self.config.wake_word
        return data

    def run(self) -> str:
        lines = [
            self.render_banner(),
            "",
            "System status: READY",
            "Features: voice assistant, AI automation, screen understanding, productivity tools",
            "",
            "Suggested command: myra --help",
        ]
        return "\n".join(lines)

    def demo(self) -> str:
        return "\n".join(
            [
                self.render_banner(),
                "",
                "Demo mode activated.",
                self.assistant.listen("Open the terminal and create a website draft."),
                self.assistant.respond("Create a landing page for a tech startup."),
            ]
        )
