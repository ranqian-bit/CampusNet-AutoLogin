' ========================================
' 校园网自动登录 - VBS 静默启动器
' ========================================
' 这个文件是 bat 启动器的替代方案，效果更彻底：
'   bat 启动时可能会闪一下黑色的命令行窗口
'   vbs 启动则完全没有任何窗口弹出
'
' 用法（二选一）：
'   方式1：任务计划程序直接调用 school_network.bat（简单，可能闪一下窗口）
'   方式2：任务计划程序调用 school_network.vbs（完全静默）
'
' 技术说明：
'   WshShell.Run 的第二个参数 0 = 隐藏窗口
'   第三个参数 False = 不等待进程结束（异步启动）
'   ScriptFullName = 当前 vbs 文件的完整路径，自动定位同目录下的 py 脚本
' ========================================

Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c py -3 -R -W ignore """ & CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName) & "\school_network.py""", 0, False
