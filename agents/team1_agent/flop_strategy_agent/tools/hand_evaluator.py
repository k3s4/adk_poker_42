"""
Hand Evaluator for Flop and later streets.
"""
from itertools import combinations
from collections import Counter
from typing import List, Dict, Any

# --- Constants ---
RANKS = '23456789TJQKA'
SUITS = 'shdc'

RANK_MAP = {rank: i for i, rank in enumerate(RANKS)}

HAND_RANKS = {
    "HIGH_CARD": 0,
    "ONE_PAIR": 1,
    "TWO_PAIR": 2,
    "THREE_OF_A_KIND": 3,
    "STRAIGHT": 4,
    "FLUSH": 5,
    "FULL_HOUSE": 6,
    "FOUR_OF_A_KIND": 7,
    "STRAIGHT_FLUSH": 8,
}

def _parse_card(card_str):
    """'K♣' -> ('K', 'c') or 'As' -> ('A', 's')"""
    # Unicode記号とアルファベット記号の変換マップ
    suit_map = {
        '♠': 's', '♥': 'h', '♦': 'd', '♣': 'c',
        's': 's', 'h': 'h', 'd': 'd', 'c': 'c'
    }
    
    rank_str = card_str[:-1]
    suit_str = card_str[-1]
    rank = rank_str.upper()
    
    # スート記号を正規化
    if suit_str in suit_map:
        suit = suit_map[suit_str]
    else:
        suit = suit_str.lower()
    
    if rank == '10':
        rank = 'T'
    if rank not in RANKS or suit not in SUITS:
        raise ValueError(f"Invalid card: {card_str} (rank='{rank}', suit='{suit}')")
    return rank, suit

def _get_hand_rank_and_kickers(hand):
    """
    Calculates the rank and kickers for a 5-card hand.
    Returns a tuple: (hand_rank, primary_score, secondary_score, kicker_scores)
    """
    if len(hand) != 5:
        raise ValueError("Hand must be 5 cards")

    ranks = sorted([RANK_MAP[r] for r, s in hand], reverse=True)
    suits = [s for r, s in hand]
    
    is_flush = len(set(suits)) == 1
    is_straight = all(ranks[i] - ranks[i+1] == 1 for i in range(4))
    if not is_straight and ranks == [RANK_MAP['A'], RANK_MAP['5'], RANK_MAP['4'], RANK_MAP['3'], RANK_MAP['2']]:
        is_straight = True
        ranks = [RANK_MAP['5'], RANK_MAP['4'], RANK_MAP['3'], RANK_MAP['2'], RANK_MAP['A']]

    if is_straight and is_flush:
        return (HAND_RANKS["STRAIGHT_FLUSH"], ranks[0], 0, [])

    rank_counts = Counter(ranks)
    sorted_ranks = sorted(rank_counts.keys(), key=lambda k: (rank_counts[k], k), reverse=True)
    counts = sorted(rank_counts.values(), reverse=True)

    if counts[0] == 4:
        quad_rank = sorted_ranks[0]
        kicker = sorted_ranks[1]
        return (HAND_RANKS["FOUR_OF_A_KIND"], quad_rank, kicker, [])

    if counts == [3, 2]:
        trips_rank = sorted_ranks[0]
        pair_rank = sorted_ranks[1]
        return (HAND_RANKS["FULL_HOUSE"], trips_rank, pair_rank, [])

    if is_flush:
        return (HAND_RANKS["FLUSH"], 0, 0, ranks)

    if is_straight:
        return (HAND_RANKS["STRAIGHT"], ranks[0], 0, [])

    if counts[0] == 3:
        trips_rank = sorted_ranks[0]
        kickers = sorted([r for r in sorted_ranks if r != trips_rank], reverse=True)
        return (HAND_RANKS["THREE_OF_A_KIND"], trips_rank, 0, kickers)

    if counts == [2, 2, 1]:
        p1 = sorted_ranks[0]
        p2 = sorted_ranks[1]
        kicker = sorted_ranks[2]
        return (HAND_RANKS["TWO_PAIR"], max(p1, p2), min(p1, p2), [kicker])

    if counts[0] == 2:
        pair_rank = sorted_ranks[0]
        kickers = sorted([r for r in sorted_ranks if r != pair_rank], reverse=True)
        return (HAND_RANKS["ONE_PAIR"], pair_rank, 0, kickers)

    return (HAND_RANKS["HIGH_CARD"], 0, 0, ranks)

def _calculate_strength_score(hand_name, hand_details, hole_cards, community_cards):
    """Calculates a strength score from 0-100 based on the hand rank and context."""
    base_score = 0
    # Details: (rank, primary, secondary, [kickers...])
    pair_rank = hand_details[1]
    kickers = hand_details[3]

    # --- Three of a Kind or better: 90+ --- 
    if hand_name == "STRAIGHT_FLUSH":
        # Special case for Royal Flush
        if pair_rank == RANK_MAP['A']:
            return 100
        base_score = 98 + (pair_rank / 12) * 1.99 # 98-99.99
    elif hand_name == "FOUR_OF_A_KIND":
        base_score = 96 + (pair_rank / 12) * 1.99 # 96-97.99
    elif hand_name == "FULL_HOUSE":
        base_score = 94 + (pair_rank / 12) * 1.99 # 94-95.99
    elif hand_name == "FLUSH":
        # Normalize based on all 5 card ranks
        flush_rank_score = sum(k / (13 * (i + 1)) for i, k in enumerate(kickers))
        base_score = 92 + flush_rank_score * 1.99 # 92-93.99
    elif hand_name == "STRAIGHT":
        base_score = 90 + (pair_rank / 12) * 1.99 # 90-91.99
    elif hand_name == "THREE_OF_A_KIND":
        base_score = 90

    # --- Two Pair: 80-89 --- 
    elif hand_name == "TWO_PAIR":
        top_pair = hand_details[1]
        bottom_pair = hand_details[2]
        kicker = kickers[0]
        # Weighted score for pairs and kicker
        base_score = 80 + (top_pair / 12 * 5) + (bottom_pair / 12 * 3) + (kicker / 12 * 1)

    # --- One Pair: 30-85 (highly contextual) --- 
    elif hand_name == "ONE_PAIR":
        # コミュニティカードの最高ランクを正しく計算（エラーハンドリング付き）
        try:
            # community_cardsは既にパース済みのタプルなので、直接rankを取得
            community_ranks = [RANK_MAP[c[0]] if isinstance(c, tuple) else RANK_MAP[_parse_card(c)[0]] for c in community_cards]
            max_community_rank = max(community_ranks)
        except (ValueError, KeyError):
            # パースエラーの場合はデフォルト値を使用
            max_community_rank = 0
        kicker_rank = kickers[0] if kickers else 0

        # Case 1: Overpair (pocket pair > top card on board)
        try:
            # hole_cardsがパース前の文字列の場合に対応
            hole_rank1 = _parse_card(hole_cards[0])[0] if isinstance(hole_cards[0], str) else hole_cards[0][0]
            hole_rank2 = _parse_card(hole_cards[1])[0] if isinstance(hole_cards[1], str) else hole_cards[1][0]
            is_pocket_pair = hole_rank1 == hole_rank2
        except (ValueError, IndexError):
            is_pocket_pair = False
        if is_pocket_pair and pair_rank > max_community_rank:
            base_score = 75 + (pair_rank / 12 * 10) # 75-85
        # Case 2: Top Pair (pair matches top card on board)
        elif pair_rank == max_community_rank:
            # 強いキッカー（A,K,Q）には大きなボーナス
            if kicker_rank >= RANK_MAP['Q']:
                base_score = 70 + (kicker_rank / 12 * 15) # 70-85
            else:
                base_score = 60 + (kicker_rank / 12 * 10) # 60-70
        # Case 3: Middle or Bottom Pair (大幅減点)
        else:
            base_score = 30 + (pair_rank / 12 * 10) + (kicker_rank / 12 * 5) # 30-45

    # --- High Card: 0-25 (大幅減点) ---
    elif hand_name == "HIGH_CARD":
        high_card_rank = kickers[0] if kickers else 0
        base_score = 0 + (high_card_rank / 12 * 25)

    return round(min(base_score, 100.0), 2)

def evaluate_hand(hole_cards: List[str], community_cards: List[str]) -> Dict[str, Any]:
    """
    Evaluates the best 5-card hand from hole cards and community cards.
    """
    if not isinstance(hole_cards, list) or len(hole_cards) != 2:
        return {"error": "Hole cards must be a list of 2 strings."}
    if not isinstance(community_cards, list) or not (3 <= len(community_cards) <= 5):
        return {"error": "Community cards must be a list of 3 to 5 strings."}

    try:
        parsed_hole = [_parse_card(c) for c in hole_cards]
        parsed_community = [_parse_card(c) for c in community_cards]
    except ValueError as e:
        return {"error": str(e)}

    all_cards = parsed_hole + parsed_community
    
    best_hand_rank = -1
    best_hand_details = (-1, -1, -1, [-1]*5)
    best_hand_cards = None

    for hand_combination in combinations(all_cards, 5):
        try:
            rank_details = _get_hand_rank_and_kickers(list(hand_combination))
        except ValueError:
            continue

        current_hand_score = (rank_details[0], rank_details[1], rank_details[2]) + tuple(rank_details[3])
        best_hand_score = (best_hand_details[0], best_hand_details[1], best_hand_details[2]) + tuple(best_hand_details[3])
        current_hand_score_padded = current_hand_score + (-1,) * (7 - len(current_hand_score))
        best_hand_score_padded = best_hand_score + (-1,) * (7 - len(best_hand_score))

        if current_hand_score_padded > best_hand_score_padded:
            best_hand_rank = rank_details[0]
            best_hand_details = rank_details
            best_hand_cards = hand_combination

    if best_hand_cards is None:
        return {"error": "Could not determine best hand."}

    hand_name = [k for k, v in HAND_RANKS.items() if v == best_hand_rank][0]
    
    normalized_score = _calculate_strength_score(hand_name, best_hand_details, parsed_hole, parsed_community)

    return {
        "hand_name": hand_name,
        "hand_rank": best_hand_rank,
        "best_5_cards": [f"{r}{s}" for r, s in best_hand_cards],
        "strength_score": normalized_score,
        "details": list(best_hand_details)
    }

if __name__ == '__main__':
    # Test cases
    print("Royal Flush:", evaluate_hand(['As', 'Ks'], ['Qs', 'Js', 'Ts', '3d']))
    print("Four of a Kind:", evaluate_hand(['Ac', 'Ad'], ['As', 'Ah', 'Kd', 'Qd']))
    print("Full House:", evaluate_hand(['Ac', 'Ad'], ['As', 'Kc', 'Kd']))
    print("Flush:", evaluate_hand(['As', '2s'], ['8s', '4s', '5s', 'Kc']))
    print("Straight:", evaluate_hand(['8s', '7h'], ['6c', '5d', '4s']))
    print("Three of a Kind:", evaluate_hand(['Ac', 'Ad'], ['As', 'Kc', 'Qd']))
    print("Two Pair:", evaluate_hand(['Ac', 'Kd'], ['Ah', 'Kc', '2d', '3h']))
    # One Pair Tests
    print("One Pair (Top Pair, Top Kicker):", evaluate_hand(['Ac', 'Ks'], ['Ad', '7h', '2c']))
    print("One Pair (Top Pair, Weak Kicker):", evaluate_hand(['Ac', '3s'], ['Ad', '7h', '2c']))
    print("One Pair (Overpair):", evaluate_hand(['Ks', 'Kc'], ['Jd', '7h', '2c']))
    print("One Pair (Middle Pair):", evaluate_hand(['7s', '6c'], ['Ad', '7h', '2c']))
    print("One Pair (Bottom Pair):", evaluate_hand(['2s', '3c'], ['Ad', '7h', '2h']))
    print("High Card:", evaluate_hand(['As', 'Qd'], ['2h', '4c', '6d', '8h']))