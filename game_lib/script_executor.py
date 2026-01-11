import time
import pyautogui
import traceback
from tkinter import messagebox
from typing import List
from data_models import ScriptCommand
from config_manager import CONFIG


class ScriptExecutor:
    def __init__(self, commands: List[ScriptCommand], config: dict, ui_callbacks: dict):
        self.commands = commands
        self.config = config
        self.ui_callbacks = ui_callbacks
        self.running = False
        self.paused = False
        self.current_index = 0
        self.current_loop_count = 0
        self.loop = True
        self.loop_interval = config.get("default_loop_interval", 15)

    def start(self):
        if self.running or not self.commands:
            return

        self.running = True
        self.paused = False
        self.ui_callbacks["on_start"]()

        command_count = len(self.commands)
        print(f"脚本开始执行，共有 {command_count} 条命令。")
        try:
            while self.running:
                try:
                    while self.paused and self.running:
                        print("脚本暂停中...")
                        time.sleep(1)

                    if self.current_index >= len(self.commands):
                        print("脚本循环结束，等待下一轮开始...")
                        self.current_index = 0
                        self.ui_callbacks["on_loop_end"]()

                        left = int(CONFIG["default_loop_interval"])

                        while left > 0 and self.running:
                            print(f"下一轮脚本将在 {left} 秒后开始...")
                            time.sleep(1)
                            left -= 1

                    self.current_loop_count += 1

                    cmd = self.commands[self.current_index]
                    print(
                        f"脚本执行循环中... 当前索引：{self.current_index + 1} / {command_count}, 命令：{cmd}"
                    )
                    action = cmd.action

                    try:
                        if action == "click":
                            abs_x, abs_y = self.ui_callbacks["permil_to_absolute"](
                                cmd.x, cmd.y
                            )
                            if self.ui_callbacks["check_foreground"]():
                                pyautogui.click(abs_x, abs_y)
                                # pyautogui.press(cmd.key)
                                cmd.status = "已执行"
                            else:
                                cmd.status = "主程序后台，跳过"
                        else:
                            cmd.status = "已执行"
                            self.ui_callbacks["update_status"](f"脚本状态：{cmd.key}")
                    except Exception as e:
                        traceback.print_exc()
                    finally:
                        if not self.running:
                            break
                        # self.ui_callbacks["update_tree"]()
                        self.current_index += 1

                        # if self.ui_callbacks["bubbles_visible"]():
                        #     self.ui_callbacks["update_bubbles"]()
                        time.sleep(1)
                except Exception as e:
                    print(f"脚本执行异常：{str(e)}")
                    traceback.print_exc()
                    messagebox.showerror("脚本错误", f"脚本执行异常：{str(e)}")
                    self.stop()
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
