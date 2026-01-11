from tkinter import ttk
import tkinter as tk
from typing import List
from data_models import DiabloWindowInfo
from config_manager import CONFIG


class WindowTreeFrame:
    def __init__(self, parent, update_window_tree_callback):
        self.window_frame = ttk.LabelFrame(
            parent,  # Parent container
            text="暗黑窗口信息（双击选中主程序）",
            padding=10,
        )
        self.window_frame.pack(fill=tk.X, padx=20, pady=5)

        window_tree_style = ttk.Style()
        window_tree_style.configure("Treeview", font=("微软雅黑", 10))
        window_tree_style.configure("Treeview.Heading", font=("微软雅黑", 10, "bold"))
        window_tree_style.configure("main.Treeview", background="#e8f4f8")

        self.window_tree = ttk.Treeview(
            self.window_frame,
            columns=("标题", "位置", "大小", "状态"),
            show="headings",
            height=3,
        )
        columns_config = {"标题": 300, "位置": 120, "大小": 120, "状态": 100}
        for col, width in columns_config.items():
            self.window_tree.heading(col, text=col)
            self.window_tree.column(col, width=width)

        self.window_tree.pack(fill=tk.BOTH, expand=True)
        self.window_tree.bind("<Double-1>", self._on_window_double_click)

        self.update_window_tree_callback = update_window_tree_callback

        self.main_diablo_window = CONFIG["main_diablo_window"]

    def update_window_tree(self, windows_info: List[DiabloWindowInfo]):
        for item in self.window_tree.get_children():
            self.window_tree.delete(item)

        if not windows_info:
            self.window_tree.insert(
                "", tk.END, values=("未检测到暗黑破坏神窗口", "", "", "")
            )
            return

        for win_info in windows_info:
            self.window_tree.insert(
                "",
                tk.END,
                values=(win_info.title, win_info.pos, win_info.size, win_info.status),
            )

    def _on_window_double_click(self, event):
        item = self.window_tree.identify_row(event.y)
        if not item:
            return

        values = self.window_tree.item(item, "values")
        if not values or values[0] == "未检测到暗黑破坏神窗口":
            return

        self.main_diablo_window = values[0]

        self.update_window_tree_callback(values[0])
