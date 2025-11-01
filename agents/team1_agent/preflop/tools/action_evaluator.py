"""
Action Evaluator - アクション評価
"""

from typing import List, Dict, Any, Optional
from .position_analyzer import analyze_preflop_position_value


def evaluate_preflop_action(
    hole_cards: List[str],
    position: str = "BTN",
    action_before_you: Optional[List[str]] = None,
    your_stack: int = 1000,
    to_call: int = 0,
    blind_size: int = 20,
    hand_classification: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    プリフロップアクションの評価（ハンドレンジに基づく）
    
    Args:
        hole_cards: ホールカード
        position: あなたのポジション
        action_before_you: これまでのアクション（例: ["UTG: fold", "MP: raise 40"]）
        your_stack: あなたのスタック
        to_call: コールに必要な金額
        blind_size: BBサイズ
    
    Returns:
        アクション提案を含む分析結果
    """
    try:
        # 既存の分類結果が与えられていればそれを利用し、再計算を避ける
        if hand_classification is not None and isinstance(hand_classification, dict):
            category_score = hand_classification.get("category_score", 0)
            position_for_calc = hand_classification.get("position", position) or position

            # ポジション係数（5人プレイ用）
            position_multiplier = {
            "UTG": 1.0,      # アンダーザガン（5人では相対的に良い）
            "CO": 1.1,       # カットオフ
            "BTN": 1.2,      # ボタン - 最有利
            "SB": 1.0,       # スモールブラインド
            "BB": 1.1,       # ビッグブラインド - ディフェンス有利
        }
            pos_mult = position_multiplier.get(position_for_calc, 0.9)
            adj_score = round(category_score * pos_mult, 1)
        else:
            position_value = analyze_preflop_position_value(hole_cards, position)
            if "error" in position_value:
                return position_value
            adj_score = position_value["position_adjusted_score"]
        
        # 先行アクション解析
        raise_count = 0
        if action_before_you:
            raise_count = sum(1 for a in action_before_you if "raise" in a.lower())
        
        # デバッグ出力
        print(f"\033[93m[EVALUATE_ACTION] adj_score: {adj_score}\033[0m")
        print(f"\033[93m[EVALUATE_ACTION] prior_raises: {raise_count}\033[0m")
        
        # 推奨アクション（スコア0-6ベース）
        action_recommendation = ""
        amount_recommendation = 0
        
        if raise_count >= 4:
            # 4回以上のレイズ → オールインかフォールドのみ
            if adj_score >= 5.5:  # 最強クラスのハンドのみ
                action_recommendation = "call"  # オールインシナリオ
                amount_recommendation = min(your_stack, to_call)
            else:
                action_recommendation = "fold"
                amount_recommendation = 0
        elif raise_count == 3:
            # 3レイズ目 → 極めて強いハンドのみ
            if adj_score >= 5.0:
                action_recommendation = "call"  # 5bet相当だがcallで応答
                amount_recommendation = min(your_stack, to_call)
            else:
                action_recommendation = "fold"
                amount_recommendation = 0
        elif raise_count == 2:
            # 2レイズ目 → 強いハンドのみ
            if adj_score >= 5.0:
                action_recommendation = "4bet"
                amount_recommendation = min(blind_size * 10, your_stack)
            else:
                action_recommendation = "fold"
                amount_recommendation = 0
        elif raise_count == 1:
            # 1レイズ入っている
            if adj_score >= 3.5:
                action_recommendation = "3bet"
                amount_recommendation = blind_size * 3
            elif adj_score >= 1:
                action_recommendation = "call"
                amount_recommendation = to_call
            else:
                action_recommendation = "fold"
                amount_recommendation = 0
        else:
            # オープンポット
            if adj_score >= 1:
                action_recommendation = "raise"
                amount_recommendation = blind_size * 3
            else:
                action_recommendation = "fold"
                amount_recommendation = 0
        
        # 推奨結果の出力
        print(f"\033[93m[EVALUATE_ACTION] recommended_action: {action_recommendation}\033[0m")
        print(f"\033[93m[EVALUATE_ACTION] recommended_amount: {round(amount_recommendation)}\033[0m")

        return {
            "hole_cards": hole_cards,
            "position": position,
            "strength_score": adj_score,
            "prior_raises": raise_count,
            "to_call": to_call,
            "your_stack": your_stack,
            "recommended_action": action_recommendation,
            "recommended_amount": round(amount_recommendation),
        }
    
    except Exception as e:
        return {"error": str(e)}
