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

class DiabloWindowMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("暗黑破坏神窗口监控工具 | 脚本执行版")
        self.root.geometry("900x750")
        self.root.resizable(False, False)
        
        # 核心变量
        self.current_diablo_window = None  # 当前鼠标所在的暗黑窗口
        self.is_diablo_foreground = False  # 暗黑窗口是否前台
        self.key_pos_records = {}          # 按键-坐标记录字典 {按键: (x,y)}
        self.is_tool_foreground = True     # 工具是否前台
        
        # 脚本执行相关变量
        self.script_commands = []          # CSV加载的脚本命令列表
        self.script_running = False        # 脚本是否运行
        self.script_paused = False         # 脚本是否暂停
        self.script_thread = None          # 脚本执行线程
        self.script_current_index = 0      # 脚本当前执行位置
        self.script_loop = True            # 是否循环执行脚本
        self.loop_interval = 5             # 循环间隔时间（默认5秒）
        
        # 初始化UI
        self._init_ui()
        
        # 绑定按键监听事件
        self.root.bind("<Key>", self._on_key_press)
        self.root.bind("<FocusIn>", lambda e: setattr(self, "is_tool_foreground", True))
        self.root.bind("<FocusOut>", lambda e: setattr(self, "is_tool_foreground", False))
        
        # 启动监控线程
        self.monitor_running = True
        self.window_monitor_thread = threading.Thread(target=self._monitor_windows, daemon=True)
        self.mouse_monitor_thread = threading.Thread(target=self._monitor_mouse, daemon=True)
        self.window_monitor_thread.start()
        self.mouse_monitor_thread.start()

    def _init_ui(self):
        """初始化界面布局"""
        # 1. 标题区域
        title_label = ttk.Label(
            self.root, 
            text="暗黑破坏神窗口监控工具 | 脚本执行版", 
            font=("微软雅黑", 14, "bold")
        )
        title_label.pack(pady=10)
        
        # 2. 鼠标位置区域
        mouse_frame = ttk.LabelFrame(self.root, text="鼠标位置信息", padding=10)
        mouse_frame.pack(fill=tk.X, padx=20, pady=5)
        
        self.mouse_abs_label = ttk.Label(mouse_frame, text="绝对位置：(X: 0, Y: 0)", font=("微软雅黑", 10))
        self.mouse_abs_label.pack(side=tk.LEFT, padx=10)
        
        self.mouse_rel_label = ttk.Label(mouse_frame, text="相对位置：(X: --, Y: --)", font=("微软雅黑", 10))
        self.mouse_rel_label.pack(side=tk.LEFT, padx=10)
        
        # 3. 暗黑窗口状态区域
        self.status_label = ttk.Label(
            self.root,
            text="暗黑破坏神状态：后台运行",
            font=("微软雅黑", 11, "bold")
        )
        self.status_label.pack(pady=5)
        
        # 4. 暗黑窗口信息表格
        window_frame = ttk.LabelFrame(self.root, text="暗黑窗口信息", padding=10)
        window_frame.pack(fill=tk.X, padx=20, pady=5)
        
        window_tree_style = ttk.Style()
        window_tree_style.configure("Treeview", font=("微软雅黑", 10))
        window_tree_style.configure("Treeview.Heading", font=("微软雅黑", 10, "bold"))
        
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
        record_frame = ttk.LabelFrame(self.root, text="按键-坐标记录", padding=10)
        record_frame.pack(fill=tk.X, padx=20, pady=5)
        
        # 记录表格
        record_tree_style = ttk.Style()
        record_tree_style.configure("Record.Treeview", font=("微软雅黑", 10))
        record_tree_style.configure("Record.Treeview.Heading", font=("微软雅黑", 10, "bold"))
        
        self.record_tree = ttk.Treeview(record_frame, columns=("按键", "相对坐标"), show="headings", style="Record.Treeview", height=5)
        self.record_tree.heading("按键", text="按键")
        self.record_tree.heading("相对坐标", text="暗黑窗口内相对坐标")
        self.record_tree.column("按键", width=100)
        self.record_tree.column("相对坐标", width=200)
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
        script_frame = ttk.LabelFrame(self.root, text="脚本执行模块", padding=10)
        script_frame.pack(fill=tk.BOTH, padx=20, pady=5, expand=True)
        
        # 脚本加载/控制按钮
        script_ctrl_frame = ttk.Frame(script_frame)
        script_ctrl_frame.pack(fill=tk.X, pady=5)
        
        self.load_script_btn = ttk.Button(script_ctrl_frame, text="加载CSV脚本", command=self._load_script)
        self.load_script_btn.pack(side=tk.LEFT, padx=5)
        
        self.start_script_btn = ttk.Button(script_ctrl_frame, text="启动脚本", command=self._start_script, state=tk.DISABLED)
        self.start_script_btn.pack(side=tk.LEFT, padx=5)
        
        self.pause_script_btn = ttk.Button(script_ctrl_frame, text="暂停脚本", command=self._pause_script, state=tk.DISABLED)
        self.pause_script_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_script_btn = ttk.Button(script_ctrl_frame, text="停止脚本", command=self._stop_script, state=tk.DISABLED)
        self.stop_script_btn.pack(side=tk.LEFT, padx=5)
        
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
        
        # 脚本命令表格
        self.script_tree = ttk.Treeview(script_frame, columns=("序号", "按键", "坐标", "状态"), show="headings", height=8)
        self.script_tree.heading("序号", text="序号")
        self.script_tree.heading("按键", text="按键")
        self.script_tree.heading("坐标", text="相对坐标")
        self.script_tree.heading("状态", text="执行状态")
        
        self.script_tree.column("序号", width=60)
        self.script_tree.column("按键", width=80)
        self.script_tree.column("坐标", width=200)
        self.script_tree.column("状态", width=100)
        
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

    def _set_loop_interval(self):
        """设置循环间隔时间"""
        try:
            interval = float(self.interval_entry.get())
            if interval < 0:
                raise ValueError("间隔时间不能为负数")
            self.loop_interval = interval
            messagebox.showinfo("成功", f"循环间隔已设置为：{self.loop_interval} 秒")
        except ValueError as e:
            messagebox.showerror("错误", f"输入无效：{e}\n请输入非负数字")
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
            time.sleep(0.5)

    def _monitor_mouse(self):
        """监控鼠标位置（10ms刷新）"""
        while self.monitor_running:
            try:
                mouse_x, mouse_y = pyautogui.position()
                rel_x, rel_y = "--", "--"
                self.current_diablo_window = None
                
                diablo_windows = self._get_diablo_windows()
                for win_info in diablo_windows:
                    win = win_info["window_obj"]
                    if (win.left <= mouse_x <= win.left + win.width and
                        win.top <= mouse_y <= win.top + win.height):
                        rel_x = mouse_x - win.left
                        rel_y = mouse_y - win.top
                        self.current_diablo_window = win
                        break
                
                self.root.after(0, self._update_mouse_info, mouse_x, mouse_y, rel_x, rel_y)
                time.sleep(0.01)
            except Exception:
                time.sleep(0.01)

    def _on_key_press(self, event):
        """按键监听：工具前台时记录按键-相对坐标"""
        # 仅工具前台且有暗黑窗口时记录
        if not self.is_tool_foreground or not self.current_diablo_window or self.script_running:
            return
        
        # 过滤功能键，只记录字母/数字/符号
        key = event.char
        if not key or len(key) != 1:
            return
        
        # 获取当前相对坐标
        mouse_x, mouse_y = pyautogui.position()
        rel_x = mouse_x - self.current_diablo_window.left
        rel_y = mouse_y - self.current_diablo_window.top
        
        # 记录/覆盖按键坐标
        self.key_pos_records[key] = (int(rel_x), int(rel_y))
        self.root.after(0, self._update_record_tree)

    def _update_window_tree(self, windows_info):
        """更新暗黑窗口表格（前台红色/后台黑色）"""
        for item in self.window_tree.get_children():
            self.window_tree.delete(item)
        
        if not windows_info:
            item = self.window_tree.insert("", tk.END, values=("未检测到暗黑破坏神窗口", "", "", ""))
            self.window_tree.item(item, tags=("inactive",))
        else:
            for win in windows_info:
                item = self.window_tree.insert("", tk.END, values=(win["title"], win["pos"], win["size"], win["status"]))
                self.window_tree.item(item, tags=("active" if win["is_active"] else "inactive"))
        
        self.window_tree.tag_configure("active", foreground="red")
        self.window_tree.tag_configure("inactive", foreground="black")

    def _update_record_tree(self):
        """更新按键-坐标记录表格"""
        for item in self.record_tree.get_children():
            self.record_tree.delete(item)
        
        for key, (x, y) in sorted(self.key_pos_records.items()):
            self.record_tree.insert("", tk.END, values=(key, f"{x}, {y}"))

    def _update_mouse_info(self, abs_x, abs_y, rel_x, rel_y):
        """更新鼠标位置显示"""
        self.mouse_abs_label.config(text=f"绝对位置：(X: {abs_x}, Y: {abs_y})")
        self.mouse_rel_label.config(text=f"相对位置：(X: {rel_x}, Y: {rel_y})")

    def _update_status_label(self):
        """更新暗黑窗口状态标签"""
        if self.is_diablo_foreground:
            self.status_label.config(text="暗黑破坏神状态：前台运行", foreground="red")
        else:
            self.status_label.config(text="暗黑破坏神状态：后台运行", foreground="black")

    def _on_window_double_click(self, event):
        """双击暗黑窗口行复制标题"""
        item = self.window_tree.identify_row(event.y)
        if not item:
            return
        values = self.window_tree.item(item, "values")
        if values and values[0] != "未检测到暗黑破坏神窗口":
            self.root.clipboard_clear()
            self.root.clipboard_append(values[0])
            messagebox.showinfo("成功", f"已复制窗口标题：\n{values[0]}")

    def _export_records(self):
        """导出记录到CSV文件"""
        if not self.key_pos_records:
            messagebox.showwarning("提示", "暂无记录可导出")
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
                    writer.writerow(["按键", "相对X", "相对Y"])  # 表头
                    for key, (x, y) in sorted(self.key_pos_records.items()):
                        writer.writerow([key, x, y])
                messagebox.showinfo("成功", f"记录已导出到：\n{file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败：{str(e)}")

    def _import_records(self):
        """从CSV文件导入记录"""
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
                            key, x, y = row
                            if len(key) == 1 and x.isdigit() and y.isdigit():
                                self.key_pos_records[key] = (int(x), int(y))
                                imported_count += 1
                self._update_record_tree()
                messagebox.showinfo("成功", f"成功导入 {imported_count} 条记录")
            except Exception as e:
                messagebox.showerror("错误", f"导入失败：{str(e)}")

    def _clear_records(self):
        """清空所有记录"""
        if not self.key_pos_records:
            messagebox.showwarning("提示", "暂无记录可清空")
            return
        
        if messagebox.askyesno("确认", "是否确定清空所有按键-坐标记录？"):
            self.key_pos_records.clear()
            self._update_record_tree()
            messagebox.showinfo("成功", "记录已清空")

    def _load_script(self):
        """加载CSV脚本文件"""
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
                        if len(row) == 3 and len(row[0]) == 1 and row[1].isdigit() and row[2].isdigit():
                            self.script_commands.append({
                                "key": row[0],
                                "x": int(row[1]),
                                "y": int(row[2]),
                                "status": "未执行"
                            })
                
                # 更新脚本表格
                self._update_script_tree()
                # 更新按钮状态
                self.start_script_btn.config(state=tk.NORMAL)
                self.pause_script_btn.config(state=tk.DISABLED)
                self.stop_script_btn.config(state=tk.DISABLED)
                # 更新状态标签
                self.script_status_label.config(text=f"脚本状态：已加载({len(self.script_commands)}条命令)", foreground="blue")
                messagebox.showinfo("成功", f"成功加载 {len(self.script_commands)} 条脚本命令")
            except Exception as e:
                messagebox.showerror("错误", f"加载脚本失败：{str(e)}")

    def _update_script_tree(self):
        """更新脚本命令表格"""
        for item in self.script_tree.get_children():
            self.script_tree.delete(item)
        
        for idx, cmd in enumerate(self.script_commands):
            self.script_tree.insert("", tk.END, values=(
                idx+1,
                cmd["key"],
                f"{cmd['x']}, {cmd['y']}",
                cmd["status"]
            ), tags=(cmd["status"],))
        
        # 设置标签颜色
        self.script_tree.tag_configure("未执行", foreground="black")
        self.script_tree.tag_configure("执行中", foreground="blue")
        self.script_tree.tag_configure("已完成", foreground="green")
        self.script_tree.tag_configure("暂停", foreground="orange")
        self.script_tree.tag_configure("执行失败", foreground="red")

    def _toggle_loop(self):
        """切换循环执行状态"""
        self.script_loop = self.loop_var.get()

    def _start_script(self):
        """启动脚本执行"""
        if not self.script_commands or self.script_running:
            return
        
        # 检查是否有暗黑窗口
        if not self._get_diablo_windows():
            messagebox.showwarning("提示", "未检测到暗黑破坏神窗口，无法执行脚本")
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
        self.set_interval_btn.config(state=tk.DISABLED)  # 运行时禁止修改间隔
        
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
            # 更新当前命令状态
            if self.script_current_index < len(self.script_commands):
                self.script_commands[self.script_current_index]["status"] = "暂停"
                self._update_script_tree()
        else:
            self.pause_script_btn.config(text="暂停脚本")
            self.script_status_label.config(text="脚本状态：运行中", foreground="green")
            # 恢复当前命令状态
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
        self.set_interval_btn.config(state=tk.NORMAL)  # 停止后允许修改间隔
        
        # 更新状态标签
        self.script_status_label.config(text="脚本状态：已停止", foreground="red")
        
        # 重置命令状态
        for cmd in self.script_commands:
            cmd["status"] = "未执行"
        self._update_script_tree()

    def _run_script(self):
        """脚本执行核心逻辑（新增左键单击操作）"""
        while self.script_running:
            # 检查是否暂停
            while self.script_paused and self.script_running:
                time.sleep(0.1)
            
            if not self.script_running:
                break
            
            # 执行当前命令
            if self.script_current_index < len(self.script_commands):
                cmd = self.script_commands[self.script_current_index]
                # 更新命令状态为执行中
                cmd["status"] = "执行中"
                self.root.after(0, self._update_script_tree)
                
                try:
                    # 获取暗黑窗口（确保窗口存在）
                    diablo_windows = self._get_diablo_windows()
                    if diablo_windows:
                        main_window = diablo_windows[0]["window_obj"]
                        # 计算绝对坐标
                        abs_x = main_window.left + cmd["x"]
                        abs_y = main_window.top + cmd["y"]
                        # 1. 移动鼠标到目标位置
                        pyautogui.moveTo(abs_x, abs_y, duration=0.1)
                        time.sleep(0.05)  # 移动后短暂等待，确保定位准确
                        # 2. 左键单击
                        pyautogui.click(button='left')
                        time.sleep(0.05)  # 点击后短暂等待
                        # 3. 模拟按键（原有逻辑保留）
                        pyautogui.press(cmd["key"])
                    
                    # 更新命令状态为已完成
                    cmd["status"] = "已完成"
                    self.root.after(0, self._update_script_tree)
                except Exception as e:
                    cmd["status"] = "执行失败"
                    self.root.after(0, self._update_script_tree)
                    print(f"命令执行失败：{e}")
                
                # 移动到下一条命令
                self.script_current_index += 1
                time.sleep(0.5)  # 命令间间隔
            else:
                # 所有命令执行完成
                if self.script_loop:
                    # 循环执行：先等待设定的间隔时间
                    self.root.after(0, lambda: self.script_status_label.config(
                        text=f"脚本状态：循环等待({self.loop_interval}秒)", 
                        foreground="purple"
                    ))
                    
                    # 等待间隔时间（期间检查是否暂停/停止）
                    wait_start = time.time()
                    while time.time() - wait_start < self.loop_interval:
                        if not self.script_running or self.script_paused:
                            break
                        time.sleep(0.1)
                    
                    if not self.script_running:
                        break
                    
                    # 重置索引和状态
                    self.script_current_index = 0
                    for cmd in self.script_commands:
                        cmd["status"] = "未执行"
                    self.root.after(0, self._update_script_tree)
                    self.root.after(0, lambda: self.script_status_label.config(
                        text="脚本状态：循环中", 
                        foreground="green"
                    ))
                else:
                    # 单次执行：停止脚本
                    self.root.after(0, self._stop_script)
                    self.root.after(0, lambda: self.script_status_label.config(
                        text="脚本状态：执行完成", 
                        foreground="purple"
                    ))
                    break

    def _stop_monitor(self):
        """停止监控并退出"""
        # 先停止脚本
        if self.script_running:
            self._stop_script()
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