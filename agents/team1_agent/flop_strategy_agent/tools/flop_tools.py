# agents/team1_agent/flop_strategy_agent/tools/flop_tools.py

from . import analysis, hand, util

# 定数
EQUITY_SAMPLE_COUNT = 1000  # 勝率計算のシミュレーション回数

# カード形式変換用の辞書
SUIT_MAP = {'♥': 'h', '♦': 'd', '♠': 's', '♣': 'c'}
RANK_MAP = {'10': 'T'}

def _convert_cards(cards_llm_format: list[str]) -> list[str]:
    """ゲームステートのカード形式（例: ["A♥"]）をpokerkit形式（例: ["Ah"]）に変換する。"""
    pokerkit_cards = []
    for card_str in cards_llm_format:
        rank = card_str[:-1]
        suit = card_str[-1]
        rank_pk = RANK_MAP.get(rank, rank)
        suit_pk = SUIT_MAP.get(suit)
        if suit_pk:
            pokerkit_cards.append(f"{rank_pk}{suit_pk}")
    return pokerkit_cards

def _get_opponent_ranges(num_opponents: int):
    """相手のハンドレンジをランダム（Any Two）として生成する。"""
    any_two_range_str = 'AA-22s,KQs-K2s,QJs-Q2s,JTs-J2s,T9s-T2s,98s-92s,87s-82s,76s-72s,65s-62s,54s-52s,43s-42s,32s,AKo-A2o,KQo-K2o,QJo-Q2o,JTo-J2o,T9o-T2o,98o-92o,87o-82o,76o-72o'
    any_two_range = analysis.parse_range(any_two_range_str)
    return [any_two_range] * num_opponents

def evaluate_hand(hole_cards: list[str], board_cards: list[str]) -> str:
    """自分の手札と場のカードから、現在のポーカーの役を判定します。"""
    try:
        my_cards_pk = _convert_cards(hole_cards)
        board_cards_pk = _convert_cards(board_cards)
        
        if not my_cards_pk or len(board_cards_pk) < 3:
            return "情報不足のため役を判定できません。"

        current_hand = hand.StandardHighHand.from_game(my_cards_pk, board_cards_pk)
        return f"現在の役は「{current_hand.entry.label.value}」です。"
    except Exception as e:
        return f"役の判定中にエラーが発生しました: {e}"

def calculate_equity(hole_cards: list[str], board_cards: list[str], num_opponents: int) -> str:
    """現在の状況での勝率（エクイティ）を計算します。相手はランダムなハンドを持っていると仮定します。"""
    try:
        my_cards_pk = _convert_cards(hole_cards)
        board_cards_pk = _convert_cards(board_cards)

        if not my_cards_pk or not isinstance(num_opponents, int) or num_opponents <= 0:
            return "情報不足のため勝率を計算できません。"

        hole_ranges = [analysis.parse_range(''.join(my_cards_pk))] + _get_opponent_ranges(num_opponents)
        
        known_cards = set(util.Card.parse(''.join(my_cards_pk + board_cards_pk)))
        deck = [card for card in util.Deck.STANDARD if card not in known_cards]

        equities = analysis.calculate_equities(
            hole_ranges=hole_ranges,
            board_cards=board_cards_pk,
            hole_dealing_count=2,
            board_dealing_count=5,
            deck=deck,
            hand_types=[hand.StandardHighHand],
            sample_count=EQUITY_SAMPLE_COUNT,
        )
        my_equity = equities[0]
        return f"アクティブな相手が{num_opponents}人いる状況での勝率は、約{my_equity:.1%}です。"
    except Exception as e:
        return f"勝率の計算中にエラーが発生しました: {e}"
