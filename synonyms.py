import csv
import re
import jaconv

def get_potential_synonyms(script_a:list, script_b:list, final_mapping: dict[int,int]):
  # Find all matched lines less longer than 10
  synm = []
  for pos_a, pos_b in final_mapping.items():
    if len(script_a[pos_a]) < 10 and len(script_b[pos_b]) < 10 and script_a[pos_a] != script_b[pos_b]:
      synm.append([script_a[pos_a], script_b[pos_b]])
  
  with open("synonyms.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["script_a", "script_b"])
    writer.writerows(synm)
  
def strip_ruby_brackets(text):
    # 匹配 汉字(片假名) 或 汉字（片假名）
    # 同时也处理游撃士（ブレイサー）这种情况
    # 策略：将括号及其内容全部删掉，只保留核心词
    return re.sub(r'[（\(][ぁ-んァ-ヶー]+[）\)]', '', text)

kanji_to_katakana = {
    # --- 组织与职衔 ---
    "身喰らう蛇": "ウロボロス",
    "結社": "ウロボロス",
    "使徒": "アングイス",
    "執行者": "エンフォーサー",
    "星杯騎士団": "グラールリッター",
    "守護騎士": "ドミニオン",
    "猟兵": "イェーガー",
    "遊撃士": "ブレイサー",
    "協会": "ブレイサーギルド",
    "鉄路憲兵隊": "アイゼンリッター",
    "鉄機隊": "シュタールリッター",
    "黒月": "ヘイユエ",
    "斑鳩": "イカルガ",
    
    # --- 技术与系统 ---
    "導力器": "オーブメント",
    "導力魔法": "アーツ",
    "戦技": "クラフト",
    "結晶回路": "クオーツ",
    "七耀石": "セプチウム",
    "古代遺物": "アーティファクト",
    "至宝": "セプテリオン",
    "起動者": "アウェイカー",
    "戦術導力器": "ザイファ",  # 根据版本可选 エニグマ/アークス/ザイファ
    "空洞核心": "ホロウコア",
    "晶片": "シャード",
    "魔装鬼": "グレンデル",
    "戦術リンク": "リンク",
    
    # --- 称号与关键名词 ---
    "灰の騎士": "シュバリエ",
    "鋼の聖女": "アリアンロード",
    "剣帝": "レーヴェ",
    "紫電": "エクレール",
    "聖獣": "レグナート",
    "影の国": "ファンタズマ",
    "原型導力器": "ゲネシス",
    "琥珀" : "こはく",
    "紺碧" : "こんぺき",
    "紅蓮" : "ぐれん",
    "翡翠" : "ひすい",
}

katakana_to_kanji = {
    # --- 组织与职衔 ---
    "ウロボロス": "身喰らう蛇",  # 也对应 "結社"
    "アングイス": "使徒",
    "エンフォーサー": "執行者",
    "グラールリッター": "星杯騎士団",
    "ドミニオン": "守護騎士",
    "イェーガー": "猟兵",
    "ブレイサー": "遊撃士",
    "ギルド": "協会",
    "アイゼンリッター": "鉄路憲兵隊",
    "シュタールリッター": "鉄機隊",
    "ヘイユエ": "黒月",
    "イカルガ": "斑鳩",
    
    # --- 技术与系统 ---
    "オーブメント": "導力器",
    "アーツ": "導力魔法",
    "クラフト": "戦技",
    "クオーツ": "結晶回路",
    "セプチウム": "七耀石",
    "アーティファクト": "古代遺物",
    "セプテリオン": "至宝",
    "アウェイカー": "起動者",
    "エニグマ": "戦術導力器",   # 零/碧时代
    "アークス": "戦術導力器",   # 闪时代 (ARCUS)
    "ザイファ": "戦術導力器",   # 黎/界时代 (Xipha)
    "ホロウコア": "空洞核心",
    "シャード": "晶片",
    "グレンデル": "魔装鬼",
    "リンク": "戦術リンク",
    
    # --- 称号与角色相关 ---
    "シュバリエ": "灰の騎士",
    "アリアンロード": "鋼の聖女",
    "レーヴェ": "剣帝",
    "エクレール": "紫電",
    "レグナート": "聖獣",
    "ファンタズマ": "影の国",
    "ゲネシス": "原型導力器",
    "こはく" : "琥珀",
    "こんぺき": "紺碧",
    "ぐれん" : "紅蓮",
    "ひすい" : "翡翠",
}

falcom_gaiji = {
        "(株)": "♥", 
        "①": "♪", 
        "②": "❗", 
        "③": "❓", 
        "⑴": "!",
        "⑵": "?",
        "④": "💧", # 汗水/流汗
        "Ⅰ": "⚡", # 闪电
        "(有)": "→",
        "(代)": "←",
        "㈲": "↑",
        "㈹": "↓",
        "\u3231": "❤"
}
gaiji_chars = list(falcom_gaiji.keys()) + list(falcom_gaiji.values()) + ['☆', '!']



def replace_kiseki_terms(text):
    text = strip_ruby_brackets(text)
    mapping = katakana_to_kanji
    # 长度降序排列 key
    for gaiji in gaiji_chars :
      text = text.replace(gaiji,'')
    pattern_str = "|".join(re.escape(k) for k in sorted(mapping.keys(), key=len, reverse=True))
    text = re.sub(pattern_str, lambda m: mapping[m.group(0)], text)
    kiseki_terms = katakana_to_kanji.values()
    pattern_brackets = r'[（《](' + '|'.join(re.escape(t) for t in kiseki_terms) + r')[）》]'
    text = re.sub(pattern_brackets, r'\1', text)
    
    return text


def normalize(texts):
    """
    归一化日语UTF-8字符串，用于清洗后相等但标点符号次序不同的情况。
    感受下轨迹的片假名震撼。
    """
    if isinstance(texts, str):
      text = texts
    else:
      text = "".join(texts)
    if not text: return ""
    text = "".join(text.split())
    text = replace_kiseki_terms(text)
    text = jaconv.normalize(text, 'NFKC')
    text = "".join(text.split())
    return text


if __name__ == "__main__" :
  sample_text = "ウロボロスのアングイスがオーブメントを使用した。"
  print(normalize(sample_text))
  sample_text = "《翡翠（ ひすい）の塔》って遺跡だ。《導力器》ち、無事、遊撃士（ブレイサー）になれたかい？"
  print(normalize(sample_text))
  sample_text = "ツァイス地方の《紅蓮（ぐれん）の塔》……"
  print(normalize(sample_text))
  sample_text = "てば♪さっ、気(株)分かも❤ノンキ"
  print(normalize(sample_text))
