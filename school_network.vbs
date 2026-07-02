Set WshShell = CreateObject("WScript.Shell")
' 使用 %USERPROFILE% 和 py 启动器，自动适配不同用户环境
' 最后一个参数 0 = 隐藏窗口，False = 不等待进程结束
WshShell.Run "cmd /c py -3 -R -W ignore """ & CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName) & "\school_network.py""", 0, False
