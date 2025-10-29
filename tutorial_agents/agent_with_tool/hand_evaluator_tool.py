from typing import List, Optional, Dict, Any
from enum import Enum
from collections import Counter
from itertools import combinations


class Suit(Enum):
    SPADES = "spades"
    HEARTS = "hearts"
    DIAMONDS = "diamonds"
    CLUBS = "clubs"


class Card:
    RANK_NAMES = {
        2: "2",
        3: "3",
        4: "4",
        5: "5",
        6: "6",
        7: "7",
        8: "8",
        9: "9",
        10: "10",
        11: "J",
        12: "Q",
        13: "K",
        14: "A",
    }

    SUIT_SYMBOLS = {
        Suit.HEARTS: "♥",
        Suit.DIAMONDS: "♦",
        Suit.CLUBS: "♣",
        Suit.SPADES: "♠",
    }

    def __init__(self, rank: int, suit: Suit):
        if rank < 2 or rank > 14:
            raise ValueError("Rank must be between 2 and 14")
        self.rank = rank
        self.suit = suit

    def __str__(self) -> str:
        return f"{self.RANK_NAMES[self.rank]}{self.SUIT_SYMBOLS[self.suit]}"

    def __repr__(self) -> str:
        return f"Card({self.RANK_NAMES[self.rank]}, {self.suit.value})"

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, Card)
            and self.rank == other.rank
            and self.suit == other.suit
        )

    def __hash__(self) -> int:
        return hash((self.rank, self.suit))


class HandRank(Enum):
    ROYAL_FLUSH = 10
    STRAIGHT_FLUSH = 9
    FOUR_OF_A_KIND = 8
    FULL_HOUSE = 7
    FLUSH = 6
    STRAIGHT = 5
    THREE_OF_A_KIND = 4
    TWO_PAIR = 3
    ONE_PAIR = 2
    HIGH_CARD = 1


class HandResult:
    def __init__(
        self,
        rank: HandRank,
        cards: List[Card],
        kickers: List[int] = None,
        description: str = "",
    ):
        self.rank = rank
        self.cards = cards
        self.kickers = kickers or []
        self.description = description

    def __lt__(self, other):
        if self.rank.value != other.rank.value:
            return self.rank.value < other.rank.value
        for a, b in zip(self.kickers, other.kickers):
            if a != b:
                return a < b
        return False

    def __eq__(self, other):
        return self.rank == other.rank and self.kickers == other.kickers


class SimpleHandEvaluator:
    @staticmethod
    def evaluate_hand(
        hole_cards: List[Card], community_cards: List[Card]
    ) -> HandResult:
        all_cards = hole_cards + community_cards
        if len(all_cards) < 5:
            sorted_cards = sorted(all_cards, key=lambda c: c.rank, reverse=True)
            return HandResult(
                HandRank.HIGH_CARD,
                sorted_cards,
                [c.rank for c in sorted_cards],
                f"High Card: {sorted_cards[0]}",
            )

        best: Optional[HandResult] = None
        for five in combinations(all_cards, 5):
            hr = SimpleHandEvaluator._eval_five(list(five))
            if (
                best is None
                or hr.rank.value > best.rank.value
                or (hr.rank == best.rank and not hr < best)
            ):
                best = hr
        return best  # type: ignore

    @staticmethod
    def _eval_five(cards: List[Card]) -> HandResult:
        if len(cards) != 5:
            raise ValueError("Must evaluate exactly 5 cards")
        sorted_cards = sorted(cards, key=lambda c: c.rank, reverse=True)
        ranks = [c.rank for c in sorted_cards]
        suits = [c.suit for c in sorted_cards]

        rank_counts = Counter(ranks)
        counts = sorted(rank_counts.values(), reverse=True)

        is_flush = len(set(suits)) == 1
        is_straight = SimpleHandEvaluator._is_straight(ranks)

        if (
            is_flush
            and is_straight
            and ranks[0] == 14
            and set(ranks) == {10, 11, 12, 13, 14}
        ):
            return HandResult(HandRank.ROYAL_FLUSH, sorted_cards, [14], "Royal Flush")

        if is_flush and is_straight:
            high = ranks[0] if ranks != [14, 5, 4, 3, 2] else 5
            return HandResult(
                HandRank.STRAIGHT_FLUSH,
                sorted_cards,
                [high],
                f"Straight Flush: {sorted_cards[0]}-high",
            )

        if counts == [4, 1]:
            four_rank = [r for r, c in rank_counts.items() if c == 4][0]
            kicker = [r for r, c in rank_counts.items() if c == 1][0]
            return HandResult(
                HandRank.FOUR_OF_A_KIND,
                sorted_cards,
                [four_rank, kicker],
                f"Four of a Kind: {Card.RANK_NAMES[four_rank]}s",
            )

        if counts == [3, 2]:
            three = [r for r, c in rank_counts.items() if c == 3][0]
            pair = [r for r, c in rank_counts.items() if c == 2][0]
            return HandResult(
                HandRank.FULL_HOUSE,
                sorted_cards,
                [three, pair],
                f"Full House: {Card.RANK_NAMES[three]}s over {Card.RANK_NAMES[pair]}s",
            )

        if is_flush:
            return HandResult(
                HandRank.FLUSH, sorted_cards, ranks, f"Flush: {sorted_cards[0]}-high"
            )

        if is_straight:
            high = ranks[0] if ranks != [14, 5, 4, 3, 2] else 5
            return HandResult(
                HandRank.STRAIGHT,
                sorted_cards,
                [high],
                f"Straight: {Card.RANK_NAMES[high]}-high",
            )

        if counts == [3, 1, 1]:
            three = [r for r, c in rank_counts.items() if c == 3][0]
            kickers = sorted(
                [r for r, c in rank_counts.items() if c == 1], reverse=True
            )
            return HandResult(
                HandRank.THREE_OF_A_KIND,
                sorted_cards,
                [three] + kickers,
                f"Three of a Kind: {Card.RANK_NAMES[three]}s",
            )

        if counts == [2, 2, 1]:
            pairs = sorted([r for r, c in rank_counts.items() if c == 2], reverse=True)
            kicker = [r for r, c in rank_counts.items() if c == 1][0]
            return HandResult(
                HandRank.TWO_PAIR,
                sorted_cards,
                pairs + [kicker],
                f"Two Pair: {Card.RANK_NAMES[pairs[0]]}s and {Card.RANK_NAMES[pairs[1]]}s",
            )

        if counts == [2, 1, 1, 1]:
            pair = [r for r, c in rank_counts.items() if c == 2][0]
            kickers = sorted(
                [r for r, c in rank_counts.items() if c == 1], reverse=True
            )
            return HandResult(
                HandRank.ONE_PAIR,
                sorted_cards,
                [pair] + kickers,
                f"One Pair: {Card.RANK_NAMES[pair]}s",
            )

        return HandResult(
            HandRank.HIGH_CARD, sorted_cards, ranks, f"High Card: {sorted_cards[0]}"
        )

    @staticmethod
    def _is_straight(ranks: List[int]) -> bool:
        unique = sorted(set(ranks), reverse=True)
        if len(unique) != 5:
            return False
        if unique[0] - unique[4] == 4:
            return True
        if unique == [14, 5, 4, 3, 2]:
            return True
        return False

    @staticmethod
    def get_hand_strength_description(hand: HandResult) -> str:
        mapping = {
            HandRank.ROYAL_FLUSH: "ロイヤルフラッシュ",
            HandRank.STRAIGHT_FLUSH: "ストレートフラッシュ",
            HandRank.FOUR_OF_A_KIND: "フォーカード",
            HandRank.FULL_HOUSE: "フルハウス",
            HandRank.FLUSH: "フラッシュ",
            HandRank.STRAIGHT: "ストレート",
            HandRank.THREE_OF_A_KIND: "スリーカード",
            HandRank.TWO_PAIR: "ツーペア",
            HandRank.ONE_PAIR: "ワンペア",
            HandRank.HIGH_CARD: "ハイカード",
        }
        return mapping.get(hand.rank, "不明なハンド")


def _parse_card(card_text: str) -> Card:
    """
    Parse a single card string into a Card object.

    Supported examples:
    - "A♠", "K♥", "10♦", "7♣"
    - "As", "Kh", "Td", "7c"

    Rank symbols: 2-10, J, Q, K, A
    Suit symbols: ♠/s, ♥/h, ♦/d, ♣/c
    """

    if not isinstance(card_text, str):
        raise ValueError("Card must be a string")

    text = card_text.strip().replace(" ", "")

    # Try to detect unicode suit first
    suit_symbol_map = {
        "♠": Suit.SPADES,
        "♤": Suit.SPADES,
        "♥": Suit.HEARTS,
        "♡": Suit.HEARTS,
        "♦": Suit.DIAMONDS,
        "♢": Suit.DIAMONDS,
        "♣": Suit.CLUBS,
        "♧": Suit.CLUBS,
    }

    suit: Optional[Suit] = None
    rank_str: Optional[str] = None

    # Unicode suit present
    for sym, suit_enum in suit_symbol_map.items():
        if sym in text:
            suit = suit_enum
            rank_str = text.replace(sym, "")
            break

    # If no unicode suit, expect trailing ascii suit char
    if suit is None:
        if not text:
            raise ValueError(f"Invalid card: '{card_text}'")
        ascii_suit = text[-1].lower()
        suit_ascii_map = {
            "s": Suit.SPADES,
            "h": Suit.HEARTS,
            "d": Suit.DIAMONDS,
            "c": Suit.CLUBS,
        }
        suit = suit_ascii_map.get(ascii_suit)
        if suit is None:
            raise ValueError(f"Invalid suit in card: '{card_text}'")
        rank_str = text[:-1]

    if not rank_str:
        raise ValueError(f"Invalid rank in card: '{card_text}'")

    rank_str = rank_str.upper()
    rank_map: Dict[str, int] = {
        "2": 2,
        "3": 3,
        "4": 4,
        "5": 5,
        "6": 6,
        "7": 7,
        "8": 8,
        "9": 9,
        "10": 10,
        "T": 10,
        "J": 11,
        "Q": 12,
        "K": 13,
        "A": 14,
    }

    # Some users might write leading zero like "09"; normalize it
    if rank_str.startswith("0"):
        rank_str = rank_str.lstrip("0") or "0"

    rank_val = rank_map.get(rank_str)
    if rank_val is None:
        raise ValueError(f"Invalid rank in card: '{card_text}'")

    return Card(rank=rank_val, suit=suit)


def _parse_cards(cards: Optional[List[str]]) -> List[Card]:
    if not cards:
        return []
    parsed: List[Card] = []
    for raw in cards:
        parsed.append(_parse_card(raw))
    # basic duplication check
    if len(set(parsed)) != len(parsed):
        raise ValueError("Duplicate cards detected")
    return parsed


def _score_from_rank_value(rank_value: int) -> float:
    """
    Simple 0.0-1.0 score based solely on category rank.
    HIGH_CARD=1 ... ROYAL_FLUSH=10 => normalize to [0,1].
    """
    # Clamp just in case
    rank_value = max(1, min(rank_value, 10))
    return (rank_value - 1) / 9.0


def hand_evaluator_tool(
    your_cards: List[str],
    community_cards: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    シンプルなハンド強さ評価ツール（ADK FunctionTool）

    Args:
        your_cards: あなたのホールカード（2枚）例: ["A♥", "K♠"] or ["As", "Kh"]
        community_cards: コミュニティカード（0-5枚）例: ["Q♥", "J♦", "10♣"]

    Returns:
        dict: {"rank", "rank_value", "strength_score", "description",
               "best_five_cards", "kickers", "normalized_input"}
    """

    hole = _parse_cards(your_cards)
    board = _parse_cards(community_cards)

    if len(hole) != 2:
        raise ValueError("your_cards must contain exactly 2 cards")

    result = SimpleHandEvaluator.evaluate_hand(hole, board)

    score = _score_from_rank_value(result.rank.value)

    return {
        "rank": result.rank.name,
        "rank_value": result.rank.value,
        "strength_score": round(score, 4),
        "description": SimpleHandEvaluator.get_hand_strength_description(result),
        "best_five_cards": [str(c) for c in result.cards],
        "kickers": result.kickers,
        "normalized_input": {
            "your_cards": [str(c) for c in hole],
            "community_cards": [str(c) for c in board],
        },
    }
