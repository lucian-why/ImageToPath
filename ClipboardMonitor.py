"""
剪贴板监测器 — 后台轮询检测剪贴板中的图片
参考 ShareX ClipboardMonitor / ClipboardWatcher 的概念
"""
import hashlib
import threading
import time
from io import BytesIO

from ClipboardHelper import contains_image, get_image, copy_file_path
from ScreenshotCapture import save_image, generate_filename
from AppConfig import AppConfig


class ClipboardMonitor:
    """剪贴板图片监测器（后台线程）"""

    def __init__(self, config: AppConfig, on_saved=None, on_error=None):
        self.config = config
        self.on_saved = on_saved or (lambda path: None)
        self.on_error = on_error or (lambda msg: None)
        self._running = False
        self._thread: threading.Thread | None = None
        self._last_image_hash: str = ""

    def start(self):
        """启动监测"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """停止监测"""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def _poll_loop(self):
        """轮询循环"""
        interval = self.config.clipboard_poll_interval / 1000.0
        while self._running:
            try:
                self._check_clipboard()
            except Exception as e:
                self.on_error(f"监测异常: {e}")
            time.sleep(interval)

    def _check_clipboard(self):
        """检查剪贴板是否有新图片"""
        if not self.config.auto_save_clipboard_image:
            return
        if not contains_image():
            return

        img = get_image()
        if img is None:
            return

        # 计算图片哈希，避免重复处理同一张图
        img_hash = self._hash_image(img)
        if img_hash == self._last_image_hash:
            return
        # 保存图片
        filepath = save_image(img, self.config, source="clipboard")
        if filepath is None:
            self.on_error("保存图片失败")
            return

        # 复制文件路径到剪贴板
        if self.config.copy_path_to_clipboard:
            if not copy_file_path(filepath):
                self.on_error("复制文件路径到剪贴板失败")
                return

        self._last_image_hash = img_hash
        self.on_saved(filepath)

    @staticmethod
    def _hash_image(img) -> str:
        """计算图片 MD5 哈希"""
        buf = BytesIO()
        img.save(buf, format="PNG")
        return hashlib.md5(buf.getvalue()).hexdigest()
