
from google.adk.agents import Agent, SequentialAgent
from google.adk.models.lite_llm import LiteLlm
from .tools.hand_evaluator import evaluate_hand

MODEL_GPT_4O_MINI = LiteLlm(model="gpt-4o-mini")
AGENT_MODEL = MODEL_GPT_4O_MINI

hand_evaluator_agent = Agent(
    name="poker_hand_evaluator",
    model=AGENT_MODEL,
    description="現在のポーカーハンドの強さを評価します。",
    instruction='''あなたはポーカーのハンド評価の専門家です。
あなたのタスクは、ホールカードとコミュニティカードに基づいてポーカーハンドの強さを評価することです。

現在のフェーズ: {current_phase}
もし {current_phase} が "preflop" の場合、タスクを実行せずに "SKIP" と出力してください。

タスク (フロップ、ターン、リバーのフェーズでのみ実行):
- `evaluate_hand` ツールを使用して、ベストな5枚のカードの組み合わせ、その役、そして強さのスコアを決定します。
- 強さのスコアは0から100の間の数値です。

出力:
- ツールから返されるJSONオブジェクト。追加のテキストや説明は一切含めないでください。
''',
    tools=[evaluate_hand],
    output_key="hand_evaluation",
)

flop_action_agent = Agent(
    name="poker_flop_action_decider",
    model=AGENT_MODEL,
    description="ハンド評価に基づいて推奨アクションを決定します。",
    instruction='''あなたはポストフロップ戦略に特化したポーカー戦略アナリストです。
あなたのタスクは、ハンド評価に基づいて推奨アクションを決定することです。

現在のフェーズ: {current_phase}
ハンド評価: {hand_evaluation}

もし {current_phase} が "preflop" であるか、{hand_evaluation} が "SKIP" の場合、タスクを実行せずに "SKIP" と出力してください。

タスク (フロップ、ターン、リバーのフェーズでのみ実行):
- {hand_evaluation} から `strength_score` を参照します。
- 推奨アクション「fold」、「check」、「call」、「raise」、「all_in」を決定します。
- あなたの決定について簡単な根拠を提供してください。

意思決定ロジック:
- strength_score > 80: "raise" (強いバリューベット)
- strength_score > 60: "raise" (バリューベット)
- strength_score > 40: "call" (中程度の強さのハンド)
- strength_score > 20: "check" (可能であれば。そうでなければ、小さなベットには "call"、大きなベットには "fold")
- strength_score <= 20: "fold" (弱いハンド)

出力:
- 以下の形式で単一のJSONオブジェクト。追加のテキストや説明は一切含めないでください:
{{
  "action": "fold|check|call|raise|all_in",
  "amount": <数値>,
  "reasoning": "戦略的理由の簡単な要約（日本語）。"
}}

ルール:
- "fold"と"check"の場合、`amount`は0にしてください。
- "call"の場合、コールに必要な正確な金額を指定してください。
- "raise"の場合、レイズ後の合計金額を指定してください。
- "all_in"の場合、残りのチップ全額を指定してください。
''',
    output_key="flop_strategy_analysis",
)

flop_strategy_agent = SequentialAgent(
    name="poker_flop_sequential_strategy",
    sub_agents=[
        hand_evaluator_agent,
        flop_action_agent,
    ],
)

__all__ = ["flop_strategy_agent"]
