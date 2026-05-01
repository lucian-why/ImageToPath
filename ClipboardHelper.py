"""
剪贴板操作 — 精简自 ShareX ClipboardHelpers.cs
支持文本写入、图片获取、文件路径复制
"""
import time
import ctypes
import threading
import struct
from io import BytesIO
from typing import Optional

import win32con
import win32clipboard
from PIL import Image

# ShareX 中的重试机制：最多重试 10 次，间隔 100ms
RETRY_TIMES = 10
RETRY_DELAY = 0.1

_clipboard_lock = threading.Lock()


def copy_text(text: str) -> bool:
    """复制文本到剪贴板，带重试机制（同 ShareX）"""
    if not text:
        return False

    for attempt in range(RETRY_TIMES):
        try:
            with _clipboard_lock:
                win32clipboard.OpenClipboard()
                try:
                    win32clipboard.EmptyClipboard()
                    win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
                finally:
                    win32clipboard.CloseClipboard()
            return True
        except Exception:
            if attempt < RETRY_TIMES - 1:
                time.sleep(RETRY_DELAY)
    return False


def copy_file_path(path: str) -> bool:
    """复制文件路径到剪贴板（同时放文本和文件拖放格式）"""
    if not path:
        return False

    import os
    for attempt in range(RETRY_TIMES):
        try:
            with _clipboard_lock:
                win32clipboard.OpenClipboard()
                try:
                    win32clipboard.EmptyClipboard()
                    win32clipboard.SetClipboardText(path, win32clipboard.CF_UNICODETEXT)
                    try:
                        win32clipboard.SetClipboardData(win32con.CF_HDROP, _build_hdrop_data(path))
                    except Exception:
                        pass
                finally:
                    win32clipboard.CloseClipboard()
            return True
        except Exception:
            if attempt < RETRY_TIMES - 1:
                time.sleep(RETRY_DELAY)
    return False


def copy_image(img: Image.Image) -> bool:
    """复制 PIL Image 到剪贴板，保留为图片数据。"""
    if img is None:
        return False

    data = _image_to_dib_bytes(img)
    for attempt in range(RETRY_TIMES):
        try:
            with _clipboard_lock:
                win32clipboard.OpenClipboard()
                try:
                    win32clipboard.EmptyClipboard()
                    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
                finally:
                    win32clipboard.CloseClipboard()
            return True
        except Exception:
            if attempt < RETRY_TIMES - 1:
                time.sleep(RETRY_DELAY)
    return False


def _image_to_dib_bytes(img: Image.Image) -> bytes:
    """将 PIL Image 转为剪贴板 CF_DIB 数据。"""
    save_img = img
    if save_img.mode not in ("RGB", "RGBA"):
        save_img = save_img.convert("RGB")

    buf = BytesIO()
    save_img.save(buf, "BMP")
    return buf.getvalue()[14:]


def _build_hdrop_data(path: str) -> bytes:
    """构造 CF_HDROP Unicode DROPFILES 数据。"""
    header = struct.pack("<IiiII", 20, 0, 0, 0, 1)
    file_list = path.encode("utf-16le") + b"\x00\x00\x00\x00"
    return header + file_list


def contains_image() -> bool:
    """检查剪贴板是否包含图片"""
    try:
        with _clipboard_lock:
            win32clipboard.OpenClipboard()
            try:
                # 检查多种图片格式
                for fmt in [win32clipboard.CF_DIB, win32clipboard.CF_BITMAP, win32clipboard.CF_DIBV5]:
                    try:
                        if win32clipboard.IsClipboardFormatAvailable(fmt):
                            return True
                    except Exception:
                        pass
                return False
            finally:
                win32clipboard.CloseClipboard()
    except Exception:
        return False


def get_image() -> Optional[Image.Image]:
    """从剪贴板获取图片，参考 ShareX GetImage 的多格式降级策略"""
    try:
        with _clipboard_lock:
            win32clipboard.OpenClipboard()
            try:
                # 优先尝试 DIB（设备无关位图）
                if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB):
                    try:
                        data = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)
                        return _dib_to_image(data)
                    except Exception:
                        pass

                # 尝试 DIBV5
                if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIBV5):
                    try:
                        data = win32clipboard.GetClipboardData(win32clipboard.CF_DIBV5)
                        return _dibv5_to_image(data)
                    except Exception:
                        pass

                # 尝试 BITMAP (GDI 位图)
                if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_BITMAP):
                    try:
                        data = win32clipboard.GetClipboardData(win32clipboard.CF_BITMAP)
                        return _bitmap_to_image(data)
                    except Exception:
                        pass

                return None
            finally:
                win32clipboard.CloseClipboard()
    except Exception:
        return None


def _dib_to_image(data: bytes) -> Optional[Image.Image]:
    """将 DIB 数据转为 PIL Image"""
    try:
        # DIB 文件头是 BITMAPFILEHEADER(14) + BITMAPINFOHEADER(40)
        # 剪贴板中的 DIB 不带 BITMAPFILEHEADER
        from io import BytesIO
        import struct

        # 解析 BITMAPINFOHEADER
        header_size = struct.unpack_from('I', data, 0)[0]
        width = struct.unpack_from('i', data, 4)[0]
        height = struct.unpack_from('i', data, 8)[0]
        bit_count = struct.unpack_from('H', data, 14)[0]

        # 构建完整的 BMP 文件头
        bmp_header = bytearray(14)
        bmp_header[0:2] = b'BM'
        file_size = 14 + len(data)
        struct.pack_into('<I', bmp_header, 2, file_size)
        struct.pack_into('<I', bmp_header, 10, 14 + header_size)

        bmp_data = bytes(bmp_header) + data
        return Image.open(BytesIO(bmp_data)).copy()

    except Exception:
        return None


def _dibv5_to_image(data: bytes) -> Optional[Image.Image]:
    """将 DIBV5 数据转为 PIL Image"""
    try:
        from io import BytesIO

        bmp_header = bytearray(14)
        bmp_header[0:2] = b'BM'
        file_size = 14 + len(data)
        import struct
        struct.pack_into('<I', bmp_header, 2, file_size)
        struct.pack_into('<I', bmp_header, 10, 14 + struct.unpack_from('I', data, 0)[0])

        bmp_data = bytes(bmp_header) + data
        return Image.open(BytesIO(bmp_data)).copy()
    except Exception:
        return None


def _bitmap_to_image(handle) -> Optional[Image.Image]:
    """将 GDI Bitmap handle 转为 PIL Image"""
    try:
        from win32gui import GetObject
        import struct

        # GetObject 获取位图信息
        bm = GetObject(handle, 24, None)
        if bm:
            width, height, _, bpp = struct.unpack_from('iiHH', bm, 4)
            if width <= 0 or height <= 0:
                return None

            # 使用 win32 API 获取像素数据
            import win32ui
            import win32gui
            import win32con

            hdc = win32gui.GetDC(0)
            try:
                memdc = win32gui.CreateCompatibleDC(hdc)
                try:
                    old_bmp = win32gui.SelectObject(memdc, handle)
                    try:
                        # 创建 BITMAPINFO
                        import ctypes
                        class BITMAPINFOHEADER(ctypes.Structure):
                            _fields_ = [
                                ("biSize", ctypes.c_uint32),
                                ("biWidth", ctypes.c_int32),
                                ("biHeight", ctypes.c_int32),
                                ("biPlanes", ctypes.c_uint16),
                                ("biBitCount", ctypes.c_uint16),
                                ("biCompression", ctypes.c_uint32),
                                ("biSizeImage", ctypes.c_uint32),
                                ("biXPelsPerMeter", ctypes.c_int32),
                                ("biYPelsPerMeter", ctypes.c_int32),
                                ("biClrUsed", ctypes.c_uint32),
                                ("biClrImportant", ctypes.c_uint32),
                            ]

                        bi = BITMAPINFOHEADER()
                        bi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
                        bi.biWidth = width
                        bi.biHeight = -abs(height)  # top-down
                        bi.biPlanes = 1
                        bi.biBitCount = 32
                        bi.biCompression = 0  # BI_RGB
                        bi.biSizeImage = width * abs(height) * 4

                        buf = ctypes.create_string_buffer(bi.biSizeImage)
                        if win32gui.GetDIBits(memdc, handle, 0, abs(height), buf, ctypes.byref(bi), 0):
                            from PIL import Image
                            img = Image.frombuffer('RGBA', (width, abs(height)), buf.raw, 'raw', 'BGRA', 0, 1)
                            return img.copy()
                    finally:
                        win32gui.SelectObject(memdc, old_bmp)
                finally:
                    win32gui.DeleteDC(memdc)
            finally:
                win32gui.ReleaseDC(0, hdc)
            return None
        return None
    except Exception:
        return None


def contains_text() -> bool:
    """检查剪贴板是否包含文本"""
    try:
        with _clipboard_lock:
            win32clipboard.OpenClipboard()
            try:
                return win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT)
            finally:
                win32clipboard.CloseClipboard()
    except Exception:
        return False


def get_text() -> Optional[str]:
    """从剪贴板获取文本"""
    try:
        with _clipboard_lock:
            win32clipboard.OpenClipboard()
            try:
                if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                    return win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
            finally:
                win32clipboard.CloseClipboard()
    except Exception:
        pass
    return None


def clear() -> bool:
    """清空剪贴板"""
    try:
        with _clipboard_lock:
            win32clipboard.OpenClipboard()
            try:
                win32clipboard.EmptyClipboard()
            finally:
                win32clipboard.CloseClipboard()
        return True
    except Exception:
        return False
