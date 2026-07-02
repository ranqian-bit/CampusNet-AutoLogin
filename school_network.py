"""
校园网自动登录脚本
==================
适用于使用锐捷/Dr.com 类 Captive Portal 认证系统的高校校园网。

工作原理：
  1. 定时访问外部服务器（Google/Cloudflare/小米等）检测网络连通性
  2. 如果返回 204 状态码 → 网络正常，无需操作
  3. 如果返回非 204 → 说明被校园网拦截，会跳转到登录页
  4. 脚本解析重定向页面，提取登录接口地址和查询参数
  5. 模拟浏览器发送登录请求，自动完成认证
  6. 登录后再次验证，确认是否真正连通

运行方式：
  - 直接运行：python school_network.py
  - 静默运行：pythonw school_network.py（无窗口）
  - 开机自启：通过 install.bat 安装后由 Windows 任务计划程序自动触发

依赖：pip install requests
"""

import requests
import time
import random
import sys
import os
from datetime import datetime

# ==================== 【需修改】配置区 ====================
# 部署前把下面三个值改成你自己的，搜索 "YOUR_" 即可定位

USERNAME = 'YOUR_STUDENT_ID'      # 你的学号或身份证号（校园网登录账号）
PASSWORD = 'YOUR_PASSWORD'         # 你的校园网密码
SERVICE = 'YOUR_CARRIER_CODE'     # 运营商编码，根据你学校选，见下方编码表

# 运营商编码参考（URL 二次编码后的值，直接复制粘贴即可）：
#   联通:    %25E8%2581%2594%25E9%2580%259A
#   移动:    %25E7%25A7%25BB%25E5%258A%25A8
#   电信:    %25E7%2594%25B5%25E4%25BF%25A1
#   校园网:  %E6%A0%A1%E5%9B%AD%E7%BD%91
#
# 不确定选哪个？登录校园网看看页面上的下拉菜单，选你买的那个运营商就行
# ==========================================================

# 日志文件路径：存放在用户主目录下（如 C:\Users\你的用户名\school_network.log）
LOG_FILE = os.path.join(os.path.expanduser('~'), 'school_network.log')

def log(msg):
    """写日志：追加模式写入文件，带时间戳，失败静默忽略"""
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {msg}\n')
    except:
        pass

# ==================== 网络检测服务器列表 ====================
# 这些服务器访问时会返回 204（无内容）状态码
# 如果网络正常 → 直接拿到 204
# 如果网络被校园网拦截 → 会被 302 重定向到登录页面，拿不到 204
# 随机选一个访问，避免某个服务器抽风导致误判
CAPTIVE_SERVERS = [
    {'url': 'http://www.google-analytics.com/generate_204', 'expected_success_codes': [204]},   # Google 分析
    {'url': 'http://www.gstatic.com/generate_204', 'expected_success_codes': [204]},            # Google 静态资源
    {'url': 'http://cp.cloudflare.com/', 'expected_success_codes': [204]},                       # Cloudflare
    {'url': 'http://connectivitycheck.gstatic.com/generate_204', 'expected_success_codes': [204]}, # Android 连通性检测
    {'url': 'http://connect.rom.miui.com/generate_204', 'expected_success_codes': [204]},       # 小米 MIUI
    {'url': 'http://connectivitycheck.platform.hicloud.com/generate_204', 'expected_success_codes': [204]}, # 华为鸿蒙
]

# Windows 下静默运行：把标准输出和错误输出都丢到黑洞，不弹窗口
if sys.platform == 'win32':
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')

# ==================== 检测频率配置 ====================
# 策略：刚开机网络不稳定，检测频繁一些；稳定后就降低频率省资源
FAST_INTERVAL = 10          # 快速检测间隔：10 秒
SLOW_INTERVAL = 30 * 60     # 慢速检测间隔：30 分钟
WARMUP_SECONDS = 10 * 60    # 热身期：开机后前 10 分钟用快速检测


def get_captive_server_response():
    """
    随机选一个检测服务器发请求，判断网络是否连通。
    - 返回 204 → 网络正常
    - 返回其他状态码（通常 302/200 + 登录页 HTML）→ 被校园网拦截了
    - 全部超时 → 抛出 ConnectionError（可能断网了）
    """
    servers = CAPTIVE_SERVERS.copy()
    random.shuffle(servers)  # 随机打乱，不总盯着同一个服务器
    for server_info in servers:
        server = server_info['url']
        try:
            # allow_redirects=False 是关键：不跟随重定向，这样才能拿到校园网的 302 跳转
            response = requests.get(server, timeout=5, allow_redirects=False)
            response.expected_success_codes = server_info['expected_success_codes']
            return response
        except requests.exceptions.RequestException:
            continue  # 这个服务器不通，换下一个
    raise requests.exceptions.ConnectionError("所有监控服务器均不可用")


def login(response):
    """
    解析校园网 Captive Portal 的重定向页面，提取登录接口并发送登录请求。

    流程：
    1. 检测服务器返回的不是 204，而是一段 HTML，里面包含校园网登录页的 URL
    2. 从 HTML 中提取登录页 URL，解析出登录接口地址和查询参数
    3. 把查询参数里的 & 和 = 做二次 URL 编码（校园网认证系统的特殊要求）
    4. 拼接 POST 请求体，发送登录请求
    """
    # 从响应 HTML 中提取登录页 URL（通常在 script 标签的引号里）
    response_text = response.text
    login_page_url = response_text.split('\'')[1]

    # 把登录页 URL 转换成登录接口 URL
    # 例如: http://10.0.0.1/index.jsp?wlanuserip=xxx → http://10.0.0.1/InterFace.do?method=login
    login_url = login_page_url.split('?')[0].replace('index.jsp', 'InterFace.do?method=login')

    # 提取查询参数并做二次编码（校园网认证系统的坑，& 要编码成 %2526，= 要编码成 %253D）
    query_string = login_page_url.split('?')[1]
    query_string = query_string.replace('&', '%2526')
    query_string = query_string.replace('=', '%253D')

    # 伪装成浏览器请求
    headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0'
    }

    # 拼接登录请求体：账号、密码、运营商、查询参数
    login_post_data = 'userId={}&password={}&service={}&queryString={}&operatorPwd=&operatorUserId=&validcode=&passwordEncrypt=false'.format(
        USERNAME, PASSWORD, SERVICE, query_string)

    try:
        login_result = requests.post(url=login_url, data=login_post_data, headers=headers, timeout=10)
        log(f'登录请求发送完成，状态码: {login_result.status_code}')
        log(f'登录响应: {login_result.text[:200]}')
    except Exception as e:
        log(f'登录请求异常: {e}')


def check_connection():
    """
    一次完整的网络检测 + 自动登录流程：
    1. 访问检测服务器，看网络通不通
    2. 通了 → 记日志，返回 True
    3. 不通 → 被校园网拦截了 → 调用 login() 自动登录
    4. 登录后再从检测服务器验证一次，确认真的连上了
    """
    try:
        response = get_captive_server_response()
        success_status_codes = response.expected_success_codes

        if response.status_code in success_status_codes:
            # 网络正常，啥也不用干
            log(f'网络正常，状态码: {response.status_code}')
            return True
        else:
            # 被校园网拦截了，开始自动登录
            log(f'需要登录，状态码: {response.status_code}，开始登录...')
            login(response)

            # 登录完了，重新检测一下看看是不是真的通了
            recheck_success = False
            recheck_servers = CAPTIVE_SERVERS.copy()
            random.shuffle(recheck_servers)
            for server_info in recheck_servers[:5]:  # 最多试 5 个服务器
                server = server_info['url']
                server_success_codes = server_info['expected_success_codes']
                try:
                    recheck_response = requests.get(server, timeout=5, allow_redirects=False)
                    if recheck_response.status_code in server_success_codes:
                        recheck_success = True
                        log('登录成功')
                        break
                except requests.exceptions.RequestException:
                    continue
            return recheck_success
    except Exception as e:
        log(f'检测异常: {e}')
        return False


def main():
    """
    主循环：
    - 启动时立刻检测一次
    - 前 10 分钟（热身期）每 10 秒检测一次 → 应对刚开机网络不稳定
    - 之后每 30 分钟检测一次 → 省资源，够用了
    """
    start_time = time.time()
    log('脚本启动')
    check_connection()  # 启动时立刻检测一次

    while True:
        elapsed = time.time() - start_time
        if elapsed < WARMUP_SECONDS:
            interval = FAST_INTERVAL   # 热身期：频繁检测
        else:
            interval = SLOW_INTERVAL   # 稳定后：降低频率
        time.sleep(interval)
        check_connection()


if __name__ == '__main__':
    main()
