from .card import parse_cards
from .poker.evaluator import HandEvaluator, HandRank
from .poker.game_models import Card, Suit

PROBABILITY = [[0.0, 2.2, 4.3, 6.5, 8.7, 10.9, 13.0, 15.2, 17.4, 19.6, 21.7,
                23.9, 26.1, 28.3, 30.4, 32.6, 34.8, 37.0, 39.1, 41.3, 43.5],
               [0.0, 4.3, 8.4, 12.5, 16.5, 20.3, 24.1, 27.8, 31.5, 35.0, 38.4,
                41.7, 45.0, 48.1, 51.2, 54.1, 57.0, 59.8, 62.4, 65.0, 67.5]]


def get_outs_info(hands: list[str], community: list[str]) -> dict:
    """
    現在の役よりも強い役について、outsの情報を求める。
    現在の役よりも弱い役についての情報は出力されない。
    Args:
        hands (list[str]): 自身のカード (2枚)
        community (list[str]): 場のカード (3, 4枚)
    Return:
        現在よりも強い役にそれぞれ対するoutsの情報についての辞書
        以下の形式で出力される。
        {
        役の名前: {
            "cards": [outsとなるカードのリスト],
            "outs": outs数,
            "probability": 残りのドローでそれを引く確率 (%表記),
            }
        }
    """
    calc = CalcOuts(hands, community)
    outs_by_rank = calc.get_outs_by_rank()

    result = dict()
    for rank, outs in outs_by_rank.items():
        result[rank.name] = {
            "card": [str(card) for card in outs],
            "outs": len(outs),
            "probability": PROBABILITY[6-len(calc.all_cards)][len(outs)]
        }

    return result


class CalcOuts:
    def __init__(self, hands: list[str], community: list[str]):
        self.hands = parse_cards(hands)
        self.community = parse_cards(community)

        self.count()
        self.result = HandEvaluator.evaluate_hand(self.hands, self.community)

    @property
    def all_cards(self) -> list[Card]:
        return self.hands + self.community

    def count(self):
        self.rank_counts = {rank: 0 for rank in Card.RANK_NAMES}
        for card in self.all_cards:
            self.rank_counts[card.rank] += 1

        self.ranks_by_count = {count: [] for count in range(5)}
        for rank, count in self.rank_counts.items():
            self.ranks_by_count[count].append(rank)

        self.suit_counts = {suit: 0 for suit in Suit}
        for card in self.all_cards:
            self.suit_counts[card.suit] += 1

    def get_outs_by_rank(self):
        outs_by_rank: dict[HandRank, set[Card]] = dict()
        for hand_rank in reversed(HandRank):
            if hand_rank.value <= self.result.rank.value:
                continue
            match hand_rank:
                case HandRank.ROYAL_FLUSH:
                    outs_by_rank[hand_rank] = self.get_royal_flush_outs()
                case HandRank.STRAIGHT_FLUSH:
                    outs_by_rank[hand_rank] = self.get_straight_flush_outs()
                case HandRank.FOUR_OF_A_KIND:
                    outs_by_rank[hand_rank] = self.get_four_of_a_kind_outs()
                case HandRank.FULL_HOUSE:
                    outs_by_rank[hand_rank] = self.get_full_house_outs()
                case HandRank.FLUSH:
                    outs_by_rank[hand_rank] = self.get_flush_outs()
                case HandRank.STRAIGHT:
                    outs_by_rank[hand_rank] = self.get_straight_outs()
                case HandRank.THREE_OF_A_KIND:
                    outs_by_rank[hand_rank] = self.get_three_of_a_kind_outs()
                case HandRank.TWO_PAIR:
                    outs_by_rank[hand_rank] = self.get_two_pair_outs()
                case HandRank.ONE_PAIR:
                    outs_by_rank[hand_rank] = self.get_one_pair_outs()

            for rank, outs in outs_by_rank.items():
                if hand_rank.value <= rank.value:
                    continue
                outs.difference_update(outs_by_rank[hand_rank])

        return outs_by_rank

    def get_royal_flush_outs(self) -> set[Card]:
        for suit in Suit:
            needed_cards = {Card(rank, suit) for rank in range(10, 15)}
            needed_cards.difference_update(self.all_cards)
            if len(needed_cards) <= 1:
                return needed_cards
        return set()

    def get_straight_flush_outs(self) -> set[Card]:
        outs = set()
        for suit in Suit:
            for start in range(2, 10):
                needed_cards = {Card(rank, suit)
                                for rank in range(start, start + 5)}
                needed_cards.difference_update(self.all_cards)
                if len(needed_cards) <= 1:
                    outs.update(needed_cards)

        return outs

    def get_four_of_a_kind_outs(self) -> set[Card]:
        outs = set()
        for rank in self.ranks_by_count[3]:
            outs.update({Card(rank, suit) for suit in Suit})

        outs.difference_update(self.all_cards)
        return outs

    def get_full_house_outs(self) -> set[Card]:
        outs = set()
        if self.ranks_by_count[3]:  # 3枚組があれば1枚の残りがoutsになる
            for rank in self.ranks_by_count[1]:
                outs.update({Card(rank, suit) for suit in Suit})
        elif len(self.ranks_by_count[2]) >= 2:  # 2枚組が2つ以上2枚組の残りがoutsになる
            for rank in self.ranks_by_count[2]:
                outs.update({Card(rank, suit) for suit in Suit})

        outs.difference_update(self.all_cards)
        return outs

    def get_flush_outs(self) -> set[Card]:
        outs = set()
        for suit, count in self.suit_counts.items():
            if count >= 4:
                outs.update({Card(rank, suit) for rank in range(2, 15)})
                break

        outs.difference_update(self.all_cards)
        return outs

    def get_straight_outs(self) -> set[Card]:
        ranks = {card.rank for card in self.all_cards}
        outs = set()
        for start in range(2, 11):
            needed_ranks = set(range(start, start + 5))
            needed_ranks.difference_update(ranks)

            if len(needed_ranks) <= 1:
                rank = needed_ranks.pop()
                outs.update({Card(rank, suit) for suit in Suit})

        return outs

    def get_three_of_a_kind_outs(self) -> set[Card]:
        outs = set()
        for rank in self.ranks_by_count[2]:
            outs.update({Card(rank, suit) for suit in Suit})

        outs.difference_update(self.all_cards)
        return outs

    def get_two_pair_outs(self) -> set[Card]:
        outs = set()
        if not self.ranks_by_count[2]:
            return outs

        for rank in self.ranks_by_count[1]:
            outs.update({Card(rank, suit) for suit in Suit})

        outs.difference_update(self.all_cards)
        return outs

    def get_one_pair_outs(self) -> set[Card]:
        outs = set()
        for rank in self.ranks_by_count[1]:
            outs.update({Card(rank, suit) for suit in Suit})

        outs.difference_update(self.all_cards)
        return outs
