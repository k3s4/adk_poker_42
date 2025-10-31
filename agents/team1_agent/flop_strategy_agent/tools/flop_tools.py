# agents/team1_agent/flop_strategy_agent/tools/flop_tools.py

import json
import traceback
from . import analysis, hand, util

# 定数
EQUITY_SAMPLE_COUNT = 1000  # 勝率計算のシミュレーション回数

# カード形式変換用の辞書
SUIT_MAP = {'♥': 'h', '♦': 'd', '♠': 's', '♣': 'c'}
RANK_MAP = {'10': 'T'}

def _convert_cards(cards_llm_format: list[str]) -> list[str]:
    """ゲームステートのカード形式（例: ["A♥"]）をpokerkit形式（例: ["Ah"]）に変換する。"""
    pokerkit_cards = []
    for card_str in cards_llm_format:
        rank = card_str[:-1]
        suit = card_str[-1]
        rank_pk = RANK_MAP.get(rank, rank)
        suit_pk = SUIT_MAP.get(suit)
        if suit_pk:
            pokerkit_cards.append(f"{rank_pk}{suit_pk}")
    return pokerkit_cards

def _get_opponent_ranges(num_opponents: int):
    """相手のハンドレンジをランダム（Any Two）として生成する。"""
    any_two_range_str = 'AA-22s,KQs-K2s,QJs-Q2s,JTs-J2s,T9s-T2s,98s-92s,87s-82s,76s-72s,65s-62s,54s-52s,43s-42s,32s,AKo-A2o,KQo-K2o,QJo-Q2o,JTo-J2o,T9o-T2o,98o-92o,87o-82o,76o-72o'
    any_two_range = analysis.parse_range(any_two_range_str)
    return [any_two_range] * num_opponents

def evaluate_hand(hole_cards: list[str], board_cards: list[str]) -> str:
    """自分の手札と場のカードから、現在のポーカーの役を判定します。"""
    try:
        my_cards_pk = _convert_cards(hole_cards)
        board_cards_pk = _convert_cards(board_cards)
        
        if not my_cards_pk or len(board_cards_pk) < 3:
            return "情報不足のため役を判定できません。"

        current_hand = hand.StandardHighHand.from_game(my_cards_pk, board_cards_pk)
        return f"現在の役は「{current_hand.entry.label.value}」です。"
    except Exception as e:
        return f"役の判定中にエラーが発生しました: {e}"

def calculate_equity(hole_cards: list[str], board_cards: list[str], num_opponents: int) -> str:
    """現在の状況での勝率（エクイティ）を計算します。相手はランダムなハンドを持っていると仮定します。"""
    try:
        my_cards_pk = _convert_cards(hole_cards)
        board_cards_pk = _convert_cards(board_cards)

        if not my_cards_pk or not isinstance(num_opponents, int) or num_opponents <= 0:
            return "情報不足のため勝率を計算できません。"

        hole_ranges = [analysis.parse_range(''.join(my_cards_pk))] + _get_opponent_ranges(num_opponents)
        
        known_cards = set(util.Card.parse(''.join(my_cards_pk + board_cards_pk)))
        deck = [card for card in util.Deck.STANDARD if card not in known_cards]

        equities = analysis.calculate_equities(
            hole_ranges=hole_ranges,
            board_cards=board_cards_pk,
            hole_dealing_count=2,
            board_dealing_count=5,
            deck=deck,
            hand_types=[hand.StandardHighHand],
            sample_count=EQUITY_SAMPLE_COUNT,
        )
        my_equity = equities[0]
        return f"アクティブな相手が{num_opponents}人いる状況での勝率は、約{my_equity:.1%}です。"
    except Exception as e:
        return f"勝率の計算中にエラーが発生しました: {e}"

def suggest_flop_action(game_state: dict) -> str:
    """
    フロップ以降のゲーム状況を分析し、最適なアクションを提案します。
    """
    try:
        # 1. ゲームステートから情報を抽出
        hole_cards = game_state.get("hole_cards", [])
        board_cards = game_state.get("board_cards", [])
        to_call = game_state.get("to_call", 0)
        pot = game_state.get("pot", {}).get("total", 0)
        my_chips = game_state.get("your_chips", 0)
        
        # 自分以外の「active」なプレイヤー数を数える
        active_players = [p for p in game_state.get("players", []) if p.get("status") == "active" and p.get("name") != game_state.get("your_name")]
        num_opponents = len(active_players)

        if not hole_cards or len(board_cards) < 3:
            return '{"action": "skip", "reason": "情報不足、またはプリフロップの可能性があります。"}'
        
        if num_opponents <= 0:
            # 相手がいない場合は常にチェック/ベット
            action = "raise"
            amount = int(pot * 0.5) if pot > 0 else 10 # ブラインドベット相当
            if amount == 0 and my_chips > 0:
                amount = 10
            if amount > my_chips:
                amount = my_chips
            return json.dumps({"action": action, "amount": amount, "reason": "相手が全員フォールドしたため、ポットを獲得するためにベットします。"}, ensure_ascii=False)


        # 2. 役の評価と勝率の計算
        hand_evaluation_str = evaluate_hand(hole_cards, board_cards)
        equity_str = calculate_equity(hole_cards, board_cards, num_opponents)

        # 文字列から数値や役名を抽出
        try:
            hand_strength = hand_evaluation_str.split("「")[1].split("」")[0]
        except IndexError:
            hand_strength = "不明"
        
        try:
            equity = float(equity_str.split("約")[1].split("%")[0]) / 100
        except (IndexError, ValueError):
            equity = 0.0

        # 3. アクション決定ロジック
        action = "fold"
        reason = ""
        amount = 0

        # ポットオッズの計算
        pot_odds = to_call / (pot + to_call) if (pot + to_call) > 0 else 0

        # 基本的な戦略
        if equity > 0.8:
            action = "raise"
            amount = int(pot * 0.75)
            reason = f"非常に強い役（{hand_strength}）を持っており、勝率が{equity:.1%}と極めて高いため、バリューを最大化するためにレイズします。"
        elif equity > 0.6: # 少し基準を上げる
            action = "raise"
            amount = int(pot * 0.5)
            reason = f"良い役（{hand_strength}）で、勝率が{equity:.1%}と高いため、バリューベットをします。"
        elif equity > 0.4:
             action = "call" if to_call > 0 else "check"
             reason = f"中程度の役（{hand_strength}）ですが、勝率が{equity:.1%}あるため、コールして様子を見ます。"
        elif equity > pot_odds and to_call > 0:
            action = "call"
            reason = f"役はまだ弱いが、勝率（{equity:.1%}）がポットオッズ（{pot_odds:.1%}）を上回っているため、ドローを期待してコールします。"
        else:
            if to_call > 0:
                action = "fold"
                reason = f"役が弱く（{hand_strength}）、勝率（{equity:.1%}）もポットオッズ（{pot_odds:.1%}）に見合わないため、損失を避けるためにフォールドします。"
            else:
                action = "check"
                reason = f"役は弱いが（{hand_strength}）、追加のコストなしで次のカードを見ることができるため、チェックします。"

        # チップ量に応じた調整
        if action == "raise":
            if amount <= to_call and my_chips > to_call: # レイズ額がコール額以下の場合
                amount = to_call + int(pot * 0.5) # ポットの半分を追加でレイズ
            
            if amount > my_chips:
                action = "all_in"
                amount = my_chips
                reason = f"非常に強い役（{hand_strength}）で勝率も{equity:.1%}と高いため、オールインで利益の最大化を狙います。"
            elif amount == 0 and my_chips > 0:
                action = "raise"
                amount = 10 # ミニマムベット
                reason = f"非常に強い役（{hand_strength}）で勝率も{equity:.1%}と高いため、ベットします。"

        if action == "call" and to_call >= my_chips:
            action = "all_in"
            amount = my_chips
            reason = f"コール額が残りチップ以上のため、オールインします。勝率は{equity:.1%}です。"
        
        if action == "all_in" and to_call >= my_chips:
             action = "call" # all_inではなくcallになる
             amount = my_chips
             reason = f"コール額が残りチップ以上のため、コールしてオールインします。勝率は{equity:.1%}です。"


        # 4. 結果をJSON文字列で返す
        result = {"action": action, "reason": reason}
        if action in ["raise", "all_in"]:
            # 金額は整数に丸める
            result["amount"] = int(amount)

        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        # スタックトレースも出力するとデバッグしやすい
        error_info = f"分析中に予期せぬエラーが発生しました: {e}\\n{traceback.format_exc()}"
        return f'{{"action": "error", "reason": "{error_info}"}}'