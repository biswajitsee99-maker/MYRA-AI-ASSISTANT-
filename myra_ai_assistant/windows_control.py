"""Allowlisted Windows application and system controls."""

from __future__ import annotations

import ctypes
import os
import platform
import re
import subprocess
import sys
from ctypes import wintypes


class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", wintypes.DWORD),
        ("dwMemoryLoad", wintypes.DWORD),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


class WindowsController:
    """Run a small, explicit set of Windows actions; never execute free-form commands."""

    APPLICATIONS = {
        "notepad": ("notepad.exe", "Notepad"),
        "calculator": ("calc.exe", "Calculator"),
        "file explorer": ("explorer.exe", "File Explorer"),
        "paint": ("mspaint.exe", "Paint"),
    }

    def handle_command(self, command: str) -> str | None:
        normalized = re.sub(r"[.!?]+$", "", command.strip().lower())

        app_match = re.fullmatch(
            r"(?:open|launch|start)\s+(notepad|calculator|calc|file explorer|explorer|paint)",
            normalized,
        )
        if app_match:
            return self.open_application(app_match.group(1))

        if normalized in {"system status", "check system status", "show system status"}:
            return self.system_status()

        volume_actions = {
            "volume up": "up",
            "increase volume": "up",
            "turn volume up": "up",
            "volume down": "down",
            "decrease volume": "down",
            "turn volume down": "down",
            "mute volume": "mute",
            "toggle mute": "mute",
        }
        action = volume_actions.get(normalized)
        if action:
            return self.adjust_volume(action)

        return None

    def open_application(self, application: str) -> str:
        key = application.lower()
        if key == "calc":
            key = "calculator"
        elif key == "explorer":
            key = "file explorer"

        executable, display_name = self.APPLICATIONS[key]
        if sys.platform != "win32":
            return "Opening Windows applications is only supported on Windows."

        try:
            subprocess.Popen([executable], close_fds=True)
        except OSError as exc:
            return f"Could not open {display_name}: {exc}"
        return f"Opened {display_name}."

    def system_status(self) -> str:
        metrics = self.system_metrics()
        memory_used = metrics.get("memory_used_percent")
        memory_line = (
            f"Memory used: {memory_used}%"
            if memory_used is not None
            else "Memory: unavailable"
        )
        return (
            f"System: {metrics['system']}\n"
            f"Logical processors: {metrics['logical_processors']}\n"
            f"{memory_line}"
        )

    def system_metrics(self) -> dict[str, str | int | None]:
        logical_processors = os.cpu_count() or "unknown"
        if sys.platform != "win32":
            return {
                "system": f"{platform.system()} {platform.release()}",
                "logical_processors": logical_processors,
                "memory_used_percent": None,
            }

        memory = MEMORYSTATUSEX()
        memory.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):
            raise ctypes.WinError()

        return {
            "system": f"Windows {platform.release()}",
            "logical_processors": logical_processors,
            "memory_used_percent": memory.dwMemoryLoad,
        }

    def adjust_volume(self, action: str) -> str:
        if sys.platform != "win32":
            return "Volume controls are only supported on Windows."

        virtual_keys = {"up": 0xAF, "down": 0xAE, "mute": 0xAD}
        virtual_key = virtual_keys[action]
        keybd_event = ctypes.windll.user32.keybd_event
        keybd_event(virtual_key, 0, 0, 0)
        keybd_event(virtual_key, 0, 0x0002, 0)

        if action == "mute":
            return "Toggled system mute."
        return f"Pressed volume {action}."
