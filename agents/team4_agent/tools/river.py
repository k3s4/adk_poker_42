from itertools import combinations

# 役の強さを数値化（大きいほど強い）
HAND_RANKS = {
    "royal_flush": 10,
    "straight_flush": 9,
    "four_of_a_kind": 8,
    "full_house": 7,
    "flush": 6,
    "straight": 5,
    "three_of_a_kind": 4,
    "two_pair": 3,
    "one_pair": 2,
    "high_card": 1,
}


def card_to_tuple(card: str):
    # 例: "A♥" → ("A", "♥")
    return (card[:-1], card[-1])


def rank_to_value(rank: str):
    order = {
        "A": 14,
        "K": 13,
        "Q": 12,
        "J": 11,
        "10": 10,
        "9": 9,
        "8": 8,
        "7": 7,
        "6": 6,
        "5": 5,
        "4": 4,
        "3": 3,
        "2": 2,
    }
    return order[rank]


def evaluate_hand(cards):
    # cards: [(rank, suit), ...] 5枚
    ranks = [rank_to_value(r) for r, s in cards]
    suits = [s for r, s in cards]
    rank_counts = {r: ranks.count(r) for r in set(ranks)}
    is_flush = len(set(suits)) == 1
    sorted_ranks = sorted(ranks, reverse=True)
    is_straight = False
    # ストレート判定（A-2-3-4-5も考慮）
    if len(set(ranks)) == 5:
        if max(ranks) - min(ranks) == 4:
            is_straight = True
        elif set(ranks) == {14, 2, 3, 4, 5}:
            is_straight = True
            sorted_ranks = [5, 4, 3, 2, 1]
    # ロイヤルフラッシュ
    if is_flush and set(sorted_ranks) == {14, 13, 12, 11, 10}:
        return (HAND_RANKS["royal_flush"], sorted_ranks)
    # ストレートフラッシュ
    if is_flush and is_straight:
        return (HAND_RANKS["straight_flush"], sorted_ranks)
    # フォーカード
    if 4 in rank_counts.values():
        return (HAND_RANKS["four_of_a_kind"], sorted_ranks)
    # フルハウス
    if 3 in rank_counts.values() and 2 in rank_counts.values():
        return (HAND_RANKS["full_house"], sorted_ranks)
    # フラッシュ
    if is_flush:
        return (HAND_RANKS["flush"], sorted_ranks)
    # ストレート
    if is_straight:
        return (HAND_RANKS["straight"], sorted_ranks)
    # スリーカード
    if 3 in rank_counts.values():
        return (HAND_RANKS["three_of_a_kind"], sorted_ranks)
    # ツーペア
    if list(rank_counts.values()).count(2) == 2:
        return (HAND_RANKS["two_pair"], sorted_ranks)
    # ワンペア
    if 2 in rank_counts.values():
        return (HAND_RANKS["one_pair"], sorted_ranks)
    # ハイカード
    return (HAND_RANKS["high_card"], sorted_ranks)


def river(your_cards: list[str], community: list[str]) -> float:
    """
    リバーフェーズで自分の手札2枚とコミュニティカード5枚から作れる全ての5枚役を列挙し、
    その中で自分の役（最強の5枚役）が何割に位置するかをfloatで返す関数。

    役の強さはポーカーの一般的な役（ロイヤルフラッシュ＞ストレートフラッシュ＞フォーカード…）で判定。
    返り値は1.0に近いほど強い役、0.0に近いほど弱い役となる。

    Args:
        your_cards (list[str]): 自分の手札2枚（例: ["A♥", "K♠"]）
        community (list[str]): コミュニティカード5枚（例: ["Q♥", "J♦", "10♣", "9♠", "6♦"]）

    Returns:
        float: 7枚から作れる全ての5枚役の中で自分の役が上位何割に入るか（1.0=最強, 0.0=最弱）
    """
    # 1. 自分の役
    all_cards = your_cards + community
    card_tuples = [card_to_tuple(c) for c in all_cards]
    my_best = max([evaluate_hand(hand) for hand in combinations(card_tuples, 5)])

    # 2. 残りデッキから相手の手札候補を生成
    all_ranks = ["A", "K", "Q", "J", "10", "9", "8", "7", "6", "5", "4", "3", "2"]
    all_suits = ["♥", "♦", "♠", "♣"]
    # すべてのカード
    all_deck = set(f"{r}{s}" for r in all_ranks for s in all_suits)
    used = set(your_cards + community)
    remain = list(all_deck - used)

    # 相手の手札の全組み合わせ
    opp_hands = [
        (remain[i], remain[j])
        for i in range(len(remain))
        for j in range(len(remain))
        if i != j
    ]

    # 3. 自分より強い役の数をカウント
    stronger = 0
    for opp in opp_hands:
        opp_all = list(opp) + community
        opp_tuples = [card_to_tuple(c) for c in opp_all]
        opp_best = max([evaluate_hand(hand) for hand in combinations(opp_tuples, 5)])
        if opp_best > my_best:
            stronger += 1

    percentile = 1 - stronger / len(opp_hands)
    return percentile


"""
riverのinput例
{
  "your_id": 0,
  "phase": "river",
  "your_cards": ["A♥", "K♠"],
  "community": ["Q♦", "J♦", "10♦", "9♠", "6♦"],
  "your_chips": 950,
  "your_bet_this_round": 0,
  "your_total_bet_this_hand": 50,
  "pot": 200,
  "to_call": 0,
  "dealer_button": 3,
  "current_turn": 0,
  "players": [
    {"id": 1, "chips": 950, "bet": 0, "status": "active"},
    {"id": 2, "chips": 950, "bet": 0, "status": "active"},
    {"id": 3, "chips": 950, "bet": 0, "status": "active"}
  ],
  "actions": ["check", "bet (min 20)", "all-in (950)"],
  "history": [
    "Flop: Player 3 bet 20, all players called",
    "Turn dealt: 9♠"
  ]
}
"""
if __name__ == "__main__":
    # テストケース例
    test_cases = [
        # 強い手
        {
            "your_cards": ["A♥", "K♠"],
            "community": ["Q♦", "J♦", "10♦", "9♠", "6♦"],
        },
        # フラッシュ
        {
            "your_cards": ["2♣", "3♣"],
            "community": ["4♣", "5♣", "6♣", "7♣", "8♣"],
        },
        # フォーカード
        {
            "your_cards": ["A♠", "A♦"],
            "community": ["A♣", "A♥", "K♠", "K♦", "2♠"],
        },
        # 激弱な手（ハイカードのみ）
        {
            "your_cards": ["2♣", "7♦"],
            "community": ["9♠", "J♥", "4♦", "8♣", "Q♠"],
        },
    ]
    for i, case in enumerate(test_cases):
        print(f"Test case {i+1}:")
        print(f"  your_cards: {case['your_cards']}")
        print(f"  community: {case['community']}")
        result = river(case["your_cards"], case["community"])
        print(f"  percentile: {result}")
        print()
