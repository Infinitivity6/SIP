"""
step2_extract.py

调用硅基流动 API，对豆瓣电影 Top250 列表页爬取的非结构化文本进行信息抽取，
输出结构化 JSON，并统计优化前后 Token 消耗对比。
"""

import json
import os
import time
from openai import OpenAI

# ============================================================
# 通过环境变量 SIP_API_KEY 配置硅基流动 API Key
# ============================================================
API_KEY  = os.getenv("SIP_API_KEY", "")
BASE_URL = "https://api.siliconflow.cn/v1"
MODEL    = "Qwen/Qwen2.5-7B-Instruct"

# ============================================================
# Prompt 设计
# 方案A（冗长）vs 方案B（精简），用于成本优化对比
# ============================================================

# ── 方案A：优化前，冗长 System Prompt（约115 tokens）────────
SYS_A = (
    "你是一位经验丰富的数据治理专家，专门负责对从影视数据库网站爬取的非结构化文本"
    "进行清洗、解析与结构化处理工作。你的职责是仔细阅读用户提供的原始文本，从中识别"
    "并提取电影片名、导演、主演、上映年份、制片国家、类型、豆瓣评分、评价人数以及"
    "一句话推荐语等关键字段，并严格以 JSON 格式输出，不得包含任何额外解释文字或"
    "Markdown 格式符号。"
)

USER_A = """请对以下从豆瓣电影网站爬取的非结构化原始文本进行深入分析，
按照 JSON 格式提取以下字段：
- title: 中文片名（字符串）
- title_foreign: 外文片名，若无则为空字符串（字符串）
- director: 导演姓名（字符串）
- cast: 主演列表，最多3人（数组）
- year: 上映年份（字符串）
- country: 制片国家/地区（字符串）
- genres: 类型标签（数组）
- rating: 豆瓣评分（浮点数）
- rating_count: 评价人数，仅保留数字（整数）
- quote: 编辑推荐一句话，若无则为空字符串（字符串）

原始文本：
{text}"""

# ── 方案B：优化后，精简 System Prompt（约18 tokens）────────
SYS_B = "你是数据治理专家。从非结构化文本提取信息，仅返回JSON，禁止输出解释或markdown。"

USER_B = """文本：
{text}

返回JSON，字段：title, title_foreign, director, cast([最多3人]), year, country, genres([]), rating(浮点数), rating_count(整数), quote"""


# ============================================================
# 核心函数
# ============================================================

def call_api(client, system_prompt, user_prompt, text):
    """调用 API，返回 (原始输出, 输入tokens, 输出tokens, 耗时秒)"""
    filled = user_prompt.format(text=text)
    t0 = time.time()
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": filled},
        ],
        temperature=0.1,   # 信息抽取用低温度，输出更稳定
        max_tokens=512,
    )
    elapsed = time.time() - t0
    content = response.choices[0].message.content
    usage   = response.usage
    return content, usage.prompt_tokens, usage.completion_tokens, elapsed


def parse_json(raw: str) -> dict:
    """安全解析模型返回的 JSON，去除可能的 markdown 包裹"""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = [l for l in cleaned.split("\n") if not l.strip().startswith("```")]
        cleaned = "\n".join(lines)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"  [警告] JSON 解析失败: {e}")
        return {"_parse_error": str(e), "raw_output": raw}


def process_one(client, item: dict) -> dict:
    text = item["raw_text"]
    print(f"\n{'─'*55}")
    print(f"[#{item['id']}] 原始文本（前60字）: {text[:60].replace(chr(10),' ')}...")

    # 方案A（冗长）
    print("  [方案A] 冗长提示...")
    try:
        raw_a, in_a, out_a, t_a = call_api(client, SYS_A, USER_A, text)
        parsed_a = parse_json(raw_a)
        print(f"    输入={in_a} tokens  输出={out_a} tokens  耗时={t_a:.1f}s")
    except Exception as e:
        print(f"    [错误] {e}")
        parsed_a, in_a, out_a = {}, 0, 0

    time.sleep(1)

    # 方案B（精简）
    print("  [方案B] 精简提示（优化后）...")
    try:
        raw_b, in_b, out_b, t_b = call_api(client, SYS_B, USER_B, text)
        parsed_b = parse_json(raw_b)
        print(f"    输入={in_b} tokens  输出={out_b} tokens  耗时={t_b:.1f}s")
    except Exception as e:
        print(f"    [错误] {e}")
        parsed_b, in_b, out_b = {}, 0, 0

    return {
        "id":       item["id"],
        "raw_text": text,
        "token_A":  {"input": in_a, "output": out_a, "total": in_a + out_a},
        "token_B":  {"input": in_b, "output": out_b, "total": in_b + out_b},
        "result_A": parsed_a,
        "result_B": parsed_b,
    }


def print_summary(results: list):
    total_a = sum(r["token_A"]["total"] for r in results)
    total_b = sum(r["token_B"]["total"] for r in results)
    saving  = (1 - total_b / total_a) * 100 if total_a else 0

    print(f"\n{'═'*55}")
    print("【Token 消耗汇总对比】")
    print(f"  {'条目':<6} {'方案A输入':>9} {'方案B输入':>9} {'节省':>7}")
    print(f"  {'─'*38}")
    for r in results:
        ia, ib = r["token_A"]["input"], r["token_B"]["input"]
        pct = (1 - ib / ia) * 100 if ia else 0
        print(f"  #{r['id']:<4}  {ia:>9}  {ib:>9}  {pct:>6.1f}%")
    print(f"  {'─'*38}")
    print(f"  {'合计':<6} {total_a:>9} {total_b:>9}  {saving:>6.1f}%")


def main():
    try:
        with open("raw_texts.json", "r", encoding="utf-8") as f:
            all_data = json.load(f)
    except FileNotFoundError:
        print("[错误] 未找到 raw_texts.json，请先运行 step1_crawl.py")
        return

    # 取前2条进行演示
    samples = all_data[:2]
    print(f"[信息] 共加载 {len(all_data)} 条，本次处理前 {len(samples)} 条\n")

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    results = []
    for item in samples:
        result = process_one(client, item)
        results.append(result)
        time.sleep(2)

    with open("extraction_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print_summary(results)

    print(f"\n{'═'*55}")
    print("【结构化结果预览 — 方案B（精简优化版）】")
    for r in results:
        print(f"\n─ 条目 #{r['id']}")
        print(json.dumps(r["result_B"], ensure_ascii=False, indent=2))

    print(f"\n[完成] 详细结果已保存到 extraction_results.json")


if __name__ == "__main__":
    main()
