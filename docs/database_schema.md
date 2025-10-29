# Poker Game History Database Schema

## 概要

このドキュメントは、ポーカーゲームの履歴を記録するSQLiteデータベースのスキーマと使用方法について説明します。

## データベースの場所

- **パス**: `db/game_history.sqlite3`
- **タイプ**: SQLite3

## プライバシーポリシー

このデータベースは**公開情報のみ**を記録します：

✅ **記録される情報**:
- 全プレイヤーのアクション（フォールド、チェック、コール、レイズ、オールイン）
- ベット額とポット額
- コミュニティカード（フロップ、ターン、リバー）
- ショーダウンに到達したプレイヤーのホールカード
- 勝者と獲得チップ数

❌ **記録されない情報**:
- ショーダウンに至らずフォールドしたプレイヤーのホールカード

## テーブルスキーマ

### 1. `hands` テーブル

各ハンドの基本情報を記録します。

| カラム名 | 型 | 説明 |
|---------|------|------|
| `hand_id` | INTEGER PRIMARY KEY | ハンドの一意識別子（自動採番） |
| `timestamp` | TEXT | ハンド開始時刻（ISO 8601形式） |
| `small_blind` | INTEGER | スモールブラインド額 |
| `big_blind` | INTEGER | ビッグブラインド額 |
| `dealer_button` | INTEGER | ディーラーボタンの位置（プレイヤーID） |
| `player_ids` | TEXT | 参加プレイヤーIDのJSON配列 |
| `ended_at` | TEXT | ハンド終了時刻（ISO 8601形式） |

### 2. `actions` テーブル

プレイヤーの全アクションを時系列で記録します。

| カラム名 | 型 | 説明 |
|---------|------|------|
| `action_id` | INTEGER PRIMARY KEY | アクションの一意識別子（自動採番） |
| `hand_id` | INTEGER | ハンドID（外部キー） |
| `phase` | TEXT | ゲームフェーズ（preflop/flop/turn/river） |
| `player_id` | INTEGER | アクションを実行したプレイヤーID |
| `action_type` | TEXT | アクション種別（fold/check/call/raise/all_in/small_blind/big_blind） |
| `amount` | INTEGER | ベット額（フォールド・チェックは0） |
| `pot_after` | INTEGER | アクション後のポット総額 |
| `timestamp` | TEXT | アクション実行時刻（ISO 8601形式） |

**インデックス**:
- `idx_actions_hand_id` on `hand_id`
- `idx_actions_player_id` on `player_id`

### 3. `community_cards` テーブル

各フェーズで配られたコミュニティカードを記録します。

| カラム名 | 型 | 説明 |
|---------|------|------|
| `hand_id` | INTEGER | ハンドID（外部キー） |
| `phase` | TEXT | フェーズ（flop/turn/river） |
| `cards` | TEXT | カードのJSON配列（例: `["A♠", "K♥", "Q♣"]`） |
| `timestamp` | TEXT | 配布時刻（ISO 8601形式） |

**主キー**: `(hand_id, phase)`

### 4. `showdown_results` テーブル

ショーダウンに到達したプレイヤーの結果を記録します。

| カラム名 | 型 | 説明 |
|---------|------|------|
| `hand_id` | INTEGER | ハンドID（外部キー） |
| `player_id` | INTEGER | プレイヤーID |
| `hole_cards` | TEXT | ホールカードのJSON配列（例: `["A♠", "K♠"]`） |
| `hand_rank` | TEXT | 役の名前（例: "Pair of Aces"） |
| `winnings` | INTEGER | 獲得チップ数 |
| `timestamp` | TEXT | ショーダウン時刻（ISO 8601形式） |

**主キー**: `(hand_id, player_id)`
**インデックス**: `idx_showdown_player_id` on `player_id`

## 使用方法

### エージェントからの履歴取得

エージェントは `poker.game_history` モジュールの関数を使用して履歴を取得できます。

#### 1. ゲーム履歴の取得

```python
from poker.game_history import get_game_history

# 最新10件のハンド履歴を取得
history = get_game_history(limit=10)

# 特定のハンドの詳細を取得
hand_detail = get_game_history(hand_id=5)

# 特定プレイヤーの統計を含む履歴を取得
player_history = get_game_history(player_id=2, limit=20)
```

#### 2. 対戦相手の統計を取得

```python
from poker.game_history import get_opponent_stats

# 複数の相手プレイヤーの統計を一括取得
opponent_ids = [1, 2, 3]
stats = get_opponent_stats(opponent_ids)

# stats[1] = {
#     "player_id": 1,
#     "hands_played": 42,
#     "action_counts": {"fold": 15, "call": 18, "raise": 9},
#     "showdowns": 8,
#     "showdown_wins": 3,
#     "total_winnings": 450
# }
```

#### 3. 最新のハンドIDを取得

```python
from poker.game_history import get_last_hand_id

current_hand = get_last_hand_id()
```

### エージェントツールとしての実装例

```python
# agents/your_agent/tools/opponent_analysis.py

from poker.game_history import get_opponent_stats, get_game_history

def analyze_opponent(opponent_id: int) -> dict:
    """
    相手プレイヤーの行動パターンを分析
    
    Args:
        opponent_id: 分析対象のプレイヤーID
        
    Returns:
        分析結果の辞書
    """
    stats = get_opponent_stats([opponent_id])[opponent_id]
    
    # 統計から傾向を算出
    total_actions = sum(stats["action_counts"].values())
    aggression = stats["action_counts"].get("raise", 0) / max(total_actions, 1)
    
    return {
        "player_id": opponent_id,
        "hands_played": stats["hands_played"],
        "aggression_rate": aggression,
        "showdown_win_rate": stats["showdown_wins"] / max(stats["showdowns"], 1),
        "total_winnings": stats["total_winnings"]
    }
```

### team3_agent での使用例

`team3_agent` には既に `hand_history_tools.py` がありますが、新しいグローバルデータベースも利用できます：

```python
# agents/team3_agent/tools/your_tool.py

from poker.game_history import get_game_history, get_opponent_stats

def get_table_dynamics(current_player_id: int, opponent_ids: list) -> dict:
    """
    テーブル全体の傾向を分析
    """
    # 自分の統計
    my_history = get_game_history(player_id=current_player_id, limit=20)
    
    # 相手の統計
    opponent_stats = get_opponent_stats(opponent_ids)
    
    return {
        "my_recent_performance": my_history["player_stats"],
        "opponents": opponent_stats
    }
```

## データベース直接アクセス（高度な使用）

必要に応じて、`GameHistoryDB` クラスを直接使用することもできます：

```python
from poker.game_history import GameHistoryDB

db = GameHistoryDB()

# カスタムクエリの実行
cursor = db.conn.cursor()
cursor.execute("""
    SELECT player_id, COUNT(*) as raise_count
    FROM actions
    WHERE action_type = 'raise' AND phase = 'preflop'
    GROUP BY player_id
""")

for row in cursor.fetchall():
    print(f"Player {row['player_id']}: {row['raise_count']} preflop raises")

db.close()
```

## 注意事項

1. **スレッドセーフティ**: データベース接続は `check_same_thread=False` で作成されていますが、複数スレッドからの同時書き込みには注意が必要です。

2. **パフォーマンス**: 大量のハンドが蓄積された場合、クエリのパフォーマンスが低下する可能性があります。インデックスが適切に設定されていることを確認してください。

3. **プライバシー**: ショーダウンに至らなかったプレイヤーのホールカードは記録されません。これは実際のポーカーゲームのルールに準拠しています。

4. **データの永続性**: データベースファイルは `db/game_history.sqlite3` に保存されます。このファイルを削除すると、全ての履歴が失われます。

## トラブルシューティング

### データベースファイルが作成されない

`db/` ディレクトリが存在しない場合、`GameHistoryDB` の初期化時に自動的に作成されます。それでも問題がある場合は、パーミッションを確認してください。

### 古いデータをクリアする

```bash
# データベースファイルを削除
rm db/game_history.sqlite3

# 次回ゲーム起動時に自動的に再作成されます
```

### データのバックアップ

```bash
# データベースをバックアップ
cp db/game_history.sqlite3 db/game_history_backup_$(date +%Y%m%d).sqlite3
```

## 今後の拡張可能性

- プレイヤーごとのハンドレンジ分析
- ポジション別の統計
- ベットサイズのパターン認識
- 時系列での傾向分析
- エクスポート機能（CSV、JSON）

---

最終更新: 2025年10月13日

