"""
Hand Classifier Tool - ハンド分類
"""

from typing import List, Dict, Any
from .hand_category import HandCategory


def _convert_to_hand_notation(hole_cards: List[str]) -> str:
    """
    ホールカードを標準形式に変換
    
    Args:
        hole_cards: ホールカード2枚（例: ["A♥", "K♠"]）
    
    Returns:
        標準形式の手表記（例: "AKo", "AKs", "AA"）
    """
    card1_str, card2_str = hole_cards

    # 前後の空白を除去
    card1_str = card1_str.strip()
    card2_str = card2_str.strip()

    # ランクを抽出（末尾のスート記号を除いた全体）
    # 例: "10♣" -> "10", "K♠" -> "K"
    rank1_raw = card1_str[:-1].upper()
    rank2_raw = card2_str[:-1].upper()

    # '10' を 'T' に正規化（'Td' などの表記も受け入れ）
    rank1 = "T" if rank1_raw == "10" else rank1_raw
    rank2 = "T" if rank2_raw == "10" else rank2_raw

    # スーツを抽出（最後の文字: unicode/英字どちらでも比較は等価性のみで十分）
    suit1 = card1_str[-1]
    suit2 = card2_str[-1]

    # ポーカーランク強度マップ（'T' を正しく扱う）
    rank_strength = {
        "A": 14, "K": 13, "Q": 12, "J": 11, "T": 10,
        "9": 9, "8": 8, "7": 7, "6": 6, "5": 5, "4": 4, "3": 3, "2": 2,
    }
    
    # ホールカードを標準形式に変換
    # 例: ["A♥", "K♠"] → "AKo", ["A♥", "K♥"] → "AKs", ["A♥", "A♠"] → "AA"
    if rank1 == rank2:
        # ペア
        return f"{rank1}{rank2}"
    else:
        # ポーカーの強さが高い順にソート
        rank1_strength = rank_strength.get(rank1, 0)
        rank2_strength = rank_strength.get(rank2, 0)
        
        if rank1_strength < rank2_strength:
            rank1, rank2 = rank2, rank1
        
        # スーテッド判定
        suited_suffix = "s" if suit1 == suit2 else "o"
        return f"{rank1}{rank2}{suited_suffix}"


def classify_hand(hole_cards: List[str], position: str) -> Dict[str, Any]:
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
            "category_score": 0,
            "position": position
        }
    
    try:
        # ホールカードを標準形式に変換
        hand_notation = _convert_to_hand_notation(hole_cards)
        
        print(f"\033[93m[DEBUG] hand_notation: {hand_notation}\033[0m")
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
        for category in HandCategory:
            score = category_score_map[category]
            # カテゴリの値文字列に手が含まれているかチェック
            if hand_notation in category.value.replace(" ", ""):
                print(f"\033[93m[DEBUG] hole_cards: {hole_cards}\033[0m")
                print(f"\033[93m[DEBUG] category: {category.value}\033[0m")
                print(f"\033[93m[DEBUG] category_score: {score}\033[0m")
                return {
                    "hole_cards": hole_cards,
                    "category": category.value,
                    "category_score": score,
                    "position": position
                }
        
        # どのカテゴリにも含まれなかったらGRAY
        return {
            "hole_cards": hole_cards,
            "category": HandCategory.GRAY.value,
            "category_score": 0,
            "position": position
        }
    
    except Exception as e:
        return {"error": str(e), "category": "不明", "category_score": 0, "position": position}
