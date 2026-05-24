#!/usr/bin/env python3
"""build_site.py — articles.json → docs/index.html"""
import json
from datetime import datetime, timezone
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

DATA_DIR = Path(__file__).parent.parent / "data"
TMPL_DIR = Path(__file__).parent.parent / "templates"
DOCS_DIR = Path(__file__).parent.parent / "docs"
DOCS_DIR.mkdir(exist_ok=True)

CATEGORY_LABELS = {
    "ja_news":       "日本語サイト",
    "news_domestic": "国内ニュース",
    "news_intl":     "国際ニュース",
    "events":        "イベント・祭り",
    "mall_events":   "モールイベント",
}

def fmt_date_ja(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso).astimezone(timezone.utc)
        wd = "月火水木金土日"[dt.weekday()]
        return f"{dt.month}月{dt.day}日（{wd}）"
    except Exception:
        return iso

def main():
    articles = json.loads((DATA_DIR / "articles.json").read_text(encoding="utf-8"))

    # 非表示カテゴリ除外
    articles = [a for a in articles if a.get("category") in CATEGORY_LABELS]

    for a in articles:
        a["date_ja"] = fmt_date_ja(a.get("published_at", ""))

    by_cat = {}
    for a in articles:
        by_cat.setdefault(a.get("category"), []).append(a)

    ev_for_cal = [
        a for a in articles
        if a.get("category") in ("events", "mall_events") and a.get("event_start")
    ]

    updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    env = Environment(loader=FileSystemLoader(str(TMPL_DIR)), autoescape=True)
    html = env.get_template("index.html.j2").render(
        by_cat=by_cat,
        category_labels=CATEGORY_LABELS,
        updated_at=updated_at,
        total=len(articles),
        ev_json=json.dumps(ev_for_cal, ensure_ascii=False),
    )

    (DOCS_DIR / "index.html").write_text(html, encoding="utf-8")
    (DOCS_DIR / "articles.json").write_text(
        json.dumps(articles, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    counts = {k: len(v) for k, v in by_cat.items()}
    print(f"完了: 合計{len(articles)}記事 {counts}")

if __name__ == "__main__":
    main()
