# LLM 驱动的足彩投注建议系统后端

这是一个基于 Flask 的足彩投注建议系统后端。系统从中国体彩公开接口抓取足球比赛与赔率数据，写入 MySQL，并对外提供比赛查询、赔率详情和基于大模型的投注建议接口。

项目当前的实现形态更接近“数据抓取 + 赔率查询 + Prompt 驱动的建议生成”后端，而不是一个真正训练了预测模型的机器学习系统。项目中的 LLM 主要用于基于赔率和比赛信息生成投注建议文本。

## 功能概览

- 定时抓取最新足球比赛和赔率数据
- 将比赛基础信息与多种彩票玩法赔率写入 MySQL
- 提供可投注比赛列表接口
- 提供单场比赛赔率详情接口
- 提供历史比赛查询接口
- 提供用户注册、登录接口
- 调用 DashScope/Qwen 生成投注建议

## 技术栈

- Python 3
- Flask
- Flask-APScheduler
- PyMySQL
- Requests
- DashScope
- MySQL
- Gunicorn

依赖见 [requirements.txt](/d:/Projects/PythonProjects/lottery/requirements.txt)。

## 项目结构

```text
lottery/
├─ app.py                         # Flask 入口，注册蓝图、定时任务、旧版接口
├─ config.py                      # Flask 配置
├─ requirements.txt               # Python 依赖
├─ run.sh                         # Linux/Gunicorn 启动脚本
├─ prompt_template.txt            # 提示词模板草稿
├─ prompt_data_input.txt          # 提示词输入示例
├─ blueprints/
│  ├─ __init__.py                 # 蓝图注册
│  ├─ user.py                     # 用户注册/登录接口
│  └─ v2.py                       # 新版比赛查询接口
└─ crawler/
   ├─ crawler_all_match_id.py     # 抓取比赛 matchId
   ├─ crawl_insert.py             # 抓取赔率并写库
   ├─ crawl_insert_newest_match.py# 增量更新最近比赛数据
   ├─ crawl_insert_history_match.py
   ├─ crawl_insert.py
   ├─ crawl_excel_newest_match.py
   ├─ excel2database.py
   └─ crawl_insert_history_match.py
```

## 系统架构

整体链路如下：

1. 爬虫层从体彩接口抓取联赛比赛列表，获取 `gmMatchId`
2. 根据 `matchId` 抓取单场比赛的固定奖金与赔率信息
3. 将比赛、赔率、比分玩法等信息拆分写入 MySQL 多张表
4. Flask 对外提供比赛列表、详情、历史记录和用户接口
5. 投注建议接口从数据库读取两队最新赔率，拼接 Prompt 后调用 Qwen 生成建议

## 数据来源

项目当前使用了两个主要体彩接口：

- 比赛列表接口：用于按联赛和日期范围抓取比赛与 `gmMatchId`
- 固定奖金接口：用于抓取胜平负、让球、总进球、比分、半全场等赔率

这些接口的调用逻辑位于：

- [crawler_all_match_id.py](/d:/Projects/PythonProjects/lottery/crawler/crawler_all_match_id.py)
- [crawl_insert.py](/d:/Projects/PythonProjects/lottery/crawler/crawl_insert.py)

## 主要数据表

从代码逻辑看，数据库至少包含以下表：

- `match_result`：比赛基础信息与部分赛果字段
- `match_had`：胜平负赔率
- `match_hhad`：让球胜平负赔率
- `match_ttg`：总进球赔率
- `match_crs`：比分赔率
- `match_hafu`：半全场赔率
- `t_user`：用户表

说明：仓库中没有提供建表 SQL，当前 README 依据代码中的查询和插入语句整理。

## 运行机制

### 1. Web 服务

主程序入口是 [app.py](/d:/Projects/PythonProjects/lottery/app.py)。

本地直接启动：

```bash
python app.py
```

默认监听：

```text
0.0.0.0:5000
```

### 2. 定时任务

项目在 Flask 启动时会初始化 APScheduler，并每隔 1 小时执行一次最新比赛同步任务：

- 任务函数：`crawl_insert_newest_match()`
- 锁文件：`scheduler.lock`

### 3. Gunicorn 部署

Linux 环境可参考 [run.sh](/d:/Projects/PythonProjects/lottery/run.sh)：

```bash
bash run.sh
```

脚本会：

- 激活 `lottery` conda 环境
- 使用 `gunicorn` 启动 `app:app`
- 将日志输出到 `/root/lottery/log/<日期>.log`

## 安装与启动

### 环境要求

- Python 3.x
- MySQL 5.7+ 或 8.x
- Linux 部署建议安装 Gunicorn

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置数据库

你需要先准备 `lottery` 数据库，并确保代码中的账号密码可用。

当前代码中数据库连接信息是硬编码的，且不同文件不完全一致：

- `app.py` / `blueprints/user.py` 使用 `root / 123456`
- `blueprints/v2.py` 使用 `huan / huan`

建议统一改为环境变量或集中配置。

### 启动服务

```bash
python app.py
```

## LLM 建议生成逻辑

投注建议接口的核心逻辑在 [app.py](/d:/Projects/PythonProjects/lottery/app.py)。

实现方式如下：

- 先读取数据库中某场比赛的最新赔率
- 将 54 种左右的玩法及赔率拼成自然语言 Prompt
- 在 Prompt 中要求模型从概率、EV、风险管理、历史相似性等角度分析
- 最终要求模型用严格格式输出投注组合
- 服务端再用正则表达式抽取投注项和金额

注意：

- 这里并没有在本地真正实现 EV、回测、KNN、分类模型等算法
- 这些分析要求主要是通过 Prompt 交给大模型完成
- 因此系统效果高度依赖模型输出稳定性

## 开发建议

如果继续迭代这个项目，建议优先做以下改造：

1. 抽离统一配置，使用 `.env` 或环境变量管理敏感信息
2. 补充 MySQL 建表脚本和初始化说明
3. 为用户系统加入密码哈希和登录态
4. 把数据库访问封装成单独的数据访问层
5. 为爬虫、接口、LLM 调用增加结构化日志
6. 为 LLM 接口增加输出校验和兜底策略
7. 将提示词模板与代码逻辑解耦
8. 增加基本单元测试和接口测试