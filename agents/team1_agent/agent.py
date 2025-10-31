from google.adk.agents import Agent, SequentialAgent
from .preflop import preflop_strategy_agent
from .flop_strategy_agent import flop_strategy_agent
from google.adk.models.lite_llm import LiteLlm

# Define model constant
MODEL_GPT_4O_MINI = LiteLlm(model="gpt-4o-mini")
AGENT_MODEL = MODEL_GPT_4O_MINI

# フェーズ抽出Agent - 入力ゲーム状態から現在のフェーズを抽出
phase_extractor_agent = Agent(
    name="poker_phase_extractor",
    model=AGENT_MODEL,
    description="ゲーム状態テキストから現在フェーズ(preflop/flop/turn/river)を短く抽出",
    instruction='''あなたは与えられたゲーム状態（JSON風テキスト）から現在のフェーズを1語で抽出します。

出力は次のいずれかの単語のみ: preflop / flop / turn / river
余計な説明・記号や引用符は付けず、該当語のみをそのまま出力してください。''',
    output_key="current_phase",
)

# JSON整形Agent - どちらの分析を使うかをフェーズで選択してJSON化
json_formatter_agent = Agent(
    name="poker_json_formatter",
    model="gemini-2.5-flash-lite",
    description="フェーズに応じて分析結果を選択し、規定JSONに整形",
    instruction='''あなたは戦略分析結果を指定JSON形式に正確に変換します。

現在フェーズ: {current_phase}
プリフロップ分析: {preflop_strategy_analysis}
ポストフロップ分析: {flop_strategy_analysis}

手順:
1) {current_phase} が preflop の場合は {preflop_strategy_analysis} を、
   それ以外の場合は {flop_strategy_analysis} を採用する。
2) 採用対象が "SKIP" のときは、もう一方を採用する。
3) 採用した分析内容を根拠に、以下のJSONを厳密に出力する:
{
  "action": "fold|check|call|raise|all_in",
  "amount": <数値>,
  "reasoning": "戦略的理由を詳細に説明（日本語）"
}

ルール:
- "fold"と"check"の場合: amountは0
- "call"の場合: コールに必要な正確な金額
- "raise"の場合: レイズ後の合計金額
- "all_in"の場合: 残りチップ全額
- 必ず有効なJSONのみを出力（前後に説明文を付けない）
''',
)

# Sequential Agent - フェーズ抽出 → 両戦略エージェント → JSON整形
root_agent = SequentialAgent(
    name="poker_routed_workflow_agent",
    sub_agents=[
        phase_extractor_agent,
        preflop_strategy_agent,
        flop_strategy_agent,
        json_formatter_agent,
    ],
)