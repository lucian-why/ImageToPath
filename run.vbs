' ImageToPath 静默启动（无命令行窗口）
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "pythonw.exe """ & CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName) & "\Program.py""", 0, False
