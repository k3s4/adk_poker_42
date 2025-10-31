"""
Preflop Strategy Agent - プリフロップの戦略分析を3段階で順次実行
1) ポジション確認 → 2) ハンド強さ分類 → 3) アクション決定
"""

from google.adk.agents import Agent, SequentialAgent
from .tools import classify_hand, analyze_preflop_position_value, evaluate_preflop_action

# Define model constant
MODEL_GPT_4O_MINI = "gpt-4o-mini"
AGENT_MODEL = MODEL_GPT_4O_MINI

# 1) ポジション確認
position_checker_agent = Agent(
    name="poker_position_checker",
    model=AGENT_MODEL,
    description="プリフロップのあなたのポジションを短く特定",
    instruction="""あなたは与えられたゲーム状態から、あなたの現在ポジションを1語で特定します。

前提:
- 現在フェーズ: {current_phase}
- {current_phase} が "preflop" 以外なら、ただ "SKIP" と出力

タスク(プリフロップ時のみ実行):
- あなたのポジションを次のいずれか1語で厳密に出力: UTG / CO / BTN / SB / BB

出力: 上記のいずれか1語のみ（もしくは SKIP）。""",
    output_key="position",
)

# 2) ハンドの強さを分類
hand_classifier_agent = Agent(
    name="poker_preflop_hand_classifier",
    model=AGENT_MODEL,
    description="ハンドのレンジを確認し、強さスコアを付与",
    instruction="""あなたはプリフロップのハンドのレンジを確認し、強さスコアを付与します。

前提:
- 現在フェーズ: {current_phase}
- {current_phase} が "preflop" 以外、または {position} が "SKIP" の場合は "SKIP" と出力

タスク(プリフロップ時のみ実行):
- classify_hand ツールを使用して、ホールカードを分類し、強さスコアを算出
- 強さは７段階．強さスコアが6の場合が最強，1の場合が最弱

出力形式:
- ツール結果のJSONのみを厳密に出力（前後に説明文を付けない）
""",
    tools=[
        classify_hand,
    ],
    output_key="hand_classification",
)

# 3) アクションする（フォールド・コール・レイズ）
preflop_action_agent = Agent(
    name="poker_preflop_action_decider",
    model=AGENT_MODEL,
    description="プリフロップでの推奨アクションを決定",
    instruction="""あなたはプリフロップ局面の最適アクションを決定します。

前提:
- 現在フェーズ: {current_phase}
- {current_phase} が "preflop" 以外、または {position} が "SKIP" の場合は "SKIP" と出力

タスク(プリフロップ時のみ実行):
- analyze_preflop_position_value ツールでポジション調整済み強度を確認
- evaluate_preflop_action ツールを使用し、先行アクションやポット状況を踏まえた推奨アクションを導出
- アクションは fold / check / call / raise / all_in のいずれか

出力: 推奨アクション・合計額・根拠を日本語で簡潔に要約したテキスト（もしくは SKIP）。""",
    tools=[
        analyze_preflop_position_value,
        evaluate_preflop_action,
    ],
    output_key="preflop_strategy_analysis",
)

# プリフロップ専用: 3タスクを順次実行
preflop_strategy_agent = SequentialAgent(
    name="poker_preflop_sequential_strategy",
    sub_agents=[
        position_checker_agent,
        hand_classifier_agent,
        preflop_action_agent,
    ],
)

__all__ = ["preflop_strategy_agent"]
