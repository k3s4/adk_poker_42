from typing import Optional

from .poker.evaluator import HandEvaluator, HandRank
from .poker.game_models import Card

RANK = {name: rank for rank, name in Card.RANK_NAMES.items()}
SUIT = {symbol: suit for suit, symbol in Card.SUIT_SYMBOLS.items()}


def parse_card(card: str) -> Card:
    rank = RANK[card[:-1]]
    suit = SUIT[card[-1]]
    return Card(rank, suit)


def parse_cards(cards: list[str]) -> list[Card]:
    return [parse_card(card) for card in cards]


def get_hand_rank(hands: list[str], community: list[str]) -> str:
    """
    現在の状況で完成している手札の役を求める。
    Args:
        hands (list[str]): 自身のカード (2枚)
        community (list[str]): 場のカード (3, 4枚)
    Return:
        現在よりも強い役にそれぞれ対するouts数の辞書
        現在よりも弱い役については記述しない
    """
    print(hands, community)
    hands = parse_cards(hands)
    community = parse_cards(community)
    result = HandEvaluator.evaluate_hand(hands, community)
    return str(result)


def get_community_rank(community: list[str]) -> Optional[HandRank]:
    """
    場のカードのみで完成している役を求める。
    役がない場合Noneを返す。
    Args:
        community (list[str]): 場のカード (3, 4枚)
    Return:
        場のカードのみで完成している役の名前を出力
        該当する役がない場合Noneを返す
    """
    rank_counts = {rank: 0 for rank in Card.RANK_NAMES}
    for card in parse_cards(community):
        rank_counts[card.rank] += 1

    ranks_by_count = {count: [] for count in range(5)}
    for rank, count in rank_counts.items():
        ranks_by_count[count].append(rank)

    if ranks_by_count[4]:
        return HandRank.FOUR_OF_A_KIND.name
    elif ranks_by_count[3]:
        return HandRank.THREE_OF_A_KIND.name
    elif len(ranks_by_count[2]) >= 2:
        return HandRank.TWO_PAIR.name
    elif ranks_by_count[2]:
        return HandRank.ONE_PAIR.name
    return None
