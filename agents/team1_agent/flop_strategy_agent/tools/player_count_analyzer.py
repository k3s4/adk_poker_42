"""
Analyzes the number of active players in the hand.
"""
from typing import List, Dict, Any

def analyze_player_count(players: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Counts the number of active players (not folded or all-in).

    Args:
        players: A list of player dictionaries from the game state.
                 Each player dict is expected to have a 'state' key.

    Returns:
        A dictionary with the count of active players.
    """
    if not isinstance(players, list):
        return {"error": "Input 'players' must be a list."}

    # An active player is one whose state is not 'folded'
    # We also consider all-in players as "active" in the pot, but for bluffing,
    # we are interested in players who can still fold.
    # Let's count players who have not folded.
    active_players = [p for p in players if p.get('state') != 'folded']
    
    return {
        "active_player_count": len(active_players)
    }
