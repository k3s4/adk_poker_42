mark sets
```
♥♠♦♣

### testcase 1 
default case
```json
{
  "your_id": 0,
  "phase": "preflop",
  "your_cards": ["A♥", "K♥"],
  "community": [],
  "your_chips": 970,
  "your_bet_this_round": 0,
  "your_total_bet_this_hand": 30,
  "pot": 140,
  "to_call": 20,
  "dealer_button": 3,
  "current_turn": 0,
  "players": [
    {"id": 1, "chips": 970, "bet": 0, "status": "active"},
    {"id": 2, "chips": 970, "bet": 0, "status": "active"},
    {"id": 3, "chips": 950, "bet": 20, "status": "active"}
  ],
  "actions": ["fold", "call (20)", "raise (min 40)", "all-in (970)"],
  "history": [
    "Preflop: All players called 30",
    "Flop dealt: Q♥ J♦ 10♣",
    "Player 3 bet 20"
  ]
}

### testcase 2
JTs case
```json
{
  "your_id": 0,
  "phase": "preflop",
  "your_cards": ["J♥", "T♥"],
  "community": [],
  "your_chips": 950,
  "your_bet_this_round": 0,
  "your_total_bet_this_hand": 50,
  "pot": 200,
  "to_call": 50,
  "dealer_button": 1,
  "current_turn": 0,
  "players": [
    {"id": 1, "chips": 950, "bet": 50, "status": "active"},
    {"id": 2, "chips": 1000, "bet": 0, "status": "active"},
    {"id": 3, "chips": 900, "bet": 0, "status": "active"}
  ],
  "actions": ["fold", "call (50)", "raise (min 100)", "all-in (950)"],
  "history": [
    "Preflop: Player 1 raised to 50"
  ]
}

### testcase 3
J9s case
```json
{
  "your_id": 0,
  "phase": "preflop",
  "your_cards": ["J♠", "9♠"],
  "community": [],
  "your_chips": 900,
  "your_bet_this_round": 0,
  "your_total_bet_this_hand": 100,
  "pot": 300,
  "to_call": 75,
  "dealer_button": 2,
  "current_turn": 0,
  "players": [
    {"id": 1, "chips": 950, "bet": 0, "status": "active"},
    {"id": 2, "chips": 925, "bet": 75, "status": "active"},
    {"id": 3, "chips": 1000, "bet": 0, "status": "active"}
  ],
  "actions": ["fold", "call (75)", "raise (min 150)", "all-in (900)"],
  "history": [
    "Preflop: Player 2 raised to 75"
  ]
}

### testcase 4
- Flop case
- preflopのエージェントはすぐにflopのエージェントに移行するか検証

```json
{
  "your_id": 0,
  "phase": "flop",
  "your_cards": ["A♥", "K♦"],
  "community": ["A♠", "Q♣", "J♥"],
  "your_chips": 850,
  "your_bet_this_round": 0,
  "your_total_bet_this_hand": 150,
  "pot": 400,
  "to_call": 100,
  "dealer_button": 2,
  "current_turn": 0,
  "players": [
    {"id": 1, "chips": 900, "bet": 100, "status": "active"},
    {"id": 2, "chips": 800, "bet": 0, "status": "active"},
    {"id": 3, "chips": 950, "bet": 0, "status": "active"}
  ],
  "actions": ["fold", "call (100)", "raise (min 200)", "all-in (850)"],
  "history": [
    "Preflop: All players called 50",
    "Flop dealt: A♠ Q♣ J♥",
    "Player 1 bet 100"
  ]
}
