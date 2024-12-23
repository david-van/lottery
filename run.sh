# #!/bin/bash

# # 激活 conda 环境
# source activate lottery

# # 启动 gunicorn，指定输出日志文件
# LOGFILE="/root/lottery/log/12-18.log"  # 替换为你希望保存日志的路径
# nohup gunicorn -w 4 --bind 0.0.0.0:5000 app:app --timeout 120 --access-logfile - --error-logfile - > "$LOGFILE" 2>&1 &

#!/bin/bash

# 激活 conda 环境
source activate lottery

# 获取当前日期，用于生成日志文件名
DATE=$(date +"%Y-%m-%d")
LOGDIR="/root/lottery/log"  # 日志目录
LOGFILE="$LOGDIR/$DATE.log"  # 每天的日志文件路径

# 启动 gunicorn，输出日志到指定文件
nohup gunicorn -w 4 --bind 0.0.0.0:5000 app:app --timeout 120 --access-logfile - --error-logfile - > "$LOGFILE" 2>&1 &
