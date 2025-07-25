import threading
import socket
import tkinter as tk
from tkinter import messagebox
import time
import psutil

class RobotApp:
    def __init__(self):
        # 常量定义
        self.CANVAS_WIDTH = 200
        self.CANVAS_HEIGHT = 200
        self.OUTLINE_WIDTH = 2  # 外围圆环宽度保持为2
        self.INNER_ARC_WIDTH = 4
        self.TEXT_FONT_SIZE_SMALL = 14
        self.TEXT_FONT_SIZE_MEDIUM = 14
        self.TEXT_FONT_SIZE_LARGE = 24
        self.INACTIVE_SECONDS = 10
        self.BATTERY_CHECK_INTERVAL = 60000  # 毫秒
        self.RESOURCE_UPDATE_INTERVAL = 1000  # 毫秒
        self.UI_UPDATE_INTERVAL = 500  # 毫秒
        self.TIME_UPDATE_INTERVAL = 1000  # 毫秒
        self.SOCKET_PORT = 9999
        self.MAX_HOVER_MESSAGES = 5
        self.WINDOW_OFFSET_FROM_TASKBAR = 30
        self.HOVER_TEXT_OFFSET = 20
        
        # 位置坐标常量（外围圆环直径再缩小10像素，总共缩小40像素）
        # 原外圆环直径: 186-14 = 172像素
        # 新外圆环直径: 172-40 = 132像素
        # 向中心各移动20像素（在上次15像素基础上再移动5像素）
        self.OUTER_CIRCLE_LEFT = 34    # 原29，向右再移动5像素
        self.OUTER_CIRCLE_TOP = 34     # 原29，向下再移动5像素
        self.OUTER_CIRCLE_RIGHT = 166  # 原171，向左再移动5像素
        self.OUTER_CIRCLE_BOTTOM = 166 # 原171，向上再移动5像素
        
        # 内侧半圆环坐标（相应调整，保持协调比例）
        self.INNER_ARC_LEFT = 45
        self.INNER_ARC_TOP = 45
        self.INNER_ARC_RIGHT = 155
        self.INNER_ARC_BOTTOM = 155
        
        # 脚部坐标
        self.LEFT_FOOT_LEFT = 70
        self.LEFT_FOOT_TOP = 106
        self.LEFT_FOOT_RIGHT = 94
        self.LEFT_FOOT_BOTTOM = 130
        
        self.RIGHT_FOOT_LEFT = 106
        self.RIGHT_FOOT_TOP = 106
        self.RIGHT_FOOT_RIGHT = 130
        self.RIGHT_FOOT_BOTTOM = 130
        
        # 其他身体部位坐标
        self.LEFT_HAND_LEFT = 60
        self.LEFT_HAND_TOP = 88
        self.LEFT_HAND_RIGHT = 72
        self.LEFT_HAND_BOTTOM = 100
        self.RIGHT_HAND_LEFT = 128
        self.RIGHT_HAND_TOP = 88
        self.RIGHT_HAND_RIGHT = 140
        self.RIGHT_HAND_BOTTOM = 100
        self.HEAD_LEFT = 80
        self.HEAD_TOP = 56
        self.HEAD_RIGHT = 120
        self.HEAD_BOTTOM = 96
        self.BATTERY_WARN_THRESHOLD = 20
        
        # 变量初始化
        self.msg_count = 0
        self.other_num = 0
        self.messages = []
        self.left_foot_pos = (
            self.LEFT_FOOT_LEFT, 
            self.LEFT_FOOT_TOP, 
            self.LEFT_FOOT_RIGHT, 
            self.LEFT_FOOT_BOTTOM
        )
        self.right_foot_pos = (
            self.RIGHT_FOOT_LEFT, 
            self.RIGHT_FOOT_TOP, 
            self.RIGHT_FOOT_RIGHT, 
            self.RIGHT_FOOT_BOTTOM
        )
        self.left_hand_pos = (
            self.LEFT_HAND_LEFT, 
            self.LEFT_HAND_TOP, 
            self.LEFT_HAND_RIGHT, 
            self.LEFT_HAND_BOTTOM
        )
        self.right_hand_pos = (
            self.RIGHT_HAND_LEFT, 
            self.RIGHT_HAND_TOP, 
            self.RIGHT_HAND_RIGHT, 
            self.RIGHT_HAND_BOTTOM
        )
        self.head_pos = (
            self.HEAD_LEFT, 
            self.HEAD_TOP, 
            self.HEAD_RIGHT, 
            self.HEAD_BOTTOM
        )
        self.drag_data = {"x": 0, "y": 0}
        self.last_interact = None
        self.battery_warned = False
        self.cpu_arc = None
        self.vm_arc = None
        self.hover_window = None
        self.status_label = None

        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.wm_attributes('-transparentcolor', 'white')
        self.root.configure(bg='white')

        self.canvas = tk.Canvas(
            self.root, 
            width=self.CANVAS_WIDTH, 
            height=self.CANVAS_HEIGHT, 
            bg="white", 
            highlightthickness=0
        )
        self.canvas.pack()

        # 最外围绿色圆环（直径再缩小10像素，总缩小40像素）
        self.canvas.create_oval(
            self.OUTER_CIRCLE_LEFT, 
            self.OUTER_CIRCLE_TOP, 
            self.OUTER_CIRCLE_RIGHT, 
            self.OUTER_CIRCLE_BOTTOM, 
            outline="green", 
            width=self.OUTLINE_WIDTH
        )
        # 内侧半圆环（左右显示布局）
        self.draw_resource_arcs()

        # 头部（圆形）
        self.head_id = self.canvas.create_oval(
            *self.head_pos, 
            fill="lightblue", 
            outline="black", 
            width=2
        )
        # 左右手（圆形）
        self.canvas.create_oval(*self.left_hand_pos, fill="gray")
        self.canvas.create_oval(*self.right_hand_pos, fill="gray")
        # 左右脚（正方形）
        self.box_left = self.canvas.create_rectangle(
            *self.left_foot_pos, 
            fill="white", 
            outline="black"
        )
        self.box_right = self.canvas.create_rectangle(
            *self.right_foot_pos, 
            fill="white", 
            outline="black"
        )
        # 脚上的数字
        self.text_left = self.canvas.create_text(
            (self.left_foot_pos[0] + self.left_foot_pos[2]) // 2,
            (self.left_foot_pos[1] + self.left_foot_pos[3]) // 2,
            text=str(self.msg_count), 
            font=("Arial", self.TEXT_FONT_SIZE_SMALL)
        )
        self.text_right = self.canvas.create_text(
            (self.right_foot_pos[0] + self.right_foot_pos[2]) // 2,
            (self.right_foot_pos[1] + self.right_foot_pos[3]) // 2,
            text=str(self.other_num), 
            font=("Arial", self.TEXT_FONT_SIZE_SMALL)
        )

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

        # 启动时窗口位置
        self.root.update_idletasks()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        win_w = self.CANVAS_WIDTH
        win_h = self.CANVAS_HEIGHT
        self.root.geometry(
            f"{win_w}x{win_h}+0+{screen_h - win_h - self.WINDOW_OFFSET_FROM_TASKBAR}"
        )

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
        self.root.after(self.UI_UPDATE_INTERVAL, self.update_ui)

    def update_status_time(self):
        current_time_text = f"hi Alex {time.strftime('%H:%M:%S')}"
        if self.hover_window and self.status_label:
            self.status_label.config(text=current_time_text)
        self.root.after(self.TIME_UPDATE_INTERVAL, self.update_status_time)

    def check_inactive(self):
        now = self._now()
        if self.last_interact and now - self.last_interact > self.INACTIVE_SECONDS:
            self.root.wm_attributes('-alpha', 0.2)
        else:
            self.root.wm_attributes('-alpha', 1.0)
        self.root.after(1000, self.check_inactive)

    def on_any_interact(self, event):
        self.last_interact = self._now()
        self.root.wm_attributes('-alpha', 1.0)

    def start_socket_server(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('localhost', self.SOCKET_PORT))
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
        self.hide_hover_messages()
        
        if self.messages:
            msg_text = "\n".join(self.messages[-self.MAX_HOVER_MESSAGES:])
        else:
            msg_text = "暂无消息"
        status_text = f"hi Alex {time.strftime('%H:%M:%S')}"
        
        self.hover_window = tk.Toplevel(self.root)
        self.hover_window.overrideredirect(True)
        self.hover_window.wm_attributes("-topmost", True)
        
        frame = tk.Frame(self.hover_window, bg="white", padx=10, pady=5, relief=tk.SOLID, bd=1)
        frame.pack()
        
        self.status_label = tk.Label(
            frame,
            text=status_text,
            font=("Arial", self.TEXT_FONT_SIZE_MEDIUM),
            fg="black",
            bg="white",
            anchor="w",
            width=20
        )
        self.status_label.pack(fill=tk.X, pady=(0, 5))
        
        msg_label = tk.Label(
            frame,
            text=msg_text,
            font=("Arial", self.TEXT_FONT_SIZE_LARGE),
            fg="blue",
            bg="white",
            justify=tk.LEFT
        )
        msg_label.pack()
        
        # 消息框显示在机器人右侧
        robot_right = self.root.winfo_width()
        head_center_y = (self.head_pos[1] + self.head_pos[3]) // 2
        
        x = self.root.winfo_rootx() + robot_right + self.HOVER_TEXT_OFFSET
        y = self.root.winfo_rooty() + head_center_y
        
        self.hover_window.update_idletasks()
        win_height = self.hover_window.winfo_height()
        self.hover_window.geometry(f"+{x}+{y - win_height//2}")

    def hide_hover_messages(self):
        if self.hover_window:
            self.hover_window.destroy()
            self.hover_window = None
            self.status_label = None

    def on_head_right_click(self, event):
        # 交换左右脚位置和数字
        self.left_foot_pos, self.right_foot_pos = self.right_foot_pos, self.left_foot_pos
        self.canvas.coords(self.box_left, *self.left_foot_pos)
        self.canvas.coords(self.box_right, *self.right_foot_pos)
        left_text_pos = (
            (self.left_foot_pos[0] + self.left_foot_pos[2]) // 2, 
            (self.left_foot_pos[1] + self.left_foot_pos[3]) // 2
        )
        right_text_pos = (
            (self.right_foot_pos[0] + self.right_foot_pos[2]) // 2, 
            (self.right_foot_pos[1] + self.right_foot_pos[3]) // 2
        )
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
        if self.hover_window:
            self.show_hover_messages(event)

    def check_battery(self):
        try:
            battery = psutil.sensors_battery()
            if battery and battery.percent <= self.BATTERY_WARN_THRESHOLD and not self.battery_warned:
                self.battery_warned = True
                messagebox.showwarning(
                    "电量提醒", 
                    f"当前电量仅剩 {battery.percent}% ，请及时充电！"
                )
            elif battery and battery.percent > self.BATTERY_WARN_THRESHOLD:
                self.battery_warned = False
        except Exception:
            pass
        self.root.after(self.BATTERY_CHECK_INTERVAL, self.check_battery)

    def draw_resource_arcs(self):
        # 左半部分显示CPU（红色），右半部分显示VM（蓝色）
        cpu_percent = psutil.cpu_percent()
        vm_percent = psutil.virtual_memory().percent
        
        center_x = (self.INNER_ARC_LEFT + self.INNER_ARC_RIGHT) // 2
        
        # 左半部分CPU
        if self.cpu_arc:
            self.canvas.delete(self.cpu_arc)
        self.cpu_arc = self.canvas.create_arc(
            self.INNER_ARC_LEFT, 
            self.INNER_ARC_TOP, 
            center_x * 2 - self.INNER_ARC_LEFT, 
            self.INNER_ARC_BOTTOM, 
            start=90, 
            extent=180 * cpu_percent / 100,
            style=tk.ARC, 
            outline="red", 
            width=self.INNER_ARC_WIDTH
        )
        
        # 右半部分VM
        if self.vm_arc:
            self.canvas.delete(self.vm_arc)
        self.vm_arc = self.canvas.create_arc(
            center_x * 2 - self.INNER_ARC_RIGHT, 
            self.INNER_ARC_TOP, 
            self.INNER_ARC_RIGHT, 
            self.INNER_ARC_BOTTOM, 
            start=90, 
            extent=-180 * vm_percent / 100,
            style=tk.ARC, 
            outline="blue", 
            width=self.INNER_ARC_WIDTH
        )

    def update_resource_arcs(self):
        self.draw_resource_arcs()
        self.root.after(self.RESOURCE_UPDATE_INTERVAL, self.update_resource_arcs)

if __name__ == "__main__":
    RobotApp()
    