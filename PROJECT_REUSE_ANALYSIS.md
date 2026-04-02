# 旧项目代码复用分析（面向全新最小化项目）

## 目标背景

新项目目标被简化为一条最小链路：

1. 从外部接口抓取数据
2. 将数据写入 CSV 文件
3. 从 CSV 文件读取数据
4. 将数据拼接成 Prompt
5. 调用大模型接口

基于这个目标，这份文档用于判断：当前仓库中哪些代码值得复用，哪些只值得参考思路，哪些应当直接丢弃并重写。

核心原则：**按函数和能力复用，不按原项目结构整体复制。**

---

## 总体结论

这个旧项目里真正值得迁移的核心资产只有四类：

1. 体彩接口抓取逻辑
2. 赔率 JSON 的字段提取逻辑
3. Prompt 的输入格式设计
4. 大模型输出格式约束与解析思路

不值得迁移的主要部分包括：

- Flask 路由层
- MySQL 插入/更新逻辑
- APScheduler 定时任务
- 用户注册/登录逻辑
- 部署脚本与旧接口结构

也就是说，新项目应该是“抽取纯数据处理能力 + 重新组织为轻量脚本项目”，而不是继续继承这个仓库的工程结构。

---

## 一、可以直接复用的代码

这些代码与新项目目标最接近，抽出来成本低，且对 Flask/MySQL 的依赖相对较少。

### 1. 比赛列表抓取逻辑

来源文件：`crawler/crawler_all_match_id.py`

建议复用的函数：

- `fetch_data(start_date, end_date, season_id, league_id)`
- `get_match_id(data)`
- `crawl_match_ids(start_date, end_date, season_id, league_id)`
- `crawl_five_league_match_ids(start_date, end_date, leagues)`

这些函数的核心价值：

- 调用体彩比赛列表接口
- 获取指定时间范围内的比赛数据
- 从返回 JSON 中提取 `gmMatchId`
- 同时提取比赛日期等辅助信息

适合新项目的原因：

- 不依赖 Flask
- 不依赖 MySQL
- 主要是 HTTP 请求和 JSON 解析
- 可以作为新项目采集链路的起点

建议：

- 直接复用其请求与解析思路
- 输出结构保留为更清晰的字典对象，而不是多个并行列表

---

### 2. 赔率详情抓取与字段提取逻辑

来源文件：`crawler/crawl_insert.py`

建议复用的函数：

- `get_had(data)`
- `get_hhad(data)`
- `get_ttg(data)`
- `get_hafu(data)`
- `get_crs(data)`
- `get_meta(data)`
- `restore_data(data)`
- `crawl_match_bet(match_id_list)`

这些函数的核心价值：

- 从赔率详情接口返回的复杂 JSON 结构中抽取业务数据
- 将不同玩法的数据拆分出来
- 对数据完整性做基本检查
- 支持按 `matchId` 批量抓取赔率详情

适合新项目的原因：

- 这些逻辑本质上是“外部 JSON → 结构化业务字段”
- 是最容易在手工重写时出错的部分
- 在新项目里可以直接变成“抓取后写 CSV 前的数据标准化层”

建议：

- 保留函数职责
- 重写返回结构，优先使用 `dict`，不要继续使用依赖固定索引位置的 `list`

示例方向：

```python
{
  "match_id": 123,
  "team_home": "A队",
  "team_away": "B队",
  "had": {"h": 1.82, "d": 3.25, "a": 4.10},
  "ttg": {"s0": 8.5, "s1": 4.2},
}
```

---

### 3. Prompt 模板资产

来源文件：

- `prompt_template.txt`
- `prompt_data_input.txt`

它们的价值不在于“程序调用”，而在于：

- 定义了什么样的赔率文本适合喂给模型
- 定义了 Prompt 大致应该长什么样
- 定义了模型输出结果的约束格式

适合新项目的原因：

- 新项目仍然需要“CSV 数据 → Prompt”
- 这两个文件可以直接作为第一版产品原型的参考输入与模板

建议：

- `prompt_template.txt` 可作为新项目 Prompt 初稿
- `prompt_data_input.txt` 可作为 CSV 字段设计参考样例

---

## 二、可以复用思路，但建议重写的代码

这些代码有业务价值，但原实现与当前项目结构耦合过深，不适合直接复制。

### 1. Prompt 拼接逻辑

来源文件：`app.py`

相关函数：

- `get_match_data_prompt(team1, team2)`
- `enhance_prompt(bet_data_prompt, money)`

可复用的部分：

- 如何把赔率字段组织成自然语言文本
- 如何将比赛信息按固定编号写入 Prompt
- 如何将“赔率数据块”拼成完整的大模型请求

不适合直接复制的原因：

- `get_match_data_prompt()` 强依赖 MySQL
- SQL 查询与当前旧表结构深度绑定
- 与新项目的 CSV 数据源不匹配

建议：

- 保留文本组织方式
- 将数据源改为 CSV 读取结果
- 重写为例如：

```python
def build_match_data_prompt(row: dict) -> str:
    ...

def build_full_prompt(match_prompt: str, money: int) -> str:
    ...
```

其中：

- `build_match_data_prompt()` 负责 CSV 行转文本
- `build_full_prompt()` 负责包装成完整 Prompt

---

### 2. 大模型调用逻辑

来源文件：`app.py`

相关位置：`/api/getSuggestions` 路由中的 `dashscope.Generation.call(...)`

可复用的部分：

- `messages = [{"role": "user", "content": prompt}]` 这种调用形式
- 将 Prompt 发送给大模型并获取消息结果的思路

不适合直接复制的原因：

- API Key 被硬编码
- 模型名被写死
- 逻辑写在 Flask 路由内部
- 错误处理与 Web 返回耦合在一起

建议：

- 提取为独立模块
- 封装成纯函数
- 使用环境变量传入 API Key

例如：

```python
def call_llm(prompt: str) -> str:
    ...
```

---

### 3. 大模型结果解析逻辑

来源文件：`app.py`

相关逻辑：`re_extract(response)`

可复用的部分：

- 通过 Prompt 约束输出格式
- 使用正则表达式提取投注组合
- 对金额总和进行一次校验

不适合直接复制的原因：

- 现在的返回值中混入了 `jsonify(...)`
- 与 Flask 接口层耦合
- 可读性和可测试性一般

建议：

- 将其改造成纯函数
- 输入为模型原始文本
- 输出为结构化 Python 对象

例如：

```python
def parse_llm_output(text: str) -> list[dict]:
    ...
```

---

### 4. 表格数据读取思路

来源文件：`crawler/excel2database.py`

可复用的部分：

- 读取表格后按列名取值
- 将表格数据映射成结构化记录的思路

不适合直接复制的原因：

- 它面向 Excel 而不是 CSV
- 它后续目标是写 MySQL，而不是给 Prompt 用
- 数据结构是围绕旧数据库表设计的

建议：

- 借鉴“按列名映射”的思路
- 新项目单独写 `csv_io.py`

---

## 三、不建议复用的代码

这些代码与新项目目标偏离太远，继续带上只会增加复杂度。

### 1. Flask 路由层

来源：

- `blueprints/user.py`
- `blueprints/v2.py`
- `app.py` 中的所有接口路由

不建议复用的原因：

- 新项目不需要 Web API 才能完成目标链路
- 路由层会把你重新拉回旧项目架构
- `request/jsonify/Blueprint` 对最小化脚本项目没有必要

---

### 2. 所有 MySQL 写入/更新逻辑

来源：

- `crawler/crawl_insert.py` 后半段插库函数
- `crawler/crawl_insert_newest_match.py`
- `crawler/crawl_insert_history_match.py`
- `crawler/excel2database.py` 的插库逻辑

典型不建议复用的函数：

- `insert_match_result`
- `insert_match_had`
- `insert_match_hhad`
- `insert_match_crs`
- `insert_match_hafu`
- `insert_match_ttg`
- `insert_all_data`
- `insert_or_update`
- `query_match_ids_by_date_range`

不建议复用的原因：

- 新项目存储目标是 CSV，不是 MySQL
- 这些代码与当前数据库表结构强绑定
- 复制后反而会让新项目背上旧系统的表设计包袱

---

### 3. 定时任务与部署脚本

来源：

- `app.py` 中的 APScheduler 逻辑
- `run.sh`
- `kill.sh`

不建议复用的原因：

- 新项目当前目标是最小可运行链路，不需要调度系统
- 先把主流程做成一次性脚本再考虑自动化

---

### 4. 用户模块

来源：`blueprints/user.py`

不建议复用的原因：

- 与当前需求完全无关
- 且密码逻辑仍是简单明文校验，不值得迁移

---

## 四、最适合迁移的“核心能力”总结

如果只挑最有价值的能力迁移，我建议只保留下面四组：

### A. 外部比赛列表接口抓取能力

用途：获取比赛 ID 与比赛日期。

对应旧代码：

- `fetch_data`
- `get_match_id`
- `crawl_match_ids`
- `crawl_five_league_match_ids`

### B. 赔率详情 JSON 解析能力

用途：将体彩赔率详情接口的复杂 JSON 抽成结构化字段。

对应旧代码：

- `get_had`
- `get_hhad`
- `get_ttg`
- `get_hafu`
- `get_crs`
- `get_meta`
- `restore_data`

### C. Prompt 文本组织能力

用途：将一条比赛赔率记录转换成适合喂给模型的自然语言文本。

对应旧代码：

- `get_match_data_prompt` 的文本拼装思路
- `enhance_prompt`
- `prompt_template.txt`
- `prompt_data_input.txt`

### D. 模型输出结构化解析能力

用途：从模型文本结果中提取最终投注组合。

对应旧代码：

- `re_extract` 的思路

---

## 五、建议的新项目拆分方式

建议新项目不要继续沿用旧项目的目录结构，而是改成围绕“最小链路”的结构。

推荐拆分如下：

### `crawler.py`

吸收旧代码：

- `fetch_data`
- `get_match_id`
- `crawl_match_ids`
- `crawl_five_league_match_ids`
- `crawl_match_bet`

职责：

- 从外部接口获取比赛列表和赔率详情

---

### `odds_parser.py`

吸收旧代码：

- `get_had`
- `get_hhad`
- `get_ttg`
- `get_hafu`
- `get_crs`
- `get_meta`
- `restore_data`

职责：

- 将原始 JSON 转换为结构化 Python 数据

建议：

- 用 `dict` 返回数据，不再依赖位置索引

---

### `csv_io.py`

新写。

职责：

- 将结构化比赛数据写入 CSV
- 从 CSV 文件中读取指定比赛或全部记录

字段设计可参考：

- `get_meta()` 提取出的元信息
- 各 `get_*()` 提取出的赔率字段
- `prompt_data_input.txt` 的展示格式

---

### `prompt_builder.py`

吸收思路：

- `get_match_data_prompt`
- `enhance_prompt`
- `prompt_template.txt`

职责：

- 将 CSV 行转成 Prompt 数据块
- 将数据块包装成完整 Prompt

---

### `llm_client.py`

吸收思路：

- `dashscope.Generation.call(...)`
- `re_extract(...)`

职责：

- 调用大模型
- 解析模型输出

建议：

- API Key 使用环境变量
- 模型名做成配置项

---

### `main.py`

新写。

职责：

- 串起完整流程：
  1. 抓数据
  2. 写 CSV
  3. 读 CSV
  4. 生成 Prompt
  5. 调模型
  6. 输出结果

---

## 六、实际迁移建议

如果希望迁移工作最省力，建议遵循下面原则：

1. **保留业务知识，不保留旧工程结构**
2. **保留 JSON 解析函数，重写存储层**
3. **保留 Prompt 模板思路，重写数据读取方式**
4. **保留模型输出约束思路，重写调用封装**
5. **不要把 Flask、MySQL、APScheduler 一起带进新项目**

---

## 七、最终建议（最短版）

如果只能挑最值得带走的内容，请优先带走：

1. `crawler/crawler_all_match_id.py` 中的比赛列表抓取逻辑
2. `crawler/crawl_insert.py` 前半段的赔率解析逻辑
3. `app.py` 中 Prompt 拼接思路
4. `prompt_template.txt` 与 `prompt_data_input.txt`
5. `app.py` 中模型结果正则提取思路

如果只能挑最该丢掉的内容，请优先丢掉：

1. Flask 接口层
2. MySQL 插入/更新逻辑
3. 定时任务与部署脚本
4. 用户模块

一句话总结：

**新项目应当复用“抓取 + 解析 + Prompt + LLM 输出解析”的领域能力，而不是复用这个旧项目的 Flask/MySQL 工程壳子。**
