"""
Hand Category Definitions - ハンドカテゴリー分類
"""

from enum import Enum


class HandCategory(Enum):
    """ハンドカテゴリー分類"""
    NAVY = "AA, KK, AKs, AKo, QQ" # 5 hands
    RED = "JJ, TT, 99, AQs, AJs, ATs, KQs, AQo, KQo, AJo" # 9 hands
    YELLOW = "88, 77, KJs, QJs, JTs, ATo, KTs, A9s, A8s" # 9 hands
    GREEN = "66, 55, A7s, A6s, A5s, A4s, A3s, A2s, K9s, QTs, T9s, KJo" # 12 hands
    BLUE = "44, 33, 22, Q9s, J9s, T8s, 98s, QJo, KTo, JTo, A9o, QTo, K8s" # 13 hands
    WHITE = "K7s, K6s, K5s, K4s, K3s, K2s, Q8s, Q7s, Q6s, J8s, J7s, 97s, 87s, 76s, 65s, K9o, Q9o, J9o, T9o, A8o, K8o, A7o, A6o, A5o, A4o, A3o, A2o, T8o, 98o, Q5s, Q4s, Q3s, Q2s, J6s, T7s, 96s, 86s, 75s, 64s, 54s" # 40 hands
    GRAY = "それ以外"
