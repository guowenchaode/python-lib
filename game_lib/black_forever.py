import pygetwindow as gw
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
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

# Import refactored modules
from config_manager import load_settings, export_settings
from data_models import ScriptCommand, DiabloWindowInfo
from ui_components import BubbleWindow
from script_executor import ScriptExecutor


# ===================== 配置文件管理 =====================
def load_settings(config_path: str = "settings.properties") -> Dict[str, Any]:
    """加载配置文件，不存在则创建默认配置"""
    config = configparser.ConfigParser()
    default_config = {
        "pyautogui_pause": "0.1",
        "pyautogui_failsafe": "False",
        "monitor_window_interval": "0.5",
        "monitor_mouse_interval": "0.01",
        "default_loop_interval": "15",
        "bubble_alpha": "0.5",
        "bubble_font": "微软雅黑,10,bold",
        "title_font": "微软雅黑,14,bold",
        "normal_font": "微软雅黑,10",
        "highlight_bubble_color": "#ff4444",
        "normal_bubble_color": "#4444ff",
        "main_window_tag_color": "#e8f4f8",
    }

    if not os.path.exists(config_path):
        config["SETTINGS"] = default_config
        with open(config_path, "w", encoding="utf-8") as f:
            config.write(f)
        messagebox.showinfo("提示", f"未找到配置文件，已创建默认配置：{config_path}")
        return default_config

    try:
        config.read(config_path, encoding="utf-8")
        loaded_config = {}
        for key, default_value in default_config.items():
            loaded_config[key] = config.get("SETTINGS", key, fallback=default_value)

        # 类型转换
        loaded_config["pyautogui_pause"] = float(loaded_config["pyautogui_pause"])
        loaded_config["pyautogui_failsafe"] = config.getboolean(
            "SETTINGS", "pyautogui_failsafe", fallback=False
        )
        loaded_config["monitor_window_interval"] = float(
            loaded_config["monitor_window_interval"]
        )
        loaded_config["monitor_mouse_interval"] = float(
            loaded_config["monitor_mouse_interval"]
        )
        loaded_config["default_loop_interval"] = int(
            loaded_config["default_loop_interval"]
        )
        loaded_config["bubble_alpha"] = float(loaded_config["bubble_alpha"])

        # 字体格式转换
        for font_key in ["bubble_font", "title_font", "normal_font"]:
            font_parts = loaded_config[font_key].split(",")
            font_name = font_parts[0]
            font_size = int(font_parts[1]) if len(font_parts) > 1 else 10
            font_weight = font_parts[2] if len(font_parts) > 2 else ""
            loaded_config[font_key] = (
                (font_name, font_size, font_weight)
                if font_weight
                else (font_name, font_size)
            )

        return loaded_config
    except Exception as e:
        messagebox.showerror(
            "配置加载错误", f"配置文件读取失败，使用默认配置：{str(e)}"
        )
        return default_config


def export_settings(
    config_dict: Dict[str, Any], config_path: str = "settings.properties"
):
    """导出当前配置到文件"""
    config = configparser.ConfigParser()
    export_dict = {}

    for key, value in config_dict.items():
        if isinstance(value, tuple) and all(isinstance(x, (str, int)) for x in value):
            export_dict[key] = ",".join(map(str, value))
        elif isinstance(value, (int, float, bool, str)):
            export_dict[key] = str(value)
        else:
            export_dict[key] = str(value)

    config["SETTINGS"] = export_dict

    try:
        with open(config_path, "w", encoding="utf-8") as f:
            config.write(f)
        messagebox.showinfo("成功", f"配置已导出到：{os.path.abspath(config_path)}")
    except Exception as e:
        messagebox.showerror("导出失败", f"配置导出失败：{str(e)}")


# ===================== 全局配置 =====================
config_path = r"C:\Users\Alex\Desktop\暗黑脚本\settings.properties"
CONFIG = load_settings(config_path)
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
            width=1160,  # 主窗口宽度 - 滚动条宽度
            height=780,
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

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
        self._start_monitor_threads()

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

    def _init_status_label(self):
        self.status_label = ttk.Label(
            self.content_frame,  # 修改parent为content_frame
            text="暗黑破坏神状态：后台运行",
            font=("微软雅黑", 11, "bold"),
        )
        self.status_label.pack(pady=5, padx=20)

    def _init_window_tree_frame(self):
        window_frame = ttk.LabelFrame(
            self.content_frame,  # 修改parent为content_frame
            text="暗黑窗口信息（双击选中主程序）",
            padding=10,
        )
        window_frame.pack(fill=tk.X, padx=20, pady=5)

        window_tree_style = ttk.Style()
        window_tree_style.configure("Treeview", font=CONFIG["normal_font"])
        window_tree_style.configure("Treeview.Heading", font=("微软雅黑", 10, "bold"))
        window_tree_style.configure(
            "main.Treeview", background=CONFIG["main_window_tag_color"]
        )

        self.window_tree = ttk.Treeview(
            window_frame,
            columns=("标题", "位置", "大小", "状态"),
            show="headings",
            height=3,
        )
        columns_config = {"标题": 300, "位置": 120, "大小": 120, "状态": 100}
        for col, width in columns_config.items():
            self.window_tree.heading(col, text=col)
            self.window_tree.column(col, width=width)

        self.window_tree.pack(fill=tk.X)
        self.window_tree.bind("<Double-1>", self._on_window_double_click)

    def _init_record_frame(self):
        record_frame = ttk.LabelFrame(
            self.content_frame,  # 修改parent为content_frame
            text="按键-千分比坐标记录",
            padding=10,
        )
        record_frame.pack(fill=tk.X, padx=20, pady=5)

        record_tree_style = ttk.Style()
        record_tree_style.configure("Record.Treeview", font=CONFIG["normal_font"])
        record_tree_style.configure(
            "Record.Treeview.Heading", font=("微软雅黑", 10, "bold")
        )

        self.record_tree = ttk.Treeview(
            record_frame,
            columns=("按键", "千分比坐标"),
            show="headings",
            style="Record.Treeview",
            height=5,
        )
        self.record_tree.heading("按键", text="按键")
        self.record_tree.heading("千分比坐标", text="主程序千分比坐标(X‰, Y‰)")
        self.record_tree.column("按键", width=100)
        self.record_tree.column("千分比坐标", width=200)
        self.record_tree.pack(side=tk.LEFT, fill=tk.X, expand=True)

        record_btn_frame = ttk.Frame(record_frame)
        record_btn_frame.pack(side=tk.RIGHT, padx=10)

        self.export_btn = ttk.Button(
            record_btn_frame, text="导出记录(CSV)", command=self._export_records
        )
        self.import_btn = ttk.Button(
            record_btn_frame, text="导入记录(CSV)", command=self._import_records
        )
        self.clear_btn = ttk.Button(
            record_btn_frame, text="清空记录", command=self._clear_records
        )

        for btn in [self.export_btn, self.import_btn, self.clear_btn]:
            btn.pack(pady=5, fill=tk.X)

    def _init_script_frame(self):
        script_frame = ttk.LabelFrame(
            self.content_frame,  # 修改parent为content_frame
            text="脚本执行模块（千分比坐标）",
            padding=10,
        )
        script_frame.pack(fill=tk.BOTH, padx=20, pady=5, expand=True)

        script_ctrl_frame = ttk.Frame(script_frame)
        script_ctrl_frame.pack(fill=tk.X, pady=5)

        self.script_main_window_label = ttk.Label(
            script_ctrl_frame,
            text="主程序：未选中",
            font=("微软雅黑", 10, "bold"),
            foreground="red",
        )
        self.script_main_window_label.pack(side=tk.LEFT, padx=5)

        self.load_script_btn = ttk.Button(
            script_ctrl_frame, text="加载CSV脚本", command=self._load_script
        )
        self.start_script_btn = ttk.Button(
            script_ctrl_frame,
            text="启动脚本",
            command=self._start_script,
            state=tk.DISABLED,
        )
        self.pause_script_btn = ttk.Button(
            script_ctrl_frame,
            text="暂停脚本",
            command=self._pause_script,
            state=tk.DISABLED,
        )
        self.stop_script_btn = ttk.Button(
            script_ctrl_frame,
            text="停止脚本",
            command=self._stop_script,
            state=tk.DISABLED,
        )
        self.toggle_bubble_btn = ttk.Button(
            script_ctrl_frame, text="隐藏气泡", command=self._toggle_bubbles_visibility
        )

        for btn in [
            self.load_script_btn,
            self.start_script_btn,
            self.pause_script_btn,
            self.stop_script_btn,
            self.toggle_bubble_btn,
        ]:
            btn.pack(side=tk.LEFT, padx=5)

        self.stop_on_background_var = tk.BooleanVar(value=self.stop_on_background)
        self.stop_on_background_check = ttk.Checkbutton(
            script_ctrl_frame,
            text="主程序后台时自动停止脚本",
            variable=self.stop_on_background_var,
            command=lambda: setattr(
                self, "stop_on_background", self.stop_on_background_var.get()
            ),
        )
        self.stop_on_background_check.pack(side=tk.LEFT, padx=10)

        self.loop_var = tk.BooleanVar(value=True)
        self.loop_check = ttk.Checkbutton(
            script_ctrl_frame,
            text="循环执行",
            variable=self.loop_var,
            command=lambda: setattr(self, "script_loop", self.loop_var.get()),
        )
        self.loop_check.pack(side=tk.LEFT, padx=10)

        ttk.Label(
            script_ctrl_frame, text="循环间隔(秒)：", font=CONFIG["normal_font"]
        ).pack(side=tk.LEFT, padx=5)
        self.interval_entry = ttk.Entry(
            script_ctrl_frame, width=8, font=CONFIG["normal_font"]
        )
        self.interval_entry.insert(0, str(self.loop_interval))
        self.interval_entry.pack(side=tk.LEFT, padx=5)

        self.set_interval_btn = ttk.Button(
            script_ctrl_frame, text="确认", command=self._set_loop_interval
        )
        self.set_interval_btn.pack(side=tk.LEFT, padx=5)

        self.script_status_label = ttk.Label(
            script_ctrl_frame, text="脚本状态：未加载", font=CONFIG["normal_font"]
        )
        self.script_status_label.pack(side=tk.RIGHT, padx=10)

        self.script_tree = ttk.Treeview(
            script_frame,
            columns=("序号", "按键", "千分比坐标", "状态", "命令来源"),
            show="headings",
            height=8,
        )
        script_columns = {
            "序号": 60,
            "按键": 80,
            "千分比坐标": 200,
            "状态": 100,
            "命令来源": 120,
        }
        for col, width in script_columns.items():
            self.script_tree.heading(col, text=col)
            self.script_tree.column(col, width=width)

        script_scroll = ttk.Scrollbar(
            script_frame, orient=tk.VERTICAL, command=self.script_tree.yview
        )
        self.script_tree.configure(yscrollcommand=script_scroll.set)
        self.script_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        script_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def _init_config_frame(self):
        config_frame = ttk.LabelFrame(self.content_frame, text="配置管理", padding=10)
        config_frame.pack(fill=tk.X, padx=20, pady=5)

        export_config_btn = ttk.Button(
            config_frame,
            text="导出当前配置到settings.properties",
            command=lambda: export_settings(CONFIG),
        )
        export_config_btn.pack(side=tk.LEFT, padx=5)

        reload_config_btn = ttk.Button(
            config_frame, text="重新加载配置文件", command=self._reload_config
        )
        reload_config_btn.pack(side=tk.LEFT, padx=5)

        config_path_label = ttk.Label(
            config_frame,
            text=f"当前配置文件：{os.path.abspath(config_path)}",
            font=CONFIG["normal_font"],
        )
        config_path_label.pack(side=tk.LEFT, padx=20)

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
            messagebox.showerror("失败", f"重新加载配置失败：{str(e)}")

    def _bind_events(self):
        self.root.bind("<Key>", self._on_key_press)
        self.root.bind("<FocusIn>", lambda e: setattr(self, "is_tool_foreground", True))
        self.root.bind(
            "<FocusOut>", lambda e: setattr(self, "is_tool_foreground", False)
        )
        self.root.bind("<F12>", self._toggle_bubbles_visibility)
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)

    def _start_monitor_threads(self):
        self.window_monitor_thread = threading.Thread(
            target=self._monitor_windows, daemon=True, name="WindowMonitorThread"
        )
        self.mouse_monitor_thread = threading.Thread(
            target=self._monitor_mouse, daemon=True, name="MouseMonitorThread"
        )

        self.window_monitor_thread.start()
        self.mouse_monitor_thread.start()

    def _monitor_windows(self):
        last_update_time = 0
        while self.monitor_event.is_set():
            current_time = time.time()
            if current_time - last_update_time < CONFIG["monitor_window_interval"]:
                time.sleep(0.05)
                continue

            try:
                windows_info = self._get_diablo_windows()
                self.root.after_idle(self._update_window_tree, windows_info)
                self.root.after_idle(self._update_status_label)

                if (
                    self.script_running
                    and self.stop_on_background
                    and self.main_diablo_window
                ):
                    if not self._check_main_window_foreground():
                        self.root.after_idle(self._stop_script)

                if (
                    self.bubbles_visible
                    and self.script_commands
                    and self.main_diablo_window
                ):
                    self.root.after_idle(self._create_bubbles_by_script_status)

                last_update_time = current_time
            except Exception as e:
                print(f"窗口监控异常：{e}")
                time.sleep(CONFIG["monitor_window_interval"])

    def _monitor_mouse(self):
        last_mouse_pos = (0, 0)
        while self.monitor_event.is_set():
            try:
                mouse_x, mouse_y = pyautogui.position()
                if (mouse_x, mouse_y) == last_mouse_pos:
                    time.sleep(CONFIG["monitor_mouse_interval"])
                    continue

                rel_x_permil, rel_y_permil = "--", "--"
                self.current_diablo_window = None

                if self.main_diablo_window and self.main_window_size != (0, 0):
                    win_left = self.main_diablo_window.left
                    win_top = self.main_diablo_window.top
                    win_w, win_h = self.main_window_size

                    if (
                        win_left <= mouse_x <= win_left + win_w
                        and win_top <= mouse_y <= win_top + win_h
                    ):
                        rel_x_permil = round((mouse_x - win_left) / win_w, 3)
                        rel_y_permil = round((mouse_y - win_top) / win_h, 3)
                        self.current_diablo_window = self.main_diablo_window

                self.root.after_idle(
                    self._update_mouse_info,
                    mouse_x,
                    mouse_y,
                    rel_x_permil,
                    rel_y_permil,
                )
                last_mouse_pos = (mouse_x, mouse_y)
                time.sleep(CONFIG["monitor_mouse_interval"])
            except Exception as e:
                print(f"鼠标监控异常：{e}")
                time.sleep(CONFIG["monitor_mouse_interval"])

    def _get_diablo_windows(self) -> List[DiabloWindowInfo]:
        diablo_windows = []
        try:
            foreground_window = gw.getActiveWindow()
            foreground_title = (
                foreground_window.title.strip() if foreground_window else ""
            )
            self.is_diablo_foreground = False

            for window in gw.getAllWindows():
                window_title = window.title.strip()
                if (
                    "暗黑破坏神" in window_title
                    and window.width > 0
                    and window.height > 0
                ):
                    is_active = window.title == foreground_title
                    if is_active:
                        self.is_diablo_foreground = True

                    win_info = DiabloWindowInfo(
                        window_obj=window,
                        title=window_title,
                        pos=f"({window.left}, {window.top})",
                        size=f"{window.width}x{window.height}",
                        status="前台" if is_active else "后台",
                        is_active=is_active,
                    )
                    diablo_windows.append(win_info)
        except Exception as e:
            self.root.after_idle(
                messagebox.showerror, "错误", f"获取窗口信息失败：{str(e)}"
            )
        return diablo_windows

    def _permil_to_absolute(self, x_permil: float, y_permil: float) -> Tuple[int, int]:
        if not self.main_diablo_window or self.main_window_size == (0, 0):
            return (0, 0)

        win_left = self.main_diablo_window.left
        win_top = self.main_diablo_window.top
        win_w, win_h = self.main_window_size

        abs_x = max(0, win_left + int(win_w * x_permil))
        abs_y = max(0, win_top + int(win_h * y_permil))

        return (abs_x, abs_y)

    def _load_script(self):
        if not self.main_diablo_window:
            messagebox.showwarning("提示", "请先双击选中主程序窗口！")
            return

        file_path = filedialog.askopenfilename(
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")], title="加载脚本文件"
        )
        if not file_path:
            return

        self.script_file_path = file_path
        self.script_commands.clear()
        self.script_current_index = 0

        try:
            df = pd.read_csv(file_path, dtype=str).fillna("")
            rows = df.to_dict(orient="records")

            commands = []
            for index in range(len(rows)):
                row = rows[index]
                key = row.get("按键", "").strip()
                x = (
                    float(row.get("千分比坐标X", 0.0)) / 1000
                    if row.get("千分比坐标X")
                    else 0.0
                )
                y = (
                    float(row.get("千分比坐标Y", 0.0)) / 1000
                    if row.get("千分比坐标Y")
                    else 0.0
                )
                command = ScriptCommand(key=key, x=x, y=y)
                commands.append(command)

            self.script_commands = commands
            self._add_countdown_commands()
            self._update_script_tree()
            self.start_script_btn.config(state=tk.NORMAL)
            self.script_status_label.config(
                text=f"脚本状态：已加载（{len(commands)}条命令）"
            )

        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("错误", f"加载脚本失败：{str(e)}")
            self.script_status_label.config(text="脚本状态：加载失败")

    def _update_script_tree(self):
        for item in self.script_tree.get_children():
            self.script_tree.delete(item)

        for idx, cmd in enumerate(self.script_commands):
            x_show = f"{cmd.x*1000:.0f}‰"
            y_show = f"{cmd.y*1000:.0f}‰"
            self.script_tree.insert(
                "",
                tk.END,
                values=(
                    idx + 1,
                    cmd.key,
                    f"{x_show}, {y_show}",
                    cmd.status,
                    cmd.source,
                ),
            )

    def _capture_main_window_screenshot(self) -> Optional[str]:
        if not self.main_diablo_window or not self.script_file_path:
            return None

        try:
            script_dir = os.path.dirname(os.path.abspath(self.script_file_path))
            cache_dir = os.path.join(script_dir, "cache")
            os.makedirs(cache_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            screenshot_filename = f"script_screenshot_{timestamp}.png"
            screenshot_path = os.path.join(cache_dir, screenshot_filename)

            win = self.main_diablo_window
            region = (win.left, win.top, win.width, win.height)
            if all(v > 0 for v in region):
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()

            screenshot.save(screenshot_path)
            print(f"截图已保存：{screenshot_path}")
            return screenshot_path

        except Exception as e:
            error_msg = f"截图保存失败：{str(e)}"
            print(error_msg)
            self.root.after_idle(messagebox.showwarning, "截图提示", error_msg)
            return None

    def _on_window_double_click(self, event):
        item = self.window_tree.identify_row(event.y)
        if not item:
            return

        values = self.window_tree.item(item, "values")
        if not values or values[0] == "未检测到暗黑破坏神窗口":
            return

        diablo_windows = self._get_diablo_windows()
        target_title = values[0]
        self.main_diablo_window = next(
            (win.window_obj for win in diablo_windows if win.title == target_title),
            None,
        )

        if self.main_diablo_window:
            self.main_window_title = self.main_diablo_window.title.strip()
            self.main_window_size = (
                self.main_diablo_window.width,
                self.main_diablo_window.height,
            )
            self.main_window_label.config(text=f"当前主程序：{self.main_window_title}")
            self.script_main_window_label.config(
                text=f"主程序：{self.main_window_title}"
            )

            for row in self.window_tree.get_children():
                self.window_tree.item(row, tags=("normal",))
            self.window_tree.item(item, tags=("main",))
            self._create_bubbles_by_script_status()

    def _toggle_bubbles_visibility(self, event=None):
        self.bubbles_visible = not self.bubbles_visible
        self.toggle_bubble_btn.config(
            text="隐藏气泡" if self.bubbles_visible else "显示气泡"
        )

        if self.bubbles_visible:
            self._create_bubbles_by_script_status()
        else:
            self._destroy_all_bubbles()

    def _destroy_all_bubbles(self):
        for bubble in self.bubble_windows:
            bubble.destroy()
        self.bubble_windows.clear()

        if self.highlighted_bubble:
            self.highlighted_bubble.destroy()
            self.highlighted_bubble = None

    def _create_bubbles_by_script_status(self):
        if (
            not self.bubbles_visible
            or not self.script_commands
            or not self.main_diablo_window
            or self.main_window_size == (0, 0)
        ):
            return

        self._destroy_all_bubbles()

        if self.script_running:
            next_idx = self.script_current_index
            while next_idx < len(self.script_commands):
                cmd = self.script_commands[next_idx]
                if cmd.source != "系统倒计时":
                    abs_x, abs_y = self._permil_to_absolute(cmd.x, cmd.y)
                    self.highlighted_bubble = BubbleWindow(
                        self.root,
                        abs_x,
                        abs_y,
                        next_idx + 1,
                        cmd.key,
                        is_highlight=True,
                    )
                    break
                next_idx += 1
        else:
            bubbles = []
            for idx, cmd in enumerate(self.script_commands):
                if cmd.source == "系统倒计时":
                    continue
                abs_x, abs_y = self._permil_to_absolute(cmd.x, cmd.y)
                bubble = BubbleWindow(self.root, abs_x, abs_y, idx + 1, cmd.key)
                bubbles.append(bubble)
            self.bubble_windows = bubbles

    def _set_loop_interval(self):
        try:
            interval = float(self.interval_entry.get())
            if interval < 0:
                raise ValueError("间隔时间不能为负数")
            if interval > 3600:
                raise ValueError("间隔时间不能超过3600秒")

            self.loop_interval = interval
            messagebox.showinfo("提示", f"循环间隔已设置为：{interval}秒")
        except ValueError as e:
            self.interval_entry.delete(0, tk.END)
            self.interval_entry.insert(0, str(self.loop_interval))
            messagebox.showwarning("提示", f"输入错误：{str(e)}")

    def _add_countdown_commands(self):
        if not self.script_loop or self.loop_interval <= 0:
            return

        self.script_commands = [
            cmd for cmd in self.script_commands if cmd.source != "系统倒计时"
        ]

        for i in range(int(self.loop_interval), 0, -1):
            self.script_commands.append(
                ScriptCommand(
                    key=f"倒计时{i}秒",
                    x=0.0,
                    y=0.0,
                    status="未执行",
                    source="系统倒计时",
                )
            )
        self.script_commands.append(
            ScriptCommand(
                key="倒计时结束", x=0.0, y=0.0, status="未执行", source="系统倒计时"
            )
        )

    def _start_script(self):
        if self.script_running or not self.script_commands:
            return

        # Initialize ScriptExecutor
        self.script_executor = ScriptExecutor(
            commands=self.script_commands,
            config=CONFIG,
            ui_callbacks={
                "on_start": self._on_script_start,
                "on_pause": self._on_script_pause,
                "on_stop": self._on_script_stop,
                "on_loop_end": self._on_loop_end,
                "update_tree": self._update_script_tree,
                "update_status": self._update_status_label,
                "permil_to_absolute": self._permil_to_absolute,
                "check_foreground": self._check_main_window_foreground,
                "bubbles_visible": lambda: self.bubbles_visible,
                "update_bubbles": self._create_bubbles_by_script_status,
            },
        )

        self.script_running = True
        self.script_paused = False
        self.start_script_btn.config(state=tk.DISABLED)
        self.pause_script_btn.config(state=tk.NORMAL)
        self.stop_script_btn.config(state=tk.NORMAL)
        self.script_status_label.config(text="脚本状态：运行中")

        self.script_thread = threading.Thread(
            target=self._run_script, daemon=True, name="ScriptExecutionThread"
        )
        self.script_thread.start()

    def _pause_script(self):
        self.script_paused = not self.script_paused
        if self.script_paused:
            self.pause_script_btn.config(text="继续脚本")
            self.script_status_label.config(text="脚本状态：暂停中")
        else:
            self.pause_script_btn.config(text="暂停脚本")
            self.script_status_label.config(text="脚本状态：运行中")

    def _stop_script(self):
        self.script_running = False
        self.script_paused = False
        self.start_script_btn.config(state=tk.NORMAL)
        self.pause_script_btn.config(state=tk.DISABLED)
        self.stop_script_btn.config(state=tk.DISABLED)
        self.script_current_index = 0
        self.script_status_label.config(text="脚本状态：已停止")
        for cmd in self.script_commands:
            cmd.status = "未执行"
        self._update_script_tree()
        self._destroy_all_bubbles()

    def _run_script(self):
        try:
            while self.script_running and self.monitor_event.is_set():
                while self.script_paused and self.script_running:
                    time.sleep(0.5)

                if self.script_current_index >= len(self.script_commands):
                    self.root.after_idle(self._capture_main_window_screenshot)

                    if self.script_loop:
                        self.script_current_index = 0
                        self.script_status_label.config(text="脚本状态：循环等待中")
                        time.sleep(self.loop_interval)
                    else:
                        self.root.after_idle(self._stop_script)
                        break

                cmd = self.script_commands[self.script_current_index]
                if cmd.source != "系统倒计时":
                    abs_x, abs_y = self._permil_to_absolute(cmd.x, cmd.y)
                    if self._check_main_window_foreground():
                        pyautogui.click(abs_x, abs_y)
                        pyautogui.press(cmd.key)
                        cmd.status = "已执行"
                    else:
                        cmd.status = "主程序后台，跳过"
                else:
                    cmd.status = "已执行"
                    self.root.after_idle(
                        self.script_status_label.config,
                        {"text": f"脚本状态：{cmd.key}"},
                    )
                    time.sleep(1)

                self.root.after_idle(self._update_script_tree)
                self.root.after_idle(self._scroll_to_current_command)
                self.script_current_index += 1

                if self.bubbles_visible:
                    self.root.after_idle(self._create_bubbles_by_script_status)

                time.sleep(pyautogui.PAUSE)

        except Exception as e:
            error_msg = f"脚本执行异常：{str(e)}"
            print(error_msg)
            self.root.after_idle(messagebox.showerror, "脚本错误", error_msg)
            self.root.after_idle(self._stop_script)

    def _scroll_to_current_command(self):
        if self.script_current_index > 0 and self.script_tree.get_children():
            try:
                current_item = self.script_tree.get_children()[
                    self.script_current_index - 1
                ]
                self.script_tree.see(current_item)
                for item in self.script_tree.get_children():
                    self.script_tree.item(item, tags=())
                self.script_tree.item(current_item, tags=("current",))
                self.script_tree.tag_configure("current", background="#ffffcc")
            except Exception:
                pass

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
            messagebox.showerror("失败", f"导入失败：{str(e)}")

    def _clear_records(self):
        if messagebox.askyesno("确认", "是否确定清空所有按键记录？"):
            self.key_pos_records.clear()
            self._update_record_tree()

    def _update_window_tree(self, windows_info: List[DiabloWindowInfo]):
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


# ===================== 程序入口 =====================
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = DiabloWindowMonitor(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("程序启动失败", f"程序启动异常：{str(e)}")
        traceback.print_exc()
