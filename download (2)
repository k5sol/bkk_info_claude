#!/usr/bin/env python3
"""
reset_events.py
イベント系記事（events / mall_events）の翻訳フラグをリセットして
次回実行時に再取得・再分離させる。
ニュース記事はそのまま保持。

使い方: python scripts/reset_events.py
"""
import json
from pathlib import Path

DATA_DIR      = Path(__file__).parent.parent / "data"
ARTICLES_FILE = DATA_DIR / "articles.json"

def main():
    if not ARTICLES_FILE.exists():
        print("articles.json が見つかりません")
        return

    articles = json.loads(ARTICLES_FILE.read_text(encoding="utf-8"))
    before = len(articles)

    # イベント系・TATの子記事（split_from あり）を全て削除してリセット
    cleaned = []
    removed_split = 0
    reset_count   = 0

    for a in articles:
        cat = a.get("category", "")
        # TATから分離した子記事は削除
        if a.get("split_from"):
            removed_split += 1
            continue
        # TAT親記事・モールイベントは翻訳フラグをリセット
        if cat in ("events", "mall_events"):
            a["translated"]    = False
            a["event_start"]   = None
            a["event_end"]     = None
            a["event_venue"]   = None
            a["event_admission"] = None
            a.pop("title_ja",   None)
            a.pop("summary_ja", None)
            reset_count += 1
        cleaned.append(a)

    # raw_articles.json もリセット（次回fetch時に上書きされるが念のため）
    raw_file = DATA_DIR / "raw_articles.json"
    if raw_file.exists():
        raw_file.write_text("[]", encoding="utf-8")

    ARTICLES_FILE.write_text(
        json.dumps(cleaned, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"完了: 子イベント削除 {removed_split}件 / 親記事リセット {reset_count}件")
    print(f"記事数: {before} → {len(cleaned)}")
    print("\n次のステップ:")
    print("  python scripts/fetch_sources.py")
    print("  python scripts/translate.py")
    print("  python scripts/build_site.py")

if __name__ == "__main__":
    main()
