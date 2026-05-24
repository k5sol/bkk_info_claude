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

def fmt_date_ja(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso).astimezone(timezone.utc)
        wd = "月火水木金土日"[dt.weekday()]
        return f"{dt.month}月{dt.day}日（{wd}）"
    except Exception:
        return iso

def main():
    articles = json.loads((DATA_DIR / "articles.json").read_text(encoding="utf-8"))
    for a in articles:
        a["date_ja"] = fmt_date_ja(a.get("published_at", ""))

    news_articles  = [a for a in articles if a.get("category") == "news"]
    event_articles = [a for a in articles if a.get("category") == "events"]
    mall_articles  = [a for a in articles if a.get("category") == "mall_events"]
    # カレンダー用: event_start を持つイベント・モールイベントのみ
    ev_for_cal     = [a for a in articles
                      if a.get("category") in ("events", "mall_events")
                      and a.get("event_start")]

    updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # autoescape=True のまま、JSONは | safe で埋め込む
    env = Environment(loader=FileSystemLoader(str(TMPL_DIR)), autoescape=True)
    tmpl = env.get_template("index.html.j2")

    html = tmpl.render(
        news_articles=news_articles,
        event_articles=event_articles,
        mall_articles=mall_articles,
        updated_at=updated_at,
        # | safe で埋め込むためのJSON文字列
        ev_json=json.dumps(ev_for_cal, ensure_ascii=False),
    )

    (DOCS_DIR / "index.html").write_text(html, encoding="utf-8")
    (DOCS_DIR / "articles.json").write_text(
        json.dumps(articles, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"完了: {len(articles)}記事（ニュース{len(news_articles)} / イベント{len(event_articles)} / モール{len(mall_articles)}）")

if __name__ == "__main__":
    main()
