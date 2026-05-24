#!/usr/bin/env python3
"""
translate.py
未翻訳の記事を Claude API (Haiku) で日本語化する
コスト節約のため:
  - 翻訳済みはスキップ
  - タイトル+要約のみ翻訳（本文は取得しない）
  - バッチ処理で API コールを最小化
"""
import json
import os
import sys
import time
from pathlib import Path

import anthropic

DATA_DIR = Path(__file__).parent.parent / "data"
ARTICLES_FILE = DATA_DIR / "articles.json"

# 1回のAPIコールで翻訳する記事数
BATCH_SIZE = 5

SYSTEM_PROMPT = """\
あなたはタイ語→日本語の翻訳・情報抽出の専門家です。
バンコク在住の日本人向けに、ニュース・イベント情報を自然な日本語に翻訳します。

ルール:
- 固有名詞（地名・人名・施設名）はタイ語読みをカタカナ表記し、英語があれば括弧に添える
- 通貨はバーツ（THB）のまま。金額は「1,000バーツ」形式
- 日付は「5月24日（日）」形式
- 要約は2〜4文の簡潔な日本語にまとめる
- JSONのみ返答し、説明文は不要
"""

def build_batch_prompt(articles: list[dict]) -> str:
    items = []
    for a in articles:
        is_event = a.get("category") in ("events", "mall_events")
        event_note = (
            "\n※ このイベント記事からは開催日時・場所・入場料も抽出してください。"
            if is_event else ""
        )
        items.append(
            f"ID: {a['id']}\n"
            f"CATEGORY: {a.get('category', 'news')}\n"
            f"TITLE: {a['title_original']}\n"
            f"SUMMARY: {a['summary_original']}"
            f"{event_note}"
        )
    batch_text = "\n\n---\n\n".join(items)

    return f"""\
以下の記事を日本語に翻訳・情報抽出してください。
各記事のIDを必ず保持し、以下のJSON配列形式で返してください。

ニュース記事の場合:
{{
  "id": "記事ID",
  "title_ja": "日本語タイトル",
  "summary_ja": "日本語要約（2〜4文）"
}}

イベント記事（category が events または mall_events）の場合は追加フィールドも含めてください:
{{
  "id": "記事ID",
  "title_ja": "日本語タイトル",
  "summary_ja": "日本語要約（2〜4文）",
  "event_start": "ISO 8601形式の開催開始日時（例: 2026-06-14T10:00:00）。不明な場合は日付のみ（例: 2026-06-14）",
  "event_end": "ISO 8601形式の開催終了日時。単日イベントや不明な場合はnull",
  "event_venue": "開催場所の日本語名（例: アイコンサイアム 1Fリバーパーク）",
  "event_admission": "入場料（例: 無料、500バーツ〜）。不明な場合はnull"
}}

開催日時が記事から読み取れない場合は event_start をnullにしてください。

記事:
{batch_text}
"""


def translate_batch(
    client: anthropic.Anthropic,
    articles: list[dict],
    retry: int = 2,
) -> dict[str, dict]:
    """記事リストを翻訳し {id: {title_ja, summary_ja}} を返す"""
    prompt = build_batch_prompt(articles)

    for attempt in range(retry + 1):
        try:
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = message.content[0].text.strip()

            # JSON部分だけ抽出（```json ... ``` ブロック対応）
            if "```" in raw:
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]

            results = json.loads(raw)
            return {r["id"]: r for r in results}

        except json.JSONDecodeError as e:
            print(f"    JSON解析エラー (attempt {attempt+1}): {e}")
            if attempt == retry:
                return {}
            time.sleep(2)
        except anthropic.RateLimitError:
            wait = 10 * (attempt + 1)
            print(f"    レート制限 → {wait}秒待機")
            time.sleep(wait)
        except Exception as e:
            print(f"    API エラー: {e}")
            if attempt == retry:
                return {}
            time.sleep(3)

    return {}


def main():
    print("=== translate.py 開始 ===")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY が設定されていません", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    articles: list[dict] = json.loads(ARTICLES_FILE.read_text(encoding="utf-8"))

    # 未翻訳のものだけ対象にする
    untranslated = [a for a in articles if not a.get("translated")]
    print(f"未翻訳: {len(untranslated)}件 / 翻訳済み: {len(articles) - len(untranslated)}件")

    if not untranslated:
        print("翻訳対象なし。終了。")
        return

    # バッチ処理
    translated_count = 0
    for i in range(0, len(untranslated), BATCH_SIZE):
        batch = untranslated[i : i + BATCH_SIZE]
        print(f"  バッチ {i//BATCH_SIZE + 1}: {len(batch)}件を翻訳中…", end=" ", flush=True)

        results = translate_batch(client, batch)

        for article in batch:
            if article["id"] in results:
                r = results[article["id"]]
                article["title_ja"]   = r.get("title_ja",   article["title_original"])
                article["summary_ja"] = r.get("summary_ja", "")
                # イベント専用フィールド
                if article.get("category") in ("events", "mall_events"):
                    article["event_start"]     = r.get("event_start")
                    article["event_end"]       = r.get("event_end")
                    article["event_venue"]     = r.get("event_venue")
                    article["event_admission"] = r.get("event_admission")
                article["translated"] = True
                translated_count += 1

        print(f"完了 ({len(results)}件成功)")

        # API負荷を下げるため少し待つ
        if i + BATCH_SIZE < len(untranslated):
            time.sleep(1)

    ARTICLES_FILE.write_text(
        json.dumps(articles, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n翻訳完了: {translated_count}件 を {ARTICLES_FILE} に保存")


if __name__ == "__main__":
    main()
