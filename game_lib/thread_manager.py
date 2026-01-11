import threading
import time
import pyautogui
from typing import Callable, List
from data_models import DiabloWindowInfo

class ThreadManager:
    def __init__(self, config, ui_callbacks):
        self.config = config
        self.ui_callbacks = ui_callbacks
        self.monitor_event = threading.Event()
        self.monitor_event.set()

    def start_threads(self):
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
            if current_time - last_update_time < self.config["monitor_window_interval"]:
                time.sleep(0.05)
                continue

            try:
                windows_info = self.ui_callbacks["get_diablo_windows"]()
                self.ui_callbacks["update_window_tree"](windows_info)
                self.ui_callbacks["update_status_label"]()

                if (
                    self.ui_callbacks["script_running"]()
                    and self.ui_callbacks["stop_on_background"]()
                    and not self.ui_callbacks["check_main_window_foreground"]()
                ):
                    self.ui_callbacks["stop_script"]()

                if (
                    self.ui_callbacks["bubbles_visible"]()
                    and self.ui_callbacks["script_commands"]()
                ):
                    self.ui_callbacks["create_bubbles"]()

                last_update_time = current_time
            except Exception as e:
                print(f"窗口监控异常：{e}")
                time.sleep(self.config["monitor_window_interval"])

    def _monitor_mouse(self):
        last_mouse_pos = (0, 0)
        while self.monitor_event.is_set():
            try:
                mouse_x, mouse_y = pyautogui.position()
                print(f"鼠标位置：{mouse_x}, {mouse_y}")
                if (mouse_x, mouse_y) == last_mouse_pos:
                    time.sleep(self.config["monitor_mouse_interval"])
                    continue

                rel_x_permil, rel_y_permil = "--", "--"
                if self.ui_callbacks["main_window"]():
                    win_left, win_top, win_w, win_h = self.ui_callbacks["main_window_geometry"]()

                    if (
                        win_left <= mouse_x <= win_left + win_w
                        and win_top <= mouse_y <= win_top + win_h
                    ):
                        rel_x_permil = round((mouse_x - win_left) / win_w, 3)
                        rel_y_permil = round((mouse_y - win_top) / win_h, 3)

                self.ui_callbacks["update_mouse_info"](mouse_x, mouse_y, rel_x_permil, rel_y_permil)
                last_mouse_pos = (mouse_x, mouse_y)
                time.sleep(self.config["monitor_mouse_interval"])
            except Exception as e:
                print(f"鼠标监控异常：{e}")
                time.sleep(self.config["monitor_mouse_interval"])