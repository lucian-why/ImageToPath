# ImageToPath

语言：中文 | [English](README.en.md)

ImageToPath 是一个轻量 Windows 托盘工具：把截图或剪贴板里的图片保存到本地，然后把保存后的图片路径自动复制回剪贴板。

适合这种工作流：

1. 复制一张图片，或按截图热键。
2. 程序自动保存图片文件。
3. 剪贴板内容变成图片路径。
4. 在任意输入框里 `Ctrl+V`，直接粘贴文件路径。

## 功能

- 自动保存剪贴板里的图片。
- 保存后自动复制图片文件路径。
- `PrintScreen` 区域截图，保存文件并复制路径。
- `Ctrl+PrintScreen` 区域截图，不保存文件，直接把图片复制到剪贴板。
- 托盘菜单支持更改保存目录、打开保存目录。
- 首次运行会在桌面创建 `ImageToPath` 快捷方式，方便以后打开。
- 托盘菜单支持开启或关闭开机自启动。
- 单实例运行，避免重复开多个托盘程序。
- 首次启动会显示说明窗口；关闭后程序留在右下角系统托盘。
- 文件名按时间命名，例如 `20260501_184233.png`。
- 同一秒保存多张图时自动加后缀，避免覆盖：`20260501_184233_2.png`。

## 下载

Windows 包在 Release 页面：

https://github.com/lucian-why/ImageToPath/releases

下载 `ImageToPath-windows-x64.zip`，解压后运行 `ImageToPath.exe`。

**⚠️ 提示：下载这个软件的时候，如果有不安全警告（如浏览器拦截、Windows 提示“未知发布者”），这是正常的现象。** 因为当前版本没有做代码签名，确认来源是本仓库 Release 后，可以选择保留文件并继续运行。

## 从源码运行

```powershell
pip install -r requirements.txt
pythonw.exe Program.py
```

也可以双击：

```text
run.vbs
```

首次启动会出现一个说明窗口。点击“知道了，收进托盘”后，以后启动不会再显示。程序仍会在右下角系统托盘运行。

## 配置

首次运行后，程序会在脚本或 exe 同目录生成 `AppConfig.json`。

常用配置：

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

完整示例见 `AppConfig.example.json`。

## 文件命名

默认格式：

```text
{yyyy}{MM}{dd}_{HH}{mm}{ss}
```

生成结果：

```text
20260501_184233.png
```

这种格式适合按文件名排序。名称升序时，也就是时间升序。

## 注意

- 当前主要支持 Windows。
- `PrintScreen` 会被本软件接管为区域截图并复制文件路径；`Ctrl+PrintScreen` 也是区域截图，但仅把截图图片复制到剪贴板，不保存文件。
- 桌面快捷方式会在首次运行时自动创建。
- 开机自启动可在托盘菜单里打开或关闭。
- 程序会监听剪贴板图片；如果不需要，可以在托盘菜单里关闭“自动保存剪贴板图片”。
- 未做代码签名，Windows 第一次运行可能出现安全提示。
