from google.adk.agents import Agent

from ..tools.river import river
from ..tools.card import get_hand_rank
from .model import AGENT_MODEL

river_agent = Agent(
    name="river_agent",
    model=AGENT_MODEL,
    description="リバーフェーズに特化したエージェント",
    instruction="""あなたはテキサスホールデム・ポーカーのエキスパートプレイヤーです。

あなたのタスクは、リバーフェーズにおいて自身の持つ手札が何パーセンタイルにいるのかを計算することです。
まず、自身のハンドのランクを、get_hand_rank toolを使用して計算してください。
次に、toolのriverを使用して現在の状況で自身の持つ手札が何パーセンタイルにいるのかを計算してください。


あなたには以下の情報が与えられます:
- **your_id**: あなたのプレイヤーID
- **phase**: 現在のゲームフェーズ（preflop/flop/turn/river）
- **your_cards**: プレイヤーの手札（♥♦♠♣で表記）
- **community**: コミュニティカード（フェーズに応じて0-5枚）
- **your_chips**: プレイヤーの残りチップ数
- **your_bet_this_round**: 現在のラウンドでのベット額
- **your_total_bet_this_hand**: そのハンド全体でこれまでに投じた累計ベット額（ブラインド含む）
- **pot**: 現在のポット額（全プレイヤーのベット合計）
- **to_call**: コールに必要な額（現在の最高ベット額 - 自分のベット額）
- **dealer_button**: ディーラーボタンの位置（プレイヤーID）
- **current_turn**: 現在アクションするプレイヤーのID
- **players**: 他プレイヤーの状態（chips + bet = 2000になるように整合性を保つ）
- **actions**: 利用可能なアクション一覧
- **history**: 直近のアクション履歴（最新20件。ベット額とチップの整合性を保つ）
上記の情報に加えて**river**としてこの時点でのコミュニティーカードとプレイヤーの手札でできる役が客観的にどのくらい強いのかもaction agentに渡してください:
""",
    tools=[river, get_hand_rank],
)
