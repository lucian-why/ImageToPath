"""
配置管理 — JSON 读写 + 默认值
"""
import json
import os
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

# PyInstaller 打包后: sys.frozen=True, 配置存 exe 同目录
# 开发模式: 配置存脚本同目录
if getattr(sys, "frozen", False):
    _app_dir = os.path.dirname(os.path.abspath(sys.executable))
else:
    _app_dir = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(_app_dir, "AppConfig.json")


@dataclass
class AppConfig:
    """应用配置，参考 ShareX TaskSettings"""
    # 保存路径
    save_folder: str = os.path.join(os.path.expanduser("~"), "Pictures", "Screenshots")

    # 文件名格式（支持 {yyyy}{MM}{dd}{HH}{mm}{ss}{random4} 占位符）
    file_name_format: str = "{yyyy}{MM}{dd}_{HH}{mm}{ss}"

    # 图片格式: png, jpg, bmp
    image_format: str = "png"

    # JPEG 质量（仅 jpg 格式有效）
    jpeg_quality: int = 90

    # 自动保存剪贴板中的图片
    auto_save_clipboard_image: bool = True

    # 复制路径到剪贴板
    copy_path_to_clipboard: bool = True

    # 显示托盘通知
    show_notification: bool = True

    # 截图热键描述（仅供参考，实际热键在代码中注册）
    hotkey_screenshot: str = "print_screen"        # 区域截图
    hotkey_fullscreen: str = "ctrl+print_screen"   # 全屏截图

    # 最小化到托盘
    minimize_to_tray: bool = True

    # 剪贴板轮询间隔（毫秒）
    clipboard_poll_interval: int = 500

    # 开机自启
    start_with_windows: bool = False

    # 首次启动显示欢迎说明
    show_welcome_on_startup: bool = True


def load_config() -> AppConfig:
    """加载配置，不存在则创建默认"""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 合并：JSON 覆盖默认值，保留新增字段
            defaults = asdict(AppConfig())
            defaults.update(data)
            # 处理可能的旧版字段
            valid_keys = {f.name for f in AppConfig.__dataclass_fields__.values()}
            filtered = {k: v for k, v in defaults.items() if k in valid_keys}
            return AppConfig(**filtered)
        except Exception:
            pass

    # 创建默认配置
    config = AppConfig()
    save_config(config)
    return config


def save_config(config: AppConfig) -> bool:
    """保存配置到文件"""
    try:
        data = asdict(config)
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False
