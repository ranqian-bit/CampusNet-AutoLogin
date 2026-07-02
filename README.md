# CampusNet-AutoLogin —— 南京理工大学紫金学院 · 校园网自动登录脚本

Windows 下校园网 Captive Portal 自动登录工具，最初为**南京理工大学紫金学院**校园网开发。开机后自动检测网络状态，未登录时自动提交认证，断线自动重连。兼容使用锐捷/Dr.com 类认证系统的高校校园网，其他学校也可以直接用。

## 功能特性

- 开机自动运行，无需手动打开浏览器登录
- 智能检测频率：前 10 分钟每 10 秒检测（应对刚开机频繁断网），之后每 30 分钟检测
- 断线自动重连，登录后自动验证
- 完全静默运行，不弹窗口
- 一键安装，自动创建 Windows 任务计划

## 前置条件

- **系统**：Windows 10 / 11
- **Python**：3.x（安装时勾选 Add to PATH）
- **依赖**：`requests` 库

## 快速部署

### 第一步：修改配置

用记事本打开 `school_network.py`，修改顶部三个变量（搜索 `YOUR_` 即可定位）：

```python
USERNAME = 'YOUR_STUDENT_ID'      # 你的学号或身份证号
PASSWORD = 'YOUR_PASSWORD'         # 你的校园网密码
SERVICE = 'YOUR_CARRIER_CODE'     # 运营商编码（见下方编码表）
```

### 第二步：一键安装

右键 `install.bat` → **以管理员身份运行**

脚本会自动完成：
1. 复制文件到用户主目录（`%USERPROFILE%`）
2. 创建 Windows 任务计划程序任务（开机自启）
3. 测试运行

### 第三步：验证

重启电脑，打开浏览器如果能直接上网，说明配置成功。

## 运营商编码

| 运营商 | 编码 |
|--------|------|
| 联通 | `%25E8%2581%2594%25E9%2580%259A` |
| 移动 | `%25E7%25A7%25BB%25E5%258A%25A8` |
| 电信 | `%25E7%2594%25B5%25E4%25BF%25A1` |
| 校园网 | `%E6%A0%A1%E5%9B%AD%E7%BD%91` |

不同学校的运营商名称可能不同，请根据实际情况选择。

## 手动安装

如果一键安装失败：

1. 将 `school_network.py` 和 `school_network.bat` 复制到 `%USERPROFILE%\`
2. 按 Win+R 输入 `taskschd.msc`
3. 创建基本任务 → 名称「校园网自动登录」→ 触发器「当用户登录时」→ 操作「启动程序」→ 程序填 `%USERPROFILE%\school_network.bat`

## 日常管理

- **查看日志**：打开 `%USERPROFILE%\school_network.log`
- **手动测试**：双击 `%USERPROFILE%\school_network.bat`
- **停用**：Win+R → `taskschd.msc` → 找到任务 → 右键禁用
- **卸载**：任务计划程序中删除任务，然后删除 `school_network.py` 和 `school_network.bat`

## 文件说明

| 文件 | 说明 |
|------|------|
| `school_network.py` | 主脚本（网络检测 + 自动登录） |
| `school_network.bat` | 启动器（任务计划程序调用） |
| `school_network.vbs` | VBS 静默启动器（可选，隐藏窗口效果更彻底） |
| `install.bat` | 一键安装脚本 |

## 工作原理

```
开机 → 任务计划程序触发 → school_network.bat → pythonw 静默运行
  → 访问 captive portal 检测服务器（Google/Cloudflare/小米等）
  → 状态码 204 = 网络正常，跳过
  → 非 204 = 被校园网拦截，解析重定向页面，提取登录接口
  → 发送登录请求 → 验证是否成功 → 记录日志
```

## 免责声明

本项目仅供学习交流使用。脚本模拟浏览器正常登录行为，使用你自己的合法账号认证校园网。使用者需自行遵守所在学校的网络使用规定，因使用本项目产生的任何后果由使用者自行承担。

## 开源许可

MIT License，详见 [LICENSE](LICENSE) 文件。
