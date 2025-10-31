"""
Preflop Strategy Analysis Tools - pockerkitを使用したプリフロップ分析
"""

import sys
import os
import json
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

# プロジェクトルートをパスに追加
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.abspath(os.path.join(_current_dir, '../../..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

try:
    import pokerkit
    from pokerkit import State, Card
    POKERKIT_AVAILABLE = True
except ImportError:
    POKERKIT_AVAILABLE = False


class HandCategory(Enum):
    """ハンドカテゴリー分類"""
    PREMIUM = "プレミアム（AA, KK, QQ, AK）"
    STRONG = "ストロング（JJ, TT, AQ, AJs）"
    GOOD = "グッド（99, 88, KQ, KJs）"
    MARGINAL = "マージナル（77, 66, QJ, QJs）"
    WEAK = "ウィーク（その他）"


def _parse_card(card_str: str) -> Optional[Card]:
    """
    カード文字列をpokerkitのCardオブジェクトに変換
    例: "A♥" → Card(...)
    """
    if not POKERKIT_AVAILABLE:
        return None
    
    try:
        # "A♥" や "As" 形式に対応
        card_str = card_str.strip()
        
        # ランクの抽出
        rank_map = {
            "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
            "T": 10, "10": 10,
            "J": 11, "Q": 12, "K": 13, "A": 14
        }
        
        # スーツの抽出
        suit_map = {
            "♠": "s", "s": "s",
            "♥": "h", "h": "h",
            "♦": "d", "d": "d",
            "♣": "c", "c": "c"
        }
        
        # Unicode スーツを検出
        suit = None
        rank_part = card_str
        for unicode_suit, ascii_suit in suit_map.items():
            if unicode_suit in card_str:
                suit = ascii_suit
                rank_part = card_str.replace(unicode_suit, "")
                break
        
        # Unicode スーツが見つからない場合は末尾から抽出
        if suit is None and len(card_str) >= 2:
            last_char = card_str[-1].lower()
            if last_char in ["s", "h", "d", "c"]:
                suit = last_char
                rank_part = card_str[:-1]
        
        rank = rank_map.get(rank_part.upper())
        
        if rank is None or suit is None:
            return None
        
        # pokerkitのCard形式: "As", "Kh", "Qd", "Jc" など
        card_notation = f"{pokerkit.RANK_STRINGS[rank - 2]}{suit}"
        return Card(card_notation)
    
    except Exception:
        return None


def classify_hand(hole_cards: List[str]) -> Dict[str, Any]:
    """
    ハンドをカテゴリーで分類する
    
    Args:
        hole_cards: ホールカード2枚（例: ["A♥", "K♠"]）
    
    Returns:
        分類結果のdict
    """
    if len(hole_cards) != 2:
        return {
            "error": "ホールカードは2枚である必要があります",
            "category": "不明",
            "strength_score": 0
        }
    
    try:
        card1_str, card2_str = hole_cards
        # ランクを抽出（簡易的に）
        rank1_map = {"A": 14, "K": 13, "Q": 12, "J": 11, "T": 10,
                     "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9}
        rank2_map = rank1_map.copy()
        
        r1_str = card1_str[0].upper()
        r2_str = card2_str[0].upper()
        
        rank1 = rank1_map.get(r1_str)
        rank2 = rank2_map.get(r2_str)
        
        if rank1 is None or rank2 is None:
            return {"error": "カード解析失敗", "category": "不明", "strength_score": 0}
        
        is_suited = card1_str[-1] == card2_str[-1]  # 同じスーツ記号
        
        # ペアの判定
        if rank1 == rank2:
            pair_rank = rank1
            if pair_rank >= 13:  # AA, KK
                category = HandCategory.PREMIUM
                strength_score = 0.95
            elif pair_rank >= 11:  # QQ, JJ
                category = HandCategory.STRONG
                strength_score = 0.85
            elif pair_rank >= 9:  # TT, 99
                category = HandCategory.GOOD
                strength_score = 0.70
            elif pair_rank >= 7:  # 88, 77
                category = HandCategory.MARGINAL
                strength_score = 0.60
            else:  # 66 以下
                category = HandCategory.WEAK
                strength_score = 0.40
        else:
            # ペア以外
            high_rank = max(rank1, rank2)
            low_rank = min(rank1, rank2)
            gap = high_rank - low_rank
            
            # AK
            if high_rank == 14 and low_rank == 13:
                category = HandCategory.PREMIUM if is_suited else HandCategory.STRONG
                strength_score = 0.90 if is_suited else 0.88
            # AQ
            elif high_rank == 14 and low_rank == 12:
                category = HandCategory.STRONG if is_suited else HandCategory.GOOD
                strength_score = 0.80 if is_suited else 0.75
            # KQ
            elif high_rank == 13 and low_rank == 12:
                category = HandCategory.GOOD
                strength_score = 0.70 if is_suited else 0.65
            # KJ, K9以上
            elif high_rank == 13:
                category = HandCategory.GOOD if is_suited else HandCategory.MARGINAL
                strength_score = 0.65 if is_suited else 0.50
            # QJ
            elif high_rank == 12 and low_rank == 11:
                category = HandCategory.GOOD
                strength_score = 0.65 if is_suited else 0.58
            # コネクタ・ギャップが小さい
            elif gap <= 2 and high_rank >= 9:
                category = HandCategory.MARGINAL
                strength_score = 0.55 if is_suited else 0.45
            else:
                category = HandCategory.WEAK
                strength_score = 0.35
        
        return {
            "hole_cards": hole_cards,
            "category": category.value,
            "strength_score": round(strength_score, 2),
            "is_paired": rank1 == rank2,
            "is_suited": is_suited,
            "gap": abs(rank1 - rank2) if rank1 != rank2 else 0
        }
    
    except Exception as e:
        return {"error": str(e), "category": "不明", "strength_score": 0}


def analyze_preflop_position_value(
    hole_cards: List[str],
    position: str = "BTN",
    players_count: int = 6,
    stack_depth: float = 100.0,
) -> Dict[str, Any]:
    """
    ポジションに基づくプリフロップ値を分析
    
    Args:
        hole_cards: ホールカード（例: ["A♥", "K♠"]）
        position: ポジション（UTG, MP, CO, BTN, SB, BB）
        players_count: テーブルのプレイヤー数（デフォルト: 6）
        stack_depth: BBに対するスタック深さ（デフォルト: 100）
    
    Returns:
        分析結果のdict
    """
    try:
        hand_class = classify_hand(hole_cards)
        if "error" in hand_class:
            return hand_class
        
        strength_score = hand_class["strength_score"]
        category = hand_class["category"]
        
        # ポジション係数
        position_multiplier = {
            "UTG": 0.7,      # 最初のポジション - 厳しい
            "MP": 0.8,       # ミドルポジション
            "CO": 0.9,       # カットオフ
            "BTN": 1.0,      # ボタン - 最有利
            "SB": 0.85,      # スモールブラインド
            "BB": 1.1,       # ビッグブラインド - ディフェンス有利
        }
        
        pos_mult = position_multiplier.get(position, 0.9)
        position_adjusted_score = round(strength_score * pos_mult, 2)
        
        # スタック深さによる調整
        deep_stack_bonus = 0
        if stack_depth > 150:
            deep_stack_bonus = 0.1  # 深いスタックはコネクタなどが価値UP
        
        # アクション提案
        recommendation = ""
        if position_adjusted_score >= 0.85:
            recommendation = "レイズ推奨"
        elif position_adjusted_score >= 0.65:
            recommendation = "コール or レイズ"
        elif position_adjusted_score >= 0.45:
            recommendation = "フォルド or コール（位置による）"
        else:
            recommendation = "フォルド推奨"
        
        return {
            "hole_cards": hole_cards,
            "position": position,
            "position_multiplier": pos_mult,
            "base_strength": strength_score,
            "position_adjusted_score": position_adjusted_score,
            "hand_category": category,
            "stack_depth": stack_depth,
            "players_count": players_count,
            "recommendation": recommendation,
            "notes": "ポジション調整済みの強度スコア（0-1）"
        }
    
    except Exception as e:
        return {"error": str(e)}


def evaluate_preflop_action(
    hole_cards: List[str],
    position: str = "BTN",
    action_before_you: Optional[List[str]] = None,
    pot_size: int = 30,
    your_stack: int = 1000,
    to_call: int = 0,
    blind_size: int = 20,
) -> Dict[str, Any]:
    """
    プリフロップアクションの評価（ハンドレンジに基づく）
    
    Args:
        hole_cards: ホールカード
        position: あなたのポジション
        action_before_you: これまでのアクション（例: ["UTG: fold", "MP: raise 40"]）
        pot_size: 現在のポット
        your_stack: あなたのスタック
        to_call: コールに必要な金額
        blind_size: BBサイズ
    
    Returns:
        アクション提案を含む分析結果
    """
    try:
        position_value = analyze_preflop_position_value(hole_cards, position)
        if "error" in position_value:
            return position_value
        
        adj_score = position_value["position_adjusted_score"]
        
        # 先行アクション解析
        raise_count = 0
        if action_before_you:
            raise_count = sum(1 for a in action_before_you if "raise" in a.lower())
        
        # ポットオッズ計算
        pot_odds = 0.0
        if to_call > 0:
            pot_odds = round(to_call / (pot_size + to_call), 2)
        
        # 推奨アクション
        action_recommendation = ""
        amount_recommendation = 0
        
        if raise_count >= 2:
            # 複数のレイズ → 強いハンドのみ
            if adj_score >= 0.80:
                action_recommendation = "4bet"
                amount_recommendation = max(blind_size * 8, to_call * 3) if to_call > 0 else blind_size * 8
            else:
                action_recommendation = "fold"
                amount_recommendation = 0
        elif raise_count == 1:
            # 1レイズ入っている
            if adj_score >= 0.70:
                action_recommendation = "call or 3bet"
                amount_recommendation = to_call if to_call > 0 else 0
            else:
                action_recommendation = "fold"
                amount_recommendation = 0
        else:
            # オープンポット
            if adj_score >= 0.75:
                action_recommendation = "raise"
                amount_recommendation = blind_size * 2.5
            elif adj_score >= 0.60:
                action_recommendation = "call"
                amount_recommendation = to_call if to_call > 0 else 0
            else:
                action_recommendation = "fold"
                amount_recommendation = 0
        
        return {
            "hole_cards": hole_cards,
            "position": position,
            "strength_score": adj_score,
            "prior_raises": raise_count,
            "pot_odds": pot_odds,
            "to_call": to_call,
            "your_stack": your_stack,
            "recommended_action": action_recommendation,
            "recommended_amount": round(amount_recommendation),
            "reasoning": f"ハンド強度{adj_score} + ポットオッズ{pot_odds} + 先行レイズ{raise_count}を総合判断"
        }
    
    except Exception as e:
        return {"error": str(e)}
