"""
Example Tool: Game History Analysis for Poker Agents

このファイルは、エージェントがゲーム履歴データベースを活用する方法を示す例です。
各チームのエージェントは、このコードを参考にして独自のツールを実装できます。
"""

from poker.game_history import get_game_history, get_opponent_stats, get_last_hand_id
from typing import Dict, List, Any


def analyze_opponent_tendencies(opponent_id: int) -> Dict[str, Any]:
    """
    相手プレイヤーの傾向を分析
    
    Args:
        opponent_id: 分析対象のプレイヤーID
        
    Returns:
        相手の統計と傾向を含む辞書
        {
            "player_id": int,
            "hands_played": int,
            "vpip": float (Voluntarily Put money In Pot rate),
            "aggression_factor": float,
            "showdown_tendency": float,
            "win_rate_at_showdown": float
        }
    """
    stats = get_opponent_stats([opponent_id])[opponent_id]
    
    hands_played = max(stats["hands_played"], 1)  # ゼロ除算回避
    action_counts = stats["action_counts"]
    
    # 総アクション数
    total_actions = sum(action_counts.values())
    
    # VPIP（自発的に参加した割合）の概算
    # コール + レイズ + オールイン / 総アクション数
    voluntary_actions = (
        action_counts.get("call", 0) + 
        action_counts.get("raise", 0) + 
        action_counts.get("all_in", 0)
    )
    vpip = voluntary_actions / max(total_actions, 1)
    
    # アグレッションファクター（レイズ / コール）
    raise_count = action_counts.get("raise", 0) + action_counts.get("all_in", 0)
    call_count = max(action_counts.get("call", 1), 1)  # ゼロ除算回避
    aggression_factor = raise_count / call_count
    
    # ショーダウン傾向
    showdown_rate = stats["showdowns"] / hands_played
    
    # ショーダウン勝率
    win_rate = 0.0
    if stats["showdowns"] > 0:
        win_rate = stats["showdown_wins"] / stats["showdowns"]
    
    return {
        "player_id": opponent_id,
        "hands_played": hands_played,
        "vpip": round(vpip, 2),
        "aggression_factor": round(aggression_factor, 2),
        "showdown_tendency": round(showdown_rate, 2),
        "win_rate_at_showdown": round(win_rate, 2),
        "total_winnings": stats["total_winnings"],
        "action_counts": action_counts
    }


def get_table_profile(my_player_id: int, opponent_ids: List[int]) -> Dict[str, Any]:
    """
    テーブル全体のプレイヤー傾向を分析
    
    Args:
        my_player_id: 自分のプレイヤーID
        opponent_ids: 相手プレイヤーIDのリスト
        
    Returns:
        テーブル全体の傾向分析
    """
    # 自分の統計
    my_history = get_game_history(player_id=my_player_id, limit=20)
    my_stats = my_history.get("player_stats", {})
    
    # 相手の統計
    opponents_analysis = []
    for opp_id in opponent_ids:
        try:
            analysis = analyze_opponent_tendencies(opp_id)
            opponents_analysis.append(analysis)
        except Exception as e:
            print(f"Warning: Could not analyze opponent {opp_id}: {e}")
    
    # テーブル全体の傾向
    avg_vpip = sum(o["vpip"] for o in opponents_analysis) / max(len(opponents_analysis), 1)
    avg_aggression = sum(o["aggression_factor"] for o in opponents_analysis) / max(len(opponents_analysis), 1)
    
    # テーブルタイプの判定
    table_type = "unknown"
    if avg_vpip > 0.4 and avg_aggression > 2.0:
        table_type = "aggressive"  # アグレッシブなテーブル
    elif avg_vpip > 0.4:
        table_type = "loose"  # ルースなテーブル
    elif avg_aggression > 2.0:
        table_type = "tight_aggressive"  # タイト・アグレッシブ
    else:
        table_type = "passive"  # パッシブなテーブル
    
    return {
        "my_stats": my_stats,
        "opponents": opponents_analysis,
        "table_average": {
            "vpip": round(avg_vpip, 2),
            "aggression": round(avg_aggression, 2)
        },
        "table_type": table_type
    }


def get_recent_hand_summary(limit: int = 5) -> List[Dict[str, Any]]:
    """
    最近のハンドの要約を取得
    
    Args:
        limit: 取得するハンド数
        
    Returns:
        ハンド要約のリスト
    """
    history = get_game_history(limit=limit)
    recent_hands = history.get("recent_hands", [])
    
    summaries = []
    for hand in recent_hands:
        if hand is None:
            continue
            
        # 基本情報
        summary = {
            "hand_id": hand["hand_id"],
            "started": hand["timestamp"],
            "dealer_button": hand["dealer_button"],
            "players": hand["player_ids"]
        }
        
        # アクション数をカウント
        actions = hand.get("actions", [])
        summary["total_actions"] = len(actions)
        
        # ショーダウン情報
        showdown = hand.get("showdown_results", [])
        if showdown:
            winners = [s["player_id"] for s in showdown if s["winnings"] > 0]
            summary["winners"] = winners
            summary["went_to_showdown"] = True
        else:
            summary["went_to_showdown"] = False
        
        summaries.append(summary)
    
    return summaries


def should_play_aggressive(my_player_id: int, opponent_ids: List[int]) -> bool:
    """
    相手の傾向に基づいて、アグレッシブにプレイすべきかを判断
    
    Args:
        my_player_id: 自分のプレイヤーID
        opponent_ids: 相手プレイヤーIDのリスト
        
    Returns:
        True: アグレッシブにプレイすべき
        False: 慎重にプレイすべき
    """
    try:
        table_profile = get_table_profile(my_player_id, opponent_ids)
        table_type = table_profile["table_type"]
        
        # パッシブなテーブルではアグレッシブに
        # アグレッシブなテーブルでは慎重に
        return table_type in ["passive", "loose"]
    except Exception:
        # エラー時は中立的な判断
        return False


def get_player_hand_range_estimate(player_id: int, phase: str = "preflop") -> Dict[str, Any]:
    """
    プレイヤーのハンドレンジを推定（簡易版）
    
    Args:
        player_id: プレイヤーID
        phase: フェーズ（preflop/flop/turn/river）
        
    Returns:
        ハンドレンジの推定情報
    """
    stats = get_opponent_stats([player_id])[player_id]
    action_counts = stats["action_counts"]
    
    # 特定フェーズでのアクションパターン
    # 注: より精密な分析には actions テーブルを直接クエリする必要があります
    
    raise_rate = action_counts.get("raise", 0) / max(sum(action_counts.values()), 1)
    fold_rate = action_counts.get("fold", 0) / max(sum(action_counts.values()), 1)
    
    range_type = "unknown"
    if raise_rate > 0.3:
        range_type = "wide"  # 広いレンジ
    elif fold_rate > 0.6:
        range_type = "tight"  # タイトなレンジ
    else:
        range_type = "medium"  # 中程度のレンジ
    
    return {
        "player_id": player_id,
        "estimated_range": range_type,
        "raise_rate": round(raise_rate, 2),
        "fold_rate": round(fold_rate, 2)
    }


# 使用例
if __name__ == "__main__":
    # 相手プレイヤーID
    opponent_id = 1
    
    # 相手の傾向を分析
    analysis = analyze_opponent_tendencies(opponent_id)
    print(f"Opponent {opponent_id} Analysis:")
    print(f"  VPIP: {analysis['vpip']}")
    print(f"  Aggression Factor: {analysis['aggression_factor']}")
    print(f"  Showdown Win Rate: {analysis['win_rate_at_showdown']}")
    print()
    
    # テーブル全体の傾向
    table = get_table_profile(my_player_id=0, opponent_ids=[1, 2, 3])
    print(f"Table Type: {table['table_type']}")
    print(f"Average VPIP: {table['table_average']['vpip']}")
    print()
    
    # 最近のハンド要約
    recent = get_recent_hand_summary(limit=3)
    print(f"Recent {len(recent)} hands:")
    for hand in recent:
        print(f"  Hand #{hand['hand_id']}: {hand['total_actions']} actions, "
              f"Showdown: {hand['went_to_showdown']}")

