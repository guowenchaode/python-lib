from tkinter import ttk
from tkinter import messagebox
import tkinter as tk
from config_manager import CONFIG
from script_executor import ScriptExecutor

class ScriptFrame:
    def __init__(
        self,
        parent,
        load_script,
        start_script,
        pause_script,
        stop_script,
        toggle_bubbles_visibility,
        set_loop_interval,
        permil_to_absolute,
        check_main_window_foreground,
        create_bubbles_by_script_status,
        update_script_tree,
        update_status_label,
        script_commands,
        script_running,
        stop_on_background,
        loop_interval,
    ):
        self.script_frame = ttk.LabelFrame(
            parent,  # 修改parent为content_frame
            text="脚本执行模块（千分比坐标）",
            padding=10,
        )
        self.script_frame.pack(fill=tk.BOTH, padx=20, pady=5, expand=True)

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
            script_ctrl_frame, text="加载CSV脚本", command=load_script
        )
        self.start_script_btn = ttk.Button(
            script_ctrl_frame,
            text="启动脚本",
            command=start_script,
            state=tk.DISABLED,
        )
        self.pause_script_btn = ttk.Button(
            script_ctrl_frame,
            text="暂停脚本",
            command=pause_script,
            state=tk.DISABLED,
        )
        self.stop_script_btn = ttk.Button(
            script_ctrl_frame,
            text="停止脚本",
            command=stop_script,
            state=tk.DISABLED,
        )
        self.toggle_bubble_btn = ttk.Button(
            script_ctrl_frame, text="隐藏气泡", command=toggle_bubbles_visibility
        )

        for btn in [
            self.load_script_btn,
            self.start_script_btn,
            self.pause_script_btn,
            self.stop_script_btn,
            self.toggle_bubble_btn,
        ]:
            btn.pack(side=tk.LEFT, padx=5)

        self.stop_on_background_var = tk.BooleanVar(value=stop_on_background)
        self.stop_on_background_check = ttk.Checkbutton(
            script_ctrl_frame,
            text="主程序后台时自动停止脚本",
            variable=self.stop_on_background_var,
            command=lambda: setattr(
                stop_on_background, self.stop_on_background_var.get()
            ),
        )
        self.stop_on_background_check.pack(side=tk.LEFT, padx=10)

        self.loop_var = tk.BooleanVar(value=True)
        self.loop_check = ttk.Checkbutton(
            script_ctrl_frame,
            text="循环执行",
            variable=self.loop_var,
            command=lambda: setattr(script_running, self.loop_var.get()),
        )
        self.loop_check.pack(side=tk.LEFT, padx=10)

        ttk.Label(
            script_ctrl_frame, text="循环间隔(秒)：", font=CONFIG["normal_font"]
        ).pack(side=tk.LEFT, padx=5)
        self.interval_entry = ttk.Entry(
            script_ctrl_frame, width=8, font=CONFIG["normal_font"]
        )
        self.interval_entry.insert(0, str(loop_interval))
        self.interval_entry.pack(side=tk.LEFT, padx=5)

        self.set_interval_btn = ttk.Button(
            script_ctrl_frame, text="确认", command=set_loop_interval
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