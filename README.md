# ImageToPath

Lightweight Windows tray tool that saves screenshots or clipboard images to disk, then copies the saved file path back to the clipboard.

## Features

- Auto-save image data from clipboard.
- Copy saved image path back to clipboard.
- Region screenshot with `PrintScreen`.
- Fullscreen screenshot with `Ctrl+PrintScreen`.
- Tray menu for changing and opening save folder.
- Single-instance guard.
- Timestamp filenames such as `20260501_184233.png`.

## Run From Source

```powershell
pip install -r requirements.txt
pythonw.exe Program.py
```

## Config

On first run, the app creates `AppConfig.json` beside the script or executable.

Default filename format:

```text
{yyyy}{MM}{dd}_{HH}{mm}{ss}
```

If multiple images are saved in the same second, suffixes are added to prevent overwrite:

```text
20260501_184233.png
20260501_184233_2.png
```

See `AppConfig.example.json` for all options.

