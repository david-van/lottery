#!/bin/bash

# 激活 conda 环境
source activate lottery

# 启动 gunicorn，指定输出日志文件
LOGFILE="/root/lottery/log/12-18.log"  # 替换为你希望保存日志的路径
nohup gunicorn -w 4 --bind 0.0.0.0:5000 app:app --timeout 120 --access-logfile - --error-logfile - > "$LOGFILE" 2>&1 &
