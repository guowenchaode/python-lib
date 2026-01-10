import pygetwindow as gw
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import pyautogui
import csv
import os
import sys

# 设置pyautogui防故障（避免鼠标移到屏幕边缘报错）
pyautogui.FAILSAFE = False
# 设置pyautogui操作间隔（防止操作过快）
pyautogui.PAUSE = 0.1

class BubbleWindow:
    """气泡提示窗口类 - 显示执行序号+按键名字，避免遮挡点击坐标"""
    def __init__(self, parent, x, y, index, key, is_highlight=False):
        self.window = tk.Toplevel(parent)
        self.window.overrideredirect(True)  # 去掉窗口边框
        self.window.attributes('-topmost', True)  # 置顶
        # 调整透明度为50%
        self.window.attributes('-alpha', 0.5)
        
        # 气泡样式
        bg_color = "#ff4444" if is_highlight else "#4444ff"
        fg_color = "white"
        
        # 创建气泡内容：序号 + 按键
        label_text = f"[{index}] {key}"
        label = ttk.Label(
            self.window,
            text=label_text,
            font=("微软雅黑", 10, "bold"),
            background=bg_color,
            foreground=fg_color,
            padding=(8, 4)
        )
        label.pack()
        
        # 调整气泡位置：鼠标点击坐标的**右侧10px**，避免遮挡
        self.window.geometry(f"+{x+10}+{y}")
        
    def destroy(self):
        """销毁气泡"""
        self.window.destroy()

class DiabloWindowMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("暗黑破坏神窗口监控工具 | 千分比坐标版")
        self.root.geometry("1180x780")
        self.root.resizable(False, False)
        
        # 核心变量
        self.current_diablo_window = None  # 当前鼠标所在的暗黑窗口
        self.is_diablo_foreground = False  # 暗黑窗口是否前台
        self.key_pos_records = {}          # 按键-坐标记录字典 {按键: (x_permil, y_permil)} 千分比
        self.is_tool_foreground = True     # 工具是否前台
        self.main_diablo_window = None     # 选中的主程序窗口
        self.main_window_title = ""        # 主程序窗口标题
        self.main_window_size = (0, 0)     # 主程序窗口大小 (宽, 高)
        
        # 脚本执行相关变量
        self.script_commands = []          # CSV加载的脚本命令列表（存储千分比）
        self.script_running = False        # 脚本是否运行
        self.script_paused = False         # 脚本是否暂停
        self.script_thread = None          # 脚本执行线程
        self.script_current_index = 0      # 脚本当前执行位置
        self.script_loop = True            # 是否循环执行脚本
        self.loop_interval = 60             # 循环间隔时间（默认60秒）
        self.stop_on_background = False     # 主程序后台时自动停止脚本（默认开启）
        
        # 气泡相关变量
        self.bubble_windows = []           # 气泡窗口列表
        self.highlighted_bubble = None     # 当前高亮的气泡（下一个待执行命令）
        self.bubbles_visible = True        # 气泡是否显示
        
        # 初始化UI
        self._init_ui()
        
        # 绑定按键监听事件
        self.root.bind("<Key>", self._on_key_press)
        self.root.bind("<FocusIn>", lambda e: setattr(self, "is_tool_foreground", True))
        self.root.bind("<FocusOut>", lambda e: setattr(self, "is_tool_foreground", False))
        # 绑定气泡显示/隐藏快捷键（F12）
        self.root.bind("<F12>", self._toggle_bubbles_visibility)
        
        # 启动监控线程
        self.monitor_running = True
        self.window_monitor_thread = threading.Thread(target=self._monitor_windows, daemon=True)
        self.mouse_monitor_thread = threading.Thread(target=self._monitor_mouse, daemon=True)
        self.window_monitor_thread.start()
        self.mouse_monitor_thread.start()

    def _init_ui(self):
        """初始化界面布局"""
        # 1. 标题区域 + 气泡控制提示
        title_frame = ttk.Frame(self.root)
        title_frame.pack(pady=10)
        
        title_label = ttk.Label(
            title_frame, 
            text="暗黑破坏神窗口监控工具 | 千分比坐标版 | 停止显全部气泡/运行显下一个命令 | 表格自动滚动", 
            font=("微软雅黑", 14, "bold")
        )
        title_label.pack(side=tk.LEFT)
        
        bubble_hint_label = ttk.Label(
            title_frame,
            text="【F12/按钮】显示/隐藏气泡 | 双击暗黑窗口列表选中主程序 | 气泡：[序号] 按键 | 坐标：主程序千分比",
            font=("微软雅黑", 9),
            foreground="gray"
        )
        bubble_hint_label.pack(side=tk.LEFT, padx=20)
        
        # 2. 鼠标位置区域
        mouse_frame = ttk.LabelFrame(self.root, text="鼠标位置信息（主程序千分比）", padding=10)
        mouse_frame.pack(fill=tk.X, padx=20, pady=5)
        
        self.mouse_abs_label = ttk.Label(mouse_frame, text="绝对位置：(X: 0, Y: 0)", font=("微软雅黑", 10))
        self.mouse_abs_label.pack(side=tk.LEFT, padx=10)
        
        self.mouse_rel_label = ttk.Label(mouse_frame, text="相对千分比：(X: ---, Y: ---)", font=("微软雅黑", 10))
        self.mouse_rel_label.pack(side=tk.LEFT, padx=10)
        
        # 主程序提示
        self.main_window_label = ttk.Label(mouse_frame, text="当前主程序：未选中", font=("微软雅黑", 10), foreground="blue")
        self.main_window_label.pack(side=tk.LEFT, padx=20)
        
        # 3. 暗黑窗口状态区域
        self.status_label = ttk.Label(
            self.root,
            text="暗黑破坏神状态：后台运行",
            font=("微软雅黑", 11, "bold")
        )
        self.status_label.pack(pady=5)
        
        # 4. 暗黑窗口信息表格
        window_frame = ttk.LabelFrame(self.root, text="暗黑窗口信息（双击选中主程序）", padding=10)
        window_frame.pack(fill=tk.X, padx=20, pady=5)
        
        window_tree_style = ttk.Style()
        window_tree_style.configure("Treeview", font=("微软雅黑", 10))
        window_tree_style.configure("Treeview.Heading", font=("微软雅黑", 10, "bold"))
        window_tree_style.configure("main.Treeview", background="#e8f4f8")  # 主程序行高亮样式
        
        self.window_tree = ttk.Treeview(window_frame, columns=("标题", "位置", "大小", "状态"), show="headings", height=3)
        self.window_tree.heading("标题", text="窗口标题")
        self.window_tree.heading("位置", text="窗口位置(X,Y)")
        self.window_tree.heading("大小", text="窗口大小(宽x高)")
        self.window_tree.heading("状态", text="窗口状态")
        
        self.window_tree.column("标题", width=300)
        self.window_tree.column("位置", width=120)
        self.window_tree.column("大小", width=120)
        self.window_tree.column("状态", width=100)
        self.window_tree.pack(fill=tk.X)
        self.window_tree.bind("<Double-1>", self._on_window_double_click)
        
        # 5. 按键记录区域
        record_frame = ttk.LabelFrame(self.root, text="按键-千分比坐标记录", padding=10)
        record_frame.pack(fill=tk.X, padx=20, pady=5)
        
        # 记录表格
        record_tree_style = ttk.Style()
        record_tree_style.configure("Record.Treeview", font=("微软雅黑", 10))
        record_tree_style.configure("Record.Treeview.Heading", font=("微软雅黑", 10, "bold"))
        
        self.record_tree = ttk.Treeview(record_frame, columns=("按键", "千分比坐标"), show="headings", style="Record.Treeview", height=5)
        self.record_tree.heading("按键", text="按键")
        self.record_tree.heading("千分比坐标", text="主程序千分比坐标(X‰, Y‰)")
        self.record_tree.column("按键", width=100)
        self.record_tree.column("千分比坐标", width=200)
        self.record_tree.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 记录操作按钮
        record_btn_frame = ttk.Frame(record_frame)
        record_btn_frame.pack(side=tk.RIGHT, padx=10)
        
        self.export_btn = ttk.Button(record_btn_frame, text="导出记录(CSV)", command=self._export_records)
        self.export_btn.pack(pady=5, fill=tk.X)
        
        self.import_btn = ttk.Button(record_btn_frame, text="导入记录(CSV)", command=self._import_records)
        self.import_btn.pack(pady=5, fill=tk.X)
        
        self.clear_btn = ttk.Button(record_btn_frame, text="清空记录", command=self._clear_records)
        self.clear_btn.pack(pady=5, fill=tk.X)
        
        # 6. 脚本执行区域
        script_frame = ttk.LabelFrame(self.root, text="脚本执行模块（千分比坐标）", padding=10)
        script_frame.pack(fill=tk.BOTH, padx=20, pady=5, expand=True)
        
        # 脚本加载/控制按钮
        script_ctrl_frame = ttk.Frame(script_frame)
        script_ctrl_frame.pack(fill=tk.X, pady=5)
        
        # 显示主程序名称
        self.script_main_window_label = ttk.Label(
            script_ctrl_frame, 
            text="主程序：未选中", 
            font=("微软雅黑", 10, "bold"), 
            foreground="red"
        )
        self.script_main_window_label.pack(side=tk.LEFT, padx=5)
        
        self.load_script_btn = ttk.Button(script_ctrl_frame, text="加载CSV脚本", command=self._load_script)
        self.load_script_btn.pack(side=tk.LEFT, padx=5)
        
        self.start_script_btn = ttk.Button(script_ctrl_frame, text="启动脚本", command=self._start_script, state=tk.DISABLED)
        self.start_script_btn.pack(side=tk.LEFT, padx=5)
        
        self.pause_script_btn = ttk.Button(script_ctrl_frame, text="暂停脚本", command=self._pause_script, state=tk.DISABLED)
        self.pause_script_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_script_btn = ttk.Button(script_ctrl_frame, text="停止脚本", command=self._stop_script, state=tk.DISABLED)
        self.stop_script_btn.pack(side=tk.LEFT, padx=5)
        
        # 气泡显示/隐藏按钮
        self.toggle_bubble_btn = ttk.Button(script_ctrl_frame, text="隐藏气泡", command=self._toggle_bubbles_visibility)
        self.toggle_bubble_btn.pack(side=tk.LEFT, padx=5)
        
        # 主程序后台时自动停止脚本复选框
        self.stop_on_background_var = tk.BooleanVar(value=self.stop_on_background)
        self.stop_on_background_check = ttk.Checkbutton(
            script_ctrl_frame,
            text="主程序后台时自动停止脚本",
            variable=self.stop_on_background_var,
            command=self._toggle_stop_on_background
        )
        self.stop_on_background_check.pack(side=tk.LEFT, padx=10)
        
        # 循环执行相关控件
        self.loop_var = tk.BooleanVar(value=True)
        self.loop_check = ttk.Checkbutton(script_ctrl_frame, text="循环执行", variable=self.loop_var, command=self._toggle_loop)
        self.loop_check.pack(side=tk.LEFT, padx=10)
        
        # 循环间隔输入框
        ttk.Label(script_ctrl_frame, text="循环间隔(秒)：", font=("微软雅黑", 10)).pack(side=tk.LEFT, padx=5)
        self.interval_entry = ttk.Entry(script_ctrl_frame, width=8, font=("微软雅黑", 10))
        self.interval_entry.insert(0, str(self.loop_interval))
        self.interval_entry.pack(side=tk.LEFT, padx=5)
        # 确认间隔按钮
        self.set_interval_btn = ttk.Button(script_ctrl_frame, text="确认", command=self._set_loop_interval)
        self.set_interval_btn.pack(side=tk.LEFT, padx=5)
        
        # 脚本状态标签
        self.script_status_label = ttk.Label(script_ctrl_frame, text="脚本状态：未加载", font=("微软雅黑", 10))
        self.script_status_label.pack(side=tk.RIGHT, padx=10)
        
        # 脚本命令表格（存储千分比）
        self.script_tree = ttk.Treeview(script_frame, columns=("序号", "按键", "千分比坐标", "状态", "命令来源"), show="headings", height=8)
        self.script_tree.heading("序号", text="序号")
        self.script_tree.heading("按键", text="按键")
        self.script_tree.heading("千分比坐标", text="主程序千分比坐标(X‰, Y‰)")
        self.script_tree.heading("状态", text="执行状态")
        self.script_tree.heading("命令来源", text="命令来源")
        
        self.script_tree.column("序号", width=60)
        self.script_tree.column("按键", width=80)
        self.script_tree.column("千分比坐标", width=200)
        self.script_tree.column("状态", width=100)
        self.script_tree.column("命令来源", width=120)
        
        # 脚本表格滚动条
        script_scroll = ttk.Scrollbar(script_frame, orient=tk.VERTICAL, command=self.script_tree.yview)
        self.script_tree.configure(yscrollcommand=script_scroll.set)
        
        self.script_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        script_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 7. 退出按钮
        exit_frame = ttk.Frame(self.root)
        exit_frame.pack(pady=10)
        
        self.stop_btn = ttk.Button(exit_frame, text="停止监控", command=self._stop_monitor)
        self.stop_btn.pack()

    def _toggle_stop_on_background(self):
        """切换「主程序后台时自动停止脚本」的状态"""
        self.stop_on_background = self.stop_on_background_var.get()

    def _check_main_window_foreground(self):
        """检查主程序是否为前台窗口"""
        if not self.main_diablo_window:
            return False
        
        try:
            foreground_window = gw.getActiveWindow()
            if not foreground_window:
                return False
            return foreground_window.title.strip() == self.main_diablo_window.title.strip()
        except Exception:
            return False

    def _update_main_window_display(self):
        """更新主程序显示信息，记录主程序窗口大小"""
        if self.main_diablo_window:
            self.main_window_title = self.main_diablo_window.title.strip()
            # 记录主程序窗口大小（宽、高）
            self.main_window_size = (self.main_diablo_window.width, self.main_diablo_window.height)
            self.main_window_label.config(text=f"当前主程序：{self.main_window_title[:20]}... (大小：{self.main_window_size[0]}x{self.main_window_size[1]})")
            self.script_main_window_label.config(text=f"主程序：{self.main_window_title[:20]}...", foreground="green")
        else:
            self.main_window_title = ""
            self.main_window_size = (0, 0)
            self.main_window_label.config(text="当前主程序：未选中")
            self.script_main_window_label.config(text="主程序：未选中", foreground="red")

    def _on_window_double_click(self, event):
        """双击选中主程序窗口"""
        item = self.window_tree.identify_row(event.y)
        if not item:
            return
        values = self.window_tree.item(item, "values")
        if values and values[0] != "未检测到暗黑破坏神窗口":
            # 找到对应的窗口对象
            diablo_windows = self._get_diablo_windows()
            for win_info in diablo_windows:
                if win_info["title"] == values[0]:
                    self.main_diablo_window = win_info["window_obj"]
                    break
            
            # 更新显示和表格样式
            self._update_main_window_display()
            
            # 高亮选中的行
            for row in self.window_tree.get_children():
                self.window_tree.item(row, tags=("normal",))
            self.window_tree.item(item, tags=("main",))
            
            # 根据脚本状态创建气泡
            self._create_bubbles_by_script_status()

    def _toggle_bubbles_visibility(self, event=None):
        """切换气泡显示/隐藏"""
        self.bubbles_visible = not self.bubbles_visible
        
        # 更新按钮文本
        if self.bubbles_visible:
            self.toggle_bubble_btn.config(text="隐藏气泡")
            self._create_bubbles_by_script_status()
        else:
            self.toggle_bubble_btn.config(text="显示气泡")
            self._destroy_all_bubbles()

    def _destroy_all_bubbles(self):
        """销毁所有气泡（普通气泡+高亮气泡）"""
        for bubble in self.bubble_windows:
            bubble.destroy()
        self.bubble_windows = []
        if self.highlighted_bubble:
            self.highlighted_bubble.destroy()
            self.highlighted_bubble = None

    def _create_bubbles_by_script_status(self):
        """根据脚本运行状态创建气泡：停止显全部，运行显下一个"""
        if not self.bubbles_visible:
            return
        
        self._destroy_all_bubbles()
        if not self.script_commands or not self.main_diablo_window or self.main_window_size == (0, 0):
            return
        
        if self.script_running:
            # 脚本运行中：仅显示下一个待执行命令的高亮气泡
            next_idx = self.script_current_index
            # 跳过倒计时命令，找到下一个有效命令
            while next_idx < len(self.script_commands):
                cmd = self.script_commands[next_idx]
                if cmd["source"] != "系统倒计时":
                    abs_x, abs_y = self._permil_to_absolute(cmd["x"], cmd["y"])
                    self.highlighted_bubble = BubbleWindow(self.root, abs_x, abs_y, next_idx+1, cmd["key"], is_highlight=True)
                    break
                next_idx += 1
        else:
            # 脚本停止：显示所有命令的普通气泡
            for idx, cmd in enumerate(self.script_commands):
                if cmd["source"] == "系统倒计时":
                    continue
                abs_x, abs_y = self._permil_to_absolute(cmd["x"], cmd["y"])
                bubble = BubbleWindow(self.root, abs_x, abs_y, idx+1, cmd["key"])
                self.bubble_windows.append(bubble)

    def _scroll_to_current_command(self):
        """自动滚动脚本表格到当前执行的命令行"""
        if self.script_current_index < 0 or self.script_current_index >= len(self.script_commands):
            return
        
        # 获取表格中对应索引的行ID
        children = self.script_tree.get_children()
        if not children or self.script_current_index >= len(children):
            return
        
        target_item = children[self.script_current_index]
        # 滚动到目标行并高亮选中
        self.script_tree.see(target_item)
        self.script_tree.selection_set(target_item)

    def _permil_to_absolute(self, x_permil, y_permil):
        """将千分比坐标转换为绝对坐标（基于主程序）"""
        if not self.main_diablo_window or self.main_window_size == (0, 0):
            return (0, 0)
        
        # 计算像素坐标：千分比 * 窗口尺寸
        abs_x = self.main_diablo_window.left + (self.main_window_size[0] * x_permil)
        abs_x = max(0, abs_x)  # 防止坐标为负
        abs_y = self.main_diablo_window.top + (self.main_window_size[1] * y_permil)
        abs_y = max(0, abs_y)  # 防止坐标为负
        return (int(abs_x), int(abs_y))

    def _add_countdown_commands(self):
        """在脚本末尾添加系统倒计时命令"""
        # 倒计时5秒命令（仅显示，不执行鼠标/按键操作）
        for i in range(5, 0, -1):
            self.script_commands.append({
                "key": f"倒计时{i}秒",
                "x": 0.0,
                "y": 0.0,
                "status": "未执行",
                "source": "系统倒计时"
            })
        # 倒计时结束命令
        self.script_commands.append({
            "key": "倒计时结束",
            "x": 0.0,
            "y": 0.0,
            "status": "未执行",
            "source": "系统倒计时"
        })

    def _set_loop_interval(self):
        """设置循环间隔时间"""
        try:
            interval = float(self.interval_entry.get())
            if interval < 0:
                raise ValueError("间隔时间不能为负数")
            self.loop_interval = interval
        except ValueError as e:
            # 恢复原有值
            self.interval_entry.delete(0, tk.END)
            self.interval_entry.insert(0, str(self.loop_interval))

    def _get_diablo_windows(self):
        """获取所有暗黑窗口信息（含激活状态）"""
        diablo_windows = []
        try:
            foreground_window = gw.getActiveWindow()
            foreground_title = foreground_window.title.strip() if foreground_window else ""
            self.is_diablo_foreground = False
            
            for window in gw.getAllWindows():
                window_title = window.title.strip()
                if "暗黑破坏神" in window_title and window.width > 0 and window.height > 0:
                    is_active = window.title == foreground_title
                    if is_active:
                        self.is_diablo_foreground = True
                    pos = f"({window.left}, {window.top})"
                    size = f"{window.width}x{window.height}"
                    status = "前台" if is_active else "后台"
                    diablo_windows.append({
                        "window_obj": window,
                        "title": window_title,
                        "pos": pos,
                        "size": size,
                        "status": status,
                        "is_active": is_active
                    })
        except Exception as e:
            messagebox.showerror("错误", f"获取窗口信息失败：{str(e)}")
        return diablo_windows

    def _monitor_windows(self):
        """监控暗黑窗口状态（0.5秒刷新）"""
        while self.monitor_running:
            windows_info = self._get_diablo_windows()
            self.root.after(0, self._update_window_tree, windows_info)
            self.root.after(0, self._update_status_label)
            
            # 检查主程序是否前台，若开启自动停止功能则执行停止
            if self.script_running and self.stop_on_background and self.main_diablo_window:
                if not self._check_main_window_foreground():
                    self.root.after(0, self._stop_script)
            
            # 动态更新气泡（根据脚本状态）
            if self.bubbles_visible and self.script_commands and self.main_diablo_window:
                self.root.after(0, self._create_bubbles_by_script_status)
                
            time.sleep(0.5)

    def _monitor_mouse(self):
        """监控鼠标位置（基于主程序计算千分比坐标）"""
        while self.monitor_running:
            try:
                mouse_x, mouse_y = pyautogui.position()
                rel_x_permil, rel_y_permil = "--", "--"
                self.current_diablo_window = None
                
                # 仅基于主程序计算千分比坐标
                if self.main_diablo_window and self.main_window_size != (0, 0):
                    # 检查鼠标是否在主程序窗口内
                    if (self.main_diablo_window.left <= mouse_x <= self.main_diablo_window.left + self.main_window_size[0] and
                        self.main_diablo_window.top <= mouse_y <= self.main_diablo_window.top + self.main_window_size[1]):
                        # 计算千分比（保留3位小数，0.000-1.000）
                        rel_x_permil = round(((mouse_x - self.main_diablo_window.left) / self.main_window_size[0]), 3)
                        rel_y_permil = round(((mouse_y - self.main_diablo_window.top) / self.main_window_size[1]), 3)
                        self.current_diablo_window = self.main_diablo_window
                
                self.root.after(0, self._update_mouse_info, mouse_x, mouse_y, rel_x_permil, rel_y_permil)
                time.sleep(0.01)
            except Exception:
                time.sleep(0.01)

    def _on_key_press(self, event):
        """按键监听：基于主程序记录千分比坐标"""
        # 仅工具前台且有主程序时记录
        if not self.is_tool_foreground or not self.main_diablo_window or self.main_window_size == (0, 0) or self.script_running:
            return
        
        # 过滤功能键，只记录字母/数字/符号
        key = event.char
        if not key or len(key) != 1:
            return
        
        # 获取当前鼠标位置
        mouse_x, mouse_y = pyautogui.position()
        
        # 计算千分比坐标（保留3位小数，0.000-1.000）
        x_permil = round(((mouse_x - self.main_diablo_window.left) / self.main_window_size[0]), 3)
        y_permil = round(((mouse_y - self.main_diablo_window.top) / self.main_window_size[1]), 3)
        
        # 确保千分比在0.000-1.000范围内
        x_permil = max(0.000, min(1.000, x_permil))
        y_permil = max(0.000, min(1.000, y_permil))
        
        # 记录/覆盖按键坐标（存储千分比）
        self.key_pos_records[key] = (x_permil, y_permil)
        self.root.after(0, self._update_record_tree)

    def _update_window_tree(self, windows_info):
        """更新暗黑窗口表格（标记主程序行）"""
        for item in self.window_tree.get_children():
            self.window_tree.delete(item)
        
        if not windows_info:
            item = self.window_tree.insert("", tk.END, values=("未检测到暗黑破坏神窗口", "", "", ""))
            self.window_tree.item(item, tags=("inactive",))
        else:
            for win in windows_info:
                item = self.window_tree.insert("", tk.END, values=(win["title"], win["pos"], win["size"], win["status"]))
                # 标记主程序行
                if self.main_diablo_window and win["window_obj"].title == self.main_diablo_window.title:
                    self.window_tree.item(item, tags=("main",))
                else:
                    self.window_tree.item(item, tags=("active" if win["is_active"] else "inactive"))
        
        # 设置行样式
        self.window_tree.tag_configure("active", foreground="red")
        self.window_tree.tag_configure("inactive", foreground="black")
        self.window_tree.tag_configure("main", background="#e8f4f8", foreground="darkblue", font=("微软雅黑", 10, "bold"))

    def _update_record_tree(self):
        """更新按键-千分比坐标记录表格"""
        for item in self.record_tree.get_children():
            self.record_tree.delete(item)
        
        for key, (x_permil, y_permil) in sorted(self.key_pos_records.items()):
            # 显示为千分比格式（乘以1000，加‰符号）
            x_show = f"{x_permil*1000:.0f}‰"
            y_show = f"{y_permil*1000:.0f}‰"
            self.record_tree.insert("", tk.END, values=(key, f"{x_show}, {y_show}"))

    def _update_mouse_info(self, abs_x, abs_y, rel_x_permil, rel_y_permil):
        """更新鼠标位置显示（显示千分比）"""
        self.mouse_abs_label.config(text=f"绝对位置：(X: {abs_x}, Y: {abs_y})")
        # 显示为千分比格式
        if rel_x_permil != "--":
            rel_x_show = f"{rel_x_permil*1000:.0f}‰"
            rel_y_show = f"{rel_y_permil*1000:.0f}‰"
            self.mouse_rel_label.config(text=f"相对千分比：(X: {rel_x_show}, Y: {rel_y_show})")
        else:
            self.mouse_rel_label.config(text="相对千分比：(X: ---, Y: ---)")

    def _update_status_label(self):
        """更新暗黑窗口状态标签"""
        if self.is_diablo_foreground:
            self.status_label.config(text="暗黑破坏神状态：前台运行", foreground="red")
        else:
            self.status_label.config(text="暗黑破坏神状态：后台运行", foreground="black")

    def _export_records(self):
        """导出千分比坐标记录到CSV文件"""
        if not self.key_pos_records:
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
                    writer.writerow(["按键", "X千分比", "Y千分比"])  # 表头改为千分比
                    for key, (x_permil, y_permil) in sorted(self.key_pos_records.items()):
                        writer.writerow([key, x_permil, y_permil])
            except Exception as e:
                messagebox.showerror("错误", f"导出失败：{str(e)}")

    def _import_records(self):
        """从CSV文件导入千分比坐标记录"""
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")],
            title="导入按键记录"
        )
        if file_path:
            try:
                with open(file_path, "r", newline="", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    next(reader)  # 跳过表头
                    imported_count = 0
                    self.key_pos_records.clear()
                    for row in reader:
                        if len(row) == 3:
                            key, x_str, y_str = row
                            if len(key) == 1:
                                try:
                                    # 解析千分比数值（兼容带‰和不带‰的格式）
                                    x_permil = float(x_str.replace("‰", ""))
                                    y_permil = float(y_str.replace("‰", ""))
                                    # 兼容两种输入格式：0-1000 或 0.000-1.000
                                    if x_permil > 1:
                                        x_permil = x_permil / 1000
                                    if y_permil > 1:
                                        y_permil = y_permil / 1000
                                    # 确保千分比在0.000-1.000范围内
                                    x_permil = max(0.000, min(1.000, round(x_permil, 3)))
                                    y_permil = max(0.000, min(1.000, round(y_permil, 3)))
                                    self.key_pos_records[key] = (x_permil, y_permil)
                                    imported_count += 1
                                except ValueError:
                                    continue
                self._update_record_tree()
            except Exception as e:
                messagebox.showerror("错误", f"导入失败：{str(e)}")

    def _clear_records(self):
        """清空所有记录"""
        if not self.key_pos_records:
            return
        
        if messagebox.askyesno("确认", "是否确定清空所有按键-坐标记录？"):
            self.key_pos_records.clear()
            self._update_record_tree()

    def _load_script(self):
        """加载CSV脚本文件（千分比坐标）"""
        # 检查是否选中主程序
        if not self.main_diablo_window:
            messagebox.showwarning(
                "警告", "请先双击暗黑窗口列表选中主程序窗口后再加载脚本。"
            )
            return
            
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")],
            title="加载脚本文件"
        )
        if file_path:
            try:
                with open(file_path, "r", newline="", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    next(reader)  # 跳过表头
                    self.script_commands = []
                    for row in reader:
                        if len(row) == 3 and len(row[0]) == 1:
                            try:
                                # 解析千分比数值
                                x_permil = float(row[1].replace("‰", ""))
                                y_permil = float(row[2].replace("‰", ""))
                                # 兼容两种输入格式：0-1000 或 0.000-1.000
                                if x_permil > 1:
                                    x_permil = x_permil / 1000
                                if y_permil > 1:
                                    y_permil = y_permil / 1000
                                # 确保千分比在0.000-1.000范围内
                                x_permil = max(0.000, min(1.000, round(x_permil, 3)))
                                y_permil = max(0.000, min(1.000, round(y_permil, 3)))
                                self.script_commands.append({
                                    "key": row[0],
                                    "x": x_permil,
                                    "y": y_permil,
                                    "status": "未执行",
                                    "source": "CSV导入"
                                })
                            except ValueError:
                                continue
                
                # 添加系统倒计时命令
                self._add_countdown_commands()
                
                # 更新脚本表格
                self._update_script_tree()
                # 根据脚本状态创建气泡
                self.root.after(0, self._create_bubbles_by_script_status)
                # 更新按钮状态
                self.start_script_btn.config(state=tk.NORMAL)
                self.pause_script_btn.config(state=tk.DISABLED)
                self.stop_script_btn.config(state=tk.DISABLED)
                # 更新状态标签
                self.script_status_label.config(text=f"脚本状态：已加载({len(self.script_commands)}条命令，含系统倒计时)", foreground="blue")
            except Exception as e:
                messagebox.showerror("错误", f"加载脚本失败：{str(e)}")

    def _update_script_tree(self):
        """更新脚本命令表格（显示千分比）"""
        for item in self.script_tree.get_children():
            self.script_tree.delete(item)
        
        for idx, cmd in enumerate(self.script_commands):
            if cmd["source"] == "系统倒计时":
                coord_text = "--"
            else:
                # 显示为千分比格式（乘以1000，加‰符号）
                x_show = f"{cmd['x']*1000:.0f}‰"
                y_show = f"{cmd['y']*1000:.0f}‰"
                coord_text = f"{x_show}, {y_show}"
            self.script_tree.insert("", tk.END, values=(
                idx+1,
                cmd["key"],
                coord_text,
                cmd["status"],
                cmd.get("source", "未知")
            ), tags=(cmd["status"],))
        
        # 设置标签颜色
        self.script_tree.tag_configure("未执行", foreground="black")
        self.script_tree.tag_configure("执行中", foreground="blue")
        self.script_tree.tag_configure("已完成", foreground="green")
        self.script_tree.tag_configure("暂停", foreground="orange")
        self.script_tree.tag_configure("执行失败", foreground="red")
        
        # 更新表格后自动滚动到当前命令行
        self.root.after(0, self._scroll_to_current_command)

    def _toggle_loop(self):
        """切换循环执行状态"""
        self.script_loop = self.loop_var.get()

    def _start_script(self):
        """启动脚本执行（基于主程序千分比坐标）"""
        if not self.script_commands or self.script_running:
            return
        
        # 检查是否选中主程序
        if not self.main_diablo_window:
            messagebox.showwarning(
                "警告", "请先双击暗黑窗口列表选中主程序窗口后再启动脚本。"
            )
            return
        
        self.script_running = True
        self.script_paused = False
        self.script_current_index = 0
        
        # 重置命令状态
        for cmd in self.script_commands:
            cmd["status"] = "未执行"
        self._update_script_tree()
        
        # 更新按钮状态
        self.start_script_btn.config(state=tk.DISABLED)
        self.pause_script_btn.config(state=tk.NORMAL)
        self.stop_script_btn.config(state=tk.NORMAL)
        self.load_script_btn.config(state=tk.DISABLED)
        self.set_interval_btn.config(state=tk.DISABLED)
        
        # 更新状态标签
        self.script_status_label.config(text="脚本状态：运行中", foreground="green")
        
        # 启动脚本线程
        self.script_thread = threading.Thread(target=self._run_script, daemon=True)
        self.script_thread.start()

    def _pause_script(self):
        """暂停脚本执行"""
        if not self.script_running:
            return
        
        self.script_paused = not self.script_paused
        if self.script_paused:
            self.pause_script_btn.config(text="恢复脚本")
            self.script_status_label.config(text="脚本状态：暂停中", foreground="orange")
            if self.script_current_index < len(self.script_commands):
                self.script_commands[self.script_current_index]["status"] = "暂停"
                self._update_script_tree()
        else:
            self.pause_script_btn.config(text="暂停脚本")
            self.script_status_label.config(text="脚本状态：运行中", foreground="green")
            if self.script_current_index < len(self.script_commands):
                self.script_commands[self.script_current_index]["status"] = "执行中"
                self._update_script_tree()

    def _stop_script(self):
        """停止脚本执行"""
        self.script_running = False
        self.script_paused = False
        
        # 更新按钮状态
        self.start_script_btn.config(state=tk.NORMAL)
        self.pause_script_btn.config(state=tk.DISABLED)
        self.stop_script_btn.config(state=tk.DISABLED)
        self.load_script_btn.config(state=tk.NORMAL)
        self.set_interval_btn.config(state=tk.NORMAL)
        
        # 更新状态标签
        self.script_status_label.config(text="脚本状态：已停止", foreground="red")
        
        # 重置命令状态
        for cmd in self.script_commands:
            cmd["status"] = "未执行"
        self._update_script_tree()

    def _run_script(self):
        """脚本执行核心逻辑（基于主程序千分比坐标）"""
        while self.script_running:
            # 检查是否暂停
            while self.script_paused and self.script_running:
                time.sleep(0.1)
            
            if not self.script_running:
                break
            
            # 执行当前命令
            if self.script_current_index < len(self.script_commands):
                cmd = self.script_commands[self.script_current_index]
                cmd["status"] = "执行中"
                self.root.after(0, self._update_script_tree)
                
                try:
                    # 判断是否为系统倒计时命令
                    if cmd["source"] == "系统倒计时":
                        time.sleep(1)
                    else:
                        # 基于选中的主程序执行操作（千分比转绝对坐标）
                        if self.main_diablo_window and self.main_window_size != (0, 0):
                            abs_x, abs_y = self._permil_to_absolute(cmd["x"], cmd["y"])
                            # 执行鼠标和按键操作
                            pyautogui.moveTo(abs_x, abs_y, duration=0.1)
                            time.sleep(0.05)
                            pyautogui.click(button='left')
                            time.sleep(0.05)
                            pyautogui.press(cmd["key"])
                    
                    cmd["status"] = "已完成"
                    self.root.after(0, self._update_script_tree)
                    
                except Exception as e:
                    cmd["status"] = "执行失败"
                    self.root.after(0, self._update_script_tree)
                    print(f"命令执行失败：{e}")
                
                # 移动到下一条命令
                self.script_current_index += 1
                sleep_time = 1 if cmd["source"] == "系统倒计时" else 0.5
                time.sleep(sleep_time)
            else:
                # 所有命令执行完成
                if self.script_loop:
                    self.root.after(0, lambda: self.script_status_label.config(
                        text=f"脚本状态：循环等待({self.loop_interval}秒)", 
                        foreground="purple"
                    ))
                    
                    wait_start = time.time()
                    while time.time() - wait_start < self.loop_interval:
                        if not self.script_running or self.script_paused:
                            break
                        time.sleep(0.1)
                    
                    if not self.script_running:
                        break
                    
                    self.script_current_index = 0
                    for cmd in self.script_commands:
                        cmd["status"] = "未执行"
                    self.root.after(0, self._update_script_tree)
                    self.root.after(0, lambda: self.script_status_label.config(
                        text="脚本状态：循环中", 
                        foreground="green"
                    ))
                else:
                    self.root.after(0, self._stop_script)
                    self.root.after(0, lambda: self.script_status_label.config(
                        text="脚本状态：执行完成", 
                        foreground="purple"
                    ))
                    break

    def _stop_monitor(self):
        """停止监控并退出"""
        if self.script_running:
            self._stop_script()
        self._destroy_all_bubbles()
        self.monitor_running = False
        self.root.quit()

if __name__ == "__main__":
    # 自动安装依赖
    required_libs = ["pygetwindow", "pyautogui"]
    for lib in required_libs:
        try:
            __import__(lib)
        except ImportError:
            print(f"缺少{lib}库，正在自动安装...")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
            __import__(lib)

    # 启动程序
    root = tk.Tk()
    app = DiabloWindowMonitor(root)
    root.mainloop()