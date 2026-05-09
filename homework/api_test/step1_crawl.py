"""
step1_crawl.py

目标：豆瓣电影 Top250 列表页（仅第1页，25条）
URL：https://movie.douban.com/top250

列表页每条记录包含：
  - 电影名（含外文名）
  - 导演 / 主演 / 年份 / 国家 / 类型（混在一个 <p> 里，无统一分隔）
  - 豆瓣评分 + 评价人数
  - 编辑推荐一句话

这些字段混杂在 HTML 不同标签中，爬下来拼成一段非结构化纯文本，
无法用简单正则直接解析为结构化字段，需借助大模型语义理解。
"""

import requests
from bs4 import BeautifulSoup
import json

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://movie.douban.com/",
}

URL = "https://movie.douban.com/top250?start=0"


def crawl():
    resp = requests.get(URL, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    raw_texts = []
    for item in soup.select("ol.grid_view li"):

        # 片名（主标题 + 可能有副标题/外文名）
        title_main  = item.select_one(".title")
        title_other = item.select_one(".other")
        title_str   = title_main.get_text(strip=True) if title_main else ""
        if title_other:
            title_str += " " + title_other.get_text(strip=True)

        # 导演/主演/年份/国家/类型（全混在 .bd > p 的文本里，含换行和多余空格）
        info_tag   = item.select_one(".bd p")
        info_raw   = info_tag.get_text(" ", strip=False) if info_tag else ""
        info_lines = [" ".join(l.split()) for l in info_raw.splitlines()]
        info_str   = "\n".join(l for l in info_lines if l)

        # 评分 + 评价人数
        rating     = item.select_one(".rating_num")
        rating_str = rating.get_text(strip=True) if rating else ""
        people     = item.select_one(".star span:last-child")
        people_str = people.get_text(strip=True) if people else ""

        # 编辑推荐一句话
        quote     = item.select_one(".inq")
        quote_str = quote.get_text(strip=True) if quote else ""

        # 拼接成非结构化文本（不加字段标签，各来源直接拼接）
        raw_text = f"{title_str}\n{info_str}\n评分：{rating_str}  {people_str}"
        if quote_str:
            raw_text += f"\n{quote_str}"

        raw_texts.append({
            "id":       len(raw_texts) + 1,
            "raw_text": raw_text.strip(),
        })

    return raw_texts


def main():
    print("[爬虫] 正在请求豆瓣电影 Top250 第1页...")
    try:
        data = crawl()
    except Exception as e:
        print(f"[错误] {e}")
        return

    with open("raw_texts.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[完成] 共爬取 {len(data)} 条，已保存到 raw_texts.json")
    print("\n=== 前3条预览 ===")
    for item in data[:3]:
        print(f"\n[{item['id']}]\n{item['raw_text']}")
        print("─" * 40)


if __name__ == "__main__":
    main()