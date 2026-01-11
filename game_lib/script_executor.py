import time
import pyautogui
import traceback
from tkinter import messagebox
from typing import List
from data_models import ScriptCommand
from config_manager import CONFIG


class ScriptExecutor:
    def __init__(self, commands: List[ScriptCommand]):
        self.commands = commands
        self.running = False
        self.paused = False
        self.current_index = 0
        self.current_loop_count = 1
        self.loop = True
        self.loop_interval = CONFIG["default_loop_interval"]

    def toggle_pause(self):
        self.paused = not self.paused

    def resume(self):
        self.paused = False

    def stop(self):
        self.running = False

    def execute_next(self):
        try:
            cmd = self.commands[self.current_index]
            cmd_info = f"命令：{cmd.key}, 坐标：({cmd.abs_x}, {cmd.abs_y})"
            print(
                f"[{self.current_loop_count}] 脚本执行循环中... 当前索引：{self.current_index + 1} / {len(self.commands)}, 命令：{cmd_info}"
            )
            action = cmd.action

            is_ignored = (
                cmd.loop_count > 0
                and self.current_loop_count > 0
                and self.current_loop_count % cmd.loop_count != 0
            )

            if is_ignored:
                print(
                    f"命令 {cmd.key} 被忽略，循环计数：{cmd.loop_count} / {self.current_loop_count}"
                )
                return
            elif action == "click":
                pyautogui.click(cmd.abs_x, cmd.abs_y)
                cmd.status = "已执行"
            else:
                cmd.status = "已执行"
        except Exception as e:
            traceback.print_exc()
        finally:
            self.current_index += 1
            time.sleep(1)

    def wait_next_loop(self):
        print(f"[{self.current_loop_count}] 脚本循环结束，等待下一轮开始...")
        # self.ui_callbacks["on_loop_end"]()

        left = int(self.loop_interval)

        while left > 0 and self.running:
            print(f"[{self.current_loop_count}] 下一轮脚本将在 {left} 秒后开始...")
            time.sleep(1)
            left -= 1

        self.current_index = 0
        self.current_loop_count += 1

    def check_status(self):
        while self.paused and self.running:
            print("脚本暂停中...")
            time.sleep(1)

    def start(self):
        if self.running or not self.commands:
            return

        self.running = True
        self.paused = False
        # self.ui_callbacks["on_start"]()

        command_count = len(self.commands)
        print(f"脚本开始执行，共有 {command_count} 条命令。")
        try:
            while self.running:
                try:
                    self.check_status()

                    if self.current_index >= 0 and self.current_index < command_count:
                        self.execute_next()
                    else:
                        self.wait_next_loop()
                except Exception as e:
                    print(f"脚本执行异常：{str(e)}")
                    traceback.print_exc()
        except Exception as e:
            error_msg = f"脚本执行异常：{str(e)}"
            print(error_msg)
            traceback.print_exc()
            messagebox.showerror("脚本错误", error_msg)
