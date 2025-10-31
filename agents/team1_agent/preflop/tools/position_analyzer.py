"""
Position Value Analyzer - ポジション価値分析
"""

from typing import List, Dict, Any
from .hand_classifier import classify_hand


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
