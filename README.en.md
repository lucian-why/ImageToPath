# ImageToPath

Language: [中文](README.md) | English

ImageToPath is a lightweight Windows tray tool that saves screenshots or clipboard images to disk, then copies the saved image file path back to the clipboard.

It is designed for this workflow:

1. Copy an image, or press a screenshot hotkey.
2. The app saves the image file automatically.
3. The clipboard content becomes the saved image path.
4. Press `Ctrl+V` anywhere to paste the file path.

## Features

- Auto-save images from the clipboard.
- Copy the saved image path back to the clipboard.
- Region screenshot with `PrintScreen`, which saves the file and copies the path.
- `Ctrl+PrintScreen` takes a region screenshot and copies the image directly to the clipboard without saving a file.
- Tray menu for changing and opening the save folder.
- Creates an `ImageToPath` desktop shortcut on first run.
- Tray menu option for enabling or disabling startup with Windows.
- Single-instance guard to avoid duplicate tray apps.
- First-run welcome window. After closing it, the app keeps running in the system tray.
- Timestamp filenames such as `20260501_184233.png`.
- Adds a suffix when multiple images are saved in the same second, for example `20260501_184233_2.png`.

## Download

Windows builds are available on the Releases page:

https://github.com/lucian-why/ImageToPath/releases

Download `ImageToPath-windows-x64.zip`, extract it, then run `ImageToPath.exe`.

**⚠️ Note: When downloading this software, if there is an insecurity warning, this is normal.** Because this build is not code-signed, Windows or your browser may show warnings such as "unsafe" or "unknown publisher". If the file comes from this repository's Release page, you can keep the file and continue running it.

## Run From Source

```powershell
pip install -r requirements.txt
pythonw.exe Program.py
```

You can also double-click:

```text
run.vbs
```

On first launch, the app shows a short welcome window. Click "知道了，收进托盘" to hide it. Future launches will not show it again, and the app will keep running in the system tray.

## Config

On first run, the app creates `AppConfig.json` next to the script or executable.

Common options:

```json
{
  "save_folder": "C:\\Users\\YourName\\Pictures\\Screenshots",
  "file_name_format": "{yyyy}{MM}{dd}_{HH}{mm}{ss}",
  "auto_save_clipboard_image": true,
  "copy_path_to_clipboard": true,
  "start_with_windows": false,
  "clipboard_poll_interval": 500
}
```

See `AppConfig.example.json` for a full example.

## File Naming

Default format:

```text
{yyyy}{MM}{dd}_{HH}{mm}{ss}
```

Example output:

```text
20260501_184233.png
```

This format works well with name sorting. Ascending filename order is also ascending time order.

## Notes

- Windows is the main supported platform.
- `PrintScreen` is taken over by this app for region screenshots and copied file paths. `Ctrl+PrintScreen` also takes a region screenshot, but only copies the image to the clipboard without saving a file.
- A desktop shortcut is created automatically on first run.
- Startup with Windows can be enabled or disabled from the tray menu.
- The app listens for clipboard images. If you do not need this, disable "自动保存剪贴板图片" from the tray menu.
- The build is not code-signed. Windows may show a security warning on first run.
