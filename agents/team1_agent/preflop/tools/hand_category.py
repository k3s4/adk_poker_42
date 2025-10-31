"""
Hand Category Definitions - ハンドカテゴリー分類
"""

from enum import Enum


class HandCategory(Enum):
    """ハンドカテゴリー分類"""
    NAVY = "AA, KK, AKs, AKo, QQ"
    RED = "JJ, TT, 99, AQs, AJs, ATs, AQo,"
    YELLOW = "88, 77, KJs, QJs, JTs, AJo, KQo"
    GREEN = "66, 55, A9s, A8s, A7s, A6s, A5s, A4s, A3s, A2s, KTs, K9s, QTs,T9s, KJo, ATo"
    BLUE = "44, 33, 22, Q9s, J9s, T8s, 98s, QJo, KTo, JTo, A9o"
    WHITE = "K8s, K7s, K6s, K5s, K4s, K3s, K2s, Q8s, Q7s, Q6s, J8s, J7s, 97s, 87s, 76s, 65s, QTo, K9o, Q9o, J9o, T9o, A8o, A7o"
    GRAY = "それ以外"
