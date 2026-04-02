# 足球比赛预测系统 - 集成设计方案

## Context

用户已有三个足球预测项目（MatchPredict、lottery、w5-football-prediction），但因历史数据训练效果差，决定不再进行模型训练。希望直接用最近比赛数据让AI分析，并集成三个系统的优点达到最优效果。

---

## 一、设计目标

1. **不依赖历史数据训练** - 纯AI实时分析
2. **多角度AI分析** - 类似专家团队讨论
3. **详细赔率分析** - 覆盖多种玩法
4. **可操作的投注建议** - 包含金额分配和期望值计算
5. **结构化输出** - 概率分布 + 文本分析 + 置信度

---

## 二、核心架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      用户请求                               │
│              (球队A vs 球队B + 投注金额)                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    数据收集层                                │
│  1. 比赛基本信息（联赛、主客场）                               │
│  2. 54种赔率数据（胜平负/让球/比分/半全场/进球数）            │
│  3. 历史交锋数据（最近5场）                                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  多Agent辩论共识层                           │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ │
│  │统计师   │ │战术师   │ │情绪师   │ │新闻师   │ │风险师   │ │
│  │Agent    │ │Agent    │ │Agent    │ │Agent    │ │Agent    │ │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ │
│       │           │           │           │           │       │
│       └───────────┴───────────┴───────────┴───────────┘       │
│                           │                                   │
│                    辩论 → 修订 → 共识                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    输出融合层                                 │
│  1. 胜平负概率分布（含置信度）                                 │
│  2. 期望值(EV)计算                                            │
│  3. 最优投注组合及金额分配                                     │
│  4. 风险提示                                                  │
│  5. 多角度AI分析文本                                          │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Agent角色定义（继承w5）

| Agent | 角色 | 系统提示重点 | 分析重点 |
|-------|------|-------------|---------|
| **Statistician** | 统计分析师 | 数据驱动、统计显著性 | 历史战绩、ELO、进球/失球均值 |
| **Tactician** | 战术分析师 | 阵型、战术对位 | 进攻风格、防守能力、关键球员 |
| **Sentiment** | 市场情绪师 | 赔率变动、公众预期 | 赔率异常、热门/冷门判断 |
| **News** | 新闻分析师 | 伤病、士气、战意 | 伤停信息、球队动态、主客场因素 |
| **Risk** | 风险评估师 | 不确定性、高方差场景 | 意外因素、波动性、极端比分 |

---

## 三、数据流设计

### 3.1 输入数据

```json
{
  "home_team": "曼城",
  "away_team": "利物浦",
  "league": "英超",
  "match_time": "2024-12-28 20:30",
  "stake_amount": 100,
  "odds": {
    "had": { "h": 2.10, "d": 3.50, "a": 2.80 },
    "hhad": { "h": 1.95, "d": 3.40, "a": 3.20 },
    "crs": {
      "s01s00": 8.5, "s02s00": 12.0, "s02s01": 9.5,
      "s00s00": 6.0, "s11s11": 6.5, "s22s22": 25.0,
      "s00s01": 7.5, "s00s02": 13.0, "s_1sa": 35.0
    },
    "ttg": { "s0": 12.0, "s1": 4.5, "s2": 3.2, "s3": 4.0, "s4": 6.5, "s7": 15.0 },
    "hafu": { "hh": 3.8, "hd": 20.0, "ha": 45.0, "dh": 4.5, "dd": 4.2, "da": 18.0, "ah": 18.0, "ad": 5.5, "aa": 3.5 }
  },
  "h2h": [
    { "date": "2024-08-25", "home": "曼城", "away": "利物浦", "score": "2-2" },
    { "date": "2024-03-10", "home": "利物浦", "away": "曼城", "score": "1-0" }
  ]
}
```

### 3.2 Prompt设计（融合lottery的详细框架）

**每个Agent接收的统一Prompt结构**：

```
## 比赛信息
主队：{home_team} | 客队：{away_team} | 联赛：{league}

## 赔率数据（54种玩法）
[详细列出所有赔率...]

## 历史交锋
[最近5场对战记录]

## 你的角色
{agent_system_prompt}

## 分析要求（8步框架）
1. 隐含概率计算 - 从赔率计算各方概率
2. 实力对比分析 - 结合历史数据评估
3. 战术对位分析 - 阵型/风格克制
4. 市场情绪分析 - 赔率是否异常
5. 不确定性评估 - 哪些因素增加波动
6. 期望值(EV)计算 - 各选项的EV
7. 风险收益比 - 性价比评估
8. 最终预测 - 概率分布 + 推荐

## 输出格式
{
  "home_win_prob": 0.40,
  "draw_prob": 0.30,
  "away_win_prob": 0.30,
  "confidence": 0.75,
  "key_factors": ["factor1", "factor2"],
  "reasoning": "详细分析...",
  "recommended_bets": [
    { "type": "had_h", "odds": 2.10, "ev": 0.02, "stake": 50 }
  ]
}
```

### 3.3 多轮辩论流程

```
Round 1: 独立分析
─────────────────────────────────────────
Agent1 → 独立预测 → {home:0.35, draw:0.32, away:0.33, conf:0.70}
Agent2 → 独立预测 → {home:0.42, draw:0.28, away:0.30, conf:0.65}
Agent3 → 独立预测 → {home:0.38, draw:0.30, away:0.32, conf:0.72}
Agent4 → 独立预测 → {home:0.40, draw:0.35, away:0.25, conf:0.60}
Agent5 → 独立预测 → {home:0.45, draw:0.25, away:0.30, conf:0.68}
                    ↓
         ┌─────────────────────┐
         │  Peer Summary 生成   │
         │  avg_home=0.40      │
         │  avg_draw=0.30      │
         │  avg_away=0.30      │
         └─────────────────────┘
                    ↓
Round 2: 辩论修订
─────────────────────────────────────────
Agent1 → 看到平均预测后修订 → {home:0.38(+3%), draw:0.30(-2%), away:0.32(-1%)}
        ... 各Agent参考同伴后微调 ...

                    ↓
         ┌─────────────────────┐
         │  加权共识计算        │
         │  置信度加权平均      │
         │  方差一致性检验      │
         └─────────────────────┘
                    ↓
Final Consensus: {home:0.39, draw:0.30, away:0.31, confidence:0.85, agreement:0.78}
```

---

## 四、共识算法设计

### 4.1 置信度加权投票

```python
# 各Agent预测
predictions = [
    {'home': 0.35, 'draw': 0.32, 'away': 0.33, 'conf': 0.70},
    {'home': 0.42, 'draw': 0.28, 'away': 0.30, 'conf': 0.65},
    ...
]

# 置信度归一化权重
weights = [conf / sum(all_confs) for conf in all_confs]

# 加权平均
consensus_home = sum(w * p['home'] for w, p in zip(weights, predictions))
consensus_draw = sum(w * p['draw'] for w, p in zip(weights, predictions))
consensus_away = sum(w * p['away'] for w, p in zip(weights, predictions))

# 归一化
total = consensus_home + consensus_draw + consensus_away
consensus_home /= total  # 0.39
```

### 4.2 一致性分数（Agreement Score）

```python
variance = mean([
    var([p['home'] for p in predictions]),
    var([p['draw'] for p in predictions]),
    var([p['away'] for p in predictions])
])
agreement = 1 / (1 + variance * 10)  # 0.78

# 含义：
# > 0.7: 高一致性，Agent间分歧小
# 0.5-0.7: 中等一致性
# < 0.5: 低一致性，需要更多辩论
```

### 4.3 最终置信度

```python
final_confidence = agreement * weighted_avg_confidence
# 综合考虑了：Agent间一致性 + 各Agent自身置信度
```

---

## 五、投注策略设计

### 5.1 期望值(EV)计算

```python
# EV = 概率 × 赔率 - 1
# 例如：home_prob=0.40, home_odds=2.10
ev_home = 0.40 * 2.10 - 1 = -0.16  # 负EV
ev_draw = 0.30 * 3.50 - 1 = 0.05   # 正EV
ev_away = 0.30 * 2.80 - 1 = -0.16  # 负EV

# 正EV选项：仅平局具有正期望值
```

### 5.2 投注金额分配（参考lottery）

```python
# Kelly公式简化版
def kelly_fraction(prob, odds, fraction=0.25):
    ev = prob * odds - 1
    if ev <= 0: return 0
    return min(ev / (odds - 1) * fraction, 0.1)  # 最大10%仓位

# 分配示例（总投注100元）
bets = [
    {'type': 'had_d', 'odds': 3.50, 'prob': 0.30, 'kelly': 0.05},
    {'type': 'crs_11', 'odds': 6.50, 'prob': 0.12, 'kelly': 0.03},
]
total_kelly = sum(b['kelly'] for b in bets)
for bet in bets:
    bet['stake'] = 100 * (bet['kelly'] / total_kelly)  # 按比例分配
```

### 5.3 投注组合输出

```json
{
  "recommended_bets": [
    {
      "bet_type": "平局",
      "bet_code": "had_d",
      "odds": 3.50,
      "probability": 0.30,
      "ev": 0.05,
      "stake": 60,
      "reasoning": "30%概率，EV为正，风险较低"
    },
    {
      "bet_type": "1:1比分",
      "bet_code": "crs_11",
      "odds": 6.50,
      "probability": 0.12,
      "ev": -0.22,
      "stake": 40,
      "reasoning": "高赔率补充收益，金额较低"
    }
  ],
  "total_stake": 100,
  "expected_return": 110,
  "max_loss": 100,
  "risk_level": "中等"
}
```

---

## 六、输出结构设计

### 6.1 完整预测结果

```json
{
  "match": {
    "home_team": "曼城",
    "away_team": "利物浦",
    "league": "英超",
    "match_time": "2024-12-28 20:30"
  },

  "consensus_prediction": {
    "home_win": 0.39,
    "draw": 0.30,
    "away_win": 0.31,
    "predicted_score": "2-1",
    "total_goals_range": "2-3"
  },

  "confidence_metrics": {
    "overall_confidence": 0.85,
    "agreement_score": 0.78,
    "agent_count": 5
  },

  "agent_analyses": [
    {
      "agent": "Statistician",
      "prediction": {"home": 0.38, "draw": 0.30, "away": 0.32},
      "confidence": 0.72,
      "key_factors": ["主场胜率62%", "场均进球2.1"],
      "reasoning": "..."
    }
  ],

  "betting_recommendations": {
    "best_value_bets": [],
    "parlay_suggestions": [],
    "risk_warnings": []
  },

  "ai_summary": "综合5位分析师观点，曼城主场有一定优势，但平局和客胜概率也不低..."
}
```

---

## 七、与传统设计的核心区别

| 维度 | 传统ML训练 | 本设计方案 |
|------|-----------|-----------|
| **数据依赖** | 需要大量历史数据 | 仅需当前赔率 + 基本信息 |
| **模型更新** | 定期重新训练 | 无需训练，实时分析 |
| **预测方式** | 模型输出概率 | 多Agent辩论共识 |
| **可解释性** | 黑盒特征重要性 | Agent各自解释 |
| **适应性** | 滞后于市场变化 | 实时反映赔率信息 |
| **维护成本** | 高（数据+训练+部署） | 低（仅API调用） |

---

## 八、技术要点总结

### 8.1 继承自三个系统的优点

- **来自MatchPredict**: 清晰的输出格式、信心指数、多维度预测
- **来自lottery**: 54种赔率全覆盖、8步分析框架、EV计算、投注组合优化
- **来自w5**: 多Agent辩论共识、置信度加权投票、一致性分数

### 8.2 关键创新

1. **纯AI实时分析** - 无需历史训练数据
2. **多角色辩论** - 5个专业化Agent多轮讨论
3. **EV驱动的投注建议** - 科学计算期望值而非主观判断
4. **一致性验证** - 通过方差检验Agent共识强度

---

## 九、验证方案

1. **单元测试**: 测试各Agent独立分析、共识计算、EV计算
2. **模拟验证**: 用历史赔率数据回测投注策略表现
3. **对比分析**: 与单一AI调用、简单平均法的效果对比
4. **实际比赛验证**: 记录预测结果，跟踪实际赛果
