#!/usr/bin/env python3
"""
build_site.py
articles.json から静的 HTML (docs/index.html) を生成する
GitHub Pages は docs/ フォルダをサーブする設定を想定
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

DATA_DIR  = Path(__file__).parent.parent / "data"
TMPL_DIR  = Path(__file__).parent.parent / "templates"
DOCS_DIR  = Path(__file__).parent.parent / "docs"

DOCS_DIR.mkdir(exist_ok=True)

CATEGORY_LABELS = {
    "news":        "ニュース",
    "events":      "イベント・祭り",
    "mall_events": "モールイベント",
}


def format_date_ja(iso_str: str) -> str:
    """ISO 8601 → 日本語日付文字列"""
    try:
        dt = datetime.fromisoformat(iso_str).astimezone(
            timezone.utc
        )
        weekdays = "月火水木金土日"
        wd = weekdays[dt.weekday()]
        return f"{dt.month}月{dt.day}日（{wd}）"
    except Exception:
        return iso_str


def main():
    print("=== build_site.py 開始 ===")

    articles: list[dict] = json.loads(
        (DATA_DIR / "articles.json").read_text(encoding="utf-8")
    )

    # カテゴリ別に分類
    by_category: dict[str, list] = {}
    for a in articles:
        cat = a.get("category", "news")
        by_category.setdefault(cat, []).append(a)

    # 日付フォーマットを付与
    for a in articles:
        a["date_ja"] = format_date_ja(a.get("published_at", ""))

    updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    env = Environment(loader=FileSystemLoader(str(TMPL_DIR)), autoescape=True)
    tmpl = env.get_template("index.html.j2")

    html = tmpl.render(
        articles=articles,
        by_category=by_category,
        category_labels=CATEGORY_LABELS,
        updated_at=updated_at,
        total=len(articles),
    )

    out = DOCS_DIR / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"生成完了: {out}  ({len(articles)}記事)")

    # articles.json も docs/ にコピー（フロントエンドから参照可能に）
    (DOCS_DIR / "articles.json").write_text(
        json.dumps(articles, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("docs/articles.json もコピー済み")


if __name__ == "__main__":
    main()
