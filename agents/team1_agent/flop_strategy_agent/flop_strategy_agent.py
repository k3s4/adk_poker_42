"""
Flop Strategy Agent - A multi-step sequential agent for post-flop decisions.
"""
from google.adk.agents import Agent, SequentialAgent
from google.adk.models.lite_llm import LiteLlm
# Import all tools
from .tools.hand_evaluator import evaluate_hand
from .tools.analyze_bet_situation import analyze_bet_situation
from .tools.draw_analyzer import analyze_draw_potential

# --- Agent Definition ---
MODEL_GPT_4O_MINI = LiteLlm(model="gpt-4o-mini")
AGENT_MODEL = MODEL_GPT_4O_MINI

# 1) Hand Evaluator Agent
hand_evaluator_agent = Agent(
    name="poker_hand_evaluator",
    model=AGENT_MODEL,
    description="手札の完成役の強さを0〜100のスコアで評価します。",
    instruction='''現在のフェーズ: {current_phase}
{current_phase} が "preflop" の場合は "SKIP" と出力してください。
それ以外の場合は以下のタスクを実行してください。

タスク: `evaluate_hand` ツールを使い、手札の強さを評価してください。''',
    tools=[evaluate_hand],
    output_key="hand_evaluation",
)

# 2) Draw Analyzer Agent
draw_analyzer_agent = Agent(
    name="poker_draw_analyzer",
    model=AGENT_MODEL,
    description="手札がドロー（ストレートやフラッシュの可能性）かどうかを分析します。",
    instruction='''現在のフェーズ: {current_phase}
{current_phase} が "preflop" の場合は "SKIP" と出力してください。
それ以外の場合は以下のタスクを実行してください。

タスク: `analyze_draw_potential` ツールを使い、ドローの可能性を分析してください。''',
    tools=[analyze_draw_potential],
    output_key="draw_analysis",
)

# 4) Bet Situation Analyzer Agent
bet_analyzer_agent = Agent(
    name="poker_bet_analyzer",
    model=AGENT_MODEL,
    description="相手のベットサイズをポットと比較して脅威度を分析します。",
    instruction='''現在のフェーズ: {current_phase}
{current_phase} が "preflop" の場合は "SKIP" と出力してください。
それ以外の場合は以下のタスクを実行してください。

タスク: `analyze_bet_situation` ツールを使い、ベットの脅威度を判定してください。''',
    tools=[analyze_bet_situation],
    output_key="bet_situation_analysis",
)

# 5) Semi-Bluff Agent
semi_bluff_agent = Agent(
    name="poker_semi_bluff_decider",
    model=AGENT_MODEL,
    description="特定の条件が揃った場合にセミブラフを行うかどうかを決定します。",
    instruction='''あなたはポーカーの専門家として、セミブラフを行うべきか否かを判断します。

現在のフェーズ: {current_phase}
もし {current_phase} が "preflop" の場合、タスクを実行せずに "SKIP" と出力してください。

[分析結果]
- ドロー状況: {draw_analysis}
- ベット状況: {bet_situation_analysis}

[セミブラフ実行の条件]
1. ドロー状況の分析結果に `FLUSH_DRAW` または `OESD` (オープンエンドストレートドロー) が含まれているか？
2. ベット状況の脅威度が `NONE` (自分からベットできる状況) か？
3. アクティブプレイヤーが2人の場合（ヘッズアップ）か？

[プレイヤー人数の判定方法]
以下のpython形式のロジックを使用してアクティブプレイヤー数を計算してください：
```python
# ゲーム状態からプレイヤーリストを取得
players = game_state.get('players', [])
# フォールドしていないプレイヤーをカウント
active_players = [p for p in players if p.get('state') != 'folded']
active_player_count = len(active_players)
```

[判断]
- もし上記の3条件がすべて満たされている場合、セミブラフを実行します。アクションは「raise」、金額はポットの50%とします。その判断をJSON形式で出力してください。
- 条件が満たされない場合は、単語「SKIP」のみを出力してください。

[出力形式（ブラフ実行時）]
`{
  "action": "raise",
  "amount": <ポットの50%の金額>,
  "reasoning": "ヘッズアップでの強いドローによるセミブラフレイズ。"
}`''',
    output_key="bluff_decision",
)

# 6) Final Action Decider Agent
flop_action_agent = Agent(
    name="poker_flop_action_decider",
    model=AGENT_MODEL,
    description="すべての分析結果を統合し、最終的なアクションを決定します。",
    instruction='''あなたはポーカーの意思決定を行うエキスパートです。すべての分析結果を基に、以下のルールに厳密に従ってアクションを決定してください。

[前提]
- 現在のフェーズ: {current_phase}
- {current_phase} が "preflop" の場合は "SKIP" と出力してください。
- それ以外の場合は以下の分析結果を使ってアクションを決定してください。

[分析結果]
- 手の強さの分析結果: {hand_evaluation}
- ドロー状況の分析結果: {draw_analysis}
- ベット状況の分析結果: {bet_situation_analysis}
- セミブラフ判断の結果: {bluff_decision}

[ルール]
- **最優先ルール1: プロアクティブ・セミブラフ**
  - もし `bluff_decision` が "SKIP" ではない具体的なアクションを提案している場合（＝自分からベットするセミブラフ）、他のルールをすべて無視し、そのアクションに厳密に従ってください。

- **最優先ルール2: ドローハンドでのコール**
  - もし相手からベットされており (`bet_situation_analysis` の `threat_level` が "NONE" ではない)、かつ自分に強いドロー (`draw_analysis` の `draws` リストに "OESD" または "FLUSH_DRAW" が含まれる) がある場合、以下の判断を行います。
    - `threat_level` が "LOW" なら「コール」します。
    - `threat_level` が "MEDIUM" 以上なら「フォールド」します（ドローでも厳格に）。
  - このルールが適用された場合、以下の通常ルールは無視します。

- **通常ルール（上記に当てはまらない場合）**
  - `hand_evaluation` の `strength_score` と `bet_situation_analysis` の `threat_level` を使って、完成役の価値に基づいた判断を行ってください。
  - **ルールA: モンスターハンド (スコア >= 90)**: 絶対フォールドしない。threat_level="NONE"なら「ポットサイズの75-100%でレイズ」、それ以外は「コール／オールイン」。
  - **ルールB: 非常に強い手 (スコア 70〜89)**: 脅威度がEXTREMEのみフォールド。threat_level="NONE"なら「ポットサイズの60-80%でレイズ」、LOWやMEDIUMでも「積極的レイズ」。
  - **ルールC: 良い手 (スコア 60〜69)**: 脅威度がHIGH以上ならフォールド。threat_level="NONE"なら「ポットサイズの40-60%でレイズ」、LOWなら「コール」、MEDIUMは「フォールド」。
  - **ルールD: 中間的な手 (スコア 45〜59)**: 脅威度がLOW以上でフォールド。NONEでのみチェック。
  - **ルールE: ウィークハンド (スコア < 30)**: どんなベットでも即フォールド。NONEでもチェック（ベットしない）。

[レイズサイズ計算ルール]
- ポットサイズの範囲でレイズする場合、その範囲内でランダムに選択してください
- 例: "ポットサイズの50-75%でレイズ" → ポットが120なら60-90の間でランダムに選択
- bet_situation_analysisからpot_sizeの値を取得して計算してください

[出力]
- 以下のJSON形式で、決定したアクションと簡単な理由を出力してください。
- マークダウンコードブロック（```）は絶対に使用しないでください。
- 純粋なJSONのみを出力してください。

{
  "action": "fold|check|call|raise|all_in",
  "amount": <数値>,
  "reasoning": "戦略的理由の要約（日本語）"
}
''',
    output_key="flop_strategy_analysis",
)

# Main Sequential Agent for Flop Strategy
flop_strategy_agent = SequentialAgent(
    name="poker_flop_sequential_strategy",
    sub_agents=[
        hand_evaluator_agent,
        draw_analyzer_agent,
        bet_analyzer_agent,
        semi_bluff_agent,
        flop_action_agent,
    ],
)

__all__ = ["flop_strategy_agent"]