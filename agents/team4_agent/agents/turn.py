from google.adk.agents import Agent

from ..tools.card import get_community_rank, get_hand_rank
from ..tools.outs import get_outs_info
from .model import AGENT_MODEL

turn_agent = Agent(
    name="turn_agent",
    model=AGENT_MODEL,
    description="テキサスホールデム・ポーカーの状況からouts数とそれを引く確率を求める",
    instruction="あなたはテキサスホールデム・ポーカーのエキスパートプレイヤーです。"
    "現在はturn phaseであり、手札2枚と場のカード4枚が確認できます。"
    "あなたのタスクは現在のゲーム状況からouts数と残り2枚のドローでそれを引く確率を正確に求めることです。"
    "outs数とは現在の状況で完成している役以上に強い役となるために必要なカードの種類数です。"
    "あなたには以下の情報が与えられます:"
    "- あなたの2枚の手札"
    "- 4枚の場のカード"
    "以下の手順に従って正確に出力してください。順序を遵守し、データを改変してはいけません。"
    "1. tool `get_hand_rank`を使用して現在の状況で完成している役の名前を出力してください。"
    "2. tool `get_community_rank`を使用して場のカードのみで完成している役を出力してください。該当する役がない場合はないことを明示してください。"
    "3. tool `get_outs_info`を使用してそれよりも強い役それぞれについて、次の要素を箇条書きとで出力してください。 "
    "対象の役の名前, outs数, ドローで引く確率, outsとなるカードのリスト(`rank suit'の表記方法)"
    "役の名前は強い順に以下に示します。"
    "1. ROYAL_FLUSH"
    "2. STRAIGHT_FLUSH"
    "3. FOUR_OF_A_KIND"
    "4. FULL_HOUSE"
    "5. FLUSH"
    "6. STRAIGHT"
    "7. THREE_OF_A_KIND"
    "8. TWO_PAIR"
    "9. ONE_PAIR"
    "10. HIGH_CARD",
    tools=[get_hand_rank, get_community_rank, get_outs_info],
)
