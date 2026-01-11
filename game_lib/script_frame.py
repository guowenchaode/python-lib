from tkinter import ttk
from tkinter import messagebox
import tkinter as tk
from config_manager import CONFIG
from script_executor import ScriptExecutor
from tkinter import filedialog
import pandas as pd
import traceback
from ui_components import BubbleWindow
import threading


class ScriptCommand:
    def __init__(
        self, key, x, y, abs_x, abs_y, status, loop_count, source, action="click"
    ):
        self.key = key
        self.x = x
        self.y = y
        self.abs_x = abs_x
        self.abs_y = abs_y
        self.status = status
        self.source = source
        self.action = action
        self.loop_count = loop_count


class ScriptFrame:
    def __init__(self, parent, root):
        self.parent = parent
        self.root = root
        self.script_running = False
        self.stop_on_background = False
        self.script_loop = True
        self.loop_interval = CONFIG["default_loop_interval"]
        self.script_frame = ttk.LabelFrame(
            parent,  # 修改parent为content_frame
            text="脚本执行模块（千分比坐标）",
            padding=10,
        )
        self.script_executor = None
        self.script_frame.pack(fill=tk.BOTH, padx=20, pady=5, expand=True)
        self.script_current_index = 0
        script_ctrl_frame = ttk.Frame(self.script_frame)
        script_ctrl_frame.pack(fill=tk.X, pady=5)

        self.script_main_window_label = ttk.Label(
            script_ctrl_frame,
            text="主程序：未选中",
            font=("微软雅黑", 10, "bold"),
            foreground="red",
        )
        self.script_main_window_label.pack(side=tk.LEFT, padx=5)

        self.load_script_btn = ttk.Button(
            script_ctrl_frame, text="加载CSV脚本", command=self.open_file_dialog
        )
        self.start_script_btn = ttk.Button(
            script_ctrl_frame,
            text="启动脚本",
            command=self._start_script,
            # state=tk.DISABLED,
        )
        self.pause_script_btn = ttk.Button(
            script_ctrl_frame,
            text="暂停脚本",
            command=self._toggle_pause_script,
            # state=tk.DISABLED,
        )
        self.stop_script_btn = ttk.Button(
            script_ctrl_frame,
            text="停止脚本",
            command=self._stop_script,
            # state=tk.DISABLED,
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
                self.stop_on_background, self.stop_on_background_var.get()
            ),
        )
        self.stop_on_background_check.pack(side=tk.LEFT, padx=10)

        self.loop_var = tk.BooleanVar(value=True)
        self.loop_check = ttk.Checkbutton(
            script_ctrl_frame,
            text="循环执行",
            variable=self.loop_var,
            command=lambda: setattr(self.script_running, self.loop_var.get()),
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
            self.script_frame,
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
            self.script_frame, orient=tk.VERTICAL, command=self.script_tree.yview
        )
        self.script_tree.configure(yscrollcommand=script_scroll.set)
        self.script_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        script_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.script_commands = []
        self.script_file_path = CONFIG.get("script_file_path")

        # 气泡相关属性
        self.bubbles_visible = True
        self.bubble_windows = []
        self.highlighted_bubble = None
        self.main_diablo_window = None
        self.main_window_size = (0, 0)

        self._load_script()

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

    def _toggle_bubbles_visibility(self, event=None):
        self.bubbles_visible = not self.bubbles_visible
        self.toggle_bubble_btn.config(
            text="隐藏气泡" if self.bubbles_visible else "显示气泡"
        )

        if self.bubbles_visible:
            self._create_bubbles_by_script_status()
        else:
            self._destroy_all_bubbles()

    def _create_bubbles_by_script_status(self):
        self._destroy_all_bubbles()

        if self.script_running:
            next_idx = self.script_current_index
            while next_idx < len(self.script_commands):
                cmd = self.script_commands[next_idx]
                if cmd.source != "系统倒计时":
                    self.highlighted_bubble = BubbleWindow(
                        self.root.root,
                        cmd.abs_x,
                        cmd.abs_y,
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
                bubble = BubbleWindow(self.root.root, abs_x, abs_y, idx + 1, cmd.key)
                bubbles.append(bubble)
            self.bubble_windows = bubbles

    def open_file_dialog(self):
        file_path = filedialog.askopenfilename(
            title="选择脚本文件",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*")],
        )
        self.script_file_path = file_path
        self._load_script()

    def _load_script(self):
        """Load a script file (CSV) and populate the script commands using pandas."""
        file_path = self.script_file_path

        if not file_path:
            return

        CONFIG["script_file_path"] = file_path

        try:
            df = pd.read_csv(file_path, encoding="utf-8")
            records = df.to_dict(orient="records")
            self.script_commands = []
            for row in records:
                x = float(row.get("x", 0))
                y = float(row.get("y", 0))
                abs_x, abs_y = self._permil_to_absolute(x, y)
                cmd = ScriptCommand(
                    key=row.get("key", ""),
                    x=float(x),
                    y=float(y),
                    abs_x=abs_x,
                    abs_y=abs_y,
                    loop_count=row.get("loop_count", 0),
                    status="未执行",
                    source="用户脚本",
                )
                self.script_commands.append(cmd)

            self.script_file_path = file_path
            self.script_status_label.config(
                text=f"脚本状态：已加载 ({len(self.script_commands)} 条命令)"
            )
            self.start_script_btn.config(state=tk.NORMAL)
            # messagebox.showinfo("成功", "脚本加载成功！")
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("错误", f"加载脚本失败：{str(e)}")
        finally:
            self._update_script_tree()
            if self.script_executor:
                self.script_executor.commands = self.script_commands

    def _initialize_script_executor(self):
        """Initialize the ScriptExecutor with the current script commands and configuration."""
        self.script_executor = ScriptExecutor(
            commands=self.script_commands,
        )

    def _start_script(self):
        self._load_script()
        if self.script_running or not self.script_commands:
            return

        def run_script():
            self.script_running = True
            self.script_executor = ScriptExecutor(
                commands=self.script_commands,
            )
            self.script_executor.start()

        # Start the script in a new thread
        threading.Thread(target=run_script, daemon=True).start()

    def _toggle_pause_script(self):
        if self.script_executor:
            self.script_executor.toggle_pause()
            self.pause_script_btn.config(
                text="继续脚本" if self.script_executor.paused else "暂停脚本"
            )

    def _stop_script(self):
        if self.script_executor:
            self.script_executor.stop()
            self.script_running = False

    def reload(self):
        self._load_script()
        self._update_script_tree()

    def _update_script_tree(self):
        # Clear existing items
        for item in self.script_tree.get_children():
            self.script_tree.delete(item)

        # Add updated script commands
        for idx, command in enumerate(self.script_commands):
            self.script_tree.insert(
                "",
                "end",
                values=(
                    idx + 1,
                    command.key,
                    f"{command.x * 1000:.0f}‰, {command.y * 1000:.0f}‰  ({command.abs_x}, {command.abs_y})",
                    command.status,
                    command.source,
                ),
            )

    def _on_script_start(self):
        self.start_script_btn.config(state=tk.DISABLED)
        self.pause_script_btn.config(state=tk.NORMAL)
        self.stop_script_btn.config(state=tk.NORMAL)

    def _on_script_pause(self):
        self.start_script_btn.config(state=tk.NORMAL)
        self.pause_script_btn.config(state=tk.DISABLED)
        self.stop_script_btn.config(state=tk.NORMAL)

    def _on_script_stop(self):
        self.start_script_btn.config(state=tk.NORMAL)
        self.pause_script_btn.config(state=tk.DISABLED)
        self.stop_script_btn.config(state=tk.DISABLED)

    def _on_loop_end(self):
        self.start_script_btn.config(state=tk.NORMAL)
        self.pause_script_btn.config(state=tk.DISABLED)
        self.stop_script_btn.config(state=tk.DISABLED)

    def _update_status_label(self, status_text):
        self.script_status_label.config(text=status_text)

    def _permil_to_absolute(self, x_permil, y_permil):
        if not self.root.main_window_location or not x_permil or not y_permil:
            return 0, 0

        abs_x = self.root.main_window_location[0] + int(
            x_permil * self.root.main_window_size[0]
        )
        abs_y = self.root.main_window_location[1] + int(
            y_permil * self.root.main_window_size[1]
        )
        return abs_x, abs_y

    def _check_main_window_foreground(self):
        return True  # Placeholder for actual foreground check logic

    def _destroy_all_bubbles(self):
        for bubble in self.bubble_windows:
            bubble.destroy()
        self.bubble_windows.clear()

        if self.highlighted_bubble:
            self.highlighted_bubble.destroy()
            self.highlighted_bubble = None

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
