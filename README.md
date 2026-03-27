# LLM 驱动的足彩投注建议系统

基于 Flask 的足彩投注建议系统，从体彩接口抓取比赛与赔率数据，调用 Qwen 生成投注建议。

## 功能

- 定时抓取足球比赛和赔率数据
- 提供比赛查询、赔率详情接口
- 调用 DashScope/Qwen 生成投注建议
- 用户注册/登录

## 技术栈

Python 3 + Flask + MySQL + DashScope + APScheduler + Gunicorn

[依赖列表](requirements.txt)

## 项目结构

```
lottery/
├─ app.py                         # Flask 入口
├─ config.py                      # 配置文件
├─ requirements.txt
├─ run.sh                         # Gunicorn 启动脚本
├─ blueprints/
│  ├─ user.py                     # 用户接口
│  └─ v2.py                       # 比赛查询接口
└─ crawler/
   ├─ crawler_all_match_id.py     # 抓取比赛列表
   └─ crawl_insert.py             # 抓取赔率并写库
```

## 快速开始

### 环境要求

- Python 3.x
- MySQL 5.7+ 或 8.x

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置数据库

创建 `lottery` 数据库，修改代码中的数据库连接信息（当前硬编码在 `app.py` 和 `blueprints/` 各文件中）。

### 启动服务

```bash
# 本地启动
python app.py

# Gunicorn 启动
bash run.sh
```

服务默认监听 `0.0.0.0:5000`。

## 数据表

- `match_result`：比赛基础信息
- `match_had`：胜平负赔率
- `match_hhad`：让球胜平负赔率
- `match_ttg`：总进球赔率
- `match_crs`：比分赔率
- `match_hafu`：半全场赔率
- `t_user`：用户表

## 定时任务

每小时同步最新比赛数据，任务函数：`crawl_insert_newest_match()`

## LLM 建议生成

从数据库读取赔率数据，拼接 Prompt 调用 Qwen 生成投注建议，正则解析输出结果。

## 改进建议

1. 使用环境变量管理配置
2. 补充建表 SQL 脚本
3. 用户密码哈希
4. 封装数据访问层
5. 增加日志和测试
