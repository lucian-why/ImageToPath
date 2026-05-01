"""
ImageToPath 主程序入口
- 系统托盘图标 + 菜单
- 全局热键注册（PrintScreen → 截图 → 保存 → 路径入剪贴板）
- 剪贴板监测（后台轮询，检测到图片自动保存）
- 单实例运行
"""
import os
import sys
import threading
import subprocess
import ctypes
from ctypes import wintypes
from typing import Optional

import pystray
from PIL import Image as PILImage, ImageDraw
import win32con

from AppConfig import load_config, save_config, AppConfig
from ClipboardHelper import copy_file_path, copy_image
from ScreenshotCapture import capture_fullscreen, capture_region, save_image
from ClipboardMonitor import ClipboardMonitor

# ——— 全局状态 ———
_config: AppConfig = None
_monitor: ClipboardMonitor = None
_tray_icon: pystray.Icon = None
_instance_mutex_handle: Optional[int] = None

# ——— 全局热键 ID ———
HOTKEY_REGION_ID = 1      # PrintScreen → 区域截图
HOTKEY_FULLSCREEN_ID = 2  # Ctrl+PrintScreen → 全屏截图
_wm_hotkey_stop = False
_hotkey_thread = None

# ——— Windows API 常量 ———
WM_HOTKEY = 0x0312
MOD_NOREPEAT = 0x4000
ERROR_ALREADY_EXISTS = 183
SINGLE_INSTANCE_MUTEX_NAME = "Local\\ImageToPath.SingleInstance"


def acquire_single_instance_lock() -> bool:
    """用命名 Mutex 保证 exe 和 pythonw 开发模式都只运行一个实例。"""
    global _instance_mutex_handle
    kernel32 = ctypes.windll.kernel32
    kernel32.CreateMutexW.restype = wintypes.HANDLE
    kernel32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.SetLastError(0)
    handle = kernel32.CreateMutexW(None, False, SINGLE_INSTANCE_MUTEX_NAME)
    if not handle:
        return True
    if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
        kernel32.CloseHandle(handle)
        return False
    _instance_mutex_handle = handle
    return True


def release_single_instance_lock():
    """释放单实例 Mutex。"""
    global _instance_mutex_handle
    if _instance_mutex_handle:
        try:
            ctypes.windll.kernel32.CloseHandle(_instance_mutex_handle)
        except Exception:
            pass
        _instance_mutex_handle = None


def cleanup_on_exit():
    """退出时清理托盘图标"""
    global _wm_hotkey_stop, _monitor, _tray_icon
    _wm_hotkey_stop = True
    if _monitor:
        try:
            _monitor.stop()
        except Exception:
            pass
    if _tray_icon:
        try:
            _tray_icon.visible = False
            _tray_icon.stop()
        except Exception:
            pass
    release_single_instance_lock()


def _browse_folder_powershell(title: str = "选择文件夹") -> str | None:
    """通过独立 PowerShell 进程打开文件夹选择器，不受主程序消息泵影响"""
    ps_code = f'''
Add-Type -AssemblyName System.Windows.Forms
$d = New-Object System.Windows.Forms.FolderBrowserDialog
$d.Description = "{title}"
$d.ShowNewFolderButton = $true
if ($d.ShowDialog() -eq "OK") {{ $d.SelectedPath }}
'''
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_code],
            capture_output=True, text=True, timeout=60, creationflags=subprocess.CREATE_NO_WINDOW
        )
        folder = result.stdout.strip()
        return folder if folder else None
    except Exception:
        return None


def create_tray_icon_image():
    """创建托盘图标（简单的相机图标）"""
    img = PILImage.new("RGBA", (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # 画一个简单的相机/图片图标
    draw.rectangle([4, 8, 28, 24], fill="white", outline="white")
    draw.rectangle([12, 12, 20, 20], fill="black")
    draw.rectangle([8, 4, 14, 8], fill="white")
    return img


def on_screenshot():
    """热键回调：全屏截图 → 复制图片到剪贴板"""
    try:
        img = capture_fullscreen()
        if img is None:
            notify("截图失败", "无法获取屏幕截图")
            return

        if not copy_image(img):
            notify("复制失败", "无法复制全屏截图到剪贴板")
            return

        if _config.show_notification:
            notify("截图已复制", "全屏截图已放入剪贴板")
    except Exception as e:
        notify("错误", str(e))


def on_region_capture():
    """区域截图 → 保存 → 复制路径"""
    try:
        img = capture_region()
        if img is None:
            return  # 用户取消了

        filepath = save_image(img, _config, source="region")
        if filepath is None:
            notify("保存失败", "无法保存截图")
            return

        if _config.copy_path_to_clipboard:
            copy_file_path(filepath)

        if _config.show_notification:
            notify("截图已保存", filepath)
    except Exception as e:
        notify("错误", str(e))


def on_clipboard_image_saved(filepath: str):
    """剪贴板图片保存回调"""
    if _config.show_notification:
        notify("图片已保存", filepath)


def notify(title: str, message: str):
    """弹出托盘通知"""
    try:
        if _tray_icon:
            _tray_icon.notify(message, title)
    except Exception:
        pass


def mark_welcome_shown(config: AppConfig) -> bool:
    """标记欢迎弹窗已显示。"""
    old_value = config.show_welcome_on_startup
    config.show_welcome_on_startup = False
    if save_config(config):
        return True
    config.show_welcome_on_startup = old_value
    return False


def show_welcome_window():
    """首次启动说明窗口。关闭后程序继续留在托盘。"""
    try:
        import tkinter as tk
        from tkinter import ttk

        root = tk.Tk()
        root.title("ImageToPath")
        root.resizable(False, False)
        root.attributes("-topmost", True)

        width, height = 460, 320
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()
        x = max((screen_w - width) // 2, 0)
        y = max((screen_h - height) // 2, 0)
        root.geometry(f"{width}x{height}+{x}+{y}")

        frame = ttk.Frame(root, padding=20)
        frame.pack(fill="both", expand=True)

        title = ttk.Label(frame, text="ImageToPath 已在后台运行", font=("", 14, "bold"))
        title.pack(anchor="w")

        message = (
            "这个工具会把剪贴板里的图片或截图保存成文件，"
            "然后把图片文件路径放回剪贴板。\n\n"
            "解决的问题：不用先手动保存图片、再复制文件地址。"
            "复制图片后直接 Ctrl+V，就能粘贴保存后的路径。\n\n"
            "PrintScreen 会被本软件接管为区域截图并复制文件路径；"
            "Ctrl+PrintScreen 会把全屏截图图片放入剪贴板。\n\n"
            "关闭这个窗口不会退出程序。以后请在右下角系统托盘里"
            "右键 ImageToPath 图标进行设置、打开保存目录或退出。"
        )
        body = ttk.Label(frame, text=message, wraplength=420, justify="left")
        body.pack(anchor="w", pady=(14, 18))

        def close_window():
            mark_welcome_shown(_config)
            root.destroy()

        button_row = ttk.Frame(frame)
        button_row.pack(fill="x")
        ttk.Button(button_row, text="打开保存目录", command=lambda: menu_open_folder(None, None)).pack(side="left")
        ttk.Button(button_row, text="知道了，收进托盘", command=close_window).pack(side="right")

        root.protocol("WM_DELETE_WINDOW", close_window)
        root.mainloop()
    except Exception:
        try:
            mark_welcome_shown(_config)
        except Exception:
            pass


def maybe_show_welcome_window():
    """首次启动时显示说明；关闭后继续进入托盘。"""
    if _config and _config.show_welcome_on_startup:
        show_welcome_window()


def apply_save_folder(config: AppConfig, folder: str) -> tuple[bool, str]:
    """创建并验证目录成功后，再写入配置。失败时不污染当前配置。"""
    if not folder:
        return False, "未选择保存目录"

    new_folder = os.path.abspath(os.path.expanduser(folder))
    old_folder = config.save_folder

    try:
        os.makedirs(new_folder, exist_ok=True)
        if not os.path.isdir(new_folder):
            return False, "保存目录不是有效文件夹"

        test_path = os.path.join(new_folder, ".ImageToPath_write_test.tmp")
        with open(test_path, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(test_path)

        config.save_folder = new_folder
        if not save_config(config):
            config.save_folder = old_folder
            return False, "配置保存失败"

        return True, new_folder
    except Exception as e:
        config.save_folder = old_folder
        return False, str(e)


# ——— 托盘菜单 ———

def menu_capture_fullscreen(icon, item):
    threading.Thread(target=on_screenshot, daemon=True).start()


def menu_capture_region(icon, item):
    threading.Thread(target=on_region_capture, daemon=True).start()


def menu_open_folder(icon, item):
    try:
        os.makedirs(_config.save_folder, exist_ok=True)
        os.startfile(_config.save_folder)
    except Exception as e:
        notify("打开目录失败", str(e))


def menu_toggle_monitor(icon, item):
    old_value = _config.auto_save_clipboard_image
    _config.auto_save_clipboard_image = not item.checked
    if not save_config(_config):
        _config.auto_save_clipboard_image = old_value
        notify("保存配置失败", "无法更改剪贴板监测状态")
        return
    if _config.auto_save_clipboard_image:
        _monitor.start()
    else:
        _monitor.stop()


def menu_change_folder(icon, item):
    """更改保存目录 — 使用 Windows 原生文件夹选择对话框"""
    threading.Thread(target=_change_folder_worker, daemon=True).start()


def _change_folder_worker():
    """后台执行目录选择，避免阻塞托盘菜单。"""
    folder = _browse_folder_powershell("选择截图保存目录")
    if not folder:
        return
    ok, message = apply_save_folder(_config, folder)
    if ok:
        notify("保存目录已更改", message)
    else:
        notify("保存目录更改失败", message)


def menu_quit(icon, item):
    global _wm_hotkey_stop
    _wm_hotkey_stop = True
    _monitor.stop()
    _tray_icon.stop()


# ——— 全局热键 ———

def _hotkey_thread_func():
    """使用 Win32 RegisterHotKey 注册全局热键"""
    global _wm_hotkey_stop

    # PrintScreen → 区域截图
    if not ctypes.windll.user32.RegisterHotKey(None, HOTKEY_REGION_ID, 0, win32con.VK_SNAPSHOT):
        notify("热键注册失败", "PrintScreen 已被占用")
    # Ctrl+PrintScreen → 全屏截图
    if not ctypes.windll.user32.RegisterHotKey(None, HOTKEY_FULLSCREEN_ID, win32con.MOD_CONTROL, win32con.VK_SNAPSHOT):
        notify("热键注册失败", "Ctrl+PrintScreen 已被占用")

    # 消息循环
    msg = wintypes.MSG()
    while not _wm_hotkey_stop:
        # 使用 PeekMessage 非阻塞轮询
        if ctypes.windll.user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):  # PM_REMOVE
            if msg.message == WM_HOTKEY:
                if msg.wParam == HOTKEY_REGION_ID:
                    threading.Thread(target=on_region_capture, daemon=True).start()
                elif msg.wParam == HOTKEY_FULLSCREEN_ID:
                    threading.Thread(target=on_screenshot, daemon=True).start()
            ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
            ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))
        else:
            # 没有消息时短暂休眠
            ctypes.windll.kernel32.Sleep(10)

    # 清理
    ctypes.windll.user32.UnregisterHotKey(None, HOTKEY_REGION_ID)
    ctypes.windll.user32.UnregisterHotKey(None, HOTKEY_FULLSCREEN_ID)


def start_hotkey_listener():
    """启动全局热键监听线程"""
    global _hotkey_thread
    _hotkey_thread = threading.Thread(target=_hotkey_thread_func, daemon=True)
    _hotkey_thread.start()


# ——— 主入口 ———

def main():
    global _config, _monitor, _tray_icon

    if not acquire_single_instance_lock():
        return

    # 注册退出清理
    import atexit
    atexit.register(cleanup_on_exit)

    # 确保保存目录存在
    _config = load_config()
    os.makedirs(_config.save_folder, exist_ok=True)

    # 启动剪贴板监测
    _monitor = ClipboardMonitor(_config, on_saved=on_clipboard_image_saved)
    if _config.auto_save_clipboard_image:
        _monitor.start()

    # 启动全局热键
    start_hotkey_listener()

    # 创建托盘图标
    tray_image = create_tray_icon_image()

    menu = pystray.Menu(
        pystray.MenuItem("区域截图 (PrintScreen)", menu_capture_region, default=True),
        pystray.MenuItem("复制全屏截图 (Ctrl+PrintScreen)", menu_capture_fullscreen),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(
            "自动保存剪贴板图片",
            menu_toggle_monitor,
            checked=lambda item: _config.auto_save_clipboard_image,
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("更改保存目录...", menu_change_folder),
        pystray.MenuItem("打开保存目录", menu_open_folder),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("退出", menu_quit),
    )

    _tray_icon = pystray.Icon(
        "ImageToPath",
        tray_image,
        "ImageToPath - 截图保存到剪贴板路径",
        menu,
    )

    maybe_show_welcome_window()

    # 双击托盘图标 → 全屏截图
    # pystray 不直接支持双击，用默认菜单项代替

    _tray_icon.run()


if __name__ == "__main__":
    main()
