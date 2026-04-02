"""Prompt builder — pure functions for constructing LLM prompts from normalized data."""

from src.models import NormalizedOddsRow


class PromptBuildError(Exception):
    """Raised when prompt building fails due to missing data."""


def build_match_data_prompt(row: dict) -> str:
    """Build the per-match odds data block from a normalized row.

    Produces the numbered play format (玩法1-54) matching the legacy contract.
    """
    required = ["home_team", "away_team", "had_h", "had_d", "had_a"]
    for field in required:
        if not row.get(field):
            raise PromptBuildError(f"Missing required field '{field}' in normalized row")

    lines = []
    lines.append(f"主球队1:{row['home_team']}")
    lines.append(f"客球队2:{row['away_team']}")

    # Non-handicap HAD (plays 1-3)
    lines.append(f"玩法1：非让球胜，对应的赔率： {row['had_h']}")
    lines.append(f"玩法2：非让球平，对应的赔率： {row['had_d']}")
    lines.append(f"玩法3：非让球负，对应的赔率： {row['had_a']}")

    # Handicap HHAD (plays 4-6)
    lines.append(f"玩法4：让球胜，对应的赔率： {row['hhad_h']}")
    lines.append(f"玩法5：让球平，对应的赔率： {row['hhad_d']}")
    lines.append(f"玩法6：让球负，对应的赔率： {row['hhad_a']}")

    # CRS — correct score (plays 7-37)
    crs_plays = [
        (7, "1:0", "crs_1_0"), (8, "2:0", "crs_2_0"), (9, "2:1", "crs_2_1"),
        (10, "3:0", "crs_3_0"), (11, "3:1", "crs_3_1"), (12, "3:2", "crs_3_2"),
        (13, "4:0", "crs_4_0"), (14, "4:1", "crs_4_1"), (15, "4:2", "crs_4_2"),
        (16, "5:0", "crs_5_0"), (17, "5:1", "crs_5_1"), (18, "5:2", "crs_5_2"),
        (19, "胜其他", "crs_win_other"),
        (20, "0:0", "crs_0_0"), (21, "1:1", "crs_1_1"), (22, "2:2", "crs_2_2"),
        (23, "3:3", "crs_3_3"), (24, "平其他", "crs_draw_other"),
        (25, "0:1", "crs_0_1"), (26, "0:2", "crs_0_2"), (27, "1:2", "crs_1_2"),
        (28, "0:3", "crs_0_3"), (29, "1:3", "crs_1_3"), (30, "2:3", "crs_2_3"),
        (31, "0:4", "crs_0_4"), (32, "1:4", "crs_1_4"), (33, "2:4", "crs_2_4"),
        (34, "0:5", "crs_0_5"), (35, "1:5", "crs_1_5"), (36, "2:5", "crs_2_5"),
        (37, "负其他", "crs_lose_other"),
    ]
    for num, label, field in crs_plays:
        lines.append(f"玩法{num}：{label}，对应的赔率： {row[field]}")

    # TTG — total goals (plays 38-45)
    for i in range(7):
        lines.append(f"玩法{38 + i}：进球数：{i}，对应的赔率： {row[f'ttg_s{i}']}")
    lines.append(f"玩法45：进球数：7+，对应的赔率： {row['ttg_s7']}")

    # HAFU — half/full result (plays 46-54)
    hafu_plays = [
        (46, "胜胜", "hafu_hh"), (47, "胜平", "hafu_hd"), (48, "胜负", "hafu_ha"),
        (49, "平胜", "hafu_dh"), (50, "平平", "hafu_dd"), (51, "平负", "hafu_da"),
        (52, "负胜", "hafu_ah"), (53, "负平", "hafu_ad"), (54, "负负", "hafu_aa"),
    ]
    for num, label, field in hafu_plays:
        lines.append(f"玩法{num}：{label}，对应的赔率： {row[field]}")

    return "\n".join(lines) + "\n"


PROMPT_TEMPLATE = """请分析这个赔率，并结合2队的最近比赛数据，给我一个尽量不亏钱的高概率的投注组合，投注金额{money}元
以下为比赛的信息及赔率数据：{bet_data_prompt}

基于这些数据，我希望你提供一个系统性的投注建议，确保建议的科学性、合理性和高效性。请按以下步骤进行详细分析，最大化保本，按照每次10元投注，每个投注选项是2元的整数倍。

1. **赔率数据和隐含概率计算**：
   - 分析这场比赛的赔率高低，并根据隐含概率计算每个结果的发生概率。请解释各项隐含概率的计算步骤，并基于赔率分析出博彩公司对比赛结果的初步预测。
   - 若存在异常赔率或明显的赔率偏差，请详细说明这些赔率的含义，并分析可能存在的投注机会。

2. **算法与模式识别分析**：
   - 利用机器学习和数据挖掘的思路，提供可以识别赔率模式的策略，帮助判断哪些赔率组合更可能对应特定结果（例如热门选项、冷门结果）。
   - 请建议使用简单的分类算法（如逻辑回归、决策树）来识别有投注价值的赔率特征。如果可能，给出该算法的简单实现思路，并详细描述如何使用它识别投注机会。

3. **基于赔率的期望收益（EV）和投注策略**：
   - 基于隐含概率和赔率，计算每个结果的期望收益 (EV)，并判断投注是否具有正期望值。如果EV为正值，请提供一个合理的资金分配策略。
   - 提供具体的投注金额分配建议，并解释如何根据期望收益来优化投注金额，以降低风险并提高长期收益。

4. **主客场因素的模型分析**：
   - 基于主客场数据，建议一个回归模型（如线性回归或逻辑回归）来进一步优化主客场因素对比赛结果的影响分析。请解释如何利用主客场赔率来判断投注的机会，尤其是在主场优势或冷门客胜赔率存在时。

5. **风险管理与投注分散**：
   - 在推荐投注方向时，请给出合理的风险管理建议。建议一种分散投注策略，并解释如何在投注选项中分配资金，以保证收益风险比的合理性。
   - 提供小额冷门投注的策略（如平局或高赔率选项），并详细解释这种投注的预期收益与风险。

6. **基于历史数据的相似性分析**：
   - 若假设有过去类似赔率的比赛数据，使用 K 近邻算法（KNN）或其他相似性分析方法，帮助识别历史上相似赔率的结果分布。详细解释如何使用历史模式来提高预测的科学性，并判断是否有冷门投注的机会。

7. **结果回测与验证**：
   - 提供如何使用回测方法（如蒙特卡洛模拟或历史回测）评估该投注策略的长期表现。解释如何根据回测结果优化参数、调整策略以确保策略的稳定性和有效性。

8. **最终投注策略和步骤**：
   - 基于上述分析和模型计算，给出明确的投注建议，包括具体的投注方向、推荐金额分配，以及如何在多项选择中有效分散投注。
   - 请在每一步解释策略的逻辑，并建议如何根据市场数据的变化来调整投注方向。


请注意，输出的格式严格按照我的指示，我仅希望生成一组投注组合，你最后结论的投注组合用"%%"前后包围，该投注组合中的每一个投注方式用中文中括号包住，示例：%%【玩法+序号(玩法内容)，购买金额：】，【玩法+序号(玩法内容)，购买金额：】，【玩法+序号(玩法内容)，购买金额：】%%。"""


def enhance_prompt(bet_data_prompt: str, money: int) -> str:
    """Wrap the odds data block into the full analysis prompt."""
    return PROMPT_TEMPLATE.format(bet_data_prompt=bet_data_prompt, money=money)
