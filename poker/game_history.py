"""
Poker Game History Database Module

このモジュールはポーカーゲームの履歴を記録・取得するためのデータベース機能を提供します。
公開情報のみを記録し、プライバシーを保護します。
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path


class GameHistoryDB:
    """ゲーム履歴を管理するデータベースクラス"""

    def __init__(self, db_path: str = None, uuid_suffix: str = None):
        """
        データベース接続を初期化

        Args:
            db_path: データベースファイルのパス（Noneの場合はタイムスタンプ+UUID付きで自動作成）
            uuid_suffix: 統一UUID（Noneの場合は新規生成）
        """
        if db_path is None:
            db_path = self._generate_unique_db_path(uuid_suffix)
        
        # ディレクトリが存在しない場合は作成
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _generate_unique_db_path(self, uuid_suffix: str = None) -> str:
        """タイムスタンプとUUID付きのユニークなデータベースファイルパスを生成"""
        import uuid
        from datetime import datetime
        
        # タイムスタンプとUUIDを生成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if uuid_suffix is None:
            uuid_suffix = str(uuid.uuid4())[:4]  # 4桁のUUID
        
        # ファイル名を生成
        filename = f"game_history_{timestamp}_{uuid_suffix}.sqlite3"
        return os.path.join("db", filename)

    def _create_tables(self):
        """必要なテーブルを作成"""
        cursor = self.conn.cursor()

        # ハンド情報テーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hands (
                hand_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                small_blind INTEGER NOT NULL,
                big_blind INTEGER NOT NULL,
                dealer_button INTEGER NOT NULL,
                player_ids TEXT NOT NULL,
                ended_at TEXT
            )
        """)

        # アクション履歴テーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS actions (
                action_id INTEGER PRIMARY KEY AUTOINCREMENT,
                hand_id INTEGER NOT NULL,
                phase TEXT NOT NULL,
                player_id INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                amount INTEGER NOT NULL DEFAULT 0,
                pot_after INTEGER NOT NULL DEFAULT 0,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (hand_id) REFERENCES hands (hand_id)
            )
        """)

        # コミュニティカードテーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS community_cards (
                hand_id INTEGER NOT NULL,
                phase TEXT NOT NULL,
                cards TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (hand_id) REFERENCES hands (hand_id),
                PRIMARY KEY (hand_id, phase)
            )
        """)

        # ショーダウン結果テーブル（公開されたカードのみ）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS showdown_results (
                hand_id INTEGER NOT NULL,
                player_id INTEGER NOT NULL,
                hole_cards TEXT,
                hand_rank TEXT,
                winnings INTEGER NOT NULL DEFAULT 0,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (hand_id) REFERENCES hands (hand_id),
                PRIMARY KEY (hand_id, player_id)
            )
        """)

        # インデックスの作成
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_actions_hand_id 
            ON actions(hand_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_actions_player_id 
            ON actions(player_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_showdown_player_id 
            ON showdown_results(player_id)
        """)

        self.conn.commit()

    def start_new_hand(
        self,
        small_blind: int,
        big_blind: int,
        dealer_button: int,
        player_ids: List[int],
    ) -> int:
        """
        新しいハンドを開始し、hand_idを返す

        Args:
            small_blind: スモールブラインド額
            big_blind: ビッグブラインド額
            dealer_button: ディーラーボタンの位置
            player_ids: 参加プレイヤーのIDリスト

        Returns:
            新しく作成されたhand_id
        """
        cursor = self.conn.cursor()
        timestamp = datetime.now().isoformat()
        player_ids_json = json.dumps(player_ids, ensure_ascii=False)

        cursor.execute(
            """
            INSERT INTO hands (timestamp, small_blind, big_blind, dealer_button, player_ids)
            VALUES (?, ?, ?, ?, ?)
        """,
            (timestamp, small_blind, big_blind, dealer_button, player_ids_json),
        )

        self.conn.commit()
        return cursor.lastrowid

    def record_action(
        self,
        hand_id: int,
        phase: str,
        player_id: int,
        action_type: str,
        amount: int = 0,
        pot_after: int = 0,
    ):
        """
        プレイヤーのアクションを記録

        Args:
            hand_id: ハンドID
            phase: ゲームフェーズ（preflop, flop, turn, river）
            player_id: プレイヤーID
            action_type: アクション種別（fold, check, call, raise, all_in, small_blind, big_blind）
            amount: ベット額
            pot_after: アクション後のポット額
        """
        cursor = self.conn.cursor()
        timestamp = datetime.now().isoformat()

        cursor.execute(
            """
            INSERT INTO actions (hand_id, phase, player_id, action_type, amount, pot_after, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (hand_id, phase, player_id, action_type, amount, pot_after, timestamp),
        )

        self.conn.commit()

    def record_community_cards(self, hand_id: int, phase: str, cards: List[str]):
        """
        コミュニティカードを記録

        Args:
            hand_id: ハンドID
            phase: フェーズ（flop, turn, river）
            cards: カードのリスト（例: ["A♠", "K♥", "Q♣"]）
        """
        cursor = self.conn.cursor()
        timestamp = datetime.now().isoformat()
        cards_json = json.dumps(cards, ensure_ascii=False)

        cursor.execute(
            """
            INSERT OR REPLACE INTO community_cards (hand_id, phase, cards, timestamp)
            VALUES (?, ?, ?, ?)
        """,
            (hand_id, phase, cards_json, timestamp),
        )

        self.conn.commit()

    def record_showdown(
        self,
        hand_id: int,
        player_id: int,
        hole_cards: Optional[List[str]],
        hand_rank: Optional[str],
        winnings: int,
    ):
        """
        ショーダウン結果を記録（公開されたカードのみ）

        Args:
            hand_id: ハンドID
            player_id: プレイヤーID
            hole_cards: ホールカード（ショーダウンで公開された場合のみ）
            hand_rank: 役の強さ（例: "Pair of Aces"）
            winnings: 獲得チップ数
        """
        cursor = self.conn.cursor()
        timestamp = datetime.now().isoformat()
        hole_cards_json = json.dumps(hole_cards, ensure_ascii=False) if hole_cards else None

        cursor.execute(
            """
            INSERT OR REPLACE INTO showdown_results 
            (hand_id, player_id, hole_cards, hand_rank, winnings, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (hand_id, player_id, hole_cards_json, hand_rank, winnings, timestamp),
        )

        self.conn.commit()

    def end_hand(self, hand_id: int):
        """
        ハンドの終了を記録

        Args:
            hand_id: ハンドID
        """
        cursor = self.conn.cursor()
        ended_at = datetime.now().isoformat()

        cursor.execute(
            """
            UPDATE hands SET ended_at = ? WHERE hand_id = ?
        """,
            (ended_at, hand_id),
        )

        self.conn.commit()

    def get_hand_history(self, hand_id: int) -> Optional[Dict[str, Any]]:
        """
        特定ハンドの完全な履歴を取得

        Args:
            hand_id: ハンドID

        Returns:
            ハンド情報の辞書、存在しない場合はNone
        """
        cursor = self.conn.cursor()

        # ハンド基本情報
        cursor.execute("SELECT * FROM hands WHERE hand_id = ?", (hand_id,))
        hand_row = cursor.fetchone()

        if not hand_row:
            return None

        hand_data = dict(hand_row)
        hand_data["player_ids"] = json.loads(hand_data["player_ids"])

        # アクション履歴
        cursor.execute(
            """
            SELECT * FROM actions 
            WHERE hand_id = ? 
            ORDER BY action_id
        """,
            (hand_id,),
        )
        hand_data["actions"] = [dict(row) for row in cursor.fetchall()]

        # コミュニティカード
        cursor.execute(
            """
            SELECT phase, cards FROM community_cards 
            WHERE hand_id = ?
        """,
            (hand_id,),
        )
        community_cards = {}
        for row in cursor.fetchall():
            community_cards[row["phase"]] = json.loads(row["cards"])
        hand_data["community_cards"] = community_cards

        # ショーダウン結果
        cursor.execute(
            """
            SELECT * FROM showdown_results 
            WHERE hand_id = ?
        """,
            (hand_id,),
        )
        showdown_results = []
        for row in cursor.fetchall():
            result = dict(row)
            if result["hole_cards"]:
                result["hole_cards"] = json.loads(result["hole_cards"])
            showdown_results.append(result)
        hand_data["showdown_results"] = showdown_results

        return hand_data

    def get_recent_hands(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        直近のハンド履歴を取得

        Args:
            limit: 取得する件数

        Returns:
            ハンド情報のリスト
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT hand_id FROM hands 
            ORDER BY hand_id DESC 
            LIMIT ?
        """,
            (limit,),
        )

        hand_ids = [row["hand_id"] for row in cursor.fetchall()]
        return [self.get_hand_history(hand_id) for hand_id in hand_ids]

    def get_player_action_stats(self, player_id: int) -> Dict[str, Any]:
        """
        プレイヤーのアクション統計を取得

        Args:
            player_id: プレイヤーID

        Returns:
            統計情報の辞書
        """
        cursor = self.conn.cursor()

        # 総アクション数
        cursor.execute(
            """
            SELECT action_type, COUNT(*) as count
            FROM actions
            WHERE player_id = ?
            GROUP BY action_type
        """,
            (player_id,),
        )
        action_counts = {row["action_type"]: row["count"] for row in cursor.fetchall()}

        # 参加ハンド数
        cursor.execute(
            """
            SELECT COUNT(DISTINCT hand_id) as hand_count
            FROM actions
            WHERE player_id = ?
        """,
            (player_id,),
        )
        hand_count = cursor.fetchone()["hand_count"]

        # ショーダウン統計
        cursor.execute(
            """
            SELECT 
                COUNT(*) as showdowns,
                SUM(CASE WHEN winnings > 0 THEN 1 ELSE 0 END) as wins,
                SUM(winnings) as total_winnings
            FROM showdown_results
            WHERE player_id = ?
        """,
            (player_id,),
        )
        showdown_row = cursor.fetchone()

        return {
            "player_id": player_id,
            "hands_played": hand_count,
            "action_counts": action_counts,
            "showdowns": showdown_row["showdowns"] or 0,
            "showdown_wins": showdown_row["wins"] or 0,
            "total_winnings": showdown_row["total_winnings"] or 0,
        }

    def get_player_recent_actions(
        self, player_id: int, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        プレイヤーの最近のアクションを取得

        Args:
            player_id: プレイヤーID
            limit: 取得する件数

        Returns:
            アクション履歴のリスト
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM actions
            WHERE player_id = ?
            ORDER BY action_id DESC
            LIMIT ?
        """,
            (player_id, limit),
        )

        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        """データベース接続を閉じる"""
        self.conn.close()


# エージェント向けグローバルAPI関数
_db_instance: Optional[GameHistoryDB] = None


def _get_db() -> GameHistoryDB:
    """データベースインスタンスを取得（シングルトン）"""
    global _db_instance
    if _db_instance is None:
        _db_instance = GameHistoryDB()
    return _db_instance


def get_game_history(
    hand_id: Optional[int] = None,
    player_id: Optional[int] = None,
    limit: int = 10,
) -> Dict[str, Any]:
    """
    ゲーム履歴を取得するエージェント向けAPI

    Args:
        hand_id: 特定のハンドIDを指定（指定した場合はそのハンドの詳細を返す）
        player_id: プレイヤーID（指定した場合はそのプレイヤーの統計を含む）
        limit: 取得する件数（hand_idが未指定の場合）

    Returns:
        履歴情報の辞書
    """
    db = _get_db()

    result = {}

    if hand_id is not None:
        # 特定ハンドの詳細を取得
        result["hand"] = db.get_hand_history(hand_id)
    else:
        # 直近のハンドを取得
        result["recent_hands"] = db.get_recent_hands(limit)

    if player_id is not None:
        # プレイヤー統計を取得
        result["player_stats"] = db.get_player_action_stats(player_id)
        result["recent_actions"] = db.get_player_recent_actions(player_id, limit)

    return result


def get_opponent_stats(opponent_ids: List[int]) -> Dict[int, Dict[str, Any]]:
    """
    複数の相手プレイヤーの統計を一括取得

    Args:
        opponent_ids: 相手プレイヤーIDのリスト

    Returns:
        プレイヤーIDをキーとした統計情報の辞書
    """
    db = _get_db()
    return {
        player_id: db.get_player_action_stats(player_id) for player_id in opponent_ids
    }


def get_last_hand_id() -> Optional[int]:
    """
    最新のハンドIDを取得

    Returns:
        最新のハンドID、存在しない場合はNone
    """
    db = _get_db()
    cursor = db.conn.cursor()
    cursor.execute("SELECT MAX(hand_id) as max_id FROM hands")
    row = cursor.fetchone()
    return row["max_id"] if row["max_id"] else None

