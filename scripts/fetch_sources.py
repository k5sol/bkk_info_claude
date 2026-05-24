#!/usr/bin/env python3
"""
fetch_sources.py
RSS フィードの取得とウェブスクレイピングを行い
data/raw_articles.json に保存する
"""
import json
import re
import sys
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import feedparser
import httpx
from bs4 import BeautifulSoup
from dateutil import parser as dateparser

sys.path.insert(0, str(Path(__file__).parent))
from sources_config import SOURCES

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
RAW_FILE = DATA_DIR / "raw_articles.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; BangkokCurationBot/1.0; "
        "+https://github.com/your-username/bangkok-curation)"
    ),
    "Accept-Language": "th,en;q=0.9",
}
TIMEOUT = 20


def url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def normalize_date(raw: str | None) -> str:
    """不正形式の日付文字列を ISO 8601 に正規化する。失敗時は現在時刻。"""
    if not raw:
        return datetime.now(timezone.utc).isoformat()
    try:
        return dateparser.parse(raw, fuzzy=True).astimezone(timezone.utc).isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()


def clean_html(text: str | None) -> str:
    if not text:
        return ""
    return BeautifulSoup(text, "lxml").get_text(" ", strip=True)[:1000]


# ─── RSS 取得 ───────────────────────────────────────────────────────────────

def fetch_rss(source: dict) -> list[dict]:
    print(f"  [RSS] {source['name']} …", end=" ", flush=True)
    try:
        feed = feedparser.parse(
            source["url"],
            request_headers=HEADERS,
        )
        articles = []
        for entry in feed.entries[: source.get("max_items", 20)]:
            link = entry.get("link", "")
            if not link:
                continue
            pub = (
                entry.get("published")
                or entry.get("updated")
                or entry.get("dc_date")
                or None
            )
            summary = (
                entry.get("summary")
                or entry.get("content", [{}])[0].get("value", "")
                or ""
            )
            articles.append(
                {
                    "id": url_hash(link),
                    "source_id": source["id"],
                    "source_name": source["name"],
                    "category": source["category"],
                    "title_original": clean_html(entry.get("title", "")),
                    "summary_original": clean_html(summary),
                    "url": link,
                    "image_url": _extract_image(entry),
                    "published_at": normalize_date(pub),
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                    "translated": False,
                }
            )
        print(f"OK ({len(articles)}件)")
        return articles
    except Exception as e:
        print(f"FAIL: {e}")
        return []


def _extract_image(entry) -> str | None:
    """RSS エントリから画像URLを探す"""
    # media:thumbnail
    if hasattr(entry, "media_thumbnail"):
        imgs = entry.media_thumbnail
        if imgs:
            return imgs[0].get("url")
    # enclosure
    for enc in entry.get("enclosures", []):
        if enc.get("type", "").startswith("image/"):
            return enc.get("url")
    # content の img タグ
    content = entry.get("content", [{}])[0].get("value", "") or entry.get("summary", "")
    if content:
        soup = BeautifulSoup(content, "lxml")
        img = soup.find("img")
        if img and img.get("src"):
            return img["src"]
    return None


# ─── スクレイピング ──────────────────────────────────────────────────────────

def fetch_scrape(source: dict, client: httpx.Client) -> list[dict]:
    print(f"  [Scrape] {source['name']} …", end=" ", flush=True)
    rules = source.get("scrape_rules", {})

    # tatnewsはフィードURLなのでfeedparserで処理
    if source["url"].endswith("/feed/") or "feed" in source["url"]:
        return fetch_rss({**source, "type": "rss"})

    try:
        resp = client.get(source["url"], timeout=TIMEOUT)
        resp.raise_for_status()
    except Exception as e:
        print(f"FAIL: {e}")
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    base_url = "/".join(source["url"].split("/")[:3])

    item_sel  = rules.get("item_selector",  "article")
    title_sel = rules.get("title_selector", "h2, h3")
    date_sel  = rules.get("date_selector",  "time")
    link_sel  = rules.get("link_selector",  "a")
    img_sel   = rules.get("image_selector", "img")

    items = soup.select(item_sel)
    articles = []
    seen = set()

    for item in items[: source.get("max_items", 10)]:
        # リンク
        a = item.select_one(link_sel)
        href = a["href"] if a and a.get("href") else ""
        if not href:
            continue
        if not href.startswith("http"):
            href = base_url + href
        if href in seen:
            continue
        seen.add(href)

        # タイトル
        t_el = item.select_one(title_sel)
        title = t_el.get_text(strip=True) if t_el else ""
        if not title:
            continue

        # 日付
        d_el = item.select_one(date_sel)
        raw_date = (
            d_el.get("datetime") or d_el.get_text(strip=True)
            if d_el
            else None
        )

        # 概要（タイトル・日付・リンク要素以外のテキスト）
        for el in item.select(f"{title_sel}, {date_sel}, {link_sel}"):
            el.decompose()
        summary = item.get_text(" ", strip=True)[:500]

        # 画像
        img = item.select_one(img_sel)
        img_url = img.get("src") or img.get("data-src") if img else None
        if img_url and not img_url.startswith("http"):
            img_url = base_url + img_url

        articles.append(
            {
                "id": url_hash(href),
                "source_id": source["id"],
                "source_name": source["name"],
                "category": source["category"],
                "title_original": title,
                "summary_original": summary,
                "url": href,
                "image_url": img_url,
                "published_at": normalize_date(raw_date),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "translated": False,
            }
        )

    print(f"OK ({len(articles)}件)")
    return articles


# ─── メイン ─────────────────────────────────────────────────────────────────

def main():
    print("=== fetch_sources.py 開始 ===")
    all_articles: list[dict] = []

    with httpx.Client(headers=HEADERS, follow_redirects=True) as client:
        for source in SOURCES:
            if source["type"] == "rss":
                articles = fetch_rss(source)
            else:
                articles = fetch_scrape(source, client)
            all_articles.extend(articles)

    RAW_FILE.write_text(
        json.dumps(all_articles, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n合計 {len(all_articles)} 件を {RAW_FILE} に保存")


if __name__ == "__main__":
    main()
