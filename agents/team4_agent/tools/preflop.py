"""
preflop.py

テキサスホールデム・ポーカーのプリフロップ（手札2枚配布時）における、
スターティングハンドの勝率を返すツール関数を提供します。

主関数:
    preflop(your_cards: list[str], players: list[dict]) -> float

引数:
    your_cards: プレイヤーの手札2枚（例: ["A♥", "K♠"]）
    players: テーブル上のプレイヤー情報リスト（人数カウントに利用）

返り値:
    スターティングハンドの勝率（0.0〜1.0のfloat）

内部でagents/team4_agent/tools/starting_hand_dataset.pyのSTARTING_HAND_DATASETを参照し、
手札の組み合わせ・スート・人数に応じた勝率を返します。
該当データがない場合はKeyErrorを投げます。

スクリプト単体実行時は簡易テストも可能です。
"""

import sys

if __name__ == "__main__":
    # スクリプト実行時は絶対インポート
    from starting_hand_dataset import STARTING_HAND_DATASET
else:
    # パッケージとしてimportされる場合は相対インポート
    from .starting_hand_dataset import STARTING_HAND_DATASET

RANK_ORDER = ["A", "K", "Q", "J", "10", "9", "8", "7", "6", "5", "4", "3", "2"]


def preflop(your_cards: list[str], players: list[dict]) -> float:
    """
    プリフロップ（手札2枚配布時）のスターティングハンド勝率を返す。

    Returns the preflop starting hand win rate for Texas Hold'em poker.
    Uses the STARTING_HAND_DATASET to look up the win rate based on hand, suit, and player count.

    Parameters
    ----------
    your_cards : list[str]
        プレイヤーの手札2枚（例: ["A♥", "K♠"]）
    players : list[dict]
        テーブル上のプレイヤー情報リスト（人数カウントに利用）

    Returns
    -------
    float
        スターティングハンドの勝率（0.0〜1.0）

    Raises
    ------
    KeyError
        データセットに該当する勝率が存在しない場合

    Examples
    --------
    >>> preflop(["A♥", "K♠"], players)
    0.645
    """
    # 2枚のカードのランクとスートを分解
    rank1, suit1 = your_cards[0][:-1], your_cards[0][-1]
    rank2, suit2 = your_cards[1][:-1], your_cards[1][-1]
    print(rank1, suit1, rank2, suit2)
    num_players = len(players) + 1

    # ペアの場合
    if rank1 == rank2:
        return STARTING_HAND_DATASET[(rank1, rank2, "pair", num_players)]

    # ポーカーの強さ順で並べる
    if RANK_ORDER.index(rank1) < RANK_ORDER.index(rank2):
        ranks = (rank1, rank2)
    else:
        ranks = (rank2, rank1)

    # スーテッド or オフスート or combined/any
    suit_type = "suited" if suit1 == suit2 else "offsuit"
    for key_type in [suit_type, "combined", "any"]:
        key = (ranks[0], ranks[1], key_type, num_players)
        if key in STARTING_HAND_DATASET:
            return STARTING_HAND_DATASET[key]
    # 万一該当がなければKeyErrorを投げる
    raise KeyError(
        f"No winrate found for {ranks[0]}, {ranks[1]}, {suit_type}, {num_players}"
    )


if __name__ == "__main__":
    # テストケース例
    players = [{"id": 0}, {"id": 1}]
    try:
        print("A♥A♠:", preflop(["A♥", "A♠"], players))
        print("A♥K♥:", preflop(["A♥", "K♥"], players))
        print("7♣2♦:", preflop(["7♣", "2♦"], players))
        print("J♥2♥:", preflop(["2♥", "J♥"], players))
    except KeyError as e:
        print("KeyError:", e)
