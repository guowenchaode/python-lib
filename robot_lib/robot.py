import threading
import socket
import tkinter as tk
from tkinter import messagebox
import time
import psutil
from dataclasses import dataclass
from typing import Tuple, List, Optional, Dict

@dataclass(frozen=True)
class Coordinates:
    """坐标数据类，用于存储各类图形的位置信息"""
    left: int
    top: int
    right: int
    bottom: int

    @property
    def center(self) -> Tuple[int, int]:
        """返回中心点坐标"""
        return (
            (self.left + self.right) // 2,
            (self.top + self.bottom) // 2
        )

    def to_tuple(self) -> Tuple[int, int, int, int]:
        """转换为元组形式"""
        return (self.left, self.top, self.right, self.bottom)


class RobotApp:
    def __init__(self):
        # 配置常量 - 集中管理所有配置参数
        self.config = {
            "canvas_size": (200, 200),
            "outline_width": 2,
            "inner_arc_width": 2,
            "text_font_sizes": {
                "small": 14,
                "medium": 14,
                "large": 24
            },
            "inactive_seconds": 10,
            "battery_check_interval": 60000,  # 毫秒
            "resource_update_interval": 1000,  # 毫秒
            "ui_update_interval": 500,        # 毫秒
            "time_update_interval": 1000,     # 毫秒
            "socket_port": 9999,
            "max_hover_messages": 5,
            "window_offset_from_taskbar": 30,
            "hover_text_offset": 20,
            "battery_warn_threshold": 20,
            "colors": {
                "outer_circle": "green",
                "head": "lightblue",
                "head_outline": "black",
                "hands": "gray",
                "feet_outline": "black",
                "feet_fill": "white",
                "cpu_arc": "red",
                "vm_arc": "blue",
                "hover_bg": "white",
                "hover_border": "black",
                "status_text": "black",
                "message_text": "blue"
            }
        }

        # 图形坐标定义
        self.coordinates = {
            "outer_circle": Coordinates(34, 34, 166, 166),
            "inner_arc": Coordinates(45, 45, 155, 155),
            "left_foot": Coordinates(70, 106, 94, 130),
            "right_foot": Coordinates(106, 106, 130, 130),
            "left_hand": Coordinates(60, 88, 72, 100),
            "right_hand": Coordinates(128, 88, 140, 100),
            "head": Coordinates(80, 56, 120, 96)
        }

        # 状态变量初始化
        self.msg_count = 0
        self.other_num = 0
        self.messages: List[str] = []
        self.drag_data: Dict[str, int] = {"x": 0, "y": 0}
        self.last_interact: Optional[float] = None
        self.battery_warned = False
        self.cpu_arc = None
        self.vm_arc = None
        self.hover_window: Optional[tk.Toplevel] = None
        self.status_label: Optional[tk.Label] = None

        # 创建主窗口
        self.root = tk.Tk()
        self._setup_main_window()

        # 创建画布和图形元素
        self.canvas = self._create_canvas()
        self._draw_robot_elements()

        # 绑定事件处理
        self._bind_events()

        # 初始化位置
        self._set_initial_position()

        # 启动后台服务和定时任务
        self._start_background_services()
        self.last_interact = self._now()
        self._schedule_tasks()

        # 启动主循环
        self.root.mainloop()

    # 工具方法
    def _now(self) -> float:
        """获取当前时间戳"""
        return time.time()

    # 窗口设置
    def _setup_main_window(self) -> None:
        """配置主窗口属性"""
        self.root.overrideredirect(True)
        self.root.wm_attributes('-transparentcolor', 'white')
        self.root.configure(bg='white')
        self.root.title("Robot Assistant")

    def _create_canvas(self) -> tk.Canvas:
        """创建画布组件"""
        width, height = self.config["canvas_size"]
        return tk.Canvas(
            self.root,
            width=width,
            height=height,
            bg="white",
            highlightthickness=0
        )

    def _set_initial_position(self) -> None:
        """设置窗口初始位置"""
        self.root.update_idletasks()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        win_w, win_h = self.config["canvas_size"]
        
        x = 0
        y = screen_h - win_h - self.config["window_offset_from_taskbar"]
        self.root.geometry(f"{win_w}x{win_h}+{x}+{y}")

    # 绘图方法
    def _draw_robot_elements(self) -> None:
        """绘制机器人所有元素"""
        self.canvas.pack()
        self._draw_outer_circle()
        self._draw_resource_arcs()
        self._draw_body_parts()

    def _draw_outer_circle(self) -> None:
        """绘制外围圆环"""
        coords = self.coordinates["outer_circle"]
        self.canvas.create_oval(
            coords.to_tuple(),
            outline=self.config["colors"]["outer_circle"],
            width=self.config["outline_width"]
        )

    def _draw_body_parts(self) -> None:
        """绘制机器人身体部位"""
        # 头部
        head_coords = self.coordinates["head"]
        self.head_id = self.canvas.create_oval(
            head_coords.to_tuple(),
            fill=self.config["colors"]["head"],
            outline=self.config["colors"]["head_outline"],
            width=2
        )

        # 左右手
        left_hand_coords = self.coordinates["left_hand"]
        right_hand_coords = self.coordinates["right_hand"]
        self.canvas.create_oval(
            left_hand_coords.to_tuple(),
            fill=self.config["colors"]["hands"]
        )
        self.canvas.create_oval(
            right_hand_coords.to_tuple(),
            fill=self.config["colors"]["hands"]
        )

        # 左右脚
        left_foot_coords = self.coordinates["left_foot"]
        right_foot_coords = self.coordinates["right_foot"]
        self.box_left = self.canvas.create_rectangle(
            left_foot_coords.to_tuple(),
            fill=self.config["colors"]["feet_fill"],
            outline=self.config["colors"]["feet_outline"]
        )
        self.box_right = self.canvas.create_rectangle(
            right_foot_coords.to_tuple(),
            fill=self.config["colors"]["feet_fill"],
            outline=self.config["colors"]["feet_outline"]
        )

        # 脚上的数字
        self.text_left = self.canvas.create_text(
            *left_foot_coords.center,
            text=str(self.msg_count),
            font=("Arial", self.config["text_font_sizes"]["small"])
        )
        self.text_right = self.canvas.create_text(
            *right_foot_coords.center,
            text=str(self.other_num),
            font=("Arial", self.config["text_font_sizes"]["small"])
        )

    # 事件绑定
    def _bind_events(self) -> None:
        """绑定所有事件处理函数"""
        # 头部事件
        self.canvas.tag_bind(self.head_id, "<Enter>", self.on_head_enter)
        self.canvas.tag_bind(self.head_id, "<Leave>", self.on_head_leave)
        self.canvas.tag_bind(self.head_id, "<Button-3>", self.on_head_right_click)
        self.canvas.tag_bind(self.head_id, "<Motion>", self.on_head_motion)
        
        # 拖拽事件
        self.canvas.bind("<ButtonPress-1>", self.on_drag_start)
        self.canvas.bind("<B1-Motion>", self.on_drag_motion)
        
        # 交互事件
        self.root.bind_all("<Any-Motion>", self.on_any_interact)
        self.root.bind_all("<Button>", self.on_any_interact)
        self.root.bind_all("<Key>", self.on_any_interact)

    # 定时任务
    def _schedule_tasks(self) -> None:
        """调度所有定时任务"""
        self.update_ui()
        self.check_inactive()
        self.update_status_time()
        self.check_battery()
        self.update_resource_arcs()

    def _start_background_services(self) -> None:
        """启动后台服务"""
        # 启动socket服务器线程
        socket_thread = threading.Thread(
            target=self.start_socket_server,
            daemon=True
        )
        socket_thread.start()

    # 界面更新
    def update_ui(self) -> None:
        """更新UI元素"""
        self.canvas.itemconfig(self.text_left, text=str(self.msg_count))
        self.canvas.itemconfig(self.text_right, text=str(self.other_num))
        self.root.after(self.config["ui_update_interval"], self.update_ui)

    def update_status_time(self) -> None:
        """更新状态时间"""
        current_time_text = f"hi Alex {time.strftime('%H:%M:%S')}"
        if self.hover_window and self.status_label:
            self.status_label.config(text=current_time_text)
        self.root.after(self.config["time_update_interval"], self.update_status_time)

    # 闲置检测
    def check_inactive(self) -> None:
        """检查是否长时间未交互"""
        if self.last_interact:
            now = self._now()
            alpha = 0.2 if now - self.last_interact > self.config["inactive_seconds"] else 1.0
            self.root.wm_attributes('-alpha', alpha)
        self.root.after(1000, self.check_inactive)

    def on_any_interact(self, event: tk.Event) -> None:
        """处理任何交互事件"""
        self.last_interact = self._now()
        self.root.wm_attributes('-alpha', 1.0)

    # Socket服务
    def start_socket_server(self) -> None:
        """启动Socket服务器接收消息"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', self.config["socket_port"]))
                s.listen(5)
                
                while True:
                    conn, _ = s.accept()
                    with conn:
                        data = conn.recv(1024)
                        if data:
                            msg = data.decode(errors="ignore")
                            self.msg_count += 1
                            self.messages.append(msg)
        except Exception as e:
            print(f"Socket server error: {e}")

    # 头部悬停处理
    def on_head_enter(self, event: tk.Event) -> None:
        """鼠标进入头部区域"""
        self.root.config(cursor="hand2")
        self.show_hover_messages(event)
        self.on_any_interact(event)

    def on_head_leave(self, event: tk.Event) -> None:
        """鼠标离开头部区域"""
        self.root.config(cursor="arrow")
        self.hide_hover_messages()
        self.on_any_interact(event)

    def on_head_motion(self, event: tk.Event) -> None:
        """鼠标在头部移动"""
        self.show_hover_messages(event)
        self.on_any_interact(event)

    # 悬停消息窗口
    def show_hover_messages(self, event: tk.Event) -> None:
        """显示悬停消息窗口"""
        self.hide_hover_messages()
        
        # 准备消息内容
        if self.messages:
            msg_text = "\n".join(self.messages[-self.config["max_hover_messages"]:])
        else:
            msg_text = "暂无消息"
            
        status_text = f"hi Alex {time.strftime('%H:%M:%S')}"
        
        # 创建悬停窗口
        self.hover_window = tk.Toplevel(self.root)
        self.hover_window.overrideredirect(True)
        self.hover_window.wm_attributes("-topmost", True)
        
        # 创建内容框架
        frame = tk.Frame(
            self.hover_window,
            bg=self.config["colors"]["hover_bg"],
            padx=10,
            pady=5,
            relief=tk.SOLID,
            bd=1
        )
        frame.pack()
        
        # 状态标签
        self.status_label = tk.Label(
            frame,
            text=status_text,
            font=("Arial", self.config["text_font_sizes"]["medium"]),
            fg=self.config["colors"]["status_text"],
            bg=self.config["colors"]["hover_bg"],
            anchor="w",
            width=20
        )
        self.status_label.pack(fill=tk.X, pady=(0, 5))
        
        # 消息标签
        msg_label = tk.Label(
            frame,
            text=msg_text,
            font=("Arial", self.config["text_font_sizes"]["large"]),
            fg=self.config["colors"]["message_text"],
            bg=self.config["colors"]["hover_bg"],
            justify=tk.LEFT
        )
        msg_label.pack()
        
        # 定位窗口
        robot_right = self.root.winfo_width()
        head_center_y = self.coordinates["head"].center[1]
        
        x = self.root.winfo_rootx() + robot_right + self.config["hover_text_offset"]
        y = self.root.winfo_rooty() + head_center_y
        
        self.hover_window.update_idletasks()
        win_height = self.hover_window.winfo_height()
        self.hover_window.geometry(f"+{x}+{y - win_height//2}")

    def hide_hover_messages(self) -> None:
        """隐藏悬停消息窗口"""
        if self.hover_window:
            self.hover_window.destroy()
            self.hover_window = None
            self.status_label = None

    # 右键菜单处理
    def on_head_right_click(self, event: tk.Event) -> None:
        """头部右键点击事件 - 交换左右脚"""
        # 交换坐标
        self.coordinates["left_foot"], self.coordinates["right_foot"] = \
            self.coordinates["right_foot"], self.coordinates["left_foot"]
        
        # 更新图形位置
        self.canvas.coords(self.box_left, self.coordinates["left_foot"].to_tuple())
        self.canvas.coords(self.box_right, self.coordinates["right_foot"].to_tuple())
        
        # 更新文字位置
        self.canvas.coords(self.text_left, *self.coordinates["left_foot"].center)
        self.canvas.coords(self.text_right, *self.coordinates["right_foot"].center)
        
        self.on_any_interact(event)

    # 拖拽处理
    def on_drag_start(self, event: tk.Event) -> None:
        """开始拖拽"""
        self.drag_data["x"] = event.x_root
        self.drag_data["y"] = event.y_root
        self.on_any_interact(event)

    def on_drag_motion(self, event: tk.Event) -> None:
        """拖拽过程"""
        dx = event.x_root - self.drag_data["x"]
        dy = event.y_root - self.drag_data["y"]
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")
        self.drag_data["x"] = event.x_root
        self.drag_data["y"] = event.y_root
        self.on_any_interact(event)
        
        # 更新悬停窗口位置
        if self.hover_window:
            self.show_hover_messages(event)

    # 电池检查
    def check_battery(self) -> None:
        """检查电池状态"""
        try:
            battery = psutil.sensors_battery()
            if battery:
                if battery.percent <= self.config["battery_warn_threshold"] and not self.battery_warned:
                    self.battery_warned = True
                    messagebox.showwarning(
                        "电量提醒",
                        f"当前电量仅剩 {battery.percent}% ，请及时充电！"
                    )
                elif battery.percent > self.config["battery_warn_threshold"]:
                    self.battery_warned = False
        except Exception:
            pass
            
        self.root.after(self.config["battery_check_interval"], self.check_battery)

    # 资源使用情况显示
    def _draw_resource_arcs(self) -> None:
        """绘制资源使用圆弧"""
        # 获取资源使用百分比
        cpu_percent = psutil.cpu_percent()
        vm_percent = psutil.virtual_memory().percent
        
        # 计算中心点
        inner_arc = self.coordinates["inner_arc"]
        center_x = (inner_arc.left + inner_arc.right) // 2
        
        # 绘制CPU圆弧（左半部分）
        if self.cpu_arc:
            self.canvas.delete(self.cpu_arc)
        self.cpu_arc = self.canvas.create_arc(
            inner_arc.left,
            inner_arc.top,
            center_x * 2 - inner_arc.left,
            inner_arc.bottom,
            start=90,
            extent=180 * cpu_percent / 100,
            style=tk.ARC,
            outline=self.config["colors"]["cpu_arc"],
            width=self.config["inner_arc_width"]
        )
        
        # 绘制内存圆弧（右半部分）
        if self.vm_arc:
            self.canvas.delete(self.vm_arc)
        self.vm_arc = self.canvas.create_arc(
            center_x * 2 - inner_arc.right,
            inner_arc.top,
            inner_arc.right,
            inner_arc.bottom,
            start=90,
            extent=-180 * vm_percent / 100,
            style=tk.ARC,
            outline=self.config["colors"]["vm_arc"],
            width=self.config["inner_arc_width"]
        )

    def update_resource_arcs(self) -> None:
        """更新资源使用圆弧"""
        self._draw_resource_arcs()
        self.root.after(self.config["resource_update_interval"], self.update_resource_arcs)


if __name__ == "__main__":
    RobotApp()