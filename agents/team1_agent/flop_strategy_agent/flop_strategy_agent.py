
Flop Strategy Agent - A multi-step sequential agent for post-flop decisions.
"""
from google.adk.agents import Agent, SequentialAgent
from google.adk.models.lite_llm import LiteLlm
# Import all tools
from .tools.hand_evaluator import evaluate_hand
from .tools.analyze_bet_situation import analyze_bet_situation
from .tools.draw_analyzer import analyze_draw_potential
from .tools.player_count_analyzer import analyze_player_count

# --- Agent Definition ---
MODEL_GPT_4O_MINI = LiteLlm(model="gpt-4o-mini")
AGENT_MODEL = MODEL_GPT_4O_MINI

# Base instruction for agents to skip pre-flop phase
SKIP_PREFLOP_INSTRUCTION = """
現在のフェーズ: {current_phase}
もし {current_phase} が "preflop" の場合、タスクを実行せずに "SKIP" と出力してください。"""

# 1) Hand Evaluator Agent
hand_evaluator_agent = Agent(
    name="poker_hand_evaluator",
    model=AGENT_MODEL,
    description="手札の完成役の強さを0〜100のスコアで評価します。",
    instruction=f"{SKIP_PREFLOP_INSTRUCTION}\n\nタスク: `evaluate_hand` ツールを使い、手札の強さを評価してください。",
    tools=[evaluate_hand],
    output_key="hand_evaluation",
)

# 2) Draw Analyzer Agent
draw_analyzer_agent = Agent(
    name="poker_draw_analyzer",
    model=AGENT_MODEL,
    description="手札がドロー（ストレートやフラッシュの可能性）かどうかを分析します。",
    instruction=f"{SKIP_PREFLOP_INSTRUCTION}\n\nタスク: `analyze_draw_potential` ツールを使い、ドローの可能性を分析してください。",
    tools=[analyze_draw_potential],
    output_key="draw_analysis",
)

# 3) Player Count Analyzer Agent
player_count_analyzer_agent = Agent(
    name="poker_player_count_analyzer",
    model=AGENT_MODEL,
    description="現在ハンドに参加しているアクティブなプレイヤーの人数を数えます。",
    instruction=f"{SKIP_PREFLOP_INSTRUCTION}\n\nタスク: `analyze_player_count` ツールを使い、プレイヤー人数を分析してください。",
    tools=[analyze_player_count],
    output_key="player_count_analysis",
)

# 4) Bet Situation Analyzer Agent
bet_analyzer_agent = Agent(
    name="poker_bet_analyzer",
    model=AGENT_MODEL,
    description="相手のベットサイズをポットと比較して脅威度を分析します。",
    instruction=f"{SKIP_PREFLOP_INSTRUCTION}\n\nタスク: `analyze_bet_situation` ツールを使い、ベットの脅威度を判定してください。",
    tools=[analyze_bet_situation],
    output_key="bet_situation_analysis",
)

# 5) Semi-Bluff Agent
semi_bluff_agent = Agent(
    name="poker_semi_bluff_decider",
    model=AGENT_MODEL,
    description="特定の条件が揃った場合にセミブラフを行うかどうかを決定します。",
    instruction=f'''{SKIP_PREFLOP_INSTRUCTION}

あなたはポーカーの専門家として、セミブラフを行うべきか否かを判断します。

[分析結果]
- ドロー状況: {{draw_analysis}}
- プレイヤー人数: {{player_count_analysis}}
- ベット状況: {{bet_situation_analysis}}

[セミブラフ実行の条件]
1. ドロー状況で `FLUSH_DRAW` または `OESD` (オープンエンドストレートドロー) が検出されているか？
2. プレイヤー人数が `2` (ヘッズアップ) か？
3. ベット状況の脅威度が `NONE` (自分からベットできる状況) か？

[判断]
- もし上記の3条件がすべて満たされている場合、セミブラフを実行します。アクションは「ベット」、金額はポットの50%とします。その判断をJSON形式で出力してください。
- 条件が満たされない場合は、単語「SKIP」のみを出力してください。

[出力形式（ブラフ実行時）]
`{{
  "action": "bet",
  "amount": <ポットの50%の金額>,
  "reasoning": "ヘッズアップでの強いドローによるセミブラフベット。"
}}`''',
    output_key="bluff_decision",
)


# 6) Final Action Decider Agent
flop_action_agent = Agent(
    name="poker_flop_action_decider",
    model=AGENT_MODEL,
    description="すべての分析結果を統合し、最終的なアクションを決定します。",
    instruction=f'''{SKIP_PREFLOP_INSTRUCTION}

あなたはポーカーの意思決定を行うエキスパートです。すべての分析結果を基に、以下のルールに従ってアクションを決定してください。

[分析結果]
- 手の強さ: {{hand_evaluation}}
- ベット状況: {{bet_situation_analysis}}
- セミブラフ判断: {{bluff_decision}}

[ルール]
- **最優先ルール: セミブラフ**
  - もし `bluff_decision` が "SKIP" ではない具体的なアクションを提案している場合、他のルールをすべて無視し、そのアクションに厳密に従ってください。

- **通常ルール（`bluff_decision` が "SKIP" の場合）**
  - `hand_evaluation` の `strength_score` と `bet_situation_analysis` の `threat_level` を使って、以下の価値に基づいた判断（バリューベット／フォールド）を行ってください。

  - **ルール1: モンスターハンド (スコア >= 90)**: フォールドしない。脅威度に応じてコール／レイズ／ベット。
  - **ルール2: 非常に強い手 (スコア 80〜89)**: 脅威度がEXTREMEならフォールド。それ以外はコール／レイズ／ベット。
  - **ルール3: 良い手 (スコア 65〜79)**: 脅威度がHIGH以上ならフォールド。それ以外はコール／チェック。
  - **ルール4: 中間的な手 (スコア 50〜64)**: 脅威度がMEDIUM以上ならフォールド。LOWならコール、NONEならチェック。
  - **ルール5: ウィークハンド (スコア < 50)**: ベットがあれば即フォールド。なければチェック。

[出力]
- 以下のJSON形式で、決定したアクションと簡単な理由を出力してください。
`{{
  "action": "fold|check|call|raise|bet|all_in",
  "amount": <数値>,
  "reasoning": "戦略的理由の要約（日本語）"
}}`''',
    output_key="flop_strategy_analysis",
)

# Main Sequential Agent for Flop Strategy
flop_strategy_agent = SequentialAgent(
    name="poker_flop_sequential_strategy",
    sub_agents=[
        hand_evaluator_agent,
        draw_analyzer_agent,
        player_count_analyzer_agent,
        bet_analyzer_agent,
        semi_bluff_agent,
        flop_action_agent,
    ],
)

__all__ = ["flop_strategy_agent"]
