from google.adk.agents import Agent, SequentialAgent

# 戦略分析Agent - ポーカーの戦略的分析のみに集中
strategy_agent = Agent(
    name="poker_strategy_analyzer",
    model="gemini-2.5-flash-lite",
    description="テキサスホールデム・ポーカーの戦略分析を行うエキスパート",
    instruction="""あなたはテキサスホールデム・ポーカーの戦略分析エキスパートです。

与えられたゲーム状況を分析し、最善の意思決定とその理由を詳細に分析してください。

あなたには以下の情報が与えられます:
- あなたの手札（ホールカード）
- コミュニティカード（あれば）
- 選択可能なアクション
- ポットサイズやベット情報
- 対戦相手の情報

以下の点を考慮して詳細な戦略分析を行ってください:
- 手札の強さと将来性
- ポットオッズと期待値
- ポジションの有利・不利
- ブラフの機会と効果
- リスクとリターンの詳細分析

推奨するアクション（fold/check/call/raise/all_in）と具体的な金額、そしてその戦略的理由を詳しく説明してください。""",
    output_key="strategy_analysis",
)

# JSON整形Agent - 戦略分析をJSON形式に整形
json_formatter_agent = Agent(
    name="poker_json_formatter",
    model="gemini-2.5-flash-lite",
    description="ポーカーの戦略分析をJSON形式に整形するエキスパート",
    instruction="""あなたは戦略分析結果を指定されたJSON形式に正確に変換する専門家です。

戦略分析結果: {strategy_analysis}

上記の戦略分析を基に、必ず次のJSON形式で正確に回答してください:
{
  "action": "fold|check|call|raise|all_in",
  "amount": <数値>,
  "reasoning": "戦略分析から導出された決定と戦略的理由の詳細な説明"
}

ルール:
- "fold"と"check"の場合: amountは0にしてください
- "call"の場合: コールに必要な正確な金額を指定してください
- "raise"の場合: レイズ後の合計金額を指定してください
- "all_in"の場合: 残りチップ全額を指定してください
- reasoningには戦略分析の内容を要約して含めてください
- 必ずJSONの正確な構文で回答してください

戦略分析の内容を適切に解釈し、JSON形式で出力してください。""",
)

# Sequential Agent - 戦略分析してからJSON整形する
root_agent = SequentialAgent(
    name="poker_workflow_agent",
    sub_agents=[strategy_agent, json_formatter_agent],
)
