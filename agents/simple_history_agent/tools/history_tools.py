"""
Simple History Tools - 最近のハンド履歴を取得するシンプルなツール
"""

import sys
import os
from typing import Optional
import json
import glob

# プロジェクトルートをパスに追加
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.abspath(os.path.join(_current_dir, '../../..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from poker.game_history import GameHistoryDB


def _find_latest_game_db() -> Optional[str]:
    """
    db/ディレクトリから最新のgame_history_*.sqlite3ファイルを検出
    
    Returns:
        最新のデータベースファイルのパス、見つからない場合はNone
    """
    # プロジェクトルートのdb/ディレクトリを確認
    db_dir = os.path.join(_project_root, 'db')
    
    if not os.path.exists(db_dir):
        return None
    
    # game_history_*.sqlite3 パターンのファイルを検索
    pattern = os.path.join(db_dir, 'game_history_*.sqlite3')
    db_files = glob.glob(pattern)
    
    if not db_files:
        return None
    
    # 変更時刻でソートして最新のものを返す
    latest_db = max(db_files, key=os.path.getmtime)
    return latest_db


def get_recent_hands(limit: int = 5) -> str:
    """
    最近のハンド履歴を取得するツール
    
    データベースから直近のハンドを取得し、各ハンドのアクション履歴と結果を表示します。
    過去のプレイを参考にして、より良い意思決定を行うために使用できます。
    
    Args:
        limit: 取得するハンド数（デフォルト: 5）
        
    Returns:
        ハンド履歴をJSON形式の文字列で返します
        
    Example:
        >>> get_recent_hands(3)
        '[{"hand_id": 1, "timestamp": "2024-...", "actions": [...], ...}]'
    """
    try:
        # 最新のゲームデータベースを検出
        db_path = _find_latest_game_db()
        if db_path is None:
            return json.dumps({
                "error": "データベースが見つかりません",
                "message": "db/ディレクトリにgame_history_*.sqlite3ファイルが存在しません"
            }, ensure_ascii=False, indent=2)
        
        # データベースに接続
        db = GameHistoryDB(db_path=db_path)
        
        # 最近のハンドを取得
        hands = db.get_recent_hands(limit)
        
        # データベースを閉じる
        db.close()
        
        # 整形して返す
        result = {
            "database_path": db_path,
            "hands_count": len(hands),
            "hands": hands
        }

        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "error": str(e),
            "message": "ハンド履歴の取得中にエラーが発生しました"
        }, ensure_ascii=False, indent=2)

