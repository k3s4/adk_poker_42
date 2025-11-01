"""
Preflop Strategy Agent - プリフロップの戦略分析を3段階で順次実行
1) ポジション確認 → 2) ハンド強さ分類 → 3) アクション決定
"""

from google.adk.agents import Agent, SequentialAgent
from google.adk.models.lite_llm import LiteLlm
from .tools import classify_hand, evaluate_preflop_action

# Define model constant
MODEL_GPT_4O_MINI = LiteLlm(model="gpt-4o-mini")
AGENT_MODEL = MODEL_GPT_4O_MINI

# 1) ポジション確認
position_checker_agent = Agent(
    name="poker_position_checker",
    model=AGENT_MODEL,
    description="プリフロップのあなたのポジションを短く特定",
    instruction="""あなたは与えられたゲーム状態から、あなたの現在ポジションを1語で特定します。

前提:
- 現在フェーズ: {current_phase}
- {current_phase} が "preflop" 以外なら、タスクを実行せずにただ "SKIP" と出力

タスク(プリフロップ時のみ実行):
- あなたのポジションを次のいずれか1語で厳密に出力: UTG / CO / BTN / SB / BB

出力: 上記のいずれか1語と（もしくは SKIP）。""",
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
- {current_phase} が "preflop" 以外、または {position} が "SKIP" の場合はタスクを実行せずに"SKIP" と出力

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
- {current_phase} が "preflop" 以外、または {position} が "SKIP" の場合はタスクを実行せずに"SKIP" と出力
- 前ステップで計算済みのハンド強さスコア: {hand_classification}

タスク(プリフロップ時のみ実行):
- 既に計算された {hand_classification} のスコア（0-6）を参照
- evaluate_preflop_action ツールを hand_classification 引数に {hand_classification} を渡して使用
- 先行アクションを踏まえた推奨アクションを導出（ポッドオッズやポットサイズ、SPRは無視）
- アクションは fold / check / call / raise / all_in のいずれか

出力: 推奨アクション・合計額・根拠を日本語で詳細に説明したテキスト（もしくは SKIP）。

出力形式:
- ツール結果のJSONのみを厳密に出力（前後に説明文を付けない）
- 必ず次のJSON形式で回答してください:
{
  "action": "fold|check|call|raise|all_in",
  "amount": <数値>,
  "reasoning": "あなたの決定の理由を説明"
}

ルール:
- "fold"と"check"の場合: amountは0にしてください
- "call"の場合: コールに必要な正確な金額を指定してください
- "raise"の場合: レイズ後の合計金額を指定してください
- "all_in"の場合: あなたの残りチップ全額を指定してください
""",
    tools=[
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
