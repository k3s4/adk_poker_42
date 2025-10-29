# ADK Poker - テキサスホールデム ポーカーゲーム

LLMプレイヤー対応のWebアプリ（Flet）/CLIのテキサスホールデムポーカー

## ゲーム仕様

- **形式**: テキサスホールデム（No-Limit）
- **初期チップ**: 2000
- **ブラインド**: SB 10 / BB 20

## インストール・実行

### 必要なもの

- Python 3.13+
- [uv](https://github.com/astral-sh/uv)

### セットアップ

1. uvのインストール

[公式ドキュメントのインストール方法](https://docs.astral.sh/uv/getting-started/installation/)を参考にインストールしてください．

- macOS/Linuxの場合

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

- Windowsの場合

   ```bash
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. リポジトリのクローン

   ```bash
   git clone https://github.com/gochipon/adk_poker_2025
   cd adk-poker
   ```

3. 依存パッケージのインストール

   ```bash
   uv sync
   ```

#### 環境変数の設定

- [.env.example](.env.example)を参考にして.envファイルをリポジトリルートに作成してください
- 基本的には`GOOGLE_API_KEY`が設定されていれば、beginner_agentは動作します．
- インターン生が作成したagents (team1-4)については`OPENAI_API_KEY`を設定してください．

## 注意事項
- ポーカーゲームを再起動する場合は、現在起動しているポーカーのタブを閉じてから実行してください
  - viewerを実装している都合で、ゲームを複数同時に起動することはできません

## 使い方

### Webアプリモード

1. エージェントをadk api serverで起動

```bash
cd agents && uv run adk api_server --port 8000
```

2. 新しいターミナルで以下のコマンドを実行

```bash
uv run python main.py
# ブラウザで http://localhost:8551 にアクセス
```

3. 最初に表示される設定画面で、プレイヤー構成を選択
    - プレイヤータイプ: `random` / `llm_api`
      - `llm_api` の場合は利用するエージェント等を設定
3. ゲーム開始後、画面下部のボタンでアクションを選択
    - フォールド（赤）/ チェック（青）/ コール（緑）/ レイズ（オレンジ）/ オールイン（紫）
    - レイズはダイアログで金額を入力
4. ベッティングラウンド終了時は「次のフェーズへ」ボタンで進行
5. ショーダウン結果はテーブル上に表示され、「次のハンドへ」で継続

- **観戦ビューア同時起動**（別ウィンドウで自動起動）

  ```bash
  uv run python main.py --with-viewer # Viewer: http://localhost:8552
  ```

- **CLIモード**

  ```bash
  uv run python main.py --cli
  ```

- **エージェント専用モード（CLI限定）**
  - プレイヤーを全てAgentにし、高速でゲームを進行するモードです。
  - エージェントの性能評価などに使用できます。

  ```bash
  # デフォルト（team1_agent:2人, team2_agent:2人）
  uv run python main.py --cli --agent-only
  
  # カスタムエージェント構成
  uv run python main.py --cli --agent-only --agents "team1_agent:2,team3_agent:1,beginner_agent:1"
  
  # 3つのインスタンスを並列実行（エージェントの指定はcompose.yamlを修正）
  docker compose up --scale poker-app=3
  
  # ハンド数指定
  uv run python main.py --cli --agent-only --max-hands 50
  
  # 単一チーム対戦
  uv run python main.py --cli --agent-only --agents "team1_agent:4"
  ```

  **📌 エージェント専用モードの特徴:**
  - 🤖 **LLMエージェント対戦**: 各チームの戦略的AIが対戦
  - 📊 **エージェント別統計**: チーム毎の勝率と平均成績を表示
  - ⚡ **完全自動進行**: 人間の介入なしで最大20ハンド実行
  - 🎯 **カスタム構成**: エージェントの種類と人数を自由に設定
  
  **⚠️ 注意:** LLMの実際の動作には適切なAPIキーの設定が必要です。未設定の場合はランダム行動になります。

#### 利用可能なオプション

```bash
uv run python main.py --help
```

- `--cli`: CLI（コマンドライン）モードで実行（デフォルトはWeb）
- `--with-viewer`: 観戦ビューアを別ポートで同時起動（デフォルト: 8552）
- `--viewer-port <port>`: 観戦ビューアのポート指定
- `--cpu-only`: CPU専用モード（CLI限定）
- `--agent-only`: エージェント専用モード（LLMエージェントのみで完全自動進行、CLI限定）
- `--agents <config>`: 使用するエージェントと人数を指定（例: "team1_agent:2,team2_agent:1"）
- `--max-hands <N>`: CPU専用・エージェント専用モードの最大ハンド数（CPU専用:10、エージェント専用:20）


## LLMプレイヤー

### ADKを用いたエージェントの作成手順
- エージェントの作成手順は[wiki](https://github.com/gochipon/adk_poker_2025/wiki)を参照してください


### JSON状態フォーマット

`docs/game_state_format.md`で定義された構造化フォーマットでゲーム状態を提供：

```json
{
  "your_id": 0,
  "phase": "flop",
  "your_cards": ["A♥", "K♠"],
  "community": ["Q♥", "J♦", "10♣"],
  "your_chips": 970,
  "your_bet_this_round": 0,
  "your_total_bet_this_hand": 30,
  "pot": 140,
  "to_call": 20,
  "dealer_button": 3,
  "current_turn": 0,
  "players": [
    {"id": 1, "chips": 970, "bet": 0, "status": "active"},
    {"id": 2, "chips": 970, "bet": 0, "status": "active"},
    {"id": 3, "chips": 950, "bet": 20, "status": "active"}
  ],
  "actions": ["fold", "call (20)", "raise (min 40)", "all-in (970)"],
  "history": [
    "Preflop: All players called 30",
    "Flop dealt: Q♥ J♦ 10♣",
    "Player 3 bet 20"
  ]
}
```

### LLMプレイヤーの出力フォーマット

LLMプレイヤーは、意思決定の際に**必ず次のJSON形式**で出力してください。

```json
{
  "action": "fold|check|call|raise|all_in",
  "amount": <数値>,
  "reasoning": "戦略分析から導出された決定と戦略的理由の詳細な説明"
}
```

### 実行方式

- **インプロセス LLM（`llm`）**: ADKエージェントをプロセス内で実行します。`GOOGLE_API_KEY` 等の環境変数が未設定の場合はランダム行動にフォールバックします。
- **外部API LLM（`llm_api`）**: `http://localhost:8000` のADK APIサーバーに接続します（デフォルト）。
  - 必要なエンドポイント（例）: `/apps/{agent}/users/{user}/sessions/{session}`, `/run`
  - Setup画面でエージェント（例: `team1_agent`）を選択してください
  - Viewer に「LLMエージェントの最新判断」が表示されます


## ログ出力

- 実行ごとに `logs/` にタイムスタンプ付きログを自動保存（例: `poker_game_20250101_123456.log`）
- ターミナルにはINFO、ファイルにはDEBUGレベルで詳細記録（プロンプトや判定も含む）

## ログビューワー

ゲームの進行状況を可視化する簡易ログビューワーが利用可能です。

### 起動方法

```bash
uv run python log_viewer.py

# ポート番号を指定して起動
uv run python log_viewer.py --port 8554

# ヘルプを表示
uv run python log_viewer.py --help
```

### 使い方

1. ログビューワーを起動
2. 左側のパネルからログファイルを選択
3. メインパネルでゲームの進行を確認

## ゲーム履歴データベース

### 概要

ポーカーゲームは全ての公開情報をSQLiteデータベースに記録します。各エージェントはこの履歴データを活用して、相手の傾向を分析し、戦略を最適化できます。

### 記録される情報（公開情報のみ）

- ✅ 全プレイヤーのアクション（フォールド、チェック、コール、レイズ、オールイン）
- ✅ ベット額とポット額の推移
- ✅ コミュニティカード（フロップ、ターン、リバー）
- ✅ ショーダウンに到達したプレイヤーのホールカード
- ✅ 勝者と獲得チップ数

### エージェントからの利用方法

```python
from poker.game_history import get_game_history, get_opponent_stats

# 相手プレイヤーの統計を取得
opponent_stats = get_opponent_stats([1, 2, 3])

# 特定プレイヤーの詳細な履歴を取得
my_history = get_game_history(player_id=0, limit=20)

# 最近のハンド履歴を取得
recent_hands = get_game_history(limit=10)
```

詳細は [docs/database_schema.md](docs/database_schema.md) および [docs/example_history_tool.py](docs/example_history_tool.py) を参照してください。

## プロジェクト構造（主要）

```md
adk-poker/
├── main.py
├── poker/
│   ├── game.py               # ゲーム進行の中核
│   ├── game_models.py        # 型付きゲーム状態/フェーズ等
│   ├── player_models.py      # Human/Random/LLM/LLM API プレイヤー
│   ├── evaluator.py          # ハンド評価
│   ├── game_history.py       # ゲーム履歴データベース
│   ├── flet_ui.py            # Fletエントリ/統合
│   ├── setup_ui.py           # 設定画面
│   ├── game_ui.py            # 対局画面
│   ├── viewer_ui.py          # 観戦ビューア
│   ├── state_server.py       # JSON状態HTTPサーバー（:8765/state）
│   └── shared_state.py       # ゲーム共有状態
├── agents/                   # ADK Agent の例
├── db/                       # ゲーム履歴データベース
│   └── game_history.sqlite3
├── log_viewer.py             # ログ可視化アプリ
└── docs/
    ├── game_state_format.md
    ├── design.md
    ├── requirements.md
    ├── database_schema.md    # データベーススキーマ詳細
    └── example_history_tool.py  # エージェント用ツール例
```
