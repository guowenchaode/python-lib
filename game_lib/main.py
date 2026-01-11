import pygetwindow as gw
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import time
import pyautogui
import csv
import os
import sys
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import traceback
import configparser
from thread_manager import ThreadManager
import threading

# Import refactored modules
from config_frame import load_settings, export_settings
from data_models import ScriptCommand, DiabloWindowInfo
from ui_components import BubbleWindow
from window_tree_frame import WindowTreeFrame
from record_frame import RecordFrame
from script_frame import ScriptFrame
from config_frame import ConfigFrame

# ===================== 全局配置 =====================
from config_manager import CONFIG

pyautogui.FAILSAFE = CONFIG["pyautogui_failsafe"]
pyautogui.PAUSE = CONFIG["pyautogui_pause"]


# ===================== 数据类 =====================
@dataclass
class ScriptCommand:
    key: str
    x: float
    y: float
    status: str = "未执行"
    source: str = "用户导入"


@dataclass
class DiabloWindowInfo:
    window_obj: gw.Window
    title: str
    pos: str
    size: str
    status: str
    is_active: bool


# ===================== 气泡窗口类 =====================
class BubbleWindow:
    def __init__(
        self,
        parent: tk.Tk,
        x: int,
        y: int,
        index: int,
        key: str,
        is_highlight: bool = False,
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


# ===================== 主监控类（核心修改：添加滚动条） =====================
class DiabloWindowMonitor:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("暗黑破坏神窗口监控工具 | 千分比坐标版 | 支持滚动")
        self.root.geometry("1180x780")  # 固定窗口大小
        self.root.resizable(False, False)

        # ========== 核心修改1：创建滚动容器 ==========
        # 1. 垂直滚动条
        self.v_scrollbar = ttk.Scrollbar(self.root, orient=tk.VERTICAL)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 2. 画布（承载内容）
        self.canvas = tk.Canvas(
            self.root,
            yscrollcommand=self.v_scrollbar.set,
            width=1110,  # Reduced width by 50
            height=780,
        )
        self.canvas.pack(
            side=tk.LEFT, fill=tk.BOTH, expand=True, padx=25
        )  # Center-align with padding

        # 3. 绑定滚动条与画布
        self.v_scrollbar.config(command=self.canvas.yview)

        # 4. 内容容器（所有控件放入这个Frame）
        self.content_frame = ttk.Frame(self.canvas)
        self.content_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        # 5. 将内容容器嵌入画布
        self.canvas.create_window((0, 0), window=self.content_frame, anchor=tk.NW)

        # 6. 绑定鼠标滚轮事件（支持滚轮滚动）
        self.canvas.bind_all("<MouseWheel>", self._on_mouse_wheel)

        # ========== 原有状态变量 ==========
        self.current_diablo_window: Optional[gw.Window] = None
        self.is_diablo_foreground: bool = False
        self.key_pos_records: Dict[str, Tuple[float, float]] = {}
        self.is_tool_foreground: bool = True
        self.main_diablo_window: Optional[gw.Window] = None
        self.main_window_title: str = ""
        self.main_window_size: Tuple[int, int] = (0, 0)
        self.main_window_location: Tuple[int, int] = (0, 0)

        self.script_commands: List[ScriptCommand] = []
        self.script_running: bool = False
        self.script_paused: bool = False
        self.script_thread: Optional[threading.Thread] = None
        self.script_current_index: int = 0
        self.script_loop: bool = True
        self.loop_interval: int = CONFIG["default_loop_interval"]
        self.stop_on_background: bool = True
        self.script_file_path: str = ""

        self.bubble_windows: List[BubbleWindow] = []
        self.highlighted_bubble: Optional[BubbleWindow] = None
        self.bubbles_visible: bool = False

        self.monitor_event = threading.Event()
        self.monitor_event.set()

        # 初始化UI（修改：所有控件放入content_frame）
        self._init_ui()
        self._bind_events()

        # Replace threading logic with ThreadManager
        self.thread_manager = ThreadManager(
            config=CONFIG,
            ui_callbacks={
                "get_diablo_windows": self._get_diablo_windows,
                "update_window_tree": self._update_window_tree,
                "update_status_label": self._update_status_label,
                "script_running": lambda: self.script_running,
                "stop_on_background": lambda: self.stop_on_background,
                "check_main_window_foreground": self._check_main_window_foreground,
                "stop_script": self.script_frame._stop_script,
                "bubbles_visible": lambda: self.bubbles_visible,
                "script_commands": lambda: self.script_commands,
                "create_bubbles": self.script_frame._create_bubbles_by_script_status,
                "main_window": lambda: self.main_diablo_window,
                "main_window_geometry": lambda: (
                    self.main_diablo_window.left,
                    self.main_diablo_window.top,
                    self.main_window_size[0],
                    self.main_window_size[1],
                ),
                "update_mouse_info": self._update_mouse_info,
            },
        )

        self.thread_manager.start_threads()
        self._on_window_double_click(CONFIG["main_diablo_window"])

    # ========== 核心修改2：鼠标滚轮滚动事件 ==========
    def _on_mouse_wheel(self, event):
        """响应鼠标滚轮滚动"""
        self.canvas.yview_scroll(-1 * int(event.delta / 120), "units")

    # ========== 原有UI初始化方法修改：将parent改为content_frame ==========
    def _init_ui(self):
        """初始化UI - 所有控件放入content_frame"""
        self._init_title_frame()
        self._init_mouse_frame()
        self._init_status_label()
        self._init_window_tree_frame()
        self._init_record_frame()
        self._init_script_frame()
        self._init_config_frame()
        self._init_exit_frame()

    def _init_title_frame(self):
        title_frame = ttk.Frame(self.content_frame)  # 修改parent为content_frame
        title_frame.pack(pady=10, fill=tk.X, padx=20)

        title_label = ttk.Label(
            title_frame,
            text="暗黑破坏神窗口监控工具 | 千分比坐标版 | 支持滚动",
            font=CONFIG["title_font"],
        )
        title_label.pack(side=tk.LEFT)

        bubble_hint_label = ttk.Label(
            title_frame,
            text="【F12/按钮】显示/隐藏气泡 | 双击暗黑窗口列表选中主程序 | 气泡：[序号] 按键 | 坐标：主程序千分比",
            font=CONFIG["normal_font"],
            foreground="gray",
        )
        bubble_hint_label.pack(side=tk.LEFT, padx=20)

    def _init_mouse_frame(self):
        mouse_frame = ttk.LabelFrame(
            self.content_frame,  # 修改parent为content_frame
            text="鼠标位置信息（主程序千分比）",
            padding=10,
        )
        mouse_frame.pack(fill=tk.X, padx=20, pady=5)

        self.mouse_abs_label = ttk.Label(
            mouse_frame, text="绝对位置：(X: 0, Y: 0)", font=CONFIG["normal_font"]
        )
        self.mouse_abs_label.pack(side=tk.LEFT, padx=10)

        self.mouse_rel_label = ttk.Label(
            mouse_frame, text="相对千分比：(X: ---, Y: ---)", font=CONFIG["normal_font"]
        )
        self.mouse_rel_label.pack(side=tk.LEFT, padx=10)

        self.main_window_label = ttk.Label(
            mouse_frame,
            text="当前主程序：未选中",
            font=CONFIG["normal_font"],
            foreground="blue",
        )
        self.main_window_label.pack(side=tk.LEFT, padx=20)

        self.main_window_abs_label = ttk.Label(
            mouse_frame,
            text="当前主程序：未选中",
            font=CONFIG["normal_font"],
            foreground="blue",
        )
        self.main_window_abs_label.pack(side=tk.LEFT, padx=20)

    def _init_status_label(self):
        self.status_label = ttk.Label(
            self.content_frame,  # 修改parent为content_frame
            text="暗黑破坏神状态：后台运行",
            font=("微软雅黑", 11, "bold"),
        )
        self.status_label.pack(pady=5, padx=20)

    def _init_window_tree_frame(self):
        self.window_tree_frame = WindowTreeFrame(
            self.content_frame, self._on_window_double_click
        )
        self.update_window_tree = self.window_tree_frame.update_window_tree

    def _init_record_frame(self):
        self.record_frame = RecordFrame(
            self.content_frame,
            self._export_records,
            self._import_records,
            self._clear_records,
        )

    def _init_script_frame(self):
        self.script_frame = ScriptFrame(self.content_frame, self)

        # Delegate ScriptFrame methods
        self._start_script = self.script_frame._start_script
        self._update_script_tree = self.script_frame._update_script_tree

    def _init_config_frame(self):
        self.config_frame = ConfigFrame(self.content_frame, self._reload_config)

    def _init_exit_frame(self):
        exit_frame = ttk.Frame(self.content_frame)
        exit_frame.pack(pady=10)

        self.stop_btn = ttk.Button(
            exit_frame, text="停止监控", command=self._stop_monitor
        )
        self.stop_btn.pack()

    # ========== 原有方法（保持不变） ==========
    def _reload_config(self):
        global CONFIG
        try:
            new_config = load_settings()
            CONFIG.clear()
            CONFIG.update(new_config)

            pyautogui.FAILSAFE = CONFIG["pyautogui_failsafe"]
            pyautogui.PAUSE = CONFIG["pyautogui_pause"]

            self.loop_interval = CONFIG["default_loop_interval"]
            self.interval_entry.delete(0, tk.END)
            self.interval_entry.insert(0, str(self.loop_interval))

            messagebox.showinfo(
                "成功", "配置文件已重新加载！\n部分配置需要重启程序生效"
            )
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("失败", f"重新加载配置失败：{str(e)}")

    def _bind_events(self):
        self.root.bind("<Key>", self._on_key_press)
        self.root.bind("<FocusIn>", lambda e: setattr(self, "is_tool_foreground", True))
        self.root.bind(
            "<FocusOut>", lambda e: setattr(self, "is_tool_foreground", False)
        )
        self.root.bind("<F12>", self.script_frame._toggle_bubbles_visibility)
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)

    def _on_window_double_click(self, target_title):
        if not target_title:
            return

        """Handle double-click events on the window tree."""
        diablo_windows = self._get_diablo_windows()
        self.main_diablo_window = next(
            (win.window_obj for win in diablo_windows if win.title == target_title),
            None,
        )
        self._update_main_window_info()

    def _update_main_window_info(self):
        if self.main_diablo_window:
            self.main_window_title = self.main_diablo_window.title.strip()

            main_window_size = (
                self.main_diablo_window.width,
                self.main_diablo_window.height,
            )

            main_window_location = (
                self.main_diablo_window.left,
                self.main_diablo_window.top,
            )

            size_changed = main_window_size != self.main_window_size
            location_changed = main_window_location != self.main_window_location

            if not size_changed and not location_changed:
                return

            self.main_window_size = main_window_size
            self.main_window_location = main_window_location

            self.main_window_label.config(text=f"当前主程序：{self.main_window_title}")
            self.main_window_abs_label.config(
                text=f"位置：{self.main_diablo_window.left}, {self.main_diablo_window.top}"
            )
            self.script_frame.script_main_window_label.config(
                text=f"主程序：{self.main_window_title}"
            )

            for row in self.window_tree_frame.window_tree.get_children():
                self.window_tree_frame.window_tree.item(row, tags=("normal",))

            # self.script_frame.reload()

    def _on_key_press(self, event):
        if not self.main_diablo_window or not self.current_diablo_window:
            return

        key = event.keysym
        if key in [
            "Shift_L",
            "Shift_R",
            "Control_L",
            "Control_R",
            "Alt_L",
            "Alt_R",
            "Caps_Lock",
            "Tab",
            "Return",
        ]:
            return

        mouse_x, mouse_y = pyautogui.position()
        win_left = self.main_diablo_window.left
        win_top = self.main_diablo_window.top
        win_w, win_h = self.main_window_size

        rel_x_permil = round((mouse_x - win_left) / win_w, 3)
        rel_y_permil = round((mouse_y - win_top) / win_h, 3)

        self.key_pos_records[key] = (rel_x_permil, rel_y_permil)
        self._update_record_tree()

    def _update_record_tree(self):
        for item in self.record_tree.get_children():
            self.record_tree.delete(item)

        for key, (x, y) in self.key_pos_records.items():
            x_show = f"{x*1000:.0f}‰"
            y_show = f"{y*1000:.0f}‰"
            self.record_tree.insert("", tk.END, values=(key, f"{x_show}, {y_show}"))

    def _export_records(self):
        if not self.key_pos_records:
            messagebox.showwarning("提示", "暂无记录可导出！")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")],
            title="导出按键记录",
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["按键", "千分比坐标X", "千分比坐标Y"])
                for key, (x, y) in self.key_pos_records.items():
                    writer.writerow([key, x * 1000, y * 1000])
            messagebox.showinfo("成功", f"记录已导出到：{os.path.abspath(file_path)}")
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("失败", f"导出失败：{str(e)}")

    def _import_records(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")], title="导入按键记录"
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                self.key_pos_records.clear()
                for row in reader:
                    key = row.get("按键", "").strip()
                    x = float(row.get("千分比坐标X", 0)) / 1000
                    y = float(row.get("千分比坐标Y", 0)) / 1000
                    if key:
                        self.key_pos_records[key] = (x, y)
            self._update_record_tree()
            messagebox.showinfo("成功", f"成功导入{len(self.key_pos_records)}条记录")
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("失败", f"导入失败：{str(e)}")

    def _clear_records(self):
        if messagebox.askyesno("确认", "是否确定清空所有按键记录？"):
            self.key_pos_records.clear()
            self._update_record_tree()

    def _update_window_tree(self, windows_info: List[DiabloWindowInfo]):
        self.window_tree_frame.update_window_tree(windows_info)

    def _update_status_label(self):
        status_text = (
            "暗黑破坏神状态：前台运行"
            if self.is_diablo_foreground
            else "暗黑破坏神状态：后台运行"
        )
        self.status_label.config(text=status_text)

    def _update_mouse_info(self, abs_x: int, abs_y: int, rel_x: float, rel_y: float):
        self.mouse_abs_label.config(text=f"绝对位置：(X: {abs_x}, Y: {abs_y})")

        if rel_x == "--" or rel_y == "--":
            self.mouse_rel_label.config(text="相对千分比：(X: ---, Y: ---)")
        else:
            self.mouse_rel_label.config(
                text=f"相对千分比：(X: {rel_x*1000:.0f}‰, Y: {rel_y*1000:.0f}‰)"
            )

        self._update_main_window_info()

    def _check_main_window_foreground(self) -> bool:
        if not self.main_diablo_window:
            return False
        try:
            foreground_window = gw.getActiveWindow()
            return (
                foreground_window
                and foreground_window.title.strip()
                == self.main_diablo_window.title.strip()
            )
        except Exception:
            return False

    def _stop_monitor(self):
        if messagebox.askyesno("确认", "是否确定停止监控并退出？"):
            self._stop_monitor_threads()
            self.root.quit()
            self.root.destroy()

    def _stop_monitor_threads(self):
        self.monitor_event.clear()
        if self.window_monitor_thread.is_alive():
            self.window_monitor_thread.join(timeout=1)
        if self.mouse_monitor_thread.is_alive():
            self.mouse_monitor_thread.join(timeout=1)

    def _on_window_close(self):
        self._stop_monitor_threads()
        self.root.quit()

    def _get_diablo_windows(self):
        """Retrieve a list of Diablo windows."""
        try:
            main_diablo_window = CONFIG["main_diablo_window"]
            windows = gw.getWindowsWithTitle("")
            diablo_windows = [
                DiabloWindowInfo(
                    window_obj=win,
                    title=win.title.strip(),
                    pos=f"({win.left}, {win.top})",
                    size=f"{win.width}x{win.height}",
                    status="前台" if win == gw.getActiveWindow() else "后台",
                    is_active=(win == gw.getActiveWindow()),
                )
                for win in windows
                if main_diablo_window == win.title
            ]
            return diablo_windows
        except Exception as e:
            messagebox.showerror("错误", f"获取暗黑窗口失败：{str(e)}")
            return []


# ===================== 程序入口 =====================
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = DiabloWindowMonitor(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("程序启动失败", f"程序启动异常：{str(e)}")
        traceback.print_exc()
