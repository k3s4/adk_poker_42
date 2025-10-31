"""
Preflop Strategy Agent - プリフロップの戦略分析に特化したエージェント
"""

from google.adk.agents import Agent
from .tools import classify_hand, analyze_preflop_position_value, evaluate_preflop_action
from google.adk.models.lite_llm import LiteLlm

MODEL_GPT_4O_MINI = LiteLlm(model="openai/gpt-4o-mini")
AGENT_MODEL = MODEL_GPT_4O_MINI

# プリフロップ専用 戦略分析Agent
preflop_strategy_agent = Agent(
    name="poker_preflop_strategy_analyzer",
    model=AGENT_MODEL,
    description="プリフロップの戦略分析に特化したエージェント",
    instruction="""あなたはテキサスホールデムのプリフロップ戦略に特化したアナリストです。

前提:
- 現在フェーズ: {current_phase}
もし {current_phase} が "preflop" 以外であれば、分析は行わずに次の1語のみ出力: SKIP

タスク(プリフロップの場合のみ実行):
- classify_handツール: ハンドをカテゴリーで分類（プレミアム/ストロング/グッド/マージナル/ウィーク）
- analyze_preflop_position_valueツール: ポジションとハンド強度から調整値を算出
- evaluate_preflop_actionツール: 現局面での最適アクションを提案
- ハンドレンジ、ポジション、スタック深さ、ブラインド状況、先行アクションを考慮
- リンプ/レイズ/3bet/フォールド/オールインの是非を評価
- 推奨アクション（fold/check/call/raise/all_in）と合計額、および根拠を説明

出力: プリフロップの詳細な戦略分析テキスト（もしくは SKIP）。""",
    tools=[
        classify_hand,
        analyze_preflop_position_value,
        evaluate_preflop_action,
    ],
    output_key="preflop_strategy_analysis",
)

__all__ = ["preflop_strategy_agent"]
