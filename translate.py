#!/usr/bin/env python3
"""
fetch_sources.py
RSS取得。TAT記事（rss_fulltext）は本文も取得する。
"""
import json, hashlib, sys, time
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
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,th;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
TIMEOUT_RSS  = 30
TIMEOUT_BODY = 20


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


def fetch_body(url: str, client: httpx.Client) -> str:
    """記事本文を取得（失敗しても空文字で続行）"""
    for attempt in range(2):
        try:
            resp = client.get(url, timeout=TIMEOUT_BODY)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")
            for sel in ["article .entry-content", ".entry-content",
                        "article", ".post-content", "main article", "main"]:
                el = soup.select_one(sel)
                if el and len(el.get_text(strip=True)) > 200:
                    return el.get_text(" ", strip=True)[:4000]
            return soup.get_text(" ", strip=True)[:4000]
        except httpx.TimeoutException:
            print(f"      本文取得タイムアウト (attempt {attempt+1}): {url[:60]}")
            time.sleep(2)
        except Exception as e:
            print(f"      本文取得エラー: {e}")
            break
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
        "body_original":    body,
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


def fetch_rss(source: dict, client: httpx.Client) -> list[dict]:
    fulltext = source.get("type") == "rss_fulltext"
    print(f"  [{'FULL' if fulltext else 'RSS '}] {source['name']} …", end=" ", flush=True)
    try:
        feed = feedparser.parse(source["url"], request_headers=HEADERS,
                                request_parameters={"timeout": TIMEOUT_RSS})
        if not feed.entries:
            # feedparserがタイムアウト等で失敗した場合
            print(f"FAIL (エントリなし)")
            return []

        articles = []
        for entry in feed.entries[: source.get("max_items", 20)]:
            if not entry.get("link"):
                continue
            body = ""
            if fulltext:
                body = fetch_body(entry["link"], client)
                if body:
                    print(f".", end="", flush=True)  # 進捗表示
                else:
                    print(f"x", end="", flush=True)  # 取得失敗
                time.sleep(0.5)  # サーバー負荷軽減
            articles.append(make_article(entry, source, body))

        has_body = sum(1 for a in articles if a.get("body_original"))
        if fulltext:
            print(f" OK ({len(articles)}件, 本文取得:{has_body}件)")
        else:
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
