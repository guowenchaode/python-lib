import time
import pyautogui
import traceback
from tkinter import messagebox
from typing import List
from data_models import ScriptCommand

class ScriptExecutor:
    def __init__(self, commands: List[ScriptCommand], config: dict, ui_callbacks: dict):
        self.commands = commands
        self.config = config
        self.ui_callbacks = ui_callbacks
        self.running = False
        self.paused = False
        self.current_index = 0
        self.loop = True
        self.loop_interval = config.get("default_loop_interval", 15)

    def start(self):
        if self.running or not self.commands:
            return

        self.running = True
        self.paused = False
        self.ui_callbacks["on_start"]()

        try:
            while self.running:
                while self.paused and self.running:
                    time.sleep(0.5)

                if self.current_index >= len(self.commands):
                    self.ui_callbacks["on_loop_end"]()
                    if self.loop:
                        self.current_index = 0
                        self._add_countdown_commands()
                    else:
                        break

                cmd = self.commands[self.current_index]
                if cmd.source != "系统倒计时":
                    abs_x, abs_y = self.ui_callbacks["permil_to_absolute"](cmd.x, cmd.y)
                    if self.ui_callbacks["check_foreground"]():
                        pyautogui.click(abs_x, abs_y)
                        pyautogui.press(cmd.key)
                        cmd.status = "已执行"
                    else:
                        cmd.status = "主程序后台，跳过"
                else:
                    cmd.status = "已执行"
                    self.ui_callbacks["update_status"](f"脚本状态：{cmd.key}")
                    time.sleep(1)

                self.ui_callbacks["update_tree"]()
                self.current_index += 1

                if self.ui_callbacks["bubbles_visible"]():
                    self.ui_callbacks["update_bubbles"]()

                time.sleep(pyautogui.PAUSE)

        except Exception as e:
            error_msg = f"脚本执行异常：{str(e)}"
            print(error_msg)
            traceback.print_exc()
            messagebox.showerror("脚本错误", error_msg)
            self.stop()

    def pause(self):
        self.paused = not self.paused
        self.ui_callbacks["on_pause"](self.paused)

    def stop(self):
        self.running = False
        self.paused = False
        self.current_index = 0
        self.ui_callbacks["on_stop"]()
        for cmd in self.commands:
            cmd.status = "未执行"
        self.ui_callbacks["update_tree"]()

    def _add_countdown_commands(self):
        if not self.loop or self.loop_interval <= 0:
            return

        self.commands = [cmd for cmd in self.commands if cmd.source != "系统倒计时"]

        for i in range(int(self.loop_interval), 0, -1):
            self.commands.append(
                ScriptCommand(
                    key=f"倒计时{i}秒",
                    x=0.0,
                    y=0.0,
                    status="未执行",
                    source="系统倒计时",
                )
            )
        self.commands.append(
            ScriptCommand(
                key="倒计时结束", x=0.0, y=0.0, status="未执行", source="系统倒计时"
            )
        )