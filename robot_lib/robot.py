import threading
import socket
import tkinter as tk
import time
import psutil
from tkinter import messagebox
import math

class RobotApp:
    def __init__(self):
        self.msg_count = 0
        self.other_num = 0
        self.messages = []
        # 缩小三分之一并调整脚位置靠近头部
        self.left_foot_pos = (38, 56, 44, 62)    # 左脚正方形，向上靠近头部
        self.right_foot_pos = (56, 56, 62, 62)   # 右脚正方形，向上靠近头部
        self.left_hand_pos = (30, 44, 36, 50)    # 左手圆，缩小
        self.right_hand_pos = (64, 44, 70, 50)   # 右手圆，缩小
        self.head_pos = (40, 28, 60, 48)         # 头部圆，缩小
        self.drag_data = {"x": 0, "y": 0}
        self.last_interact = None
        self.inactive_seconds = 10
        self.battery_warned = False
        self.cpu_arc = None
        self.vm_arc = None

        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.wm_attributes('-transparentcolor', 'white')
        self.root.configure(bg='white')

        self.canvas = tk.Canvas(self.root, width=100, height=100, bg="white", highlightthickness=0)
        self.canvas.pack()

        # 最外围绿色圆环
        self.canvas.create_oval(7, 7, 93, 93, outline="green", width=3)
        # 内侧半圆环（初始绘制）
        self.draw_resource_arcs()

        # 头部（圆形）
        self.head_id = self.canvas.create_oval(*self.head_pos, fill="lightblue", outline="black", width=1)
        # 左右手（圆形）
        self.canvas.create_oval(*self.left_hand_pos, fill="gray")
        self.canvas.create_oval(*self.right_hand_pos, fill="gray")
        # 左右脚（正方形）
        self.box_left = self.canvas.create_rectangle(*self.left_foot_pos, fill="white", outline="black")
        self.box_right = self.canvas.create_rectangle(*self.right_foot_pos, fill="white", outline="black")
        # 脚上的数字
        self.text_left = self.canvas.create_text(
            (self.left_foot_pos[0] + self.left_foot_pos[2]) // 2,
            (self.left_foot_pos[1] + self.left_foot_pos[3]) // 2,
            text=str(self.msg_count), font=("Arial", 6)
        )
        self.text_right = self.canvas.create_text(
            (self.right_foot_pos[0] + self.right_foot_pos[2]) // 2,
            (self.right_foot_pos[1] + self.right_foot_pos[3]) // 2,
            text=str(self.other_num), font=("Arial", 6)
        )

        # hi Alex 和当前时间（绿色圆右侧）
        self.status_text = self.canvas.create_text(
            95, 15, anchor="w",
            text=f"hi Alex {time.strftime('%H:%M:%S')}",
            font=("Arial", 7), fill="black"
        )

        # 消息悬浮文本（初始隐藏）
        self.hover_text_id = None

        # 鼠标事件
        self.canvas.tag_bind(self.head_id, "<Enter>", self.on_head_enter)
        self.canvas.tag_bind(self.head_id, "<Leave>", self.on_head_leave)
        self.canvas.tag_bind(self.head_id, "<Button-3>", self.on_head_right_click)
        self.canvas.tag_bind(self.head_id, "<Motion>", self.on_head_motion)
        self.canvas.bind("<ButtonPress-1>", self.on_drag_start)
        self.canvas.bind("<B1-Motion>", self.on_drag_motion)
        self.root.bind_all("<Any-Motion>", self.on_any_interact)
        self.root.bind_all("<Button>", self.on_any_interact)
        self.root.bind_all("<Key>", self.on_any_interact)

        # 启动时窗口显示在左下角，距离任务栏上方30像素
        self.root.update_idletasks()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        win_w = 100
        win_h = 100
        self.root.geometry(f"{win_w}x{win_h}+0+{screen_h-win_h-30}")

        threading.Thread(target=self.start_socket_server, daemon=True).start()
        self.last_interact = self._now()
        self.update_ui()
        self.check_inactive()
        self.update_status_time()
        self.check_battery()
        self.update_resource_arcs()
        self.root.mainloop()

    def _now(self):
        return time.time()

    def update_ui(self):
        self.canvas.itemconfig(self.text_left, text=str(self.msg_count))
        self.canvas.itemconfig(self.text_right, text=str(self.other_num))
        self.root.after(500, self.update_ui)

    def update_status_time(self):
        # 定时更新时间显示
        self.canvas.itemconfig(self.status_text, text=f"hi Alex {time.strftime('%H:%M:%S')}")
        self.root.after(1000, self.update_status_time)

    def check_inactive(self):
        now = self._now()
        if self.last_interact and now - self.last_interact > self.inactive_seconds:
            self.root.wm_attributes('-alpha', 0.2)
        else:
            self.root.wm_attributes('-alpha', 1.0)
        self.root.after(1000, self.check_inactive)

    def on_any_interact(self, event):
        self.last_interact = self._now()
        self.root.wm_attributes('-alpha', 1.0)

    def start_socket_server(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('localhost', 9999))
        s.listen(5)
        while True:
            conn, addr = s.accept()
            data = conn.recv(1024)
            if data:
                msg = data.decode(errors="ignore")
                self.msg_count += 1
                self.messages.append(msg)
            conn.close()

    def on_head_enter(self, event):
        self.root.config(cursor="hand2")
        self.show_hover_messages(event)
        self.on_any_interact(event)

    def on_head_leave(self, event):
        self.root.config(cursor="arrow")
        self.hide_hover_messages()
        self.on_any_interact(event)

    def on_head_motion(self, event):
        self.show_hover_messages(event)
        self.on_any_interact(event)

    def show_hover_messages(self, event):
        # 在机器人头部上方显示所有消息
        if self.messages:
            msg_text = "\n".join(self.messages[-5:])  # 只显示最近5条
        else:
            msg_text = "暂无消息"
        if self.hover_text_id:
            self.canvas.delete(self.hover_text_id)
        self.hover_text_id = self.canvas.create_text(
            (self.head_pos[0] + self.head_pos[2]) // 2,
            self.head_pos[1] - 5,
            text=msg_text,
            font=("Arial", 12),  # 字体增大两倍
            fill="blue",
            anchor="s"
        )

    def hide_hover_messages(self):
        if self.hover_text_id:
            self.canvas.delete(self.hover_text_id)
            self.hover_text_id = None

    def on_head_right_click(self, event):
        # 交换左右脚位置和数字
        self.left_foot_pos, self.right_foot_pos = self.right_foot_pos, self.left_foot_pos
        self.canvas.coords(self.box_left, *self.left_foot_pos)
        self.canvas.coords(self.box_right, *self.right_foot_pos)
        left_text_pos = (self.left_foot_pos[0] + self.left_foot_pos[2]) // 2, (self.left_foot_pos[1] + self.left_foot_pos[3]) // 2
        right_text_pos = (self.right_foot_pos[0] + self.right_foot_pos[2]) // 2, (self.right_foot_pos[1] + self.right_foot_pos[3]) // 2
        self.canvas.coords(self.text_left, *left_text_pos)
        self.canvas.coords(self.text_right, *right_text_pos)
        self.on_any_interact(event)

    def on_drag_start(self, event):
        self.drag_data["x"] = event.x_root
        self.drag_data["y"] = event.y_root
        self.on_any_interact(event)

    def on_drag_motion(self, event):
        dx = event.x_root - self.drag_data["x"]
        dy = event.y_root - self.drag_data["y"]
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")
        self.drag_data["x"] = event.x_root
        self.drag_data["y"] = event.y_root
        self.on_any_interact(event)

    def check_battery(self):
        try:
            battery = psutil.sensors_battery()
            if battery and battery.percent <= 20 and not self.battery_warned:
                self.battery_warned = True
                messagebox.showwarning("电量提醒", f"当前电量仅剩 {battery.percent}% ，请及时充电！")
            elif battery and battery.percent > 20:
                self.battery_warned = False
        except Exception:
            pass
        self.root.after(60000, self.check_battery)  # 每分钟检查一次

    def draw_resource_arcs(self):
        # 绘制左半圆红色（CPU），右半圆蓝色（VM）
        cpu_percent = psutil.cpu_percent()
        vm_percent = psutil.virtual_memory().percent
        # 左半圆红色，角度范围180~360
        if self.cpu_arc:
            self.canvas.delete(self.cpu_arc)
        self.cpu_arc = self.canvas.create_arc(
            13, 13, 87, 87, start=180, extent=180 * cpu_percent / 100,
            style=tk.ARC, outline="red", width=2
        )
        # 右半圆蓝色，角度范围0~180
        if self.vm_arc:
            self.canvas.delete(self.vm_arc)
        self.vm_arc = self.canvas.create_arc(
            13, 13, 87, 87, start=0, extent=180 * vm_percent / 100,
            style=tk.ARC, outline="blue", width=2
        )

    def update_resource_arcs(self):
        self.draw_resource_arcs()
        self.root.after(1000, self.update_resource_arcs)

if __name__ == "__main__":
    RobotApp()
