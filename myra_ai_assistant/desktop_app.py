"""Tkinter-based desktop UI for MYRA."""

from __future__ import annotations

import tkinter as tk
from queue import Empty, Queue
from threading import Event, Thread
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from .assistant import AssistantEngine
from .config import load_config
from .voice import listen_offline, speak_offline


class DesktopApp:
    def __init__(self, root: tk.Tk | None = None) -> None:
        self.root = root or tk.Tk()
        self.config = load_config()
        self.assistant = AssistantEngine(name=self.config.name, model=self.config.model)
        self.voice_stop_event = Event()
        self.voice_events: Queue[tuple[str, str]] = Queue()
        self.voice_thread: Thread | None = None
        self.metric_refresh_ms = 5000
        self.root.title("MYRA AI Assistant")
        self.root.geometry("1100x700")
        self.root.minsize(900, 600)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        self._build_ui()
        self.root.after(100, self._process_voice_events)

    def _build_ui(self) -> None:
        self.root.configure(bg="#0f172a")

        topbar = tk.Frame(self.root, bg="#111827", padx=16, pady=12)
        topbar.pack(fill="x")

        title_row = tk.Frame(topbar, bg="#111827")
        title_row.pack(fill="x")

        title = tk.Label(
            title_row,
            text="MYRA AI Assistant",
            fg="#e2e8f0",
            bg="#111827",
            font=("Segoe UI", 18, "bold"),
        )
        title.pack(anchor="w")

        status_row = tk.Frame(topbar, bg="#111827")
        status_row.pack(anchor="w", pady=(6, 0))

        self.status_circle = tk.Label(status_row, text="●", fg="#22c55e", bg="#111827", font=("Segoe UI", 14, "bold"))
        self.status_circle.pack(side="left")

        self.status_label = tk.Label(
            status_row,
            text="System Ready",
            fg="#dbeafe",
            bg="#111827",
            font=("Segoe UI", 10, "bold"),
        )
        self.status_label.pack(side="left", padx=(8, 0))

        actions = tk.Frame(self.root, bg="#0f172a", padx=16, pady=12)
        actions.pack(fill="x")

        ttk.Style().theme_use("clam")
        ttk.Style().configure("MYRA.TButton", padding=(12, 8), font=("Segoe UI", 10, "bold"))

        self.demo_btn = ttk.Button(actions, text="Run Demo", command=self.run_demo, style="MYRA.TButton")
        self.demo_btn.pack(side="left", padx=(0, 8))

        self.status_btn = ttk.Button(actions, text="System Status", command=self.show_status, style="MYRA.TButton")
        self.status_btn.pack(side="left", padx=(0, 8))

        self.refresh_btn = ttk.Button(actions, text="Refresh Dashboard", command=self.refresh_dashboard, style="MYRA.TButton")
        self.refresh_btn.pack(side="left", padx=(0, 8))

        self.clear_btn = ttk.Button(actions, text="Clear Chat", command=self.clear_chat, style="MYRA.TButton")
        self.clear_btn.pack(side="left")

        self.quit_btn = ttk.Button(actions, text="Quit", command=self.close, style="MYRA.TButton")
        self.quit_btn.pack(side="right")

        main_area = tk.Frame(self.root, bg="#0f172a", padx=16)
        main_area.pack(fill="both", expand=True, pady=(0, 12))

        sidebar = tk.Frame(main_area, bg="#111827", padx=12, pady=12, width=240)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="Dashboard", fg="#f8fafc", bg="#111827", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 12))

        quick_actions = [
            ("System Status", "#38bdf8"),
            ("Open Notepad", "#a78bfa"),
            ("Open Calculator", "#34d399"),
            ("Open File Explorer", "#fbbf24"),
            ("Open Paint", "#fb7185"),
            ("Volume Up", "#f87171"),
            ("Volume Down", "#f97316"),
            ("Mute Volume", "#c084fc"),
        ]

        for action, accent in quick_actions:
            btn = tk.Button(
                sidebar,
                text=action,
                bg="#1e293b",
                fg="#e2e8f0",
                relief="flat",
                padx=12,
                pady=10,
                anchor="w",
                activebackground="#334155",
                activeforeground="#f8fafc",
                highlightthickness=0,
                command=lambda text=action: self.send_quick_action(text),
            )
            btn.pack(fill="x", pady=3)
            btn.configure(fg="#e2e8f0")
            btn.bind("<Enter>", lambda event, b=btn, c=accent: b.configure(bg=c, fg="#0f172a"))
            btn.bind("<Leave>", lambda event, b=btn: b.configure(bg="#1e293b", fg="#e2e8f0"))

        sidebar_footer = tk.Frame(sidebar, bg="#111827", pady=18)
        sidebar_footer.pack(side="bottom", fill="x")
        tk.Label(
            sidebar_footer,
            text="AI Ready",
            fg="#86efac",
            bg="#111827",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w")

        content = tk.Frame(main_area, bg="#0f172a")
        content.pack(side="left", fill="both", expand=True, padx=(12, 0))

        overview = tk.Frame(content, bg="#0f172a")
        overview.pack(fill="x", pady=(0, 12))

        cards = [
            ("Operating System", "Loading..."),
            ("Memory Used", "Loading..."),
            ("Processors", "Loading..."),
            ("AI", "Local demo"),
        ]
        self.metric_values: dict[str, tk.Label] = {}
        for i, (title, value) in enumerate(cards):
            card = tk.Frame(overview, bg="#111827", padx=14, pady=12, width=160, height=80)
            card.grid(row=0, column=i, padx=(0, 10), sticky="nsew")
            tk.Label(card, text=title, fg="#94a3b8", bg="#111827", font=("Segoe UI", 10)).pack(anchor="w")
            value_label = tk.Label(
                card,
                text=value,
                fg="#f8fafc",
                bg="#111827",
                font=("Segoe UI", 15, "bold"),
            )
            value_label.pack(anchor="w", pady=(8, 0))
            self.metric_values[title] = value_label
        overview.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.chat = ScrolledText(
            content,
            wrap="word",
            bg="#020817",
            fg="#e2e8f0",
            insertbackground="#e2e8f0",
            font=("Segoe UI", 11),
            padx=12,
            pady=12,
            height=12,
        )
        self.chat.pack(fill="both", expand=True)
        self.chat.configure(state="disabled")

        self._append_message("MYRA", "Welcome back. I’m ready to assist you.")

        input_box = tk.Frame(self.root, bg="#0f172a", padx=16)
        input_box.pack(fill="x", pady=(0, 16))

        self.prompt_var = tk.StringVar()
        self.prompt_entry = ttk.Entry(input_box, textvariable=self.prompt_var, font=("Segoe UI", 11))
        self.prompt_entry.pack(side="left", fill="x", expand=True)
        self.prompt_entry.bind("<Return>", lambda event: self.handle_input())

        self.listen_btn = ttk.Button(input_box, text="Start Mic", command=self.toggle_listening, style="MYRA.TButton")
        self.listen_btn.pack(side="left", padx=(8, 0))

        self.speak_replies_var = tk.BooleanVar(value=False)
        speak_replies = ttk.Checkbutton(input_box, text="Speak replies", variable=self.speak_replies_var)
        speak_replies.pack(side="left", padx=(8, 0))

        send_btn = ttk.Button(input_box, text="Send", command=self.handle_input, style="MYRA.TButton")
        send_btn.pack(side="left", padx=(8, 0))

        footer = tk.Frame(self.root, bg="#111827", padx=16, pady=10)
        footer.pack(fill="x")

        feature_labels = [
            ("Voice", "Optional"),
            ("AI", "Local stub"),
            ("Automation", "Allowlisted"),
            ("Screen", "Not connected"),
        ]

        for label, state in feature_labels:
            value = tk.Label(
                footer,
                text=f"{label}: {state}",
                fg="#dbeafe",
                bg="#111827",
                font=("Segoe UI", 9, "bold"),
            )
            value.pack(side="left", padx=(0, 20))

        self._build_login_screen()
        self.refresh_dashboard()

    def _build_login_screen(self) -> None:
        self.login_overlay = tk.Frame(self.root, bg="#050914")
        self.login_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)

        tk.Label(
            self.login_overlay,
            text="ADVANCED REALTIME INTELLIGENCE ASSISTANT",
            fg="#22d3ee",
            bg="#050914",
            font=("Segoe UI", 9, "bold"),
        ).pack(pady=(58, 18))

        card = tk.Frame(
            self.login_overlay,
            bg="#080d19",
            highlightbackground="#7f1d3f",
            highlightthickness=1,
            padx=44,
            pady=30,
        )
        card.pack(padx=24, pady=12)

        tk.Label(
            card,
            text="MYRA",
            fg="#f43f76",
            bg="#080d19",
            font=("Segoe UI", 28, "bold"),
        ).pack(pady=(0, 6))

        self.login_form = tk.Frame(card, bg="#080d19")
        self.login_form.pack(fill="x")

        tk.Label(
            self.login_form,
            text="WELCOME BACK",
            fg="#cbd5e1",
            bg="#080d19",
            font=("Segoe UI", 11, "bold"),
        ).pack(fill="x", pady=(4, 20))

        self.login_email_var = tk.StringVar()
        self.login_email_entry = ttk.Entry(self.login_form, textvariable=self.login_email_var, width=38)
        self.login_email_entry.insert(0, "Email address")
        self.login_email_entry.pack(fill="x", ipady=10, pady=(0, 12))
        self.login_email_entry.bind("<FocusIn>", self._clear_login_placeholder)

        self.login_password_var = tk.StringVar()
        self.login_password_entry = ttk.Entry(self.login_form, textvariable=self.login_password_var, width=38, show="*")
        self.login_password_entry.pack(fill="x", ipady=10, pady=(0, 18))

        continue_button = ttk.Button(
            self.login_form,
            text="CONTINUE IN DEMO MODE",
            command=self._dismiss_login,
            style="MYRA.TButton",
        )
        continue_button.pack(fill="x", ipady=6)

        tk.Label(
            self.login_form,
            text="Demo screen only. Credentials are not checked or stored.",
            fg="#fbbf24",
            bg="#080d19",
            font=("Segoe UI", 9),
            wraplength=330,
        ).pack(pady=(16, 0))

        ttk.Button(
            self.login_form,
            text="Activate MYRA Premium with a key",
            command=self._show_activation_form,
        ).pack(pady=(12, 0))

        self.activation_form = tk.Frame(card, bg="#080d19")
        tk.Label(
            self.activation_form,
            text="ACTIVATE MYRA PREMIUM",
            fg="#cbd5e1",
            bg="#080d19",
            font=("Segoe UI", 11, "bold"),
        ).pack(fill="x", pady=(4, 10))
        tk.Label(
            self.activation_form,
            text="Enter your activation key",
            fg="#94a3b8",
            bg="#080d19",
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(0, 6))
        self.activation_key_var = tk.StringVar()
        self.activation_key_entry = ttk.Entry(
            self.activation_form,
            textvariable=self.activation_key_var,
            width=38,
        )
        self.activation_key_entry.pack(fill="x", ipady=10, pady=(0, 12))
        self.activation_message_var = tk.StringVar()
        tk.Label(
            self.activation_form,
            textvariable=self.activation_message_var,
            fg="#fbbf24",
            bg="#080d19",
            font=("Segoe UI", 9),
            wraplength=330,
            justify="left",
        ).pack(fill="x", pady=(0, 12))
        ttk.Button(
            self.activation_form,
            text="ACTIVATE",
            command=self._submit_activation_key,
            style="MYRA.TButton",
        ).pack(fill="x", ipady=6)
        ttk.Button(
            self.activation_form,
            text="Back to Login",
            command=self._show_login_form,
        ).pack(pady=(10, 0))

    def _clear_login_placeholder(self, _event: tk.Event[tk.Misc]) -> None:
        if self.login_email_var.get() == "Email address":
            self.login_email_var.set("")

    def _show_activation_form(self) -> None:
        self.login_form.pack_forget()
        self.activation_message_var.set("")
        self.activation_form.pack(fill="x")
        self.activation_key_entry.focus_set()

    def _show_login_form(self) -> None:
        self.activation_form.pack_forget()
        self.login_form.pack(fill="x")
        self.login_email_entry.focus_set()

    def _submit_activation_key(self) -> None:
        if not self.activation_key_var.get().strip():
            self.activation_message_var.set("Enter an activation key to continue.")
            return
        self.activation_message_var.set(
            "Activation service is not configured. This key was not validated and "
            "Premium has not been enabled."
        )

    def _dismiss_login(self) -> None:
        self.login_overlay.place_forget()
        self.prompt_entry.focus_set()

    def _append_message(self, sender: str, text: str) -> None:
        self.chat.configure(state="normal")
        self.chat.insert(tk.END, f"{sender}: {text}\n\n")
        self.chat.see(tk.END)
        self.chat.configure(state="disabled")

    def handle_input(self) -> None:
        prompt = self.prompt_var.get().strip()
        if not prompt:
            return
        self._append_message("You", prompt)
        self.prompt_var.set("")
        self._respond(prompt)

    def _respond(self, prompt: str) -> None:
        response = self.assistant.respond(prompt)
        self._append_message("MYRA", response)
        if self.speak_replies_var.get():
            Thread(target=self._speak_response, args=(response,), daemon=True).start()

    def _speak_response(self, response: str) -> None:
        try:
            speak_offline(response)
        except (RuntimeError, OSError) as exc:
            self.voice_events.put(("error", str(exc)))

    def toggle_listening(self) -> None:
        if self.voice_thread and self.voice_thread.is_alive():
            self.voice_stop_event.set()
            self.listen_btn.configure(text="Stopping...")
            return

        self.voice_stop_event.clear()
        self.listen_btn.configure(text="Stop Mic")
        self.status_label.configure(text="Starting offline microphone...")
        self.voice_thread = Thread(
            target=listen_offline,
            args=(self.voice_stop_event, self.voice_events.put),
            daemon=True,
        )
        self.voice_thread.start()

    def _process_voice_events(self) -> None:
        try:
            while True:
                event, message = self.voice_events.get_nowait()
                if event == "transcript":
                    self._append_message("You (voice)", message)
                    self._respond(message)
                elif event == "error":
                    self.status_label.configure(text="Voice unavailable")
                    self._append_message("MYRA", message)
                    self.voice_stop_event.set()
                else:
                    self.status_label.configure(text=message)
        except Empty:
            pass

        if self.voice_thread and not self.voice_thread.is_alive():
            self.listen_btn.configure(text="Start Mic")
            if self.status_label.cget("text").startswith(("Starting offline", "Stopping...")):
                self.status_label.configure(text="System Ready")

        self.root.after(100, self._process_voice_events)

    def send_quick_action(self, action: str) -> None:
        self.prompt_var.set(action)
        self.handle_input()

    def clear_chat(self) -> None:
        self.chat.configure(state="normal")
        self.chat.delete("1.0", tk.END)
        self.chat.configure(state="disabled")
        self._append_message("MYRA", "Chat cleared. How can I help?")

    def show_status(self) -> None:
        try:
            metrics = self.assistant.windows.system_metrics()
            self._append_message(
                "MYRA",
                "\n".join(
                    [
                        f"System: {metrics['system']}",
                        f"Logical processors: {metrics['logical_processors']}",
                        f"Memory used: {metrics['memory_used_percent']}%"
                        if metrics["memory_used_percent"] is not None
                        else "Memory usage is unavailable on this platform.",
                    ]
                ),
            )
            self.refresh_dashboard(schedule_next=False)
        except (OSError, AttributeError) as exc:
            self._append_message("MYRA", f"Could not read system status: {exc}")

    def refresh_dashboard(self, schedule_next: bool = True) -> None:
        try:
            metrics = self.assistant.windows.system_metrics()
        except (OSError, AttributeError) as exc:
            self.status_label.configure(text="System metrics unavailable")
            self._append_message("MYRA", f"Could not refresh system metrics: {exc}")
        else:
            self.metric_values["Operating System"].configure(text=str(metrics["system"]))
            memory_used = metrics["memory_used_percent"]
            self.metric_values["Memory Used"].configure(
                text=f"{memory_used}%" if memory_used is not None else "Unavailable"
            )
            self.metric_values["Processors"].configure(text=str(metrics["logical_processors"]))
            self.status_label.configure(text="System Ready")

        if schedule_next:
            self.root.after(self.metric_refresh_ms, self.refresh_dashboard)

    def run_demo(self) -> None:
        self._append_message("MYRA", self.assistant.listen("Open the terminal and create a website draft."))
        self._append_message("MYRA", self.assistant.respond("Create a landing page for a tech startup."))

    def run(self) -> None:
        self.root.mainloop()

    def close(self) -> None:
        self.voice_stop_event.set()
        self.root.destroy()


def main() -> None:
    app = DesktopApp()
    app.run()


if __name__ == "__main__":
    main()
