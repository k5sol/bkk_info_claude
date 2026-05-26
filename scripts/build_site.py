#!/usr/bin/env python3
"""build_site.py — articles.json → docs/index.html"""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

DATA_DIR = Path(__file__).parent.parent / "data"
TMPL_DIR = Path(__file__).parent.parent / "templates"
DOCS_DIR = Path(__file__).parent.parent / "docs"
DOCS_DIR.mkdir(exist_ok=True)

CATEGORY_LABELS = {
    "ja_news":       "日本語サイト",
    "privilege":     "Thailand Privilege",
    "news_domestic": "国内ニュース",
    "news_intl":     "国際ニュース",
    "events":        "イベント・祭り",
    "mall_events":   "モールイベント",
}

# カレンダー・今日のイベントに表示する最大期間（日）
# これを超える長期キャンペーンはカレンダー/今日のイベントから除外
MAX_EVENT_DAYS = 14


def fmt_date_ja(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso).astimezone(timezone.utc)
        wd = "月火水木金土日"[dt.weekday()]
        return f"{dt.month}月{dt.day}日（{wd}）"
    except Exception:
        return iso


def event_duration_days(article: dict) -> int | None:
    """イベントの期間（日数）を返す。終了日不明はNone"""
    try:
        s = datetime.fromisoformat(article["event_start"])
        e = datetime.fromisoformat(article["event_end"]) if article.get("event_end") else None
        if e:
            return (e - s).days
    except Exception:
        pass
    return None


def is_short_event(article: dict) -> bool:
    """MAX_EVENT_DAYS 以内の短期イベントかどうか"""
    days = event_duration_days(article)
    if days is None:
        return True   # 単日イベントは表示する
    return days <= MAX_EVENT_DAYS


def main():
    articles = json.loads((DATA_DIR / "articles.json").read_text(encoding="utf-8"))
    articles = [a for a in articles if a.get("category") in CATEGORY_LABELS]

    now_utc = datetime.now(timezone.utc)
    today_str = now_utc.strftime("%Y-%m-%d")

    for a in articles:
        a["date_ja"] = fmt_date_ja(a.get("published_at", ""))

    by_cat: dict[str, list] = {}
    for a in articles:
        by_cat.setdefault(a.get("category"), []).append(a)

    # カレンダー用（event_startがあり、MAX_EVENT_DAYS以内のイベントのみ）
    ev_for_cal = [
        a for a in articles
        if a.get("category") in ("events", "mall_events")
        and a.get("event_start")
        and is_short_event(a)
    ]

    # 今日のイベント（カレンダーと同じデータから抽出）
    todays_events = [
        a for a in ev_for_cal
        if a.get("event_start", "") <= today_str
        and (not a.get("event_end") or a.get("event_end", "") >= today_str)
    ]

    # 新着記事：カテゴリ順 × 直近48時間
    cutoff_48h = now_utc - timedelta(hours=48)
    cat_order = list(CATEGORY_LABELS.keys())

    recent_by_cat: dict[str, list] = {}
    for a in articles:
        try:
            pub = datetime.fromisoformat(a.get("published_at", ""))
            if pub >= cutoff_48h:
                cat = a.get("category", "")
                recent_by_cat.setdefault(cat, []).append(a)
        except Exception:
            pass

    # カテゴリ順に並べて各カテゴリ最大8件
    recent_articles: list[dict] = []
    for cat in cat_order:
        items = sorted(
            recent_by_cat.get(cat, []),
            key=lambda x: x.get("published_at", ""),
            reverse=True,
        )[:8]
        recent_articles.extend(items)

    updated_at = now_utc.strftime("%Y-%m-%d %H:%M UTC")
    env = Environment(loader=FileSystemLoader(str(TMPL_DIR)), autoescape=True)
    html = env.get_template("index.html.j2").render(
        by_cat=by_cat,
        category_labels=CATEGORY_LABELS,
        updated_at=updated_at,
        today_str=today_str,
        total=len(articles),
        ev_json=json.dumps(ev_for_cal, ensure_ascii=False),
        todays_events_json=json.dumps(todays_events, ensure_ascii=False),
        recent_articles_json=json.dumps(recent_articles, ensure_ascii=False),
        cat_order_json=json.dumps(cat_order, ensure_ascii=False),
        cat_labels_json=json.dumps(CATEGORY_LABELS, ensure_ascii=False),
    )

    (DOCS_DIR / "index.html").write_text(html, encoding="utf-8")
    (DOCS_DIR / "articles.json").write_text(
        json.dumps(articles, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    counts = {k: len(v) for k, v in by_cat.items()}
    print(f"完了: 合計{len(articles)}記事 {counts}")
    print(f"今日のイベント: {len(todays_events)}件 / カレンダー対象: {len(ev_for_cal)}件 / 新着48h: {len(recent_articles)}件")


if __name__ == "__main__":
    main()
