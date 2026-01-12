import json
from dotenv import load_dotenv
from openai import OpenAI
import os
import logging 

logger = logging.getLogger()

# 默认配置（可根据你的服务商修改）
load_dotenv()
client = OpenAI(
    base_url=os.getenv("OPENAI_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY")
)

def call_llm_for_local_alignment(sub_a, sub_b):
    """
    sub_a: 剧本A的子列表 (list of strings)
    sub_b: 剧本B的子列表 (list of strings)
    """
    
    # 构建输入文本，带上索引以便LLM引用
    formatted_a = "\n".join([f"A[{i}]: {text}" for i, text in enumerate(sub_a)])
    formatted_b = "\n".join([f"B[{j}]: {text}" for j, text in enumerate(sub_b)])

    system_prompt = """你是一个高精度的剧本语音对齐专家。
任务：判断剧本 A 的每一行与剧本 B 的对应行是否可以共用【同一段语音文件】。
### 判定逻辑：
1. 语音兼容性：如果配音员照着 A 朗读，玩家看着 B 文本，只要不产生明显的词汇冲突，则视为匹配。
2. 允许匹配的情况：
   - 语气助词差异（よ、ね、かな、わ）。
   - 汉字/假名转换或敬语层级微调（です/だ）。
   - 忽略《》、☆、♪、❤等符号差异以及Ruby括号（振假名）。
3. 必须判定为 null 的情况：
   - 核心动词、名词被替换（意义发生重大改变）。
   - 句子结构大幅度重排。
   - A 的内容在 B 中完全消失，或 B 增加了 A 没说出的关键信息。
### 匹配准则与评分标准：
- **1.0 (完全一致)**：文本完全相同，或仅有标点、全半角、空格差异。
- **0.9 (语音兼容)**：核心名词、动词完全一致。仅有语气词（よ、ね）、特殊符号（☆）、或汉字假名转换的差异。或者文字一致，但在 B 中进行了断句拆分或合并。
- **0.8 (微小变体)**：核心词汇一致，但存在轻微的敬语转换（如 です->だ）或时态微调，且不影响语音重用。
- **0.0 (不匹配/重写)**：核心词汇（名词/动词）发生重大改变，或句子结构重排，即使意思相近也必须判定为 0 分，并将 b 设为 null。
### Few-Shot 示例（必须严格参考此格式）：
**输入：**
剧本 A:
A[0]: 行くわよ、みんな！
A[1]: 行くわよ。準備はいいかしら？
A[2]: わかりました。☆
A[3]: すぐに向かいます。
A[4]: 準備は整いました。
A[5]: 時間がありませんから。
A[6]: これもあの語呂合わせのおかげかな。
A[7]: お腹が空きましたね。
剧本 B:
B[0]: 行くわよ、みんな……☆
B[1]: 行くわよ。
B[2]: 準備はいいかしら？
B[3]: わかりました、すぐに向かいます。
B[4]: 準備は整ったわ。
B[5]: ……助かりました。
B[6]: 結構デタラメだったんだけど。
B[7]: 腹減ったな。
**输出：**
{
  "alignment": [
    { "a": [0], "b": [0], "score": 1.0, "reason": "仅标点符号和特殊符号差异。" },
    { "a": [1], "b": [1, 2], "score": 0.9, "reason": "文本一致，A[1]在B中被拆分为两句（拆分）。" },
    { "a": [2, 3], "b": [3], "score": 0.9, "reason": "文本一致，A的连续两句在B中被合并为一句（合并）。" },
    { "a": [4], "b": [4], "score": 0.8, "reason": "核心词'準備/整う'一致，仅敬语语气微调。" },
    { "a": [5], "b": null, "score": 0.0, "reason": "A[5]的内容在剧本B中被删除。" },
    { "a": null, "b": [5], "score": 0.0, "reason": "B[5]是新增台词，A中无对应语音。" },
    { "a": [6], "b": null, "score": 0.0, "reason": "核心词替换（语吕合わせ vs デタラメ），语音不兼容。" },
    { "a": [7], "b": null, "score": 0.0, "reason": "核心句式完全重写（お腹空いた vs 腹減った），不可重用语音。" }
  ]
}
### 任务要求：
1. 必须分析剧本 A 的每一行。
2. 结果必须严格按照 JSON 格式输出，所有对齐项放在 "alignment" 数组中。
3. 只要分数低于 0.8，b 必须设为 null。
"""
    user_prompt = f"""
### 待处理剧本：
剧本 A:
{formatted_a}
剧本 B:
{formatted_b}
请输出对齐结果 JSON："""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # 或 deepseek-chat, qwen-turbo 等小模型
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}, # 强制要求返回 JSON
            temperature=0.1 # 降低随机性，保证稳定性
        )
        
        # 解析返回内容
        result = json.loads(response.choices[0].message.content)
        logger.info(f"LLM Alignment Result: {result}")
        return result.get("alignment", [])

    except Exception as e:
        logger.error(f"LLM Alignment Error: {e}")
        return None

# --- 使用示例 ---
if __name__ == "__main__":
    sub_a = [
        "やったねヨシュア!これで晴れてあたしたちも協会の一员よ",
        "そうか、僕が遊撃士か......"
    ]
    sub_b = [
        "やったねヨシュア!これで晴れてあたしたちも協会の一员よ☆そうか、僕が遊撃士か......"
    ]
#  A[19517]: メーヴェ海道沿いの砂浜にガケに囲まれた窪地のような場所があってね。
#  A[19518]: その場所こそ──ズバリこの△印で描かれている地点だと思うんだ。
#  B[12693]: メーヴェ海道沿いの砂浜にガケに囲まれた窪地のような場所があるんだけど……
#  B[12694]: 宝の地図にはその窪地が目印として描かれているんだ。
    sub_a += [
        "メーヴェ海道沿いの砂浜にガケに囲まれた窪地のような場所があってね。",
        "その場所こそ──ズバリこの△印で描かれている地点だと思うんだ。"
    ]
    sub_b += [
        "メーヴェ海道沿いの砂浜にガケに囲まれた窪地のような場所があるんだけど……",
        "宝の地図にはその窪地が目印として描かれているんだ。"
    ]
#  A[0]: これもあの語呂合わせのおかげかな。
#  A[1]: “御用よ、ハイヤー！”、だっけ。
#  A[2]: ワードのチョイスはともあれ、確かに覚えやすかったかもね。
#  B[0]: 結構デタラメだったんだけど、たまたま合ってたみたい。
#  B[1]: やっぱり。
#  B[2]: まったく、君って子は……
    sub_a += [
        "これもあの語呂合わせのおかげかな。",
        "御用よ、ハイヤー！、だっけ。",
        "ワードのチョイスはともあれ、確かに覚えやすかったかもね。"
    ]
    sub_b += [
        "結構デタラメだったんだけど、たまたま合ってたみたい。",
        "やっぱり。",
        "まったく、君って子は……"
    ]
#  A[0]: あとは、オーブメントを交換して…………と。
#  B[0]: あとは、オーブメントを
#  B[1]: 交換して…………と。
    sub_a += [
        "あとは、オーブメントを交換して…………と。"
    ]
    sub_b += [
        "あとは、オーブメントを☆",
        "交換して…………と。"
    ]
    alignment = call_llm_for_local_alignment(sub_a, sub_b)
    print(alignment)
    # 输出预想: [{"a": [0, 1], "b": [0]}]
