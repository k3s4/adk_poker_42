import json


def json_output(action: str, amount: int, reasoning: str) -> str:
    """
    最終的な出力を生成
    Args:
        action (str): 行動 "fold", "check", "call", "raise", "all_in"のいずれか
        amount (int): 
            - "fold"と"check"の場合: amountは0にしてください
            - "call"の場合: コールに必要な正確な金額を指定してください
            - "raise"の場合: レイズ後の合計金額を指定してください
            - "all_in"の場合: あなたの残りチップ全額を指定してください
        reasoning (str): あなたの決定の理由 根拠を明確にして簡潔に説明
    Return:
        最終的に出力するべきもの
    """
    output_json = {"amount": amount, "reasoning": reasoning}
    if "check" in action:
        output_json["action"] = "check"
        output_json["amount"] = 0
    elif "call" in action:
        output_json["action"] = "call"
    elif "raise" in action:
        output_json["action"] = "raise"
    elif "all_in" in action:
        output_json["action"] = "all_in"
    else:
        output_json["action"] = "fold"
        output_json["amount"] = 0

    return json.dumps(output_json)
