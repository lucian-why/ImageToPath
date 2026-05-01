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
- Region screenshot with `PrintScreen`.
- Fullscreen screenshot with `Ctrl+PrintScreen`.
- Tray menu for changing and opening the save folder.
- Single-instance guard to avoid duplicate tray apps.
- Timestamp filenames such as `20260501_184233.png`.
- Adds a suffix when multiple images are saved in the same second, for example `20260501_184233_2.png`.

## Download

Windows builds are available on the Releases page:

https://github.com/lucian-why/ImageToPath/releases

Download `ImageToPath-windows-x64.zip`, extract it, then run `ImageToPath.exe`.

## Run From Source

```powershell
pip install -r requirements.txt
pythonw.exe Program.py
```

You can also double-click:

```text
run.vbs
```

## Config

On first run, the app creates `AppConfig.json` next to the script or executable.

Common options:

```json
{
  "save_folder": "C:\\Users\\YourName\\Pictures\\Screenshots",
  "file_name_format": "{yyyy}{MM}{dd}_{HH}{mm}{ss}",
  "auto_save_clipboard_image": true,
  "copy_path_to_clipboard": true,
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
- The app listens for clipboard images. If you do not need this, disable "自动保存剪贴板图片" from the tray menu.
- The build is not code-signed. Windows may show a security warning on first run.
