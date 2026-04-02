#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2026/3/29 19:47
# @Author  : david_van
# @Desc    :
import os

from llm_client import OpenAILLMClient, parse_suggestions
from prompt_builder import enhance_prompt
OPENAI_API_BASE_URL="https://bytecat.lamclod.cn/v1"
OPENAI_API_KEY="sk-MRQ3H4InjzKD8XfJ4O6Vf4az2zrSJ0Tb3qNdXOfaRuXejlgW"
MODEL = "gpt-5.4"
MODEL_CLAUDE = "claude-opus-4-6"
MODEL_gemini = "gemini-3.1-pro-high"
GOOGLE_API_KEY='sk-WSfhbYxR9u2P7UiYAXedLE3LS60FnpAGF3CPukNRJXozKWJj'

# chatgpt
# ## 12. 最终结论
#
# 这是我认为在你给出的赔率里，**最偏向“高概率、低波动、尽量不亏”**的一组：
#
# %%【玩法3（非让球负），购买金额：10元】，【玩法12（进球数2-3），购买金额：10元】，【玩法11（进球数0-1），购买金额：10元】%%

# Claude code
# %%【玩法3(非让球负)，购买金额：10元】，【玩法12(进球数：2-3)，购买金额：10元】，【玩法29(负负)，购买金额：6元】，【玩法25(平平)，购买金额：4元】%%


# Gemini网页
# 稳健基石：投注**【玩法3：非让球负】**。只要丹麦获胜，即可收回 20.5元，极大地保护了本金。
#
# 概率之选：投注**【玩法12：进球数2-3】**。这是历史概率最高的分布区间，回报 20.2元。
#
# 高赔对冲/保本：投注**【玩法25：平平】**。针对 0:0 或 1:1（半场平局且全场平局）的救赎剧本，一旦命中回报高达 45元，足以覆盖全场损失并实现翻倍盈利。

# Gemini api的方式
# ### 8. 最终投注策略和步骤
# 基于以上所有严密的数据挖掘和对冲计算，我为您生成了完全符合指示的投注组合。该组合覆盖了赛果的绝大部分高概率空间，将风险降到了极低，并具备合理的重叠盈利机会。
#
# %%【玩法3(非让球负)，购买金额：14元】，【玩法2(非让球平)，购买金额：8元】，【玩法12(进球数：2-3)，购买金额：8元】%%

if __name__ == '__main__':
    with open('prompt_data_demo.txt', 'r', encoding='utf-8') as f:
        bet_data = f.read()
    money = 30
    prompt = enhance_prompt(bet_data, money)
    print(f"prompt is {prompt}")

    llm_client = OpenAILLMClient(base_url=OPENAI_API_BASE_URL,api_key=GOOGLE_API_KEY,
                                 model=MODEL_gemini
     )
    response_text = llm_client.chat(prompt)
    suggestions = parse_suggestions(response_text, money)