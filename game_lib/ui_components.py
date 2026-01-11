import tkinter as tk
from tkinter import ttk
from typing import Tuple

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
        self.window.attributes("-alpha", config["bubble_alpha"])

        bg_color = (
            config["highlight_bubble_color"]
            if is_highlight
            else config["normal_bubble_color"]
        )
        fg_color = "white"

        label_text = f"[{index}] {key}"
        label = ttk.Label(
            self.window,
            text=label_text,
            font=config["bubble_font"],
            background=bg_color,
            foreground=fg_color,
            padding=(8, 4),
        )
        label.pack()

        screen_width = parent.winfo_screenwidth()
        screen_height = parent.winfo_screenheight()
        final_x = min(x + 10, screen_width - 100)
        final_y = min(y, screen_height - 50)
        self.window.geometry(f"+{final_x}+{final_y}")

    def destroy(self):
        try:
            self.window.destroy()
        except Exception:
            pass