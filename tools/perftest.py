import os
import subprocess
import time
import socket
from datetime import datetime

# 设置参数
MAX_RESTARTS = 30
REPEAT_COUNT = 10000  # -n 参数的值
restart_count = 0

# 文件名参数
ft_value = 1  # 可以根据需要修改
thre_value = 2  # 可以根据需要修改
version = "v1"  # 可以根据需要修改


RESOURCES_DIR = "./resources/prototype"  
FILENAME = f"prototype_ft_{ft_value}_thre_{thre_value}_{version}.log"
LOG_FILE = os.path.join(RESOURCES_DIR, FILENAME)  

# 获取主机名
hostname = socket.gethostname()

# 创建resources目录（如果不存在）  
os.makedirs(RESOURCES_DIR, exist_ok=True)  

# 删除已存在的日志文件并创建新的
if os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)
open(LOG_FILE, 'a').close()

print(f"Starting application monitor... Maximum restarts: {MAX_RESTARTS}")
print(f"Current hostname: {hostname}")
print(f"Log file: {LOG_FILE}")

while restart_count < MAX_RESTARTS:
    # 根据主机名构建不同的命令
    if hostname == "FNIL-2022DEC-GPU-7":
        cmd = ["sudo", "ib_send_bw", "-d", "mlx5_1", "-n", str(REPEAT_COUNT)]
    elif hostname == "FNIL-2022DEC-GPU-8":
        cmd = ["sudo", "ib_send_bw", "10.10.10.4", "-n", str(REPEAT_COUNT)]
    else:
        message = f"Unsupported hostname: {hostname}"
        print(message)
        with open(LOG_FILE, 'a') as log:
            log.write(message + '\n')
        break
    
    # 打开日志文件以追加模式
    with open(LOG_FILE, 'a') as log:
        # 记录当前执行的命令
        log.write(f"\nExecuting command: {' '.join(cmd)} at {datetime.now()}\n")
        
        # 运行命令并重定向输出到日志文件
        process = subprocess.run(
            cmd,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True
        )
    
    # 增加重启计数
    restart_count += 1
    
    # 如果达到最大重启次数，退出循环
    if restart_count == MAX_RESTARTS:
        message = f"Maximum restart count ({MAX_RESTARTS}) reached at {datetime.now()}. Stopping monitor..."
        print(message)
        with open(LOG_FILE, 'a') as log:
            log.write(message + '\n')
        break
    
    # 应用退出后，输出重启信息到日志
    message = f"Application exited at {datetime.now()}. Restart count: {restart_count}/{MAX_RESTARTS}. Waiting 1 second before restart..."
    print(message)
    with open(LOG_FILE, 'a') as log:
        log.write(message + '\n')
    
    # 等待1秒
    time.sleep(1)