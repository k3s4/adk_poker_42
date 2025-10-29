"""
Side pot distribution tests
"""

from poker.game import PokerGame, GamePhase
from poker.player_models import RandomPlayer, PlayerStatus
from poker.game_models import Card, Suit


def test_side_pot_distribution_basic():
    """All-in creates main and side pots; distribute correctly.

    Scenario:
    - P0 all-in 50
    - P1, P2, P3 each invest 200
    Pot layers:
      main  = 50 * 4 = 200 (eligible: P0,P1,P2,P3)
      side1 = 150 * 3 = 450 (eligible: P1,P2,P3)

    Hands:
      P0: Trips Aces (best overall)
      P1: Trips Kings (best among P1,P2,P3)
      P2: Trips Queens
      P3: Pair Nines

    Expected:
      P0 wins 200 (main pot only)
      P1 wins 450 (side pot)
      P2, P3 win 0
    """

    game = PokerGame()
    # Add 4 players
    p0 = RandomPlayer(0, "P0", 0)
    p1 = RandomPlayer(1, "P1", 0)
    p2 = RandomPlayer(2, "P2", 0)
    p3 = RandomPlayer(3, "P3", 0)
    game.add_player(p0)
    game.add_player(p1)
    game.add_player(p2)
    game.add_player(p3)

    # Assign community cards
    game.community_cards = [
        Card(14, Suit.CLUBS),  # A♣
        Card(13, Suit.DIAMONDS),  # K♦
        Card(12, Suit.HEARTS),  # Q♥
        Card(2, Suit.SPADES),  # 2♠
        Card(3, Suit.SPADES),  # 3♠
    ]

    # Hole cards
    p0.hole_cards = [Card(14, Suit.DIAMONDS), Card(14, Suit.HEARTS)]  # A♦ A♥ (Trips A)
    p1.hole_cards = [Card(13, Suit.CLUBS), Card(13, Suit.SPADES)]  # K♣ K♠ (Trips K)
    p2.hole_cards = [Card(12, Suit.CLUBS), Card(12, Suit.SPADES)]  # Q♣ Q♠ (Trips Q)
    p3.hole_cards = [Card(9, Suit.CLUBS), Card(9, Suit.DIAMONDS)]  # 9♣ 9♦ (Pair 9)

    # Set statuses at showdown
    p0.status = PlayerStatus.ALL_IN
    p1.status = PlayerStatus.ACTIVE
    p2.status = PlayerStatus.ACTIVE
    p3.status = PlayerStatus.ACTIVE

    # Contributed chips this hand
    p0.total_bet_this_hand = 50
    p1.total_bet_this_hand = 200
    p2.total_bet_this_hand = 200
    p3.total_bet_this_hand = 200
    # Ensure current_bet does not interfere
    p0.current_bet = 0
    p1.current_bet = 0
    p2.current_bet = 0
    p3.current_bet = 0

    # Total pot
    game.pot = 50 + 200 + 200 + 200

    # Move to showdown phase
    game.current_phase = GamePhase.SHOWDOWN

    results = game.conduct_showdown()

    # Map winnings
    pid_to_win = {r["player_id"]: r["winnings"] for r in results["results"]}

    assert pid_to_win.get(0, 0) == 200
    assert pid_to_win.get(1, 0) == 450
    assert pid_to_win.get(2, 0) == 0
    assert pid_to_win.get(3, 0) == 0


def test_side_pot_multiple_allins_three_layers():
    """Multiple all-ins produce three pot layers and distribute correctly.

    Scenario contributions:
    - P0 all-in 50
    - P1 all-in 120
    - P2 invests 200
    - P3 invests 200

    Pot layers:
      main  = 50 * 4 = 200 (eligible: P0,P1,P2,P3)
      side1 = 70 * 3 = 210 (eligible: P1,P2,P3)
      side2 = 80 * 2 = 160 (eligible: P2,P3)

    Hands (reuse basic ranking setup):
      P0: Trips Aces (best overall)
      P1: Trips Kings (best among P1,P2,P3)
      P2: Trips Queens (best among P2,P3)
      P3: Pair Nines

    Expected:
      P0: 200, P1: 210, P2: 160, P3: 0
    """

    game = PokerGame()
    # Players
    p0 = RandomPlayer(0, "P0", 0)
    p1 = RandomPlayer(1, "P1", 0)
    p2 = RandomPlayer(2, "P2", 0)
    p3 = RandomPlayer(3, "P3", 0)
    game.add_player(p0)
    game.add_player(p1)
    game.add_player(p2)
    game.add_player(p3)

    # Board
    game.community_cards = [
        Card(14, Suit.CLUBS),  # A♣
        Card(13, Suit.DIAMONDS),  # K♦
        Card(12, Suit.HEARTS),  # Q♥
        Card(2, Suit.SPADES),  # 2♠
        Card(3, Suit.SPADES),  # 3♠
    ]

    # Hole cards mapping to desired strengths
    p0.hole_cards = [Card(14, Suit.DIAMONDS), Card(14, Suit.HEARTS)]  # A♦ A♥ (Trips A)
    p1.hole_cards = [Card(13, Suit.CLUBS), Card(13, Suit.SPADES)]  # K♣ K♠ (Trips K)
    p2.hole_cards = [Card(12, Suit.CLUBS), Card(12, Suit.SPADES)]  # Q♣ Q♠ (Trips Q)
    p3.hole_cards = [Card(9, Suit.CLUBS), Card(9, Suit.DIAMONDS)]  # 9♣ 9♦ (Pair 9)

    # Statuses at showdown
    p0.status = PlayerStatus.ALL_IN
    p1.status = PlayerStatus.ALL_IN
    p2.status = PlayerStatus.ACTIVE
    p3.status = PlayerStatus.ACTIVE

    # Contributions
    p0.total_bet_this_hand = 50
    p1.total_bet_this_hand = 120
    p2.total_bet_this_hand = 200
    p3.total_bet_this_hand = 200
    p0.current_bet = p1.current_bet = p2.current_bet = p3.current_bet = 0
    game.pot = 50 + 120 + 200 + 200

    game.current_phase = GamePhase.SHOWDOWN
    results = game.conduct_showdown()

    pid_to_win = {r["player_id"]: r["winnings"] for r in results["results"]}
    assert pid_to_win.get(0, 0) == 200
    assert pid_to_win.get(1, 0) == 210
    assert pid_to_win.get(2, 0) == 160
    assert pid_to_win.get(3, 0) == 0
    # Pot fully distributed
    assert game.pot == 0


def test_side_pot_excludes_folded_contributor():
    """Folded player's contribution remains in pot but cannot win any layer."""

    game = PokerGame()
    p0 = RandomPlayer(0, "P0", 0)
    p1 = RandomPlayer(1, "P1", 0)
    p2 = RandomPlayer(2, "P2", 0)
    p3 = RandomPlayer(3, "P3", 0)
    game.add_player(p0)
    game.add_player(p1)
    game.add_player(p2)
    game.add_player(p3)

    # Board
    game.community_cards = [
        Card(14, Suit.CLUBS),
        Card(13, Suit.DIAMONDS),
        Card(12, Suit.HEARTS),
        Card(2, Suit.SPADES),
        Card(3, Suit.SPADES),
    ]

    # Hole cards for ranking
    p0.hole_cards = [Card(8, Suit.CLUBS), Card(7, Suit.DIAMONDS)]  # irrelevant (folded)
    p1.hole_cards = [Card(13, Suit.CLUBS), Card(13, Suit.SPADES)]  # Trips K
    p2.hole_cards = [Card(14, Suit.DIAMONDS), Card(14, Suit.HEARTS)]  # Trips A (best)
    p3.hole_cards = [Card(9, Suit.CLUBS), Card(9, Suit.DIAMONDS)]  # Pair 9

    # Statuses
    p0.status = PlayerStatus.FOLDED
    p1.status = PlayerStatus.ACTIVE
    p2.status = PlayerStatus.ALL_IN
    p3.status = PlayerStatus.ACTIVE

    # Contributions: p0 also contributed but folded
    p0.total_bet_this_hand = 200
    p1.total_bet_this_hand = 200
    p2.total_bet_this_hand = 50
    p3.total_bet_this_hand = 200
    p0.current_bet = p1.current_bet = p2.current_bet = p3.current_bet = 0
    game.pot = 200 + 200 + 50 + 200

    game.current_phase = GamePhase.SHOWDOWN
    results = game.conduct_showdown()

    pid_to_win = {r["player_id"]: r["winnings"] for r in results["results"]}
    # Main pot goes to P2 (best among eligible in layer1)
    assert pid_to_win.get(2, 0) == 200
    # Side pot goes to P1 (best among P1,P3)
    assert pid_to_win.get(1, 0) == 450
    # Folded contributor wins nothing
    assert pid_to_win.get(0, 0) == 0
    assert pid_to_win.get(3, 0) == 0
    assert game.pot == 0


def test_side_pot_tie_split_remainder_by_id():
    """Tie within a layer splits with remainder assigned by ascending player id."""

    game = PokerGame()
    p0 = RandomPlayer(0, "P0", 0)
    p1 = RandomPlayer(1, "P1", 0)
    p2 = RandomPlayer(2, "P2", 0)
    p3 = RandomPlayer(3, "P3", 0)
    game.add_player(p0)
    game.add_player(p1)
    game.add_player(p2)
    game.add_player(p3)

    # Board yields two-pair AAKK; kicker determined by hole card
    game.community_cards = [
        Card(14, Suit.CLUBS),  # A♣
        Card(14, Suit.DIAMONDS),  # A♦
        Card(13, Suit.CLUBS),  # K♣
        Card(13, Suit.DIAMONDS),  # K♦
        Card(5, Suit.CLUBS),  # 5♣ (board kicker if no better)
    ]

    # P0 and P1 share T kicker; P2 has 9 kicker -> loses
    p0.hole_cards = [Card(10, Suit.SPADES), Card(2, Suit.CLUBS)]
    p1.hole_cards = [Card(10, Suit.HEARTS), Card(3, Suit.CLUBS)]
    p2.hole_cards = [Card(9, Suit.SPADES), Card(4, Suit.DIAMONDS)]
    p3.hole_cards = [Card(2, Suit.HEARTS), Card(7, Suit.SPADES)]

    # Statuses
    p0.status = PlayerStatus.ACTIVE
    p1.status = PlayerStatus.ACTIVE
    p2.status = PlayerStatus.ACTIVE
    p3.status = PlayerStatus.FOLDED

    # Single layer: 101 * 3 = 303; two winners (P0,P1) tie -> base 151, remainder 1 -> goes to lower id (P0)
    p0.total_bet_this_hand = 101
    p1.total_bet_this_hand = 101
    p2.total_bet_this_hand = 101
    p3.total_bet_this_hand = 0
    p0.current_bet = p1.current_bet = p2.current_bet = p3.current_bet = 0
    game.pot = 101 * 3

    game.current_phase = GamePhase.SHOWDOWN
    results = game.conduct_showdown()

    pid_to_win = {r["player_id"]: r["winnings"] for r in results["results"]}
    assert pid_to_win.get(0, 0) == 152
    assert pid_to_win.get(1, 0) == 151
    assert pid_to_win.get(2, 0) == 0
    assert pid_to_win.get(3, 0) == 0
    assert game.pot == 0
