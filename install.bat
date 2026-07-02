@echo off
chcp 65001 >nul
title 校园网自动登录 - 一键安装

echo ========================================
echo   校园网自动登录脚本 - 一键安装
echo ========================================
echo.

:: 获取当前脚本所在目录
set "SCRIPT_DIR=%~dp0"

:: 目标目录：当前用户主目录（自动适配，无需手动修改）
set "TARGET_DIR=%USERPROFILE%"

echo [1/4] 复制文件到 %TARGET_DIR% ...
copy /Y "%SCRIPT_DIR%school_network.py" "%TARGET_DIR%\school_network.py" >nul
if errorlevel 1 (
    echo   错误：复制 school_network.py 失败！
    pause
    exit /b 1
)
echo   - school_network.py OK

copy /Y "%SCRIPT_DIR%school_network.bat" "%TARGET_DIR%\school_network.bat" >nul
if errorlevel 1 (
    echo   错误：复制 school_network.bat 失败！
    pause
    exit /b 1
)
echo   - school_network.bat OK

echo.
echo [2/4] 检查 Python 是否安装...
py -3 --version >nul 2>&1
if errorlevel 1 (
    echo   错误：未检测到 Python！
    echo   请先安装 Python 3.x，安装时勾选 Add to PATH
    echo   下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('py -3 --version 2^>^&1') do echo   - %%i

echo.
echo [3/4] 创建 Windows 任务计划程序任务...
:: 删除旧任务（如果存在）
schtasks /delete /tn "SchoolNetworkAutoLogin" /f >nul 2>&1

:: 创建新任务：用户登录时运行
schtasks /create /tn "SchoolNetworkAutoLogin" /tr "%TARGET_DIR%\school_network.bat" /sc onlogon /rl limited /f >nul
if errorlevel 1 (
    echo   错误：创建任务失败！
    echo   请尝试以管理员身份运行此脚本
    pause
    exit /b 1
)
echo   - 任务创建成功：SchoolNetworkAutoLogin
echo   - 触发条件：用户登录时

echo.
echo [4/4] 测试运行...
start "" "%TARGET_DIR%\school_network.bat"
timeout /t 3 /nobreak >nul

if exist "%TARGET_DIR%\school_network.log" (
    echo   - 日志文件已生成
    echo.
    echo ========================================
    echo   安装成功！
    echo ========================================
    echo.
    echo   文件位置：
    echo   - 脚本：%TARGET_DIR%\school_network.py
    echo   - 启动器：%TARGET_DIR%\school_network.bat
    echo   - 日志：%TARGET_DIR%\school_network.log
    echo.
    echo   下次重启电脑将自动登录校园网
    echo.
    echo   管理任务：Win+R 输入 taskschd.msc
    echo   查看日志：打开 school_network.log
) else (
    echo   警告：日志文件未生成，请检查脚本是否正常运行
)

echo.
pause
