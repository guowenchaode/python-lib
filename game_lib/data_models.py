from dataclasses import dataclass
from typing import Tuple, Optional
import pygetwindow as gw

@dataclass
class ScriptCommand:
    key: str
    x: float
    y: float
    status: str = "未执行"
    source: str = "用户导入"

@dataclass
class DiabloWindowInfo:
    window_obj: gw.Window
    title: str
    pos: str
    size: str
    status: str
    is_active: bool