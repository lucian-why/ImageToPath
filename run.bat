@echo off
:: ImageToPath - 截图自动保存，路径入剪贴板
:: 启动后右键托盘图标操作

cd /d "%~dp0"
start "" pythonw.exe "%~dp0Program.py"
echo ImageToPath 已启动，查看系统托盘图标
timeout /t 3 >nul
