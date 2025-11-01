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

# JSON選択Agent - フェーズに応じて適切な分析結果を選択
json_selector_agent = Agent(
    name="poker_json_selector",
    model=AGENT_MODEL,
    description="フェーズに応じて適切な分析結果を選択してそのまま出力",
    instruction='''現在フェーズ: {current_phase}
プリフロップ分析: {preflop_strategy_analysis}
ポストフロップ分析: {flop_strategy_analysis}

タスク:
1) {current_phase} が "preflop" の場合は {preflop_strategy_analysis} を選択
2) それ以外の場合は {flop_strategy_analysis} を選択
3) 選択した結果が "SKIP" の場合は、もう一方を選択
4) 選択した結果からマークダウンコードブロック（```json や ```）を除去
5) 純粋なJSONのみを出力してください

出力形式: 以下の形式の純粋なJSONのみ（マークダウン記号なし）
{
  "action": "fold|check|call|raise|all_in",
  "amount": <数値>,
  "reasoning": "決定理由の説明"
}''',
)

# Sequential Agent - フェーズ抽出 → 両戦略エージェント → JSON選択
root_agent = SequentialAgent(
    name="poker_routed_workflow_agent",
    sub_agents=[
        phase_extractor_agent,
        preflop_strategy_agent,
        flop_strategy_agent,
        json_selector_agent,
    ],
)