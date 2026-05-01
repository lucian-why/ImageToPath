# ImageToPath

ImageToPath 是一个轻量 Windows 托盘工具：把截图或剪贴板里的图片保存到本地，然后把保存后的图片路径自动复制回剪贴板。

适合这种工作流：

1. 复制一张图片，或按截图热键。
2. 程序自动保存图片文件。
3. 剪贴板内容变成图片路径。
4. 在任意输入框里 `Ctrl+V`，直接粘贴文件路径。

## 功能

- 自动保存剪贴板里的图片。
- 保存后自动复制图片文件路径。
- `PrintScreen` 区域截图。
- `Ctrl+PrintScreen` 全屏截图。
- 托盘菜单支持更改保存目录、打开保存目录。
- 单实例运行，避免重复开多个托盘程序。
- 文件名按时间命名，例如 `20260501_184233.png`。
- 同一秒保存多张图时自动加后缀，避免覆盖：`20260501_184233_2.png`。

## 下载

Windows 包在 Release 页面：

https://github.com/lucian-why/ImageToPath/releases

下载 `ImageToPath-windows-x64.zip`，解压后运行 `ImageToPath.exe`。

## 从源码运行

```powershell
pip install -r requirements.txt
pythonw.exe Program.py
```

也可以双击：

```text
run.vbs
```

## 配置

首次运行后，程序会在脚本或 exe 同目录生成 `AppConfig.json`。

常用配置：

```json
{
  "save_folder": "C:\\Users\\YourName\\Pictures\\Screenshots",
  "file_name_format": "{yyyy}{MM}{dd}_{HH}{mm}{ss}",
  "auto_save_clipboard_image": true,
  "copy_path_to_clipboard": true,
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
- 程序会监听剪贴板图片；如果不需要，可以在托盘菜单里关闭“自动保存剪贴板图片”。
- 未做代码签名，Windows 第一次运行可能出现安全提示。
