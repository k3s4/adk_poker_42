"""
Preflop Strategy Analysis Tools - プリフロップ分析
"""

import sys
import os
from typing import List, Dict, Any, Optional
from enum import Enum

# プロジェクトルートをパスに追加
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.abspath(os.path.join(_current_dir, '../../..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


class HandCategory(Enum):
    """ハンドカテゴリー分類"""
    NAVY = "AA, KK, AKs, AKo, QQ"
    RED = "JJ, TT, 99, AQs, AJs, ATs, AQo,"
    YELLOW = "88, 77, KJs, QJs, JTs, AJo, KQo"
    GREEN = "66, 55, A9s, A8s, A7s, A6s, A5s, A4s, A3s, A2s, KTs, K9s, QTs,T9s, KJo, ATo"
    BLUE = "44, 33, 22, Q9s, J9s, T8s, 98s, QJo, KTo, A9o"
    WHITE = "K8s, K7s, K6s, K5s, K4s, K3s, K2s, Q8s, Q7s, Q6s, J8s, J7s, 97s, 87s, 76s, 65s, QTo, K9o, Q9o, J9o, T9o, A8o, A7o"
    GRAY = "それ以外"


def classify_hand(hole_cards: List[str]) -> Dict[str, Any]:
    """
    ハンドをカテゴリーで分類し、スコア(0-6)を返す
    
    Args:
        hole_cards: ホールカード2枚（例: ["A♥", "K♠"]）
    
    Returns:
        分類結果のdict（category_scoreは0-6の整数）
    """
    if len(hole_cards) != 2:
        return {
            "error": "ホールカードは2枚である必要があります",
            "category": "不明",
            "category_score": 0
        }
    
    try:
        card1_str, card2_str = hole_cards
        
        # ランクを抽出（最初の文字）
        rank1 = card1_str[0].upper()
        rank2 = card2_str[0].upper()
        
        # スーツを抽出（最後の文字）
        suit1 = card1_str[-1]
        suit2 = card2_str[-1]
        
        # ホールカードを標準形式に変換
        # 例: ["A♥", "K♠"] → "AKo", ["A♥", "K♥"] → "AKs", ["A♥", "A♠"] → "AA"
        if rank1 == rank2:
            # ペア
            hand_notation = f"{rank1}{rank2}"
        else:
            # 高いランクを先に
            if ord(rank1) < ord(rank2):
                rank1, rank2 = rank2, rank1
            
            # スーテッド判定
            suited_suffix = "s" if suit1 == suit2 else "o"
            hand_notation = f"{rank1}{rank2}{suited_suffix}"
        
        # カテゴリ→スコアマッピング
        category_score_map = {
            HandCategory.NAVY: 6,
            HandCategory.RED: 5,
            HandCategory.YELLOW: 4,
            HandCategory.GREEN: 3,
            HandCategory.BLUE: 2,
            HandCategory.WHITE: 1,
            HandCategory.GRAY: 0,
        }
        
        # HandCategoryから手を探す
        for category, score in category_score_map.items():
            # カテゴリの値文字列に手が含まれているかチェック
            if hand_notation in category.value.replace(" ", ""):
                return {
                    "hole_cards": hole_cards,
                    "category": category.value,
                    "category_score": score,
                }
        
        # どのカテゴリにも含まれなかったらGRAY
        return {
            "hole_cards": hole_cards,
            "category": HandCategory.GRAY.value,
            "category_score": 0,
        }
    
    except Exception as e:
        return {"error": str(e), "category": "不明", "category_score": 0}


def analyze_preflop_position_value(
    hole_cards: List[str],
    position: str = "BTN",
) -> Dict[str, Any]:
    """
    ポジションに基づくプリフロップ値を分析
    
    Args:
        hole_cards: ホールカード（例: ["A♥", "K♠"]）
        position: ポジション（UTG, MP, CO, BTN, SB, BB）
    
    Returns:
        分析結果のdict
    """
    try:
        hand_class = classify_hand(hole_cards)
        if "error" in hand_class:
            return hand_class
        
        category_score = hand_class["category_score"]  # 0-6の整数
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
        position_adjusted_score = round(category_score * pos_mult, 1)
        
        # アクション提案（スコア0-6ベース）
        recommendation = ""
        if position_adjusted_score >= 5:
            recommendation = "レイズ推奨"
        elif position_adjusted_score >= 3:
            recommendation = "コール or レイズ"
        elif position_adjusted_score >= 1.5:
            recommendation = "フォルド or コール（位置による）"
        else:
            recommendation = "フォルド推奨"
        
        return {
            "hole_cards": hole_cards,
            "position": position,
            "position_multiplier": pos_mult,
            "base_score": category_score,
            "position_adjusted_score": position_adjusted_score,
            "hand_category": category,
            "recommendation": recommendation,
            "notes": "ポジション調整済みのスコア（0-6ベース）"
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
        
        # 推奨アクション（スコア0-6ベース）
        action_recommendation = ""
        amount_recommendation = 0
        
        if raise_count >= 2:
            # 複数のレイズ → 強いハンドのみ
            if adj_score >= 5:
                action_recommendation = "4bet"
                amount_recommendation = max(blind_size * 8, to_call * 3) if to_call > 0 else blind_size * 8
            else:
                action_recommendation = "fold"
                amount_recommendation = 0
        elif raise_count == 1:
            # 1レイズ入っている
            if adj_score >= 4:
                action_recommendation = "call or 3bet"
                amount_recommendation = to_call if to_call > 0 else 0
            else:
                action_recommendation = "fold"
                amount_recommendation = 0
        else:
            # オープンポット
            if adj_score >= 4.5:
                action_recommendation = "raise"
                amount_recommendation = blind_size * 2.5
            elif adj_score >= 3:
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
