from tkinter import ttk
from tkinter import messagebox
import tkinter as tk
import os
import configparser
from config_manager import config_path, CONFIG


class ConfigFrame:
    def __init__(self, parent, reload_config):
        self.parent = parent
        self.reload_config = reload_config

        self.config_frame = ttk.LabelFrame(parent, text="配置管理", padding=10)
        self.config_frame.pack(fill=tk.X, padx=20, pady=5)

        export_config_btn = ttk.Button(
            self.config_frame,
            text="导出当前配置到settings.properties",
            command=self.export_settings,
        )
        export_config_btn.pack(side=tk.LEFT, padx=5)

        reload_config_btn = ttk.Button(
            self.config_frame, text="重新加载配置文件", command=self.reload_config
        )
        reload_config_btn.pack(side=tk.LEFT, padx=5)

        config_path_label = ttk.Label(
            self.config_frame,
            text=f"当前配置文件：{os.path.abspath(config_path)}",
            font=CONFIG["normal_font"],
        )
        config_path_label.pack(side=tk.LEFT, padx=20)

        self.load_settings()

    def load_settings(self):
        """Load configuration file, create default if missing."""
        self.config = configparser.ConfigParser()
        self.default_config = {
            "pyautogui_pause": "0.1",
            "pyautogui_failsafe": "False",
            "monitor_window_interval": "0.5",
            "monitor_mouse_interval": "0.01",
            "default_loop_interval": "15",
            "bubble_alpha": "0.5",
            "bubble_font": "微软雅黑,10,bold",
            "title_font": "微软雅黑,14,bold",
            "normal_font": "微软雅黑,10",
            "highlight_bubble_color": "#ff4444",
            "normal_bubble_color": "#4444ff",
            "main_window_tag_color": "#e8f4f8",
        }

        if not os.path.exists(config_path):
            self.config["SETTINGS"] = self.default_config
            with open(config_path, "w", encoding="utf-8") as f:
                self.config.write(f)
            messagebox.showinfo(
                "提示", f"未找到配置文件，已创建默认配置：{config_path}"
            )
            self.config = self.default_config
            return

        try:
            self.config.read(config_path, encoding="utf-8")
            loaded_config = {}
            for key, default_value in self.default_config.items():
                loaded_config[key] = self.config.get(
                    "SETTINGS", key, fallback=default_value
                )

            # Type conversion
            loaded_config["pyautogui_pause"] = float(loaded_config["pyautogui_pause"])
            loaded_config["pyautogui_failsafe"] = self.config.getboolean(
                "SETTINGS", "pyautogui_failsafe", fallback=False
            )
            loaded_config["monitor_window_interval"] = float(
                loaded_config["monitor_window_interval"]
            )
            loaded_config["monitor_mouse_interval"] = float(
                loaded_config["monitor_mouse_interval"]
            )
            loaded_config["default_loop_interval"] = int(
                loaded_config["default_loop_interval"]
            )
            loaded_config["bubble_alpha"] = float(loaded_config["bubble_alpha"])

            # Font format conversion
            for font_key in ["bubble_font", "title_font", "normal_font"]:
                font_parts = loaded_config[font_key].split(",")
                font_name = font_parts[0]
                font_size = int(font_parts[1]) if len(font_parts) > 1 else 10
                font_weight = font_parts[2] if len(font_parts) > 2 else ""
                loaded_config[font_key] = (
                    (font_name, font_size, font_weight)
                    if font_weight
                    else (font_name, font_size)
                )

            self.config = loaded_config
        except Exception as e:
            messagebox.showerror(
                "配置加载错误", f"配置文件读取失败，使用默认配置：{str(e)}"
            )
            self.config = self.default_config

    def export_settings(self):
        """Export current configuration to file."""
        config = configparser.ConfigParser()
        export_dict = {}

        for key, value in self.config.items():
            if isinstance(value, tuple) and all(
                isinstance(x, (str, int)) for x in value
            ):
                export_dict[key] = ",".join(map(str, value))
            elif isinstance(value, (int, float, bool, str)):
                export_dict[key] = str(value)
            else:
                export_dict[key] = str(value)

        config["SETTINGS"] = export_dict

        try:
            with open(config_path, "w", encoding="utf-8") as f:
                config.write(f)
            messagebox.showinfo("成功", f"配置已导出到：{os.path.abspath(config_path)}")
        except Exception as e:
            messagebox.showerror("导出失败", f"配置导出失败：{str(e)}")

    def reload_settings(self):
        self.load_settings()
        messagebox.showinfo("成功", "配置文件已重新加载！")


import configparser
import os
from tkinter import messagebox


def load_settings(config_path: str = "settings.properties") -> dict:
    """Load configuration file, create default if missing."""
    config = configparser.ConfigParser()
    default_config = {
        "pyautogui_pause": "0.1",
        "pyautogui_failsafe": "False",
        "monitor_window_interval": "0.5",
        "monitor_mouse_interval": "0.01",
        "default_loop_interval": "15",
        "bubble_alpha": "0.5",
        "bubble_font": "微软雅黑,10,bold",
        "title_font": "微软雅黑,14,bold",
        "normal_font": "微软雅黑,10",
        "highlight_bubble_color": "#ff4444",
        "normal_bubble_color": "#4444ff",
        "main_window_tag_color": "#e8f4f8",
    }

    if not os.path.exists(config_path):
        config["SETTINGS"] = default_config
        with open(config_path, "w", encoding="utf-8") as f:
            config.write(f)
        messagebox.showinfo("提示", f"未找到配置文件，已创建默认配置：{config_path}")
        return default_config

    try:
        config.read(config_path, encoding="utf-8")
        loaded_config = {}
        for key, default_value in default_config.items():
            loaded_config[key] = config.get("SETTINGS", key, fallback=default_value)

        # Type conversion
        loaded_config["pyautogui_pause"] = float(loaded_config["pyautogui_pause"])
        loaded_config["pyautogui_failsafe"] = config.getboolean(
            "SETTINGS", "pyautogui_failsafe", fallback=False
        )
        loaded_config["monitor_window_interval"] = float(
            loaded_config["monitor_window_interval"]
        )
        loaded_config["monitor_mouse_interval"] = float(
            loaded_config["monitor_mouse_interval"]
        )
        loaded_config["default_loop_interval"] = int(
            loaded_config["default_loop_interval"]
        )
        loaded_config["bubble_alpha"] = float(loaded_config["bubble_alpha"])

        # Font format conversion
        for font_key in ["bubble_font", "title_font", "normal_font"]:
            font_parts = loaded_config[font_key].split(",")
            font_name = font_parts[0]
            font_size = int(font_parts[1]) if len(font_parts) > 1 else 10
            font_weight = font_parts[2] if len(font_parts) > 2 else ""
            loaded_config[font_key] = (
                (font_name, font_size, font_weight)
                if font_weight
                else (font_name, font_size)
            )

        return loaded_config
    except Exception as e:
        messagebox.showerror(
            "配置加载错误", f"配置文件读取失败，使用默认配置：{str(e)}"
        )
        return default_config


def export_settings(config_dict: dict, config_path: str = "settings.properties"):
    """Export current configuration to file."""
    config = configparser.ConfigParser()
    export_dict = {}

    for key, value in config_dict.items():
        if isinstance(value, tuple) and all(isinstance(x, (str, int)) for x in value):
            export_dict[key] = ",".join(map(str, value))
        elif isinstance(value, (int, float, bool, str)):
            export_dict[key] = str(value)
        else:
            export_dict[key] = str(value)

    config["SETTINGS"] = export_dict

    try:
        with open(config_path, "w", encoding="utf-8") as f:
            config.write(f)
        messagebox.showinfo("成功", f"配置已导出到：{os.path.abspath(config_path)}")
    except Exception as e:
        messagebox.showerror("导出失败", f"配置导出失败：{str(e)}")
