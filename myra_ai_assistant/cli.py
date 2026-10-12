"""Command-line interface for MYRA."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from .app import MYRAApp
from .config import AppConfig, save_config
from .video_editor import VideoProject


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MYRA AI Assistant")
    parser.add_argument(
        "command",
        nargs="?",
        default="run",
        choices=["run", "status", "demo", "config", "video"],
        help="Action to execute",
    )
    parser.add_argument("--print-json", action="store_true", help="Print the result as JSON")
    parser.add_argument("--save-config", action="store_true", help="Persist the default configuration")
    parser.add_argument("--gui", action="store_true", help="Open the video editor GUI when using the video command")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    app = MYRAApp()

    if args.command == "run":
        result = app.run()
    elif args.command == "status":
        result = app.status()
    elif args.command == "demo":
        result = app.demo()
    elif args.command == "video":
        project = VideoProject(name="MYRA Video Project")
        project.add_clip("assets/intro.mp4", duration=12.5, color="#60a5fa")
        project.add_clip("assets/clip_01.mp4", duration=18.0, color="#34d399")
        project.add_clip("assets/clip_02.mp4", duration=15.0, color="#fbbf24")
        result = project.summary()
        if args.gui:
            from .video_editor import VideoEditorApp

            gui = VideoEditorApp()
            gui.root.mainloop()
            return 0
    else:
        result = app.config.as_dict()

    if args.save_config:
        config_path = save_config(app.config)
        if isinstance(result, dict):
            result["config_path"] = str(config_path)

    if args.print_json:
        if isinstance(result, dict):
            print(json.dumps(result, indent=2, ensure_ascii=True))
        else:
            print(json.dumps({"output": result}, indent=2, ensure_ascii=True))
        return 0

    if isinstance(result, dict):
        print(json.dumps(result, indent=2, ensure_ascii=True))
    else:
        try:
            print(result)
        except UnicodeEncodeError:
            print(result.encode("ascii", "ignore").decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
