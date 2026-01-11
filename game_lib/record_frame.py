from tkinter import ttk
from tkinter import messagebox
import tkinter as tk
import os
from config_manager import CONFIG

class RecordFrame:
    def __init__(self, parent, export_records, import_records, clear_records):
        self.record_frame = ttk.LabelFrame(
            parent,  # 修改parent为content_frame
            text="按键-千分比坐标记录",
            padding=10,
        )
        self.record_frame.pack(fill=tk.X, padx=20, pady=5, ipadx=80)

        record_tree_style = ttk.Style()
        record_tree_style.configure("Record.Treeview", font=CONFIG["normal_font"])
        record_tree_style.configure(
            "Record.Treeview.Heading", font=("微软雅黑", 10, "bold")
        )

        self.record_tree = ttk.Treeview(
            self.record_frame,
            columns=("按键", "千分比坐标"),
            show="headings",
            style="Record.Treeview",
            height=5,
        )
        self.record_tree.heading("按键", text="按键")
        self.record_tree.heading("千分比坐标", text="主程序千分比坐标(X‰, Y‰)")
        self.record_tree.column("按键", width=100)
        self.record_tree.column("千分比坐标", width=200)
        self.record_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        record_btn_frame = ttk.Frame(self.record_frame)
        record_btn_frame.pack(side=tk.RIGHT, padx=10)

        self.export_btn = ttk.Button(
            record_btn_frame, text="导出记录(CSV)", command=export_records
        )
        self.import_btn = ttk.Button(
            record_btn_frame, text="导入记录(CSV)", command=import_records
        )
        self.clear_btn = ttk.Button(
            record_btn_frame, text="清空记录", command=clear_records
        )

        for btn in [self.export_btn, self.import_btn, self.clear_btn]:
            btn.pack(pady=5, fill=tk.X)