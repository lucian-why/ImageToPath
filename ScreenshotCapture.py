"""
屏幕截图 — 全屏 / 区域截图
"""
import os
import random
import string
from datetime import datetime
from typing import Optional, Callable

from PIL import Image, ImageGrab

from AppConfig import AppConfig


def generate_filename(config: AppConfig, source: str = "screenshot") -> str:
    """根据配置的文件名格式生成文件名"""
    now = datetime.now()
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))

    fmt = config.file_name_format
    fmt = fmt.replace("{yyyy}", now.strftime("%Y"))
    fmt = fmt.replace("{MM}", now.strftime("%m"))
    fmt = fmt.replace("{dd}", now.strftime("%d"))
    fmt = fmt.replace("{HH}", now.strftime("%H"))
    fmt = fmt.replace("{mm}", now.strftime("%M"))
    fmt = fmt.replace("{ss}", now.strftime("%S"))
    fmt = fmt.replace("{source}", source)
    fmt = fmt.replace("{random4}", random_str)

    ext = config.image_format.lower()
    if not fmt.endswith(f".{ext}"):
        fmt += f".{ext}"

    return fmt


def capture_fullscreen() -> Optional[Image.Image]:
    """全屏截图，返回 PIL Image"""
    try:
        img = ImageGrab.grab(all_screens=True)
        return img
    except Exception:
        return None


def capture_region() -> Optional[Image.Image]:
    """区域截图 — 弹出半透明全屏窗口，用户拖选区域"""
    import tkinter as tk

    result = {"image": None}

    class RegionSelector:
        def __init__(self):
            self.root = tk.Tk()
            self.root.attributes("-fullscreen", True)
            self.root.attributes("-alpha", 0.4)
            self.root.attributes("-topmost", True)
            self.root.configure(cursor="cross")
            self.root.configure(bg="black")

            self.canvas = tk.Canvas(self.root, bg="black", highlightthickness=0)
            self.canvas.pack(fill="both", expand=True)

            self.start_x = 0
            self.start_y = 0
            self.rect = None

            self.canvas.bind("<ButtonPress-1>", self.on_press)
            self.canvas.bind("<B1-Motion>", self.on_drag)
            self.canvas.bind("<ButtonRelease-1>", self.on_release)
            self.root.bind("<Escape>", lambda e: self.root.destroy())

        def on_press(self, event):
            self.start_x = event.x
            self.start_y = event.y
            self.rect = self.canvas.create_rectangle(
                self.start_x, self.start_y, self.start_x, self.start_y,
                outline="red", width=2
            )

        def on_drag(self, event):
            if self.rect:
                self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

        def on_release(self, event):
            self.root.withdraw()
            x1, y1 = min(self.start_x, event.x), min(self.start_y, event.y)
            x2, y2 = max(self.start_x, event.x), max(self.start_y, event.y)

            if x2 - x1 > 5 and y2 - y1 > 5:
                try:
                    img = ImageGrab.grab(bbox=(x1, y1, x2, y2), all_screens=True)
                    result["image"] = img
                except Exception:
                    pass
            self.root.destroy()

        def run(self):
            self.root.mainloop()

    selector = RegionSelector()
    selector.run()

    return result["image"]


def save_image(img: Image.Image, config: AppConfig, source: str = "screenshot") -> Optional[str]:
    """保存图片到配置目录，返回文件路径"""
    try:
        os.makedirs(config.save_folder, exist_ok=True)
        filename = generate_filename(config, source=source)
        filepath = os.path.join(config.save_folder, filename)
        filepath = _next_available_path(filepath)

        fmt = config.image_format.upper()
        save_img = img

        if fmt == "JPG" or fmt == "JPEG":
            # JPEG 需要转换 RGBA → RGB
            if save_img.mode in ("RGBA", "P", "LA"):
                background = Image.new("RGB", save_img.size, (255, 255, 255))
                if save_img.mode == "P":
                    save_img = save_img.convert("RGBA")
                background.paste(save_img, mask=save_img.split()[-1] if save_img.mode == "RGBA" else None)
                save_img = background
            elif save_img.mode != "RGB":
                save_img = save_img.convert("RGB")
            save_img.save(filepath, "JPEG", quality=config.jpeg_quality)
        elif fmt == "BMP":
            save_img.save(filepath, "BMP")
        else:
            # 默认 PNG
            save_img.save(filepath, "PNG")

        return filepath
    except Exception:
        return None


def _next_available_path(filepath: str) -> str:
    """返回未占用路径；同秒多张时追加 _2, _3，避免覆盖。"""
    if not os.path.exists(filepath):
        return filepath

    stem, ext = os.path.splitext(filepath)
    index = 2
    while True:
        candidate = f"{stem}_{index}{ext}"
        if not os.path.exists(candidate):
            return candidate
        index += 1
