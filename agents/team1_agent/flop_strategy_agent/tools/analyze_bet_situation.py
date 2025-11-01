"""
Analyzes the betting situation based on pot size and the amount to call.
"""
from typing import Dict, Any

def analyze_bet_situation(pot_size: int, to_call: int) -> Dict[str, Any]:

    if to_call == 0:
        return {
            "pot_size": pot_size,
            "to_call": to_call,
            "bet_as_pot_percentage": 0.0,
            "threat_level": "NONE"  # No bet to call
        }

    # Ensure pot_size is not zero to avoid division errors, though unlikely in poker
    if pot_size == 0:
        pot_size = to_call # Treat the bet as the pot if pot was empty

    bet_percentage = round((to_call / pot_size) * 100, 2)
    
    threat_level = "LOW"
    if bet_percentage >= 100:
        threat_level = "EXTREME" # PotOver-bet or all-in
    elif bet_percentage >= 75:
        threat_level = "HIGH"
    elif bet_percentage >= 30:
        threat_level = "MEDIUM"

    return {
        "pot_size": pot_size,
        "to_call": to_call,
        "bet_as_pot_percentage": bet_percentage,
        "threat_level": threat_level
    }