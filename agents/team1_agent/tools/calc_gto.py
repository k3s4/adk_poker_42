import random
from typing import List, Dict, Any, Optional
from pokerkit import Card, Deck, calculate_equities, parse_range, StandardHighHand


def calc_gto(
    phase: str,
    your_cards: List[str],
    community: List[str] | None,
    pot: int,
    to_call: int,
    actions: List[str],
    num_players: int = 2,
    stack: int = 1000,
    iterations: int = 300,
) -> Dict[str, Any]:
    """
    Estimates equity using pokerkit and provides a GTO-like strategy.

    Args:
        phase: "preflop" | "flop" | "turn" | "river"
        your_cards: e.g., ["As", "Ks"]
        community: e.g., ["7h", "Jd", "2c"] (or [] / None if none)
        pot: Current pot size
        to_call: Amount required to call
        actions: List of available actions, e.g., ["fold", "call (20)"]
        num_players: Total players at the table (including yourself)
        stack: Your remaining chip stack
        iterations: Number of Monte Carlo simulations

    Returns:
        A dictionary containing equity, pot_odds, spr, strategy,
        a recommended action, and a reasoning string.
    """
    
    # Convert card strings to pokerkit Card objects
    def parse_cards(card_strings: List[str]) -> List[Card]:
        """Convert card strings like 'As' to pokerkit Card objects."""
        cards = []
        for card_str in card_strings:
            # Use Card.parse which returns a generator
            parsed_cards = list(Card.parse(card_str))
            if parsed_cards:
                cards.extend(parsed_cards)
        return cards
    
    try:
        # Parse your cards
        your_cards_parsed = parse_cards(your_cards)
        if len(your_cards_parsed) != 2:
            raise ValueError("Invalid hole cards")
        
        # Parse community cards
        community_parsed = []
        if community:
            community_parsed = parse_cards(community)
        
        # Calculate equity using Monte Carlo simulation
        equity = calculate_equity(your_cards_parsed, community_parsed, phase, num_players, iterations)
        
        # Calculate pot odds
        pot_odds = to_call / (pot + to_call) if to_call > 0 else 0
        
        # Calculate Stack-to-Pot Ratio (SPR)
        spr = stack / pot if pot > 0 else float('inf')
        
        # Determine strategy based on equity and pot odds
        strategy = determine_strategy(equity, pot_odds, spr, phase, actions)
        
        # Get recommended action
        recommended_action = get_recommended_action(strategy, actions, to_call, stack)
        
        # Generate reasoning
        reasoning = generate_reasoning(equity, pot_odds, spr, strategy, phase, recommended_action)
        
        return {
            "equity": equity,
            "pot_odds": pot_odds,
            "spr": spr,
            "strategy": strategy,
            "action": recommended_action,
            "reasoning": reasoning
        }
        
    except Exception as e:
        # Fallback strategy if calculations fail
        fallback_pot_odds = to_call / (pot + to_call) if to_call > 0 else 0
        return {
            "equity": 0.5,
            "pot_odds": fallback_pot_odds,
            "spr": stack / pot if pot > 0 else float('inf'),
            "strategy": "balanced",
            "action": {"action": "call", "amount": to_call} if "call" in actions else {"action": "fold", "amount": 0},
            "reasoning": f"Calculation error: {str(e)}. Using fallback strategy."
        }


def calculate_equity(
    your_cards: List[Card], 
    community_cards: List[Card], 
    phase: str, 
    num_players: int, 
    iterations: int
) -> float:
    """Calculate hand equity using pokerkit's calculate_equities function."""
    
    try:
        # Convert cards to string format for parse_range
        def cards_to_range(cards: List[Card]) -> str:
            """Convert Card objects to range string format."""
            if len(cards) != 2:
                return ""
            # Convert to format like "AsKh"
            card_strs = []
            for card in cards:
                rank = card.rank
                suit = card.suit[0].lower()  # First letter of suit, lowercase
                card_strs.append(f"{rank}{suit}")
            return "".join(card_strs)
        
        # Convert community cards to string format
        def community_to_string(cards: List[Card]) -> str:
            """Convert community cards to string format."""
            if not cards:
                return ""
            card_strs = []
            for card in cards:
                rank = card.rank
                suit = card.suit[0].lower()
                card_strs.append(f"{rank}{suit}")
            return "".join(card_strs)
        
        # Create your hand range
        your_range = cards_to_range(your_cards)
        if not your_range:
            return 0.5  # Fallback if cards can't be parsed
        
        # Create opponent range (use a specific hand for simplicity)
        # For now, we'll use a medium strength hand as opponent
        opponent_range = "KsKh"
        
        # Convert community cards to string
        community_str = community_to_string(community_cards)
        
        # Calculate equities
        hole_ranges = (parse_range(your_range), parse_range(opponent_range))
        board_cards = Card.parse(community_str) if community_str else []
        
        # Determine board dealing count based on phase
        if phase == "preflop":
            board_dealing_count = 0
        elif phase == "flop":
            board_dealing_count = 3
        elif phase == "turn":
            board_dealing_count = 4
        elif phase == "river":
            board_dealing_count = 5
        else:
            board_dealing_count = len(community_cards)
        
        equities = calculate_equities(
            hole_ranges,
            board_cards,
            hole_dealing_count=2,
            board_dealing_count=board_dealing_count,
            deck=Deck.STANDARD,
            hand_types=(StandardHighHand,),
            sample_count=iterations
        )
        
        # Return your equity (first player)
        return equities[0] if equities else 0.5
        
    except Exception as e:
        # Fallback to simple estimation
        print(f"Equity calculation error: {e}")
        return 0.5


def determine_strategy(equity: float, pot_odds: float, spr: float, phase: str, actions: List[str]) -> str:
    """Determine GTO strategy based on equity, pot odds, and SPR."""
    
    # Preflop adjustments
    if phase == "preflop":
        if equity > 0.65:
            return "aggressive"
        elif equity > 0.55:
            return "balanced"
        elif equity > 0.45:
            return "cautious"
        else:
            return "tight"
    
    # Post-flop strategy
    if equity > 0.75:
        return "very_aggressive"
    elif equity > 0.65:
        return "aggressive"
    elif equity > 0.55:
        return "balanced"
    elif equity > 0.45:
        return "cautious"
    elif equity > 0.35:
        return "tight"
    else:
        return "very_tight"


def get_recommended_action(strategy: str, actions: List[str], to_call: int, stack: int) -> Dict[str, Any]:
    """Get recommended action based on strategy."""
    
    # Parse available actions
    available_actions = []
    for action in actions:
        if action == "fold":
            available_actions.append({"action": "fold", "amount": 0})
        elif action.startswith("call"):
            # Extract amount from "call (20)" format
            amount_str = action.split("(")[1].split(")")[0]
            amount = int(amount_str)
            available_actions.append({"action": "call", "amount": amount})
        elif action.startswith("raise"):
            # Extract amount from "raise (50)" or "raise (min 50)" format
            amount_str = action.split("(")[1].split(")")[0]
            # Handle "min 50" format
            if amount_str.startswith("min "):
                amount_str = amount_str.split(" ")[1]
            amount = int(amount_str)
            available_actions.append({"action": "raise", "amount": amount})
        elif action == "check":
            available_actions.append({"action": "check", "amount": 0})
        elif action == "all_in":
            available_actions.append({"action": "all_in", "amount": stack})
    
    # Strategy-based action selection
    if strategy in ["very_aggressive", "aggressive"]:
        # Prefer raise or all-in
        for action in available_actions:
            if action["action"] in ["raise", "all_in"]:
                return action
        # Fallback to call
        for action in available_actions:
            if action["action"] == "call":
                return action
    
    elif strategy == "balanced":
        # Mix of actions based on pot odds
        if to_call > 0 and to_call < stack * 0.3:  # Good pot odds
            for action in available_actions:
                if action["action"] == "call":
                    return action
        # Consider raise for value
        for action in available_actions:
            if action["action"] == "raise":
                return action
    
    elif strategy in ["cautious", "tight"]:
        # Prefer call over raise, fold if pot odds are bad
        for action in available_actions:
            if action["action"] == "call":
                return action
    
    elif strategy == "very_tight":
        # Prefer fold unless pot odds are excellent
        for action in available_actions:
            if action["action"] == "fold":
                return action
    
    # Default fallback
    if available_actions:
        return available_actions[0]
    
    return {"action": "fold", "amount": 0}


def generate_reasoning(
    equity: float, 
    pot_odds: float, 
    spr: float, 
    strategy: str, 
    phase: str, 
    recommended_action: Dict[str, Any]
) -> str:
    """Generate reasoning for the recommended action."""
    
    reasoning_parts = []
    
    # Equity analysis
    if equity > 0.7:
        reasoning_parts.append(f"Strong hand equity ({equity:.1%})")
    elif equity > 0.6:
        reasoning_parts.append(f"Good hand equity ({equity:.1%})")
    elif equity > 0.5:
        reasoning_parts.append(f"Decent hand equity ({equity:.1%})")
    else:
        reasoning_parts.append(f"Low hand equity ({equity:.1%})")
    
    # Pot odds analysis
    if pot_odds > 0:
        if equity > pot_odds:
            reasoning_parts.append("Pot odds favorable")
        else:
            reasoning_parts.append("Pot odds unfavorable")
    
    # SPR analysis
    if spr < 3:
        reasoning_parts.append("Low SPR - stack committed")
    elif spr < 10:
        reasoning_parts.append("Medium SPR - standard play")
    else:
        reasoning_parts.append("High SPR - deep stack play")
    
    # Strategy explanation
    strategy_explanations = {
        "very_aggressive": "Very aggressive strategy due to strong equity",
        "aggressive": "Aggressive strategy for value",
        "balanced": "Balanced approach considering position and odds",
        "cautious": "Cautious play due to marginal equity",
        "tight": "Tight play to avoid difficult spots",
        "very_tight": "Very tight play due to weak equity"
    }
    
    reasoning_parts.append(strategy_explanations.get(strategy, "Standard play"))
    
    # Action justification
    action = recommended_action.get("action", "fold")
    amount = recommended_action.get("amount", 0)
    
    if action == "fold":
        reasoning_parts.append("Fold due to unfavorable odds or weak hand")
    elif action == "call":
        reasoning_parts.append(f"Call {amount} to see next street")
    elif action == "raise":
        reasoning_parts.append(f"Raise to {amount} for value/protection")
    elif action == "all_in":
        reasoning_parts.append(f"All-in for {amount} - strong hand or desperate situation")
    elif action == "check":
        reasoning_parts.append("Check to control pot size")
    
    return ". ".join(reasoning_parts)
