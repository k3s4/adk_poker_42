from google.adk.agents import Agent
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.agent_tool import AgentTool
from google.adk.agents import SequentialAgent
from team1_agent.tools.calc_gto import calc_gto
from google.adk.agents import ParallelAgent

MODEL_GPT_4_1 = LiteLlm(model="openai/gpt-4o-mini")

# SequentialAgentのモデル名を引数に入れていたのが原因だった
calc_confidence = Agent(
    name="calc_confidence",
    #model="gemini-2.5-flash-lite",
    model=MODEL_GPT_4_1,
    description=("コンフリクト率を計算するエージェント"),
    instruction=("あなたはテキサスホールデム・ポーカーのプレイを補佐するエージェントです。"
                "あなたは各対戦相手のコンフリクト率を計算します。"
                "計算には、入力のhistoryを参考にしてください。"
                "コンフリクト率は、対戦相手が強気なプレイヤーであるか、弱気なプレイヤーであるかを0~100の整数で示します。"
                "100に近いほど対戦相手が強気なプレイヤーである確率が高く、0に近いほど対戦相手が弱気なプレイヤーである確率が高くなります。"
                "コンフリクト率の計算には、各対戦相手の過去の行動を参考にしてください。"
                "historyの情報が少なく、確実性を得られない場合にはその旨も記述してください。"
                ),
    output_key="confidence_result"
)

calc_bluff_rate = Agent(
    name="calc_bluff_rate",
    #model="gemini-2.5-flash-lite",
    model=MODEL_GPT_4_1,
    description=("ブラフ率を計算するエージェント"),
    instruction=("あなたはテキサスホールデム・ポーカーのプレイを補佐するエージェントです。"
                "あなたは各対戦相手のブラフ率を計算します。"
                "計算には、入力のhistoryを参考にしてください。"
                "ブラフ率は、対戦相手のベットがブラフである確率を示します。"
                "100に近いほど対戦相手のベットがブラフである確率が高く、0に近いほど対戦相手のベットがブラフである確率が低くなります。"
                "ベットをしていない対戦相手については、ブラフ率を0にしてください。"
                "historyの情報が少なく、確実性を得られない場合にはその旨も記述してください。"
                ),
    output_key="bluff_rate_result"
)

GTO_agent = Agent(
    name="GTO_agent",
    #model="gemini-2.5-flash-lite",
    model=MODEL_GPT_4_1,
    description=("GTOエージェント"),
    instruction=("""あなたはテキサスホルデムのゲーム理論的な最適戦略を考案するエージェントです。

                  あなたは以下のツールを使用して、最善の意思決定を行います。
                  - calc_gto: 現在の手札とコミュニティカードから勝率を計算するツール

                  ツールがエラーを吐いた場合は、あなたが世界一のプレイヤーとして代わりに意思決定を行ってください。
                 
                  あなたには以下の情報が与えられます:
                  - あなたの手札（ホールカード）
                  - コミュニティカード（あれば）
                  - 選択可能なアクション
                  - ポットサイズやベット情報
                  - 対戦相手の情報

                  
                  必ず次のJSON形式で回答してください:
                  {
                    "action": "fold|check|call|raise|all_in",
                    "reasoning": "あなたの決定の理由を説明"
                  }
                  """
                ),
    output_key="GTO_result",
    tools=[calc_gto]
)

memory_agent = Agent(
    name="memory_agent",
    #model="gemini-2.5-flash-lite",
    model=MODEL_GPT_4_1,
    description=("入力情報を記録するエージェント"),
    instruction=("入力情報をそのまま出力してください。"),
    output_key="input_info"
)

analyze_agent = ParallelAgent(
    name="analyze_agent",
    sub_agents=[calc_confidence, calc_bluff_rate, GTO_agent, memory_agent],
    description=("Runs multiple agents in parallel to analyze the situation.")
)

decision_agent = Agent(
    name="decision_agent",
    #model="gemini-2.5-flash-lite",
    model=MODEL_GPT_4_1,
    description=("Decides on the best action to take based on the situation."),
    instruction=("""あなたはテキサスホールデム・ポーカーのエキスパートプレイヤーです。

                あなたは、以下の情報を参考に、最適なアクションを決定してください:

                - プレイ状況
                  {input_info}
                
                - 現在のプレイ状況からGTO戦略に基づいて考えられた行動
                  {GTO_result}
                  この行動は、GTO戦略に基づいて考えられており、とても論理的な案です。
                  しかし、ブラフといった、対戦相手のミスを利用する様な行動ではありません。

                - 各対戦相手のコンフリクト率
                  {confidence_result}
                  コンフリクト率は、対戦相手が強気なプレイヤーであるか、弱気なプレイヤーであるかを0~100の整数で示します。
                  100に近いほど対戦相手が強気なプレイヤーである確率が高く、0に近いほど対戦相手が弱気なプレイヤーである確率が高くなります。
                  例えば、コンフリクト率が低い対戦相手に対しては、ブラフが通用し易いと考えられます。
                  対して、コンフリクト率が高い対戦相手に対しては、ブラフが通用し難いと考えられます。

                - 各対戦相手のブラフ率
                  {bluff_rate_result}
                  ブラフ率は、各対戦相手のベットがブラフである確率を示します。
                  100に近いほど対戦相手のベットがブラフである確率が高く、0に近いほど対戦相手のベットがブラフである確率が低くなります。
                  ブラフ率が低く、かつその対戦相手のベットが大きければ、その対戦相手の手札は強い可能性が高いです。
                  ブラフ率が高ければ、相手のベットが大きくても、その対戦相手の手札は弱い可能性が高いです。

                アクションの方針:
                  勝つ可能性が少しでもあれば、あなたの所持チップを増やすように行動してください。
                  例えば、レイズを行ってポットを大きくすることで、相手のチップを奪います。
                  ブラフを使用して、相手のチップを奪うことも視野に入れてください。
                  また、コールやチェックを利用して、様子見をする事も大事な戦略です。
                  負ける可能性が高いハンドでは、あなたの所持チップを守るように行動してください。
                  例えば、フォールドを選択して、自分のチップを維持します。
                  但し、バーストは防いでください。

                  必ず次のJSON形式で回答してください:
                  {
                    "action": "fold|check|call|raise|all_in",
                    "reasoning": "あなたの決定の理由を説明"
                  }

                  アクションとしてレイズを行う場合には、それが堅実なレイズであるか、ブラフであるかを判断してください。
                  堅実なレイズである場合には、その旨をreasoningに説明してください。
                  ブラフである場合には、その旨をreasoningに説明してください。
                  """
                  ),
    output_key="decision_result"
)

calc_raise_amount = Agent(
    name="calc_raise_amount",
    #model="gemini-2.5-flash-lite",
    model=MODEL_GPT_4_1,
    description=("Calculates the amount to raise based on the situation."),
    instruction=("""あなたはテキサスホールデム・ポーカーのプレイを補佐するエージェントです。

                あなたには、以下の情報が与えられます:

                - プレイ状況
                  {input_info}

                - 現在のプレイ状況から考えられた行動
                  {decision_result}

                現在の状況から考えられた行動がレイズである場合には、最適なレイズ量を計算してください。
                レイズ量の計算は、reasoningとプレイ状況に基づいて行ってください。

                レイズの方針:
                  勝負を仕掛けるべき時には、チップを惜しまずにレイズしてください。
                  特にブラフを仕掛けるときには、強気にレイズしてください。
                  堅実にポットを大きくする場合には、ポットの大きさと自分の所持チップに応じてレイズ量を調整してください。

                現在の状況から考えられた行動がレイズではない場合には、以下の形式に従って行動を出力してください。
                  
                  必ず次のJSON形式で回答してください:
                  {
                    "action": "fold|check|call|raise|all_in",
                    "amount": <数値>,
                    "reasoning": "あなたの決定の理由を簡潔に説明"
                  }

                  ルール:
                  - "fold"と"check"の場合: amountは0にしてください
                  - "call"の場合: コールに必要な正確な金額を指定してください
                  - "raise"の場合: レイズ後の合計金額を指定してください
                  - "all_in"の場合: あなたの残りチップ全額を指定してください

                  初心者がわかるように専門用語には解説を加えてください""")
)

pipeline_agent = SequentialAgent(
    name="pipeline_agent",
    sub_agents=[analyze_agent, decision_agent, calc_raise_amount],
    description=("Coordinating agents to analyze the situation and make a decision.")
)

root_agent = pipeline_agent