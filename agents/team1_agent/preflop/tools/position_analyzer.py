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
        hand_class = classify_hand(hole_cards, position)
        if "error" in hand_class:
            return hand_class
        
        category_score = hand_class["category_score"]  # 0-6の整数
        category = hand_class["category"]
        
        # ポジション係数（5人プレイ用）
        position_multiplier = {
            "UTG": 1.0,      # アンダーザガン（5人では相対的に良い）
            "CO": 1.1,       # カットオフ
            "BTN": 1.2,      # ボタン - 最有利
            "SB": 1.0,       # スモールブラインド
            "BB": 1.1,       # ビッグブラインド - ディフェンス有利
        }
        
        pos_mult = position_multiplier.get(position, 0.9)
        position_adjusted_score = round(category_score * pos_mult, 1)
        
        # アクション提案（スコア0-6ベース）
        recommendation = ""
        if position_adjusted_score >= 5:
            recommendation = "レイズ or 3bet or 4bet"
        elif position_adjusted_score >= 4:
            recommendation = "レイズ or 3bet"
        elif position_adjusted_score >= 1:
            recommendation = "レイズ"
        else:
            recommendation = "フォールド推奨"
        
        return {
            "hole_cards": hole_cards,
            "position": position,
            "position_multiplier": pos_mult,
            "base_score": category_score,
            "position_adjusted_score": position_adjusted_score,
            "hand_category": category,
            "recommendation": recommendation
        }
    
    except Exception as e:
        return {"error": str(e)}
