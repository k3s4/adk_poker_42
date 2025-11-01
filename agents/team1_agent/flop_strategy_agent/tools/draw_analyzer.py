"""
Analyzes the hand for draw potential (flush or straight draws).
"""
from typing import List, Dict, Any, Set

RANKS = '23456789TJQKA'
RANK_MAP = {rank: i for i, rank in enumerate(RANKS)}

def _parse_card(card_str):
    rank_str = card_str[:-1]
    suit_str = card_str[-1]
    rank = rank_str.upper()
    suit = suit_str.lower()
    if rank == '10':
        rank = 'T'
    return rank, suit

def analyze_draw_potential(hole_cards: List[str], community_cards: List[str]) -> Dict[str, Any]:
    """
    Identifies flush and open-ended straight draws.

    Args:
        hole_cards: The player's two hole cards.
        community_cards: The 3 or 4 community cards on the board.

    Returns:
        A dictionary containing information about potential draws.
    """
    all_cards = hole_cards + community_cards
    if len(all_cards) < 4 or len(all_cards) > 6:
        return {"draws": [], "total_outs": 0}

    parsed_cards = [_parse_card(c) for c in all_cards]
    draws = []
    total_outs = 0
    all_outs: Set[str] = set()

    # 1. Flush Draw Analysis
    suit_counts = {}
    for rank, suit in parsed_cards:
        suit_counts[suit] = suit_counts.get(suit, 0) + 1
    
    for suit, count in suit_counts.items():
        if count == 4:
            # It's a flush draw
            outs = 9
            draws.append({"type": "FLUSH_DRAW", "outs": outs})
            # Add actual out cards to the set
            drawn_ranks = {RANK_MAP[r] for r, s in parsed_cards if s == suit}
            for i in range(len(RANKS)):
                if i not in drawn_ranks:
                    all_outs.add(f"{RANKS[i]}{suit}")

    # 2. Straight Draw Analysis
    unique_ranks = sorted(list(set([RANK_MAP[r] for r, s in parsed_cards])))
    
    # Open-ended straight draw (OESD)
    for i in range(len(unique_ranks) - 2):
        # Check for 4 cards in a 5-card window
        sub_sequence = unique_ranks[i:i+4]
        if len(sub_sequence) == 4 and (sub_sequence[3] - sub_sequence[0] == 3):
            # It's an open-ended draw, e.g., 5,6,7,8
            low_end = sub_sequence[0]
            high_end = sub_sequence[3]
            outs = 0
            if low_end > 0: # Not a straight starting with 2
                outs += 4
            if high_end < 12: # Not a straight ending with Ace
                outs += 4
            if outs > 0:
                draws.append({"type": "OESD", "outs": outs})
                # This is a simplification; doesn't calculate actual card outs for straights yet
                # to avoid conflicts with flush draw outs.

    # Sum up unique outs
    # For now, we will just sum the raw outs, acknowledging they can overlap
    # A more advanced version would use the `all_outs` set.
    total_outs = sum(d['outs'] for d in draws)

    return {
        "draws": draws,
        "total_outs": total_outs
    }
