"""Lightweight video editing support for the MYRA project.

This module provides a tiny but usable in-memory project model and a Tkinter
UI that behaves like a simple editing studio: clips can be added, trimmed,
previewed, and exported as a structured JSON summary.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
import sys
from typing import Any, Sequence

try:  # pragma: no cover - GUI is optional at import time.
    import tkinter as tk
    from tkinter import ttk
except ImportError:  # pragma: no cover
    tk = None  # type: ignore[assignment]
    ttk = None  # type: ignore[assignment]


@dataclass
class VideoClip:
    """Single clip inside a project timeline."""

    name: str
    path: str
    duration: float
    start: float = 0.0
    end: float | None = None
    color: str = "#60a5fa"

    def __post_init__(self) -> None:
        if self.duration <= 0:
            raise ValueError("Clip duration must be greater than zero.")
        if self.end is None:
            self.end = self.duration
        if self.end < self.start:
            raise ValueError("Clip end must be greater than or equal to the start time.")

    @property
    def trimmed_duration(self) -> float:
        return max(0.0, float(self.end if self.end is not None else self.duration) - float(self.start))

    def trim(self, new_start: float | None = None, new_end: float | None = None) -> None:
        if new_start is not None:
            self.start = max(0.0, min(float(new_start), self.duration))
        if new_end is not None:
            self.end = max(self.start, min(float(new_end), self.duration))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class VideoProject:
    """A light-weight project model for simple editing workflows."""

    name: str = "My Video Project"
    width: int = 1920
    height: int = 1080
    fps: int = 30
    clips: list[VideoClip] = field(default_factory=list)

    def add_clip(
        self,
        path: str,
        name: str | None = None,
        duration: float | None = None,
        start: float = 0.0,
        end: float | None = None,
        color: str = "#60a5fa",
    ) -> VideoClip:
        clip_name = name or Path(path).stem or "clip"
        clip_duration = duration if duration is not None else 10.0
        clip = VideoClip(
            name=clip_name,
            path=path,
            duration=float(clip_duration),
            start=float(start),
            end=None if end is None else float(end),
            color=color,
        )
        self.clips.append(clip)
        return clip

    def delete_clip(self, index: int) -> VideoClip | None:
        if 0 <= index < len(self.clips):
            return self.clips.pop(index)
        return None

    @property
    def total_duration(self) -> float:
        return sum(clip.trimmed_duration for clip in self.clips)

    def summary(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "resolution": {"width": self.width, "height": self.height},
            "fps": self.fps,
            "total_duration": round(self.total_duration, 2),
            "clips": [clip.to_dict() for clip in self.clips],
        }

    def export_summary(self, destination: str | Path | None = None) -> Path:
        export_path = Path(destination) if destination is not None else Path.cwd() / "video_project_summary.json"
        export_path.parent.mkdir(parents=True, exist_ok=True)
        export_path.write_text(json.dumps(self.summary(), indent=2), encoding="utf-8")
        return export_path


class VideoEditorApp:
    """Tkinter-based editor interface for a lightweight video studio."""

    def __init__(self, root: Any | None = None) -> None:
        if tk is None:
            raise RuntimeError("Tkinter is required to launch the video editor GUI.")

        self.root = root or tk.Tk()
        self.project = VideoProject(name="Highlight Reel")
        self._seed_demo_project()
        self.root.title("MYRA Video Editor")
        self.root.geometry("980x620")
        self.root.minsize(820, 520)
        self.root.configure(bg="#0f172a")
        self._build_ui()

    def _seed_demo_project(self) -> None:
        self.project.clips = []
        self.project.add_clip("assets/intro.mp4", duration=8.0, color="#60a5fa")
        self.project.add_clip("assets/scene_a.mp4", duration=12.5, color="#34d399")
        self.project.add_clip("assets/scene_b.mp4", duration=10.0, color="#fbbf24")

    def _build_ui(self) -> None:
        topbar = tk.Frame(self.root, bg="#111827", padx=16, pady=12)
        topbar.pack(fill="x")

        title = tk.Label(
            topbar,
            text="MYRA Video Editor",
            fg="#f8fafc",
            bg="#111827",
            font=("Segoe UI", 18, "bold"),
        )
        title.pack(anchor="w")

        subtext = tk.Label(
            topbar,
            text="Edit clips, trim scenes, and export your project summary.",
            fg="#cbd5e1",
            bg="#111827",
            font=("Segoe UI", 10),
        )
        subtext.pack(anchor="w", pady=(6, 0))

        actions = tk.Frame(self.root, bg="#0f172a", padx=16, pady=12)
        actions.pack(fill="x")

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Editor.TButton", padding=(12, 8), font=("Segoe UI", 10, "bold"))

        ttk.Button(actions, text="Add Clip", command=self.add_clip, style="Editor.TButton").pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Trim 5s", command=self.trim_selected, style="Editor.TButton").pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Preview", command=self.preview_project, style="Editor.TButton").pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Export JSON", command=self.export_project, style="Editor.TButton").pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Quit", command=self.root.destroy, style="Editor.TButton").pack(side="right")

        main = tk.Frame(self.root, bg="#0f172a", padx=16, pady=(0, 16))
        main.pack(fill="both", expand=True)

        left = tk.Frame(main, bg="#111827", padx=12, pady=12, width=280)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        tk.Label(left, text="Project Clips", fg="#f8fafc", bg="#111827", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 10))

        self.clip_list = tk.Listbox(left, bg="#0f172a", fg="#e2e8f0", selectbackground="#2563eb", font=("Segoe UI", 10), height=14)
        self.clip_list.pack(fill="both", expand=True)
        self.clip_list.bind("<<ListboxSelect>>", self._on_clip_selected)

        right = tk.Frame(main, bg="#0f172a")
        right.pack(side="left", fill="both", expand=True, padx=(12, 0))

        self.details = tk.Text(right, bg="#020817", fg="#e2e8f0", font=("Segoe UI", 10), wrap="word", height=7)
        self.details.pack(fill="x", pady=(0, 12))
        self.details.insert("1.0", "Select a clip to inspect its timing and export settings.\n")
        self.details.configure(state="disabled")

        self.timeline = tk.Canvas(right, bg="#0f172a", highlightthickness=0, height=220)
        self.timeline.pack(fill="both", expand=True)

        self.status = tk.Label(right, text="Ready", fg="#86efac", bg="#0f172a", font=("Segoe UI", 10, "bold"), anchor="w")
        self.status.pack(fill="x", pady=(12, 0))

        self.refresh_project_view()

    def _on_clip_selected(self, _event: Any) -> None:
        if not self.clip_list.curselection():
            return
        clip_index = self.clip_list.curselection()[0]
        clip = self.project.clips[clip_index]
        summary = (
            f"Name: {clip.name}\n"
            f"Path: {clip.path}\n"
            f"Duration: {clip.duration:.2f}s\n"
            f"Trim range: {clip.start:.2f}s - {clip.end:.2f}s\n"
            f"Trimmed duration: {clip.trimmed_duration:.2f}s"
        )
        self.details.configure(state="normal")
        self.details.delete("1.0", "end")
        self.details.insert("1.0", summary)
        self.details.configure(state="disabled")

    def refresh_project_view(self) -> None:
        self.clip_list.delete(0, "end")
        for clip in self.project.clips:
            self.clip_list.insert("end", f"{clip.name}  ({clip.trimmed_duration:.1f}s)")

        self.timeline.delete("all")
        total = max(self.project.total_duration, 1.0)
        width = self.timeline.winfo_width() or 700
        height = self.timeline.winfo_height() or 220

        for index, clip in enumerate(self.project.clips):
            x0 = index * 180 + 20
            y0 = 30
            bar_length = max(80, int((clip.trimmed_duration / total) * (width - 60)))
            rect = self.timeline.create_rectangle(x0, y0, x0 + bar_length, y0 + 80, fill=clip.color, outline="#bfdbfe", width=2)
            self.timeline.create_text(x0 + 10, y0 + 18, anchor="nw", text=clip.name, fill="#f8fafc", font=("Segoe UI", 10, "bold"))
            self.timeline.create_text(x0 + 10, y0 + 42, anchor="nw", text=f"{clip.start:.1f}s - {clip.end:.1f}s", fill="#e2e8f0", font=("Segoe UI", 9))
            self.timeline.tag_bind(rect, "<Button-1>", lambda _event, idx=index: self._select_clip_with_index(idx))

        self.status.config(text=f"{len(self.project.clips)} clips • {self.project.total_duration:.1f}s total")

    def _select_clip_with_index(self, index: int) -> None:
        self.clip_list.selection_clear(0, "end")
        if 0 <= index < self.clip_list.size():
            self.clip_list.selection_set(index)
            self._on_clip_selected(None)

    def add_clip(self) -> None:
        clip_name = f"scene_{len(self.project.clips) + 1}.mp4"
        clip = self.project.add_clip(
            path=f"assets/{clip_name}",
            name=clip_name,
            duration=9.0,
            color="#a78bfa",
        )
        self.status.config(text=f"Added {clip.name}")
        self.refresh_project_view()

    def trim_selected(self) -> None:
        selection = self.clip_list.curselection()
        if not selection:
            self.status.config(text="Select a clip before trimming.")
            return
        clip = self.project.clips[selection[0]]
        clip.trim(new_start=0.0, new_end=min(clip.duration, clip.start + 5.0))
        self.status.config(text=f"Trimmed {clip.name} to 5.0s")
        self.refresh_project_view()
        self._on_clip_selected(None)

    def preview_project(self) -> None:
        summary = self.project.summary()
        self.status.config(text=f"Previewing {summary['name']} ({summary['total_duration']:.1f}s)")

    def export_project(self) -> None:
        export_path = self.project.export_summary(Path("exports") / "project_summary.json")
        self.status.config(text=f"Exported project summary to {export_path}")


def _demo_summary() -> dict[str, Any]:
    project = VideoProject(name="Demo Reel")
    project.add_clip("clips/opening.mp4", duration=12.0, color="#60a5fa")
    project.add_clip("clips/scene.mp4", duration=18.0, color="#34d399")
    return project.summary()


def run_cli() -> int:
    print(json.dumps(_demo_summary(), indent=2, ensure_ascii=True))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    if args and args[0] in {"--gui", "gui"}:
        if tk is None:
            raise RuntimeError("Tkinter is not available in this environment.")
        app = VideoEditorApp()
        app.root.mainloop()
        return 0

    if args and args[0] in {"--help", "-h", "help"}:
        print("Usage: myra-video [--gui]\nCreates a lightweight video project summary or opens the editor GUI.")
        return 0

    return run_cli()
