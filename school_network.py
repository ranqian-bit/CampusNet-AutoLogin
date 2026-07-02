import requests
import time
import random
import sys
import os
from datetime import datetime

# ==================== 【需修改】配置区 ====================
# 搜索 "YOUR_" 定位所有需要修改的项

USERNAME = 'YOUR_STUDENT_ID'      # 【需修改】你的学号或身份证号
PASSWORD = 'YOUR_PASSWORD'         # 【需修改】你的校园网密码
SERVICE = 'YOUR_CARRIER_CODE'     # 【需修改】运营商编码，见下方说明

# 运营商编码参考（URL 编码，根据你学校实际选择）：
#   联通:    %25E8%2581%2594%25E9%2580%259A
#   移动:    %25E7%25A7%25BB%25E5%258A%25A8
#   电信:    %25E7%2594%25B5%25E4%25BF%25A1
#   校园网:  %E6%A0%A1%E5%9B%AD%E7%BD%91
# ==========================================================

LOG_FILE = os.path.join(os.path.expanduser('~'), 'school_network.log')

def log(msg):
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {msg}\n')
    except:
        pass

# Captive Portal 检测服务器列表（用于判断网络是否已连通）
CAPTIVE_SERVERS = [
    {'url': 'http://www.google-analytics.com/generate_204', 'expected_success_codes': [204]},
    {'url': 'http://www.gstatic.com/generate_204', 'expected_success_codes': [204]},
    {'url': 'http://cp.cloudflare.com/', 'expected_success_codes': [204]},
    {'url': 'http://connectivitycheck.gstatic.com/generate_204', 'expected_success_codes': [204]},
    {'url': 'http://connect.rom.miui.com/generate_204', 'expected_success_codes': [204]},
    {'url': 'http://connectivitycheck.platform.hicloud.com/generate_204', 'expected_success_codes': [204]},
]

# Windows 下静默运行，不弹出控制台窗口
if sys.platform == 'win32':
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')

# 检测频率配置
FAST_INTERVAL = 10          # 前 10 分钟每 10 秒检测一次（刚开机频繁断网）
SLOW_INTERVAL = 30 * 60     # 之后每 30 分钟检测一次（节省资源）
WARMUP_SECONDS = 10 * 60    # 热身期 10 分钟


def get_captive_server_response():
    """随机选择一个检测服务器，判断网络是否连通"""
    servers = CAPTIVE_SERVERS.copy()
    random.shuffle(servers)
    for server_info in servers:
        server = server_info['url']
        try:
            response = requests.get(server, timeout=5, allow_redirects=False)
            response.expected_success_codes = server_info['expected_success_codes']
            return response
        except requests.exceptions.RequestException:
            continue
    raise requests.exceptions.ConnectionError("所有监控服务器均不可用")


def login(response):
    """解析 Captive Portal 重定向页面，提取登录接口并发送登录请求"""
    response_text = response.text
    login_page_url = response_text.split('\'')[1]
    login_url = login_page_url.split('?')[0].replace('index.jsp', 'InterFace.do?method=login')
    query_string = login_page_url.split('?')[1]
    query_string = query_string.replace('&', '%2526')
    query_string = query_string.replace('=', '%253D')
    headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0'
    }
    login_post_data = 'userId={}&password={}&service={}&queryString={}&operatorPwd=&operatorUserId=&validcode=&passwordEncrypt=false'.format(
        USERNAME, PASSWORD, SERVICE, query_string)
    try:
        login_result = requests.post(url=login_url, data=login_post_data, headers=headers, timeout=10)
        log(f'登录请求发送完成，状态码: {login_result.status_code}')
        log(f'登录响应: {login_result.text[:200]}')
    except Exception as e:
        log(f'登录请求异常: {e}')


def check_connection():
    """检测网络连通性，未登录则自动登录并验证"""
    try:
        response = get_captive_server_response()
        success_status_codes = response.expected_success_codes

        if response.status_code in success_status_codes:
            log(f'网络正常，状态码: {response.status_code}')
            return True
        else:
            log(f'需要登录，状态码: {response.status_code}，开始登录...')
            login(response)

            # 登录后重新验证
            recheck_success = False
            recheck_servers = CAPTIVE_SERVERS.copy()
            random.shuffle(recheck_servers)
            for server_info in recheck_servers[:5]:
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
    start_time = time.time()
    log('脚本启动')
    check_connection()

    while True:
        elapsed = time.time() - start_time
        if elapsed < WARMUP_SECONDS:
            interval = FAST_INTERVAL
        else:
            interval = SLOW_INTERVAL
        time.sleep(interval)
        check_connection()


if __name__ == '__main__':
    main()
