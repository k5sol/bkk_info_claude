#!/usr/bin/env python3
"""
fetch_sources.py
RSS取得 + 本文取得 + 構造化スクレイプ。
Googleニュース経由URLは元記事へリダイレクトして本文を取得する。
"""
import json, hashlib, sys, time, re
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
    "Accept-Language": "th,en;q=0.9",
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


def extract_dates_from_text(text: str) -> tuple[str | None, str | None]:
    """
    タイトルや本文のテキストから日程を正規表現で抽出する。
    タイ語の月名・日付パターン、英語の日付パターンに対応。
    返り値: (event_start, event_end) いずれもISO 8601文字列またはNone
    """
    # タイ語月名マッピング（略称）
    THAI_MONTHS = {
        'ม.ค.': 1, 'มกราคม': 1,
        'ก.พ.': 2, 'กุมภาพันธ์': 2,
        'มี.ค.': 3, 'มีนาคม': 3,
        'เม.ย.': 4, 'เมษายน': 4,
        'พ.ค.': 5, 'พฤษภาคม': 5,
        'มิ.ย.': 6, 'มิถุนายน': 6,
        'ก.ค.': 7, 'กรกฎาคม': 7,
        'ส.ค.': 8, 'สิงหาคม': 8,
        'ก.ย.': 9, 'กันยายน': 9,
        'ต.ค.': 10, 'ตุลาคม': 10,
        'พ.ย.': 11, 'พฤศจิกายน': 11,
        'ธ.ค.': 12, 'ธันวาคม': 12,
    }

    found_dates = []

    # タイ語日付パターン: "16 พ.ค. 2569" または "16 พฤษภาคม 2569"
    for month_th, month_num in THAI_MONTHS.items():
        pattern = rf'(\d{{1,2}})\s*{re.escape(month_th)}\s*(?:25)?(\d{{2}})'
        for m in re.finditer(pattern, text):
            day = int(m.group(1))
            year_raw = int(m.group(2))
            # 仏暦→西暦変換（2500台は-543、下2桁は2500+xx-543）
            year = (2500 + year_raw - 543) if year_raw < 100 else (year_raw - 543)
            if 2020 <= year <= 2030 and 1 <= day <= 31:
                found_dates.append(f"{year:04d}-{month_num:02d}-{day:02d}")

    # 英語日付パターン: "16 May 2026" or "May 16, 2026"
    EN_MONTHS = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
    }
    en_pat = r'(\d{1,2})\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*(\d{4})'
    for m in re.finditer(en_pat, text, re.IGNORECASE):
        day = int(m.group(1))
        month_num = EN_MONTHS[m.group(2).lower()[:3]]
        year = int(m.group(3))
        if 2020 <= year <= 2030:
            found_dates.append(f"{year:04d}-{month_num:02d}-{day:02d}")

    en_pat2 = r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*(\d{1,2}),?\s*(\d{4})'
    for m in re.finditer(en_pat2, text, re.IGNORECASE):
        month_num = EN_MONTHS[m.group(1).lower()[:3]]
        day = int(m.group(2))
        year = int(m.group(3))
        if 2020 <= year <= 2030:
            found_dates.append(f"{year:04d}-{month_num:02d}-{day:02d}")

    found_dates = sorted(set(found_dates))
    if not found_dates:
        return None, None
    if len(found_dates) == 1:
        return found_dates[0], None
    return found_dates[0], found_dates[-1]


def fetch_body(url: str, client: httpx.Client) -> str:
    """記事本文を取得。Googleニュース経由URLは自動リダイレクト後の本文を取得。"""
    for attempt in range(2):
        try:
            resp = client.get(url, timeout=TIMEOUT_BODY)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")
            for sel in [
                "article .entry-content", ".entry-content",
                ".post-content", ".article-content", ".content-body",
                "article", "main article", ".single-content", "main",
            ]:
                el = soup.select_one(sel)
                if el and len(el.get_text(strip=True)) > 200:
                    return el.get_text(" ", strip=True)[:4000]
            return soup.get_text(" ", strip=True)[:4000]
        except httpx.TimeoutException:
            print(f"x(TO)", end="", flush=True)
            time.sleep(2)
        except Exception:
            print(f"x(ER)", end="", flush=True)
            break
    return ""


def make_article(entry, source: dict, body: str = "") -> dict:
    link = entry.get("link", "")
    pub  = (entry.get("published") or entry.get("updated")
            or entry.get("dc_date") or None)
    summary = (entry.get("summary")
               or (entry.get("content") or [{}])[0].get("value", "") or "")

    title = clean_html(entry.get("title", ""))
    summary_clean = clean_html(summary)

    # タイトル＋要約から日程を事前抽出（本文なしでも日程を取れるケースがある）
    date_text = f"{title} {summary_clean} {body[:500]}"
    pre_start, pre_end = extract_dates_from_text(date_text)

    return {
        "id":               url_hash(link),
        "source_id":        source["id"],
        "source_name":      source["name"],
        "category":         source["category"],
        "lang":             source.get("lang", "th"),
        "title_original":   title,
        "summary_original": summary_clean,
        "body_original":    body,
        "url":              link,
        "image_url":        extract_image(entry),
        "published_at":     normalize_date(pub),
        "fetched_at":       datetime.now(timezone.utc).isoformat(),
        "translated":       False,
        "event_start":      pre_start,   # 事前抽出（Claudeが上書き可能）
        "event_end":        pre_end,
        "event_venue":      None,
        "event_admission":  None,
    }


def fetch_rss(source: dict, client: httpx.Client) -> list[dict]:
    fulltext = source.get("type") in ("rss_fulltext",)
    label = "FULL" if fulltext else "RSS "
    print(f"  [{label}] {source['name']} …", end=" ", flush=True)
    try:
        feed = feedparser.parse(source["url"], request_headers=HEADERS)
        if not feed.entries:
            print("FAIL (エントリなし)")
            return []

        articles = []
        for entry in feed.entries[: source.get("max_items", 20)]:
            if not entry.get("link"):
                continue
            body = ""
            if fulltext:
                body = fetch_body(entry["link"], client)
                print("." if body else "x", end="", flush=True)
                time.sleep(0.5)
            articles.append(make_article(entry, source, body))

        has_body   = sum(1 for a in articles if a.get("body_original"))
        has_date   = sum(1 for a in articles if a.get("event_start"))
        if fulltext:
            print(f" OK ({len(articles)}件, 本文:{has_body}件, 日程抽出:{has_date}件)")
        else:
            print(f"OK ({len(articles)}件, 日程抽出:{has_date}件)")
        return articles

    except Exception as e:
        print(f"FAIL: {e}")
        return []


def fetch_scrape_structured(source: dict, client: httpx.Client) -> list[dict]:
    """ThaiTicketMajor等の構造化ページをスクレイプ"""
    print(f"  [SCRP] {source['name']} …", end=" ", flush=True)
    rules = source.get("scrape_rules", {})
    try:
        resp = client.get(source["url"], timeout=TIMEOUT_BODY)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        base = "/".join(source["url"].split("/")[:3])

        items = soup.select(rules.get("item_selector", "article"))
        articles = []
        seen = set()

        for item in items[: source.get("max_items", 15)]:
            a_el = item.select_one(rules.get("link_selector", "a"))
            href = a_el.get("href", "") if a_el else ""
            if not href or href in seen:
                continue
            if not href.startswith("http"):
                href = base + href
            seen.add(href)

            t_el = item.select_one(rules.get("title_selector", "h2"))
            title = t_el.get_text(strip=True) if t_el else ""
            if not title:
                continue

            d_el = item.select_one(rules.get("date_selector", "time"))
            date_text = ""
            if d_el:
                date_text = d_el.get("datetime", "") or d_el.get_text(strip=True)

            combined = f"{title} {date_text}"
            pre_start, pre_end = extract_dates_from_text(combined)

            img = item.select_one("img")
            img_url = img.get("src") if img else None
            if img_url and not img_url.startswith("http"):
                img_url = base + img_url

            articles.append({
                "id":               url_hash(href),
                "source_id":        source["id"],
                "source_name":      source["name"],
                "category":         source["category"],
                "lang":             source.get("lang", "th"),
                "title_original":   title,
                "summary_original": date_text,
                "body_original":    "",
                "url":              href,
                "image_url":        img_url,
                "published_at":     datetime.now(timezone.utc).isoformat(),
                "fetched_at":       datetime.now(timezone.utc).isoformat(),
                "translated":       False,
                "event_start":      pre_start,
                "event_end":        pre_end,
                "event_venue":      source["name"],
                "event_admission":  None,
            })

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
            if source.get("type") == "scrape_structured":
                articles = fetch_scrape_structured(source, client)
            else:
                articles = fetch_rss(source, client)
            all_articles.extend(articles)

    RAW_FILE.write_text(
        json.dumps(all_articles, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    pre_dates = sum(1 for a in all_articles if a.get("event_start"))
    print(f"\n合計 {len(all_articles)} 件 (うち日程事前抽出済み: {pre_dates}件) を {RAW_FILE} に保存")


if __name__ == "__main__":
    main()
