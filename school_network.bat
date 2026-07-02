@echo off
:: 使用 %USERPROFILE% 自动适配当前用户，无需手动修改路径
:: 使用 py 启动器自动寻找 Python（兼容多版本安装）
start "" py -3 -R -W ignore "%~dp0school_network.py"
