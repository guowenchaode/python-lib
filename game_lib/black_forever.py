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

# ===================== 全局配置（集中管理） =====================
CONFIG = {
    "pyautogui_pause": 0.1,
    "pyautogui_failsafe": False,
    "monitor_window_interval": 0.5,
    "monitor_mouse_interval": 0.01,
    "default_loop_interval": 15,
    "bubble_alpha": 0.5,
    "bubble_font": ("微软雅黑", 10, "bold"),
    "title_font": ("微软雅黑", 14, "bold"),
    "normal_font": ("微软雅黑", 10),
    "highlight_bubble_color": "#ff4444",
    "normal_bubble_color": "#4444ff",
    "main_window_tag_color": "#e8f4f8",
}

# 设置pyautogui全局参数
pyautogui.FAILSAFE = CONFIG["pyautogui_failsafe"]
pyautogui.PAUSE = CONFIG["pyautogui_pause"]

# ===================== 数据类（结构化数据） =====================
@dataclass
class ScriptCommand:
    """脚本命令数据类 - 替代字典，提升类型安全"""
    key: str
    x: float
    y: float
    status: str = "未执行"
    source: str = "用户导入"

@dataclass
class DiabloWindowInfo:
    """暗黑窗口信息数据类"""
    window_obj: gw.Window
    title: str
    pos: str
    size: str
    status: str
    is_active: bool

# ===================== 气泡窗口类（优化） =====================
class BubbleWindow:
    """气泡提示窗口类 - 优化封装和性能"""
    def __init__(self, parent: tk.Tk, x: int, y: int, index: int, key: str, is_highlight: bool = False):
        self.window = tk.Toplevel(parent)
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        self.window.attributes("-alpha", CONFIG["bubble_alpha"])

        # 样式优化：使用配置文件统一管理
        bg_color = CONFIG["highlight_bubble_color"] if is_highlight else CONFIG["normal_bubble_color"]
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

        # 位置校准：避免超出屏幕
        screen_width = parent.winfo_screenwidth()
        screen_height = parent.winfo_screenheight()
        final_x = min(x + 10, screen_width - 100)  # 预留气泡宽度
        final_y = min(y, screen_height - 50)       # 预留气泡高度
        self.window.geometry(f"+{final_x}+{final_y}")

    def destroy(self):
        """安全销毁气泡窗口"""
        try:
            self.window.destroy()
        except Exception:
            pass

# ===================== 主监控类（核心优化） =====================
class DiabloWindowMonitor:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("暗黑破坏神窗口监控工具 | 千分比坐标版")
        self.root.geometry("1180x780")
        self.root.resizable(False, False)
        
        # 核心状态变量（类型标注+初始值规范化）
        self.current_diablo_window: Optional[gw.Window] = None
        self.is_diablo_foreground: bool = False
        self.key_pos_records: Dict[str, Tuple[float, float]] = {}
        self.is_tool_foreground: bool = True
        self.main_diablo_window: Optional[gw.Window] = None
        self.main_window_title: str = ""
        self.main_window_size: Tuple[int, int] = (0, 0)
        
        # 脚本执行变量
        self.script_commands: List[ScriptCommand] = []
        self.script_running: bool = False
        self.script_paused: bool = False
        self.script_thread: Optional[threading.Thread] = None
        self.script_current_index: int = 0
        self.script_loop: bool = True
        self.loop_interval: int = CONFIG["default_loop_interval"]
        self.stop_on_background: bool = True
        self.script_file_path: str = ""
        
        # 气泡相关变量
        self.bubble_windows: List[BubbleWindow] = []
        self.highlighted_bubble: Optional[BubbleWindow] = None
        self.bubbles_visible: bool = False
        
        # 线程控制（使用Event替代布尔值，更安全）
        self.monitor_event = threading.Event()
        self.monitor_event.set()  # 初始为运行状态
        
        # 初始化UI
        self._init_ui()
        
        # 绑定事件（优化事件处理逻辑）
        self._bind_events()
        
        # 启动监控线程（优化线程创建）
        self._start_monitor_threads()

    def _init_ui(self):
        """初始化UI - 模块化重构，提升可读性"""
        # 1. 标题区域
        self._init_title_frame()
        
        # 2. 鼠标位置区域
        self._init_mouse_frame()
        
        # 3. 状态标签
        self._init_status_label()
        
        # 4. 暗黑窗口列表
        self._init_window_tree_frame()
        
        # 5. 按键记录区域
        self._init_record_frame()
        
        # 6. 脚本执行区域
        self._init_script_frame()
        
        # 7. 退出按钮
        self._init_exit_frame()

    def _init_title_frame(self):
        """标题区域 - 优化布局和提示"""
        title_frame = ttk.Frame(self.root)
        title_frame.pack(pady=10)

        title_label = ttk.Label(
            title_frame,
            text="暗黑破坏神窗口监控工具 | 千分比坐标版 | 停止显全部气泡/运行显下一个命令 | 表格自动滚动 | 执行结束自动截图",
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
        """鼠标位置区域 - 优化显示格式"""
        mouse_frame = ttk.LabelFrame(
            self.root, text="鼠标位置信息（主程序千分比）", padding=10
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
        """状态标签 - 简化初始化"""
        self.status_label = ttk.Label(
            self.root, text="暗黑破坏神状态：后台运行", font=("微软雅黑", 11, "bold")
        )
        self.status_label.pack(pady=5)

    def _init_window_tree_frame(self):
        """暗黑窗口列表 - 优化样式和性能"""
        window_frame = ttk.LabelFrame(
            self.root, text="暗黑窗口信息（双击选中主程序）", padding=10
        )
        window_frame.pack(fill=tk.X, padx=20, pady=5)

        # 样式优化：提前定义
        window_tree_style = ttk.Style()
        window_tree_style.configure("Treeview", font=CONFIG["normal_font"])
        window_tree_style.configure("Treeview.Heading", font=("微软雅黑", 10, "bold"))
        window_tree_style.configure("main.Treeview", background=CONFIG["main_window_tag_color"])

        self.window_tree = ttk.Treeview(
            window_frame,
            columns=("标题", "位置", "大小", "状态"),
            show="headings",
            height=3,
        )
        # 列配置（提取为常量，便于修改）
        columns_config = {
            "标题": 300,
            "位置": 120,
            "大小": 120,
            "状态": 100
        }
        for col, width in columns_config.items():
            self.window_tree.heading(col, text=col)
            self.window_tree.column(col, width=width)

        self.window_tree.pack(fill=tk.X)
        self.window_tree.bind("<Double-1>", self._on_window_double_click)

    def _init_record_frame(self):
        """按键记录区域 - 模块化重构"""
        record_frame = ttk.LabelFrame(self.root, text="按键-千分比坐标记录", padding=10)
        record_frame.pack(fill=tk.X, padx=20, pady=5)

        # 记录表格
        record_tree_style = ttk.Style()
        record_tree_style.configure("Record.Treeview", font=CONFIG["normal_font"])
        record_tree_style.configure("Record.Treeview.Heading", font=("微软雅黑", 10, "bold"))

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

        # 按钮区域
        record_btn_frame = ttk.Frame(record_frame)
        record_btn_frame.pack(side=tk.RIGHT, padx=10)

        self.export_btn = ttk.Button(record_btn_frame, text="导出记录(CSV)", command=self._export_records)
        self.import_btn = ttk.Button(record_btn_frame, text="导入记录(CSV)", command=self._import_records)
        self.clear_btn = ttk.Button(record_btn_frame, text="清空记录", command=self._clear_records)
        
        for btn in [self.export_btn, self.import_btn, self.clear_btn]:
            btn.pack(pady=5, fill=tk.X)

    def _init_script_frame(self):
        """脚本执行区域 - 优化控件布局和状态管理"""
        script_frame = ttk.LabelFrame(
            self.root, text="脚本执行模块（千分比坐标）", padding=10
        )
        script_frame.pack(fill=tk.BOTH, padx=20, pady=5, expand=True)

        # 脚本控制按钮区域
        script_ctrl_frame = ttk.Frame(script_frame)
        script_ctrl_frame.pack(fill=tk.X, pady=5)

        # 主程序名称显示
        self.script_main_window_label = ttk.Label(
            script_ctrl_frame,
            text="主程序：未选中",
            font=("微软雅黑", 10, "bold"),
            foreground="red",
        )
        self.script_main_window_label.pack(side=tk.LEFT, padx=5)

        # 核心控制按钮
        self.load_script_btn = ttk.Button(script_ctrl_frame, text="加载CSV脚本", command=self._load_script)
        self.start_script_btn = ttk.Button(script_ctrl_frame, text="启动脚本", command=self._start_script, state=tk.DISABLED)
        self.pause_script_btn = ttk.Button(script_ctrl_frame, text="暂停脚本", command=self._pause_script, state=tk.DISABLED)
        self.stop_script_btn = ttk.Button(script_ctrl_frame, text="停止脚本", command=self._stop_script, state=tk.DISABLED)
        self.toggle_bubble_btn = ttk.Button(script_ctrl_frame, text="隐藏气泡", command=self._toggle_bubbles_visibility)
        
        for btn in [self.load_script_btn, self.start_script_btn, self.pause_script_btn, self.stop_script_btn, self.toggle_bubble_btn]:
            btn.pack(side=tk.LEFT, padx=5)

        # 自动停止复选框
        self.stop_on_background_var = tk.BooleanVar(value=self.stop_on_background)
        self.stop_on_background_check = ttk.Checkbutton(
            script_ctrl_frame,
            text="主程序后台时自动停止脚本",
            variable=self.stop_on_background_var,
            command=lambda: setattr(self, "stop_on_background", self.stop_on_background_var.get())
        )
        self.stop_on_background_check.pack(side=tk.LEFT, padx=10)

        # 循环执行配置
        self.loop_var = tk.BooleanVar(value=True)
        self.loop_check = ttk.Checkbutton(
            script_ctrl_frame,
            text="循环执行",
            variable=self.loop_var,
            command=lambda: setattr(self, "script_loop", self.loop_var.get())
        )
        self.loop_check.pack(side=tk.LEFT, padx=10)

        # 循环间隔输入
        ttk.Label(script_ctrl_frame, text="循环间隔(秒)：", font=CONFIG["normal_font"]).pack(side=tk.LEFT, padx=5)
        self.interval_entry = ttk.Entry(script_ctrl_frame, width=8, font=CONFIG["normal_font"])
        self.interval_entry.insert(0, str(self.loop_interval))
        self.interval_entry.pack(side=tk.LEFT, padx=5)
        
        self.set_interval_btn = ttk.Button(script_ctrl_frame, text="确认", command=self._set_loop_interval)
        self.set_interval_btn.pack(side=tk.LEFT, padx=5)

        # 脚本状态显示
        self.script_status_label = ttk.Label(
            script_ctrl_frame, text="脚本状态：未加载", font=CONFIG["normal_font"]
        )
        self.script_status_label.pack(side=tk.RIGHT, padx=10)

        # 脚本表格
        self.script_tree = ttk.Treeview(
            script_frame,
            columns=("序号", "按键", "千分比坐标", "状态", "命令来源"),
            show="headings",
            height=8,
        )
        # 表格列配置
        script_columns = {
            "序号": 60,
            "按键": 80,
            "千分比坐标": 200,
            "状态": 100,
            "命令来源": 120
        }
        for col, width in script_columns.items():
            self.script_tree.heading(col, text=col)
            self.script_tree.column(col, width=width)

        # 滚动条
        script_scroll = ttk.Scrollbar(script_frame, orient=tk.VERTICAL, command=self.script_tree.yview)
        self.script_tree.configure(yscrollcommand=script_scroll.set)
        self.script_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        script_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def _init_exit_frame(self):
        """退出按钮区域 - 简化"""
        exit_frame = ttk.Frame(self.root)
        exit_frame.pack(pady=10)

        self.stop_btn = ttk.Button(exit_frame, text="停止监控", command=self._stop_monitor)
        self.stop_btn.pack()

    def _bind_events(self):
        """事件绑定 - 集中管理，优化逻辑"""
        # 按键监听
        self.root.bind("<Key>", self._on_key_press)
        # 焦点监听
        self.root.bind("<FocusIn>", lambda e: setattr(self, "is_tool_foreground", True))
        self.root.bind("<FocusOut>", lambda e: setattr(self, "is_tool_foreground", False))
        # 气泡快捷键
        self.root.bind("<F12>", self._toggle_bubbles_visibility)
        # 窗口关闭事件（优雅退出）
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)

    def _start_monitor_threads(self):
        """启动监控线程 - 优化线程创建和守护属性"""
        # 窗口监控线程
        self.window_monitor_thread = threading.Thread(
            target=self._monitor_windows, 
            daemon=True,
            name="WindowMonitorThread"
        )
        # 鼠标监控线程
        self.mouse_monitor_thread = threading.Thread(
            target=self._monitor_mouse, 
            daemon=True,
            name="MouseMonitorThread"
        )
        
        self.window_monitor_thread.start()
        self.mouse_monitor_thread.start()

    # ===================== 核心功能优化 =====================
    def _monitor_windows(self):
        """窗口监控 - 优化性能，减少UI刷新频率"""
        last_update_time = 0
        while self.monitor_event.is_set():
            current_time = time.time()
            # 控制刷新频率（避免频繁更新UI）
            if current_time - last_update_time < CONFIG["monitor_window_interval"]:
                time.sleep(0.05)
                continue
            
            try:
                windows_info = self._get_diablo_windows()
                # 使用after_idle减少UI阻塞
                self.root.after_idle(self._update_window_tree, windows_info)
                self.root.after_idle(self._update_status_label)

                # 自动停止脚本检查
                if self.script_running and self.stop_on_background and self.main_diablo_window:
                    if not self._check_main_window_foreground():
                        self.root.after_idle(self._stop_script)

                # 气泡更新
                if self.bubbles_visible and self.script_commands and self.main_diablo_window:
                    self.root.after_idle(self._create_bubbles_by_script_status)
                
                last_update_time = current_time
            except Exception as e:
                print(f"窗口监控异常：{e}")
                time.sleep(CONFIG["monitor_window_interval"])

    def _monitor_mouse(self):
        """鼠标监控 - 减少计算量，优化千分比计算"""
        last_mouse_pos = (0, 0)
        while self.monitor_event.is_set():
            try:
                mouse_x, mouse_y = pyautogui.position()
                # 仅当鼠标位置变化时才更新（减少计算）
                if (mouse_x, mouse_y) == last_mouse_pos:
                    time.sleep(CONFIG["monitor_mouse_interval"])
                    continue
                
                rel_x_permil, rel_y_permil = "--", "--"
                self.current_diablo_window = None

                if self.main_diablo_window and self.main_window_size != (0, 0):
                    # 鼠标在主窗口内才计算千分比
                    win_left = self.main_diablo_window.left
                    win_top = self.main_diablo_window.top
                    win_w, win_h = self.main_window_size
                    
                    if win_left <= mouse_x <= win_left + win_w and win_top <= mouse_y <= win_top + win_h:
                        rel_x_permil = round((mouse_x - win_left) / win_w, 3)
                        rel_y_permil = round((mouse_y - win_top) / win_h, 3)
                        self.current_diablo_window = self.main_diablo_window

                self.root.after_idle(self._update_mouse_info, mouse_x, mouse_y, rel_x_permil, rel_y_permil)
                last_mouse_pos = (mouse_x, mouse_y)
                time.sleep(CONFIG["monitor_mouse_interval"])
            except Exception as e:
                print(f"鼠标监控异常：{e}")
                time.sleep(CONFIG["monitor_mouse_interval"])

    def _get_diablo_windows(self) -> List[DiabloWindowInfo]:
        """获取暗黑窗口信息 - 优化异常处理，使用数据类"""
        diablo_windows = []
        try:
            foreground_window = gw.getActiveWindow()
            foreground_title = foreground_window.title.strip() if foreground_window else ""
            self.is_diablo_foreground = False

            for window in gw.getAllWindows():
                window_title = window.title.strip()
                # 过滤有效窗口
                if "暗黑破坏神" in window_title and window.width > 0 and window.height > 0:
                    is_active = window.title == foreground_title
                    if is_active:
                        self.is_diablo_foreground = True
                    
                    # 封装为数据类
                    win_info = DiabloWindowInfo(
                        window_obj=window,
                        title=window_title,
                        pos=f"({window.left}, {window.top})",
                        size=f"{window.width}x{window.height}",
                        status="前台" if is_active else "后台",
                        is_active=is_active
                    )
                    diablo_windows.append(win_info)
        except Exception as e:
            self.root.after_idle(messagebox.showerror, "错误", f"获取窗口信息失败：{str(e)}")
        return diablo_windows

    def _permil_to_absolute(self, x_permil: float, y_permil: float) -> Tuple[int, int]:
        """千分比转绝对坐标 - 优化边界检查"""
        if not self.main_diablo_window or self.main_window_size == (0, 0):
            return (0, 0)

        win_left = self.main_diablo_window.left
        win_top = self.main_diablo_window.top
        win_w, win_h = self.main_window_size

        # 计算并校准坐标（避免负数和超出屏幕）
        abs_x = max(0, win_left + int(win_w * x_permil))
        abs_y = max(0, win_top + int(win_h * y_permil))
        
        return (abs_x, abs_y)

    def _load_script(self):
        """加载脚本 - 优化错误处理，支持大文件"""
        if not self.main_diablo_window:
            messagebox.warning("提示", "请先双击选中主程序窗口！")
            return

        file_path = filedialog.askopenfilename(
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")],
            title="加载脚本文件"
        )
        if not file_path:
            return

        self.script_file_path = file_path
        self.script_commands.clear()
        self.script_current_index = 0

        try:
            with open(file_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader)  # 跳过表头
                
                # 批量读取，减少UI更新次数
                commands = []
                for row_idx, row in enumerate(reader, 1):
                    if len(row) != 3 or len(row[0]) != 1:
                        continue
                    
                    try:
                        # 兼容千分比格式（0-1000 或 0.000-1.000）
                        x_permil = float(row[1].replace("‰", ""))
                        y_permil = float(row[2].replace("‰", ""))
                        
                        if x_permil > 1:
                            x_permil /= 1000
                        if y_permil > 1:
                            y_permil /= 1000
                        
                        # 边界检查
                        x_permil = max(0.0, min(1.0, round(x_permil, 3)))
                        y_permil = max(0.0, min(1.0, round(y_permil, 3)))
                        
                        commands.append(ScriptCommand(
                            key=row[0],
                            x=x_permil,
                            y=y_permil
                        ))
                    except ValueError:
                        messagebox.warning("提示", f"第{row_idx}行数据格式错误，已跳过")
                        continue
                
                self.script_commands = commands
                # 添加倒计时命令
                self._add_countdown_commands()
                # 更新脚本表格
                self._update_script_tree()
                # 启用启动按钮
                self.start_script_btn.config(state=tk.NORMAL)
                self.script_status_label.config(text=f"脚本状态：已加载（{len(commands)}条命令）")
                
        except Exception as e:
            messagebox.showerror("错误", f"加载脚本失败：{str(e)}")
            self.script_status_label.config(text="脚本状态：加载失败")

    def _update_script_tree(self):
        """更新脚本表格 - 优化批量更新"""
        # 清空表格（批量删除，减少UI操作）
        for item in self.script_tree.get_children():
            self.script_tree.delete(item)
        
        # 批量插入数据
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
                    cmd.source
                )
            )

    def _capture_main_window_screenshot(self) -> Optional[str]:
        """截图功能 - 优化路径处理和异常捕获"""
        if not self.main_diablo_window or not self.script_file_path:
            return None

        try:
            # 创建缓存目录（兼容不同系统）
            script_dir = os.path.dirname(os.path.abspath(self.script_file_path))
            cache_dir = os.path.join(script_dir, "cache")
            os.makedirs(cache_dir, exist_ok=True)

            # 生成文件名（避免重复）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # 精确到毫秒
            screenshot_filename = f"script_screenshot_{timestamp}.png"
            screenshot_path = os.path.join(cache_dir, screenshot_filename)

            # 窗口截图（优化坐标获取）
            win = self.main_diablo_window
            region = (win.left, win.top, win.width, win.height)
            # 检查区域有效性
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
            self.root.after_idle(messagebox.warning, "截图提示", error_msg)
            return None

    # ===================== 辅助功能优化 =====================
    def _on_window_double_click(self, event):
        """双击选中主程序 - 优化窗口匹配逻辑"""
        item = self.window_tree.identify_row(event.y)
        if not item:
            return
        
        values = self.window_tree.item(item, "values")
        if not values or values[0] == "未检测到暗黑破坏神窗口":
            return
        
        # 精准匹配窗口
        diablo_windows = self._get_diablo_windows()
        target_title = values[0]
        self.main_diablo_window = next(
            (win.window_obj for win in diablo_windows if win.title == target_title),
            None
        )
        
        if self.main_diablo_window:
            self._update_main_window_display()
            # 高亮选中行
            for row in self.window_tree.get_children():
                self.window_tree.item(row, tags=("normal",))
            self.window_tree.item(item, tags=("main",))
            self._create_bubbles_by_script_status()

    def _toggle_bubbles_visibility(self, event=None):
        """气泡显示切换 - 优化销毁逻辑"""
        self.bubbles_visible = not self.bubbles_visible
        self.toggle_bubble_btn.config(text="隐藏气泡" if self.bubbles_visible else "显示气泡")
        
        if self.bubbles_visible:
            self._create_bubbles_by_script_status()
        else:
            self._destroy_all_bubbles()

    def _destroy_all_bubbles(self):
        """销毁所有气泡 - 安全遍历"""
        # 销毁普通气泡
        for bubble in self.bubble_windows:
            bubble.destroy()
        self.bubble_windows.clear()
        
        # 销毁高亮气泡
        if self.highlighted_bubble:
            self.highlighted_bubble.destroy()
            self.highlighted_bubble = None

    def _create_bubbles_by_script_status(self):
        """创建气泡 - 优化条件判断和性能"""
        if not self.bubbles_visible or not self.script_commands or not self.main_diablo_window or self.main_window_size == (0, 0):
            return

        self._destroy_all_bubbles()

        if self.script_running:
            # 运行中：显示下一个有效命令
            next_idx = self.script_current_index
            while next_idx < len(self.script_commands):
                cmd = self.script_commands[next_idx]
                if cmd.source != "系统倒计时":
                    abs_x, abs_y = self._permil_to_absolute(cmd.x, cmd.y)
                    self.highlighted_bubble = BubbleWindow(
                        self.root, abs_x, abs_y, next_idx + 1, cmd.key, is_highlight=True
                    )
                    break
                next_idx += 1
        else:
            # 停止中：显示所有有效命令（批量创建）
            bubbles = []
            for idx, cmd in enumerate(self.script_commands):
                if cmd.source == "系统倒计时":
                    continue
                abs_x, abs_y = self._permil_to_absolute(cmd.x, cmd.y)
                bubble = BubbleWindow(self.root, abs_x, abs_y, idx + 1, cmd.key)
                bubbles.append(bubble)
            self.bubble_windows = bubbles

    def _set_loop_interval(self):
        """设置循环间隔 - 优化输入验证"""
        try:
            interval = float(self.interval_entry.get())
            if interval < 0:
                raise ValueError("间隔时间不能为负数")
            if interval > 3600:  # 限制最大间隔1小时
                raise ValueError("间隔时间不能超过3600秒")
            
            self.loop_interval = interval
            messagebox.showinfo("提示", f"循环间隔已设置为：{interval}秒")
        except ValueError as e:
            # 恢复原值并提示
            self.interval_entry.delete(0, tk.END)
            self.interval_entry.insert(0, str(self.loop_interval))
            messagebox.warning("提示", f"输入错误：{str(e)}")

    def _add_countdown_commands(self):
        """添加倒计时命令 - 优化逻辑"""
        if not self.script_loop or self.loop_interval <= 0:
            return
        
        # 清空原有倒计时命令
        self.script_commands = [cmd for cmd in self.script_commands if cmd.source != "系统倒计时"]
        
        # 添加新的倒计时命令
        for i in range(int(self.loop_interval), 0, -1):
            self.script_commands.append(ScriptCommand(
                key=f"倒计时{i}秒",
                x=0.0,
                y=0.0,
                status="未执行",
                source="系统倒计时"
            ))
        self.script_commands.append(ScriptCommand(
            key="倒计时结束",
            x=0.0,
            y=0.0,
            status="未执行",
            source="系统倒计时"
        ))

    # ===================== 脚本执行控制 =====================
    def _start_script(self):
        """启动脚本 - 优化线程创建和状态管理"""
        if self.script_running or not self.script_commands:
            return
        
        self.script_running = True
        self.script_paused = False
        # 更新按钮状态
        self.start_script_btn.config(state=tk.DISABLED)
        self.pause_script_btn.config(state=tk.NORMAL)
        self.stop_script_btn.config(state=tk.NORMAL)
        self.script_status_label.config(text="脚本状态：运行中")
        
        # 启动脚本线程
        self.script_thread = threading.Thread(
            target=self._run_script,
            daemon=True,
            name="ScriptExecutionThread"
        )
        self.script_thread.start()

    def _pause_script(self):
        """暂停脚本 - 优化状态切换"""
        self.script_paused = not self.script_paused
        if self.script_paused:
            self.pause_script_btn.config(text="继续脚本")
            self.script_status_label.config(text="脚本状态：暂停中")
        else:
            self.pause_script_btn.config(text="暂停脚本")
            self.script_status_label.config(text="脚本状态：运行中")

    def _stop_script(self):
        """停止脚本 - 优雅终止，清理状态"""
        self.script_running = False
        self.script_paused = False
        # 更新按钮状态
        self.start_script_btn.config(state=tk.NORMAL)
        self.pause_script_btn.config(state=tk.DISABLED)
        self.stop_script_btn.config(state=tk.DISABLED)
        # 重置执行位置
        self.script_current_index = 0
        self.script_status_label.config(text="脚本状态：已停止")
        # 更新脚本表格状态
        for cmd in self.script_commands:
            cmd.status = "未执行"
        self._update_script_tree()
        # 销毁气泡
        self._destroy_all_bubbles()

    def _run_script(self):
        """脚本执行核心逻辑 - 优化异常处理和流程控制"""
        try:
            while self.script_running and self.monitor_event.is_set():
                # 暂停检查
                while self.script_paused and self.script_running:
                    time.sleep(0.5)
                
                # 边界检查
                if self.script_current_index >= len(self.script_commands):
                    # 执行完成，截图
                    self.root.after_idle(self._capture_main_window_screenshot)
                    
                    if self.script_loop:
                        # 循环执行：重置索引
                        self.script_current_index = 0
                        self.script_status_label.config(text="脚本状态：循环等待中")
                        time.sleep(self.loop_interval)
                    else:
                        # 单次执行：停止脚本
                        self.root.after_idle(self._stop_script)
                        break
                
                # 执行当前命令
                cmd = self.script_commands[self.script_current_index]
                if cmd.source != "系统倒计时":
                    # 转换坐标并执行点击
                    abs_x, abs_y = self._permil_to_absolute(cmd.x, cmd.y)
                    # 确保主程序在前台
                    if self._check_main_window_foreground():
                        pyautogui.click(abs_x, abs_y)
                        pyautogui.press(cmd.key)
                        cmd.status = "已执行"
                    else:
                        cmd.status = "主程序后台，跳过"
                else:
                    # 倒计时命令：仅更新状态
                    cmd.status = "已执行"
                    self.root.after_idle(self.script_status_label.config, {"text": f"脚本状态：{cmd.key}"})
                    time.sleep(1)  # 倒计时延迟
                
                # 更新UI和索引
                self.root.after_idle(self._update_script_tree)
                self.root.after_idle(self._scroll_to_current_command)
                self.script_current_index += 1
                
                # 动态更新气泡
                if self.bubbles_visible:
                    self.root.after_idle(self._create_bubbles_by_script_status)
                
                time.sleep(pyautogui.PAUSE)
        
        except Exception as e:
            error_msg = f"脚本执行异常：{str(e)}"
            print(error_msg)
            self.root.after_idle(messagebox.showerror, "脚本错误", error_msg)
            self.root.after_idle(self._stop_script)

    # ===================== 退出和清理 =====================
    def _stop_monitor(self):
        """停止监控 - 优雅退出"""
        if messagebox.askyesno("确认", "是否确定停止监控并退出？"):
            self._stop_monitor_threads()
            self.root.quit()
            self.root.destroy()

    def _stop_monitor_threads(self):
        """停止所有监控线程"""
        self.monitor_event.clear()
        # 等待线程结束（超时保护）
        if self.window_monitor_thread.is_alive():
            self.window_monitor_thread.join(timeout=1)
        if self.mouse_monitor_thread.is_alive():
            self.mouse_monitor_thread.join(timeout=1)

    def _on_window_close(self):
        """窗口关闭事件 - 确保资源释放"""
        self._stop_monitor_threads()
        self.root.quit()

    # ===================== 原有功能保留（略作优化） =====================
    def _check_main_window_foreground(self) -> bool:
        if not self.main_diablo_window:
            return False
        try:
            foreground_window = gw.getActiveWindow()
            return foreground_window and foreground_window.title.strip() == self.main_diablo_window.title.strip()
        except Exception:
            return False

    def _update_main_window_display(self):
        if self.main_diablo_window:
            self.main_window_title = self.main_diablo_window.title.strip()
            self.main_window_size = (self.main_diablo_window.width, self.main_diablo_window.height)
            title_short = self.main_window_title[:20] + "..." if len(self.main_window_title) > 20 else self.main_window_title
            self.main_window_label.config(text=f"当前主程序：{title_short} (大小：{self.main_window_size[0]}x{self.main_window_size[1]})")
            self.script_main_window_label.config(text=f"主程序：{title_short}", foreground="green")
        else:
            self.main_window_title = ""
            self.main_window_size = (0, 0)
            self.main_window_label.config(text="当前主程序：未选中")
            self.script_main_window_label.config(text="主程序：未选中", foreground="red")

    def _on_key_press(self, event):
        if not self.is_tool_foreground or not self.main_diablo_window or self.main_window_size == (0, 0) or self.script_running:
            return
        
        key = event.char
        if not key or len(key) != 1:
            return
        
        mouse_x, mouse_y = pyautogui.position()
        win_left = self.main_diablo_window.left
        win_top = self.main_diablo_window.top
        win_w, win_h = self.main_window_size
        
        # 计算千分比（边界检查）
        x_permil = round((mouse_x - win_left) / win_w, 3) if win_w > 0 else 0.0
        y_permil = round((mouse_y - win_top) / win_h, 3) if win_h > 0 else 0.0
        x_permil = max(0.0, min(1.0, x_permil))
        y_permil = max(0.0, min(1.0, y_permil))
        
        self.key_pos_records[key] = (x_permil, y_permil)
        self.root.after_idle(self._update_record_tree)

    def _update_window_tree(self, windows_info: List[DiabloWindowInfo]):
        for item in self.window_tree.get_children():
            self.window_tree.delete(item)

        if not windows_info:
            item = self.window_tree.insert("", tk.END, values=("未检测到暗黑破坏神窗口", "", "", ""))
            self.window_tree.item(item, tags=("inactive",))
        else:
            for win in windows_info:
                item = self.window_tree.insert("", tk.END, values=(win.title, win.pos, win.size, win.status))
                if self.main_diablo_window and win.window_obj.title == self.main_diablo_window.title:
                    self.window_tree.item(item, tags=("main",))
                else:
                    self.window_tree.item(item, tags=("active" if win.is_active else "inactive"))

        # 样式配置
        self.window_tree.tag_configure("active", foreground="red")
        self.window_tree.tag_configure("inactive", foreground="black")
        self.window_tree.tag_configure(
            "main",
            background=CONFIG["main_window_tag_color"],
            foreground="darkblue",
            font=("微软雅黑", 10, "bold"),
        )

    def _update_record_tree(self):
        for item in self.record_tree.get_children():
            self.record_tree.delete(item)

        for key, (x_permil, y_permil) in sorted(self.key_pos_records.items()):
            x_show = f"{x_permil*1000:.0f}‰"
            y_show = f"{y_permil*1000:.0f}‰"
            self.record_tree.insert("", tk.END, values=(key, f"{x_show}, {y_show}"))

    def _update_mouse_info(self, abs_x: int, abs_y: int, rel_x_permil: Any, rel_y_permil: Any):
        self.mouse_abs_label.config(text=f"绝对位置：(X: {abs_x}, Y: {abs_y})")
        if rel_x_permil != "--":
            rel_x_show = f"{rel_x_permil*1000:.0f}‰"
            rel_y_show = f"{rel_y_permil*1000:.0f}‰"
            self.mouse_rel_label.config(text=f"相对千分比：(X: {rel_x_show}, Y: {rel_y_show})")
        else:
            self.mouse_rel_label.config(text="相对千分比：(X: ---, Y: ---)")

    def _update_status_label(self):
        if self.is_diablo_foreground:
            self.status_label.config(text="暗黑破坏神状态：前台运行", foreground="red")
        else:
            self.status_label.config(text="暗黑破坏神状态：后台运行", foreground="black")

    def _export_records(self):
        if not self.key_pos_records:
            messagebox.warning("提示", "暂无记录可导出！")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")],
            title="导出按键记录"
        )
        if file_path:
            try:
                with open(file_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["按键", "X千分比", "Y千分比"])
                    for key, (x_permil, y_permil) in sorted(self.key_pos_records.items()):
                        writer.writerow([key, x_permil, y_permil])
                messagebox.showinfo("提示", "记录导出成功！")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败：{str(e)}")

    def _import_records(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")],
            title="导入按键记录"
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader)
                imported_count = 0
                self.key_pos_records.clear()
                
                for row_idx, row in enumerate(reader, 2):  # 从第二行开始计数
                    if len(row) != 3 or len(row[0]) != 1:
                        continue
                    
                    try:
                        x_permil = float(row[1].replace("‰", ""))
                        y_permil = float(row[2].replace("‰", ""))
                        if x_permil > 1:
                            x_permil /= 1000
                        if y_permil > 1:
                            y_permil /= 1000
                        
                        x_permil = max(0.0, min(1.0, round(x_permil, 3)))
                        y_permil = max(0.0, min(1.0, round(y_permil, 3)))
                        
                        self.key_pos_records[row[0]] = (x_permil, y_permil)
                        imported_count += 1
                    except ValueError:
                        messagebox.warning("提示", f"第{row_idx}行数据格式错误，已跳过")
                        continue
                
                self._update_record_tree()
                messagebox.showinfo("提示", f"成功导入{imported_count}条记录！")
        except Exception as e:
            messagebox.showerror("错误", f"导入失败：{str(e)}")

    def _clear_records(self):
        if not self.key_pos_records:
            return

        if messagebox.askyesno("确认", "是否确定清空所有按键-坐标记录？"):
            self.key_pos_records.clear()
            self._update_record_tree()
            messagebox.showinfo("提示", "记录已清空！")

    def _scroll_to_current_command(self):
        if 0 <= self.script_current_index < len(self.script_commands):
            children = self.script_tree.get_children()
            if children and self.script_current_index < len(children):
                target_item = children[self.script_current_index]
                self.script_tree.see(target_item)
                self.script_tree.selection_set(target_item)

# ===================== 主函数 =====================
def main():
    """主函数 - 程序入口，优化异常处理"""
    try:
        root = tk.Tk()
        app = DiabloWindowMonitor(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("致命错误", f"程序启动失败：{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()