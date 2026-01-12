import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def top_k_match(script_a:list[str], script_b:list[str], matches:list[dict], anchors:dict[int,int]):
  top_k_matches = {}
  
  for match in matches:
    pos_a = match['pos_a']
    if pos_a in anchors.keys() and pos_a + 1 in anchors.keys() and pos_a + 2 in anchors.keys():
      logger.info(f"已匹配：{pos_a}->{anchors[pos_a]}")
      logger.info(f"  内容: {match['text_a']}")
      if not any(m['pos_b'] == anchors[pos_a] for m in match['matches']):
        logger.info("  匹配位于Top-3之外")
      for i, m in enumerate(match['matches']):
          logger.info(f"  Top-{i+1} 匹配 (B第 {m['pos_b']} 行, 分数 {m['score']}%):")
          logger.info(f"    {m['text_b']}")

      continue
    
  return top_k_matches
