import tkinter as tk
from tkinter import ttk
from typing import Tuple
from config_manager import CONFIG


class BubbleWindow:
    def __init__(
        self,
        parent: tk.Tk,
        x: int,
        y: int,
        index: int,
        key: str,
        is_highlight: bool = False,
        config: dict = None,
    ):
        self.window = tk.Toplevel(parent)
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.attributes("-alpha", CONFIG["bubble_alpha"])

        bg_color = (
            CONFIG["highlight_bubble_color"]
            if is_highlight
            else CONFIG["normal_bubble_color"]
        )
        fg_color = "white"

        label_text = f"[{index}] {key}"
        label = ttk.Label(
            self.window,
            text=label_text,
            font=CONFIG["bubble_font"],
            background=bg_color,
            foreground=fg_color,
            padding=(8, 4),
        )
        label.pack()

        final_x = x + 10
        final_y = y + 10
        self.window.geometry(f"+{final_x}+{final_y}")

    def destroy(self):
        try:
            self.window.destroy()
        except Exception:
            pass
