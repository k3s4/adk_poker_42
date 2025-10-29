from typing import List, Optional, Tuple
from google.adk.tools import FunctionTool
from pokerkit import Deck, Card, StandardHighHand
import random
import re


def pokerkit_tool(
    hole_cards: List[str],
    community_cards: Optional[List[str]] = None,
    num_opponents: int = 1,
    pot_before: int = 0,
    to_call: int = 0,
    simulations: int = 5000
) -> Tuple[float, float, float]:
    """
    pokerkitを使用してポーカーハンドのエクイティとポットオッズを計算します。

    Args:
        hole_cards: ホールカード（2枚）
            例: ["As", "Kd"], ["Tc", "9h"], ["2c", "2d"]
            ランク: 2,3,4,5,6,7,8,9,T,J,Q,K,A（10は'T'で表記）
            スート: s(スペード), h(ハート), d(ダイヤ), c(クラブ)

        community_cards: コミュニティカード（0,3,4,5枚）
            例: [] (プリフロップ)
                ["Js", "Qh", "9d"] (フロップ)
                ["Js", "Qh", "9d", "2c"] (ターン)
                ["Js", "Qh", "9d", "2c", "Ah"] (リバー)

        num_opponents: 対戦相手数（1以上）
            例: 1 (ヘッズアップ), 2 (3人), 3 (4人)

        pot_before: コール前のポット総額（相手のベットも含む）
            例: 100, 1500, 0 (チェック可能な場合)

        to_call: コールに必要な額
            例: 50, 200, 0 (チェック可能な場合)

        simulations: モンテカルロシミュレーション回数（デフォルト5000）


    Returns:
        tuple[float, float, float]: (equity, required_equity, pot_odds_ratio)

        equity: ヒーローの勝率（0.0-1.0）
            例: 0.65 = 65%の勝率

        required_equity: コールに必要な勝率（ブレイクイーブンエクイティ）
            例: 0.33 = 33%以上の勝率が必要
            計算式: to_call / (pot_before + to_call)

        pot_odds_ratio: ポットオッズの比率（X:1のX）
            例: 2.0 = 2:1のオッズ（33%の勝率が必要）
            計算式: pot_before / to_call

        ## ツール使用時のルール

        pokerkit_tool を使用して勝率を計算する際は、以下のカード表記ルールを**厳密に**守ってください。

        ### カード表記のルール
        - **形式**: 全てのカードは**ランク**と**スート**を組み合わせた**2文字**の文字列で表現します。
        - **ランク**:
        - `2` から `9` はそのまま数字を使用します。
        - `10` は必ず大文字の **`T`** を使用します。
        - `Jack` は **`J`**, `Queen` は **`Q`**, `King` は **`K`**, `Ace` は **`A`** を使用します。
        - **スート**:
        - スペード(Spades)は小文字の **`s`** を使用します。
        - ハート(Hearts)は小文字の **`h`** を使用します。
        - ダイヤ(Diamonds)は小文字の **`d`** を使用します。
        - クラブ(Clubs)は小文字の **`c`** を使用します。

        ### 具体例
        - **良い例 (Correct Examples):**
        - `hole_cards=["As", "Kd"]`
        - `hole_cards=["Tc", "Th"]`
        - `community_cards=["Js", "Qh", "9d"]`

        - **悪い例 (Incorrect Examples):**
        - `["A♠", "K♦"]` (理由: スートに記号 `♠`, `♦` を使っている)
        - `["10c", "9h"]` (理由: ランク `10` が `T` ではない)
        - `["king of spades", "ace of hearts"]` (理由: 文字列形式が違う)

        ツールの正しい呼び出し方の例：
        pokerkit_tool(hole_cards=["As", "Kd"], community_cards=["Ts", "9h", "2c"], ...)

        ツールの間違った呼び出し方の例：
        - pokerkit_tool(hole_cards=["A spade", "K diamond"], ...)  // 間違い: 文字列表記
        - pokerkit_tool(hole_cards=["10s", "9h"], ...)            // 間違い: 10はTで表記
        - pokerkit_tool(hole_cards=["Asp", "Kh"], ...)             // 間違い: 'p'は不正なスート

        このルールに従って、正確な引数を生成してください。
    """
    
    # community_cardsがNoneの場合に空リストを代入
    community_cards_list = community_cards or []
    
    # ランクとスートの変換マップ
    rank_map = {
        '10': 'T', 'T': 'T', 't': 'T',
        'J': 'J', 'j': 'J',
        'Q': 'Q', 'q': 'Q',
        'K': 'K', 'k': 'K',
        'A': 'A', 'a': 'A',
        **{str(i): str(i) for i in range(2, 10)}
    }
    suit_map = {
        's': 's', '♠': 's', '♤': 's',
        'h': 'h', '♥': 'h', '♡': 'h',
        'd': 'd', '♦': 'd', '♢': 'd',
        'c': 'c', '♣': 'c', '♧': 'c',
    }
    
    # 入力された全てのカードを一時的なリストにまとめる
    raw_hole_cards_len = len(hole_cards)
    all_raw_cards = hole_cards + community_cards_list

    normalized_cards = []
    card_pattern = re.compile(r'^[2-9TJQKA][shdc]$')

    for card in all_raw_cards:
        if not isinstance(card, str):
             raise ValueError(f"カードの表記 '{card}' は不正です。文字列で指定してください。カードの表記を確認して再度実行してください。")

        card = "".join(card.split())

        if len(card) < 2:
            raise ValueError(f"カードの表記 '{card}' は不正です。2文字以上の文字列で指定してください。カードの枚数を確認して再度実行してください。")

        # 最後の一文字をスート、それより前をランクとして分離
        rank_symbol = card[:-1].upper()
        suit_symbol = card[-1].lower()
        
        # マップを使ってランクとスートを変換
        normalized_rank = rank_map.get(rank_symbol, rank_symbol)
        normalized_suit = suit_map.get(suit_symbol, suit_symbol)
        
        normalized_card = normalized_rank + normalized_suit
        
        # バリデーション
        if not card_pattern.match(normalized_card):
            raise ValueError(
                f"カードの表記 '{card}' (処理後: '{normalized_card}') は不正です。" # エラーメッセージを詳細化
                "ランク(2-9,T,J,Q,K,A)とスート(s,h,d,c)で指定してください。カードを確認して再度実行してください。"
            )
        normalized_cards.append(normalized_card)

    # これ以降の処理は全て正規化されたカードリストで行われる
    hole_cards = normalized_cards[:raw_hole_cards_len]
    community_cards = normalized_cards[raw_hole_cards_len:]

    # --- validation ---
    if len(hole_cards) != 2:
        raise ValueError("hole_cards は2枚で指定してください。カードの枚数を確認して、再度実行してください。")
    if len(community_cards) not in (0, 3, 4, 5):
        raise ValueError("community_cards の枚数は 0 / 3 / 4 / 5 のいずれかにしてください。カードの枚数を確認して、再度実行してください。")
    if num_opponents < 1:
        raise ValueError("num_opponents は1以上にしてください。対戦相手の数を確認して、再度実行してください。")

    # 重複チェック
    all_cards = hole_cards + community_cards
    if len(set(all_cards)) != len(all_cards):
        raise ValueError("重複しているカードがあります。カードの枚数を確認して、再度実行してください。")

    # カード表記をそのまま使用（pokerkitの標準形式を想定）
    hole_str  = "".join(hole_cards)
    board_str = "".join(community_cards)

    # 既知カードを取り除いた残りデッキ（Card オブジェクト）
    known_cards = set(Card.parse(hole_str + board_str))
    deck_remain = [c for c in Deck.STANDARD if c not in known_cards]

    board_needed = 5 - len(community_cards)
    draw_needed  = 2 * num_opponents + max(0, board_needed)  # 1試行で必要な残り札

    hero_share_sum = 0.0

    # --- Monte Carlo ---
    for _ in range(simulations):
        draw = random.sample(deck_remain, draw_needed)

        # 相手ホール (2枚ずつ)
        opp_holes = [draw[i*2:(i+1)*2] for i in range(num_opponents)]

        # 残りボード
        board_draw = draw[2*num_opponents:]  # board_needed 枚
        full_board = community_cards + [repr(c) for c in board_draw]

        # ヒーローとオポーネントの手を構築
        hero_hand = StandardHighHand.from_game(hole_str, "".join(full_board))
        opp_hands = [
            StandardHighHand.from_game("".join(map(repr, oh)), "".join(full_board))
            for oh in opp_holes
        ]

        # マルチウェイの分割勝ちを正しく計算
        hands = [hero_hand] + opp_hands
        best_hand = max(hands)
        winners = sum(1 for h in hands if h == best_hand)
        if hero_hand == best_hand:
            hero_share_sum += 1.0 / winners  # 等分取り分

    equity = hero_share_sum / simulations  # 期待取り分（引き分けは自動で等分）

    # --- Pot odds ---
    def _required_equity(pot_before: float, to_call: float) -> float:
        if to_call <= 0:
            return 0.0
        return to_call / (pot_before + to_call)

    def _pot_odds_ratio(pot_before: float, to_call: float) -> float:
        if to_call <= 0:
            return float("inf")
        return pot_before / to_call

    req_equity = _required_equity(pot_before, to_call)
    ratio      = _pot_odds_ratio(pot_before, to_call)

    return equity, req_equity, ratio

    
PokerKitTool = FunctionTool(func=pokerkit_tool)