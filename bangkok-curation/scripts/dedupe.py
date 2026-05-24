#!/usr/bin/env python3
"""
dedupe.py
raw_articles.json から重複を除去し、
既存の翻訳済み記事（articles.json）とマージして
data/articles.json を更新する
"""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
RAW_FILE     = DATA_DIR / "raw_articles.json"
ARTICLES_FILE = DATA_DIR / "articles.json"

# 古い記事を保持する日数
KEEP_DAYS = 7


def main():
    print("=== dedupe.py 開始 ===")

    raw: list[dict] = json.loads(RAW_FILE.read_text(encoding="utf-8"))

    # 既存の翻訳済み記事を読み込む（初回は空）
    existing: list[dict] = []
    if ARTICLES_FILE.exists():
        existing = json.loads(ARTICLES_FILE.read_text(encoding="utf-8"))

    # 既存記事をid辞書にする
    existing_map: dict[str, dict] = {a["id"]: a for a in existing}

    cutoff = datetime.now(timezone.utc) - timedelta(days=KEEP_DAYS)
    added = 0
    skipped_dup = 0
    skipped_old = 0

    for article in raw:
        aid = article["id"]

        # 既存に同じURLのものがあれば翻訳状態を引き継ぐだけ
        if aid in existing_map:
            skipped_dup += 1
            continue

        # 古すぎる記事は除外
        try:
            pub = datetime.fromisoformat(article["published_at"])
            if pub < cutoff:
                skipped_old += 1
                continue
        except Exception:
            pass

        existing_map[aid] = article
        added += 1

    # 古い記事を削除
    merged = [
        a for a in existing_map.values()
        if _is_recent(a["published_at"], cutoff)
    ]

    # 日付の新しい順に並べ替え
    merged.sort(key=lambda a: a["published_at"], reverse=True)

    ARTICLES_FILE.write_text(
        json.dumps(merged, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"追加: {added}件 / 重複スキップ: {skipped_dup}件 / 古いためスキップ: {skipped_old}件")
    print(f"合計 {len(merged)} 件を {ARTICLES_FILE} に保存")


def _is_recent(pub_str: str, cutoff: datetime) -> bool:
    try:
        pub = datetime.fromisoformat(pub_str)
        return pub >= cutoff
    except Exception:
        return True  # パース失敗は除外しない


if __name__ == "__main__":
    main()
