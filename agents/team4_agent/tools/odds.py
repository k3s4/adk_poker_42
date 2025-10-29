def get_pot_odds(to_call: int, pot: int) -> float:
    """
    コールに必要なチップとポットにあるチップからポッドオッズを計算します。
    基本的にポッドオッズよりも勝率が低く見込まれる場合foldするべきです。
    Args:
        to_call (int): コールに必要なチップの数
        pot (int): 現在ポッドにあるチップの数
    Return:
        ポッドオッズを0 ~ 100%の割合として返す
    """
    return to_call / (to_call + pot) * 100
