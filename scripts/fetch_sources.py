#!/usr/bin/env python3
"""
fetch_sources.py
RSS取得 + TAT記事は本文も取得して data/raw_articles.json に保存する
"""
import json, hashlib, sys
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
    "User-Agent": "Mozilla/5.0 (compatible; BangkokCurationBot/1.0)",
    "Accept-Language": "th,en;q=0.9",
}
TIMEOUT = 20


def url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def normalize_date(raw: str | None) -> str:
    if not raw:
        return datetime.now(timezone.utc).isoformat()
    try:
        return dateparser.parse(raw, fuzzy=True).astimezone(timezone.utc).isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()


def clean_html(text: str | None, maxlen: int = 1000) -> str:
    if not text:
        return ""
    return BeautifulSoup(text, "lxml").get_text(" ", strip=True)[:maxlen]


def extract_image(entry) -> str | None:
    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        return entry.media_thumbnail[0].get("url")
    for enc in entry.get("enclosures", []):
        if enc.get("type", "").startswith("image/"):
            return enc.get("url")
    content = (entry.get("content") or [{}])[0].get("value", "") or entry.get("summary", "")
    if content:
        soup = BeautifulSoup(content, "lxml")
        img = soup.find("img")
        if img and img.get("src"):
            return img["src"]
    return None


def fetch_article_body(url: str, client: httpx.Client) -> str:
    """記事本文を取得してテキストを返す（TAT用）"""
    try:
        resp = client.get(url, timeout=TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        # 本文候補セレクタを順に試す
        for sel in ["article", ".entry-content", ".post-content", "main"]:
            el = soup.select_one(sel)
            if el:
                return el.get_text(" ", strip=True)[:3000]
        return soup.get_text(" ", strip=True)[:3000]
    except Exception:
        return ""


def make_article(entry, source: dict, body: str = "") -> dict:
    link = entry.get("link", "")
    pub  = (entry.get("published") or entry.get("updated")
            or entry.get("dc_date") or None)
    summary = (entry.get("summary")
               or (entry.get("content") or [{}])[0].get("value", "") or "")
    return {
        "id":               url_hash(link),
        "source_id":        source["id"],
        "source_name":      source["name"],
        "category":         source["category"],
        "lang":             source.get("lang", "th"),
        "title_original":   clean_html(entry.get("title", "")),
        "summary_original": clean_html(summary),
        "body_original":    body,           # TAT記事のみ本文あり
        "url":              link,
        "image_url":        extract_image(entry),
        "published_at":     normalize_date(pub),
        "fetched_at":       datetime.now(timezone.utc).isoformat(),
        "translated":       False,
        "event_start":      None,
        "event_end":        None,
        "event_venue":      None,
        "event_admission":  None,
    }


def fetch_rss(source: dict, client: httpx.Client | None = None) -> list[dict]:
    print(f"  [RSS] {source['name']} …", end=" ", flush=True)
    fulltext = source.get("type") == "rss_fulltext"
    try:
        feed = feedparser.parse(source["url"], request_headers=HEADERS)
        articles = []
        for entry in feed.entries[: source.get("max_items", 20)]:
            if not entry.get("link"):
                continue
            body = ""
            if fulltext and client:
                body = fetch_article_body(entry["link"], client)
            articles.append(make_article(entry, source, body))
        print(f"OK ({len(articles)}件)")
        return articles
    except Exception as e:
        print(f"FAIL: {e}")
        return []


def main():
    print("=== fetch_sources.py 開始 ===")
    all_articles: list[dict] = []

    with httpx.Client(headers=HEADERS, follow_redirects=True) as client:
        for source in SOURCES:
            articles = fetch_rss(source, client)
            all_articles.extend(articles)

    RAW_FILE.write_text(
        json.dumps(all_articles, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n合計 {len(all_articles)} 件を {RAW_FILE} に保存")


if __name__ == "__main__":
    main()
