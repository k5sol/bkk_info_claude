#!/usr/bin/env python3
"""
debug_calendar.py
articles.json を読んでカレンダーに表示されるべきイベント一覧を出力する
問題の切り分けに使う
"""
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
ARTICLES_FILE = DATA_DIR / "articles.json"

def main():
    if not ARTICLES_FILE.exists():
        print("articles.json が見つかりません")
        return

    articles = json.loads(ARTICLES_FILE.read_text(encoding="utf-8"))
    print(f"総記事数: {len(articles)}")
    print()

    cats = {}
    for a in articles:
        c = a.get("category","?")
        cats[c] = cats.get(c,0) + 1
    print("カテゴリ別件数:")
    for c,n in sorted(cats.items()):
        print(f"  {c}: {n}件")
    print()

    # カレンダー対象（event_start があるもの）
    ev_articles = [
        a for a in articles
        if a.get("category") in ("events","mall_events")
        and a.get("event_start")
    ]
    print(f"カレンダー表示対象: {len(ev_articles)}件")
    for a in ev_articles:
        print(f"  [{a['category']}] {a.get('event_start','')} 〜 {a.get('event_end','')}")
        print(f"    タイトル: {a.get('title_ja') or a.get('title_original','')}")
        print(f"    会場: {a.get('event_venue','')}")
        print()

    # event_startがないイベント記事
    no_date = [
        a for a in articles
        if a.get("category") in ("events","mall_events")
        and not a.get("event_start")
    ]
    if no_date:
        print(f"⚠ event_startなし（カレンダー非表示）: {len(no_date)}件")
        for a in no_date:
            print(f"  [{a['category']}] translated={a.get('translated')} "
                  f"split_from={a.get('split_from','')}")
            print(f"    {a.get('title_ja') or a.get('title_original','')[:60]}")

if __name__ == "__main__":
    main()
