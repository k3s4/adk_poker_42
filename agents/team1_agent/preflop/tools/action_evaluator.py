"""
Action Evaluator - アクション評価
"""

from typing import List, Dict, Any, Optional
from .position_analyzer import analyze_preflop_position_value


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
