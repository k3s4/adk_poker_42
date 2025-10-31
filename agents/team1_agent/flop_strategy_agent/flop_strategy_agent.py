"""
Flop Strategy Agent - A 3-step sequential agent for post-flop decisions.
1) Evaluate hand strength.
2) Analyze betting situation.
3) Decide action based on strict rules.
"""
from google.adk.agents import Agent, SequentialAgent
from google.adk.models.lite_llm import LiteLlm
from .tools.hand_evaluator import evaluate_hand
from .tools.analyze_bet_situation import analyze_bet_situation

# Define model constant
MODEL_GPT_4O_MINI = LiteLlm(model="gpt-4o-mini")
AGENT_MODEL = MODEL_GPT_4O_MINI

# 1) Hand Evaluator Agent
hand_evaluator_agent = Agent(
    name="poker_hand_evaluator",
    model=AGENT_MODEL,
    description="現在のポーカーハンドの強さを評価します。",
    instruction='''あなたはポーカーのハンド評価の専門家です。
あなたのタスクは、ホールカードとコミュニティカードに基づいてポーカーハンドの強さを評価することです。

現在のフェーズ: {current_phase}
もし {current_phase} が "preflop" の場合、タスクを実行せずに "SKIP" と出力してください。

タスク (フロップ、ターン、リバーのフェーズでのみ実行):
- `evaluate_hand` ツールを使用して、手札の強さを0から100のスコアで決定します。

出力:
- ツールから返されるJSONオブジェクト。追加のテキストや説明は一切含めないでください。
''',
    tools=[evaluate_hand],
    output_key="hand_evaluation",
)

# 2) Bet Situation Analyzer Agent
bet_analyzer_agent = Agent(
    name="poker_bet_analyzer",
    model=AGENT_MODEL,
    description="相手のベットサイズをポットと比較して脅威度を分析します。",
    instruction='''あなたはポーカーの状況分析の専門家です。
あなたのタスクは、現在のベット状況を分析することです。

現在のフェーズ: {current_phase}
もし {current_phase} が "preflop" の場合、タスクを実行せずに "SKIP" と出力してください。

タスク (フロップ、ターン、リバーのフェーズでのみ実行):
- `analyze_bet_situation` ツールを使用して、コールに必要な額がポットの何%にあたるかを計算し、脅威度（threat_level）を判定します。

出力:
- ツールから返されるJSONオブジェクト。追加のテキストや説明は一切含めないでください。
''',
    tools=[analyze_bet_situation],
    output_key="bet_situation_analysis",
)


# 3) Flop Action Decider Agent
flop_action_agent = Agent(
    name="poker_flop_action_decider",
    model=AGENT_MODEL,
    description="手の強さとベットの脅威度に基づき、厳格なルールに従ってアクションを決定します。",
    instruction='''あなたはポーカーの意思決定を行うエキスパートです。手札の強さと相手のベット状況の分析結果に基づいて、以下のルールに厳密に従ってアクションを決定してください。

[前提]
- 現在のフェーズ: {current_phase}
- もし現在のフェーズが "preflop" の場合、または前のステップの分析結果が "SKIP" の場合は、このタスクを実行せずに "SKIP" と出力してください。

[分析結果]
- 手の強さの分析結果: {hand_evaluation}
- ベット状況の分析結果: {bet_situation_analysis}

これらの分析結果に含まれる `strength_score` と `threat_level` の値を参照して、以下のルールに従ってください。

[ルール]
- **ルール1: モンスターハンド (スコア >= 90)**
  - この手では絶対にフォールドしません。
  - 脅威度が "HIGH" または "EXTREME" の場合は「コール」します。
  - 脅威度が "MEDIUM" または "LOW" の場合は「レイズ」します。
  - 脅威度が "NONE" (ベットがない) の場合は「ベット」します。（ポットの75%程度のサイズ）

- **ルール2: 非常に強い手 (スコア 80〜89)**
  - 脅威度が "EXTREME" の場合は「フォールド」します。
  - 脅威度が "HIGH" の場合は「コール」します。
  - 脅威度が "MEDIUM" または "LOW" の場合は「レイズ」します。（ポットの50%程度のサイズ）
  - 脅威度が "NONE" の場合は「ベット」します。（ポットの50%程度のサイズ）

- **ルール3: 良い手 (スコア 65〜79)**
  - 脅威度が "HIGH" または "EXTREME" の場合は「フォールド」します。
  - 脅威度が "MEDIUM" または "LOW" の場合は「コール」します。
  - 脅威度が "NONE" の場合は「チェック」します。

- **ルール4: 中間的な手 (スコア 50〜64)**
  - 脅威度が "MEDIUM", "HIGH", "EXTREME" の場合は「フォールド」します。
  - 脅威度が "LOW" の場合は「コール」します。
  - 脅威度が "NONE" の場合は「チェック」します。

- **ルール5: ウィークハンド (スコア < 50)**
  - 脅威度が "NONE" (ベットがない) 以外の場合は、すべて「フォールド」します。
  - 脅威度が "NONE" の場合は「チェック」します。

[出力]
- 以下のJSON形式で、決定したアクションと簡単な理由を出力してください。説明文などは一切不要です。
`{
  "action": "fold|check|call|raise|all_in",
  "amount": <数値>,
  "reasoning": "戦略的理由の要約（日本語）"
}`
''',
    output_key="flop_strategy_analysis",
)

# Main Sequential Agent for Flop Strategy
flop_strategy_agent = SequentialAgent(
    name="poker_flop_sequential_strategy",
    sub_agents=[
        hand_evaluator_agent,
        bet_analyzer_agent,
        flop_action_agent,
    ],
)

__all__ = ["flop_strategy_agent"]