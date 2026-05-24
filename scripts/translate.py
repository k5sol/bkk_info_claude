#!/usr/bin/env python3
"""
translate.py
Step1: news_pending フィルタ＋国内/国際 分類
Step2: TAT記事を本文から複数イベントに分離
Step3: mall_events / events（単体）を翻訳＋イベント情報抽出
Step1b: ニュース翻訳
ja_news はスキップ
"""
import json, os, sys, time, hashlib
from pathlib import Path
import anthropic

DATA_DIR      = Path(__file__).parent.parent / "data"
ARTICLES_FILE = DATA_DIR / "articles.json"
BATCH_SIZE    = 5

client_instance = None

# ── フィルタ ──────────────────────────────────────────────────────────────────
FILTER_SYSTEM = """\
バンコク在住の日本人向け情報キュレーターとして記事を選別・分類する。
JSONのみ返答。

【除外】タイと無関係な海外スポーツ（欧州サッカー・NBA等）/商品紹介・書籍レビュー・広告/
        タイと無関係な海外政治・社会/占い・宝くじ
【掲載】タイ国内の政治・経済・社会・交通・生活/タイと他国の関係/
        外国人観光客に関係する情報/タイに影響する国際ニュース
分類: news_domestic（タイ国内）/ news_intl（他国との関係・国際情勢）
"""

def filter_and_classify(articles: list[dict]) -> list[dict]:
    if not articles:
        return []
    items = "\n\n---\n\n".join(
        f'ID: {a["id"]}\nTITLE: {a["title_original"]}\nSUMMARY: {a["summary_original"]}'
        for a in articles
    )
    prompt = f'以下の記事を選別・分類し、掲載すべき記事のみJSON配列で返してください。\n[{{"id":"...","category":"news_domestic または news_intl"}}, ...]\n\n記事:\n{items}'
    try:
        msg = client_instance.messages.create(
            model="claude-haiku-4-5-20251001", max_tokens=1024,
            system=FILTER_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip()
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"): raw = raw[4:]
        results = json.loads(raw)
        allowed = {r["id"]: r["category"] for r in results}
        kept = []
        for a in articles:
            if a["id"] in allowed:
                a["category"] = allowed[a["id"]]
                kept.append(a)
        removed = len(articles) - len(kept)
        if removed:
            print(f"    除外: {removed}件")
        return kept
    except Exception as e:
        print(f"    フィルタエラー: {e} → 全件通過")
        for a in articles:
            a["category"] = "news_domestic"
        return articles


# ── TAT 複数イベント分離 ──────────────────────────────────────────────────────
TAT_SYSTEM = """\
タイのイベント情報抽出の専門家。
記事本文から個々のイベントを全て抽出し、JSONのみ返す。
固有名詞はカタカナ＋英語名。日付はISO 8601。
イベントが多い場合も全て列挙すること。
"""

def extract_tat_events(article: dict) -> list[dict]:
    """TAT記事の本文からイベントを分離。本文が長い場合は分割して処理。"""
    body = article.get("body_original") or article.get("summary_original", "")
    if not body:
        return []

    # 本文を2000字ずつ分割して処理（イベントが多い記事に対応）
    chunks = [body[i:i+2500] for i in range(0, len(body), 2500)]
    all_events = []
    seen_titles = set()

    for chunk_idx, chunk in enumerate(chunks):
        prompt = f"""\
以下のTAT記事（パート{chunk_idx+1}/{len(chunks)}）からイベントを全て抽出してください。
元記事ID: "{article['id']}"

JSON配列で返してください（イベントが無い場合は[]）:
[
  {{
    "id": "元ID_{chunk_idx*20+1}",
    "title_ja": "イベント名（日本語）",
    "summary_ja": "2〜3文の説明（日本語）",
    "event_start": "YYYY-MM-DD または YYYY-MM-DDTHH:MM:SS、不明ならnull",
    "event_end": "同上、単日またはnull",
    "event_venue": "開催場所（日本語・県名も含める）またはnull",
    "event_admission": "無料 / 金額 / null"
  }}
]

記事本文:
{chunk}
"""
        for attempt in range(2):
            try:
                msg = client_instance.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=4096,   # 多くのイベントに対応
                    system=TAT_SYSTEM,
                    messages=[{"role": "user", "content": prompt}],
                )
                raw = msg.content[0].text.strip()
                if "```" in raw:
                    raw = raw.split("```")[1]
                    if raw.startswith("json"): raw = raw[4:]
                events = json.loads(raw)

                for ev in events:
                    title = ev.get("title_ja", "")
                    if not title or title in seen_titles:
                        continue
                    seen_titles.add(title)

                    suffix = f"_{len(all_events)+1}"
                    child_id = hashlib.sha256(
                        (article["id"] + suffix).encode()
                    ).hexdigest()[:16]

                    all_events.append({
                        **article,
                        "id":              child_id,
                        "title_ja":        title,
                        "summary_ja":      ev.get("summary_ja", ""),
                        "category":        "events",
                        "event_start":     ev.get("event_start"),
                        "event_end":       ev.get("event_end"),
                        "event_venue":     ev.get("event_venue"),
                        "event_admission": ev.get("event_admission"),
                        "translated":      True,
                        "split_from":      article["id"],
                    })
                break
            except json.JSONDecodeError as e:
                print(f"    JSON解析エラー (chunk {chunk_idx+1}, attempt {attempt+1}): {e}")
                time.sleep(1)
            except Exception as e:
                print(f"    エラー (chunk {chunk_idx+1}): {e}")
                break

        if len(chunks) > 1:
            time.sleep(0.5)

    return all_events


# ── 通常翻訳 ──────────────────────────────────────────────────────────────────
TRANSLATE_SYSTEM = """\
タイ語/英語→日本語翻訳・情報抽出。JSONのみ返答。
固有名詞はカタカナ＋英語名。通貨はバーツ表記。要約は2〜4文。
"""

def translate_batch(articles: list[dict]) -> None:
    is_event = any(a.get("category") in ("events","mall_events") for a in articles)
    items = []
    for a in articles:
        note = "\n※ event_start/end/venue/admission も抽出" if a.get("category") in ("events","mall_events") else ""
        items.append(f'ID: {a["id"]}\nTITLE: {a["title_original"]}\nSUMMARY: {a["summary_original"]}{note}')

    fmt = ('{"id":"...","title_ja":"...","summary_ja":"...",'
           '"event_start":"...or null","event_end":"...or null",'
           '"event_venue":"...or null","event_admission":"...or null"}'
           if is_event else '{"id":"...","title_ja":"...","summary_ja":"..."}')

    prompt = f'以下の記事を日本語に翻訳しJSON配列で返してください。\n形式: [{fmt}, ...]\n\n記事:\n{"\\n\\n---\\n\\n".join(items)}'

    for attempt in range(3):
        try:
            msg = client_instance.messages.create(
                model="claude-haiku-4-5-20251001", max_tokens=2048,
                system=TRANSLATE_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = msg.content[0].text.strip()
            if "```" in raw:
                raw = raw.split("```")[1]
                if raw.startswith("json"): raw = raw[4:]
            results = {r["id"]: r for r in json.loads(raw)}
            for a in articles:
                r = results.get(a["id"])
                if r:
                    a["title_ja"]        = r.get("title_ja", a["title_original"])
                    a["summary_ja"]      = r.get("summary_ja", "")
                    a["event_start"]     = r.get("event_start", a.get("event_start"))
                    a["event_end"]       = r.get("event_end",   a.get("event_end"))
                    a["event_venue"]     = r.get("event_venue", a.get("event_venue"))
                    a["event_admission"] = r.get("event_admission", a.get("event_admission"))
                    a["translated"]      = True
            return
        except json.JSONDecodeError as e:
            print(f"    JSON解析エラー (attempt {attempt+1}): {e}")
            time.sleep(2)
        except anthropic.RateLimitError:
            time.sleep(10 * (attempt+1))
        except Exception as e:
            print(f"    APIエラー: {e}")
            time.sleep(3)


# ── メイン ────────────────────────────────────────────────────────────────────
def main():
    global client_instance
    print("=== translate.py 開始 ===")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY が未設定", file=sys.stderr)
        sys.exit(1)
    client_instance = anthropic.Anthropic(api_key=api_key)

    articles: list[dict] = json.loads(ARTICLES_FILE.read_text(encoding="utf-8"))
    existing_ids = {a["id"] for a in articles}

    # ja_news: タイトル・要約をそのまま転記してスキップ
    ja_done = 0
    for a in articles:
        if a.get("lang") == "ja" and not a.get("translated"):
            a["title_ja"]   = a["title_original"]
            a["summary_ja"] = a["summary_original"]
            a["translated"] = True
            ja_done += 1
    if ja_done:
        print(f"日本語記事スキップ: {ja_done}件")

    # Step1: news_pending フィルタ＋分類
    pending = [a for a in articles if a.get("category") == "news_pending" and not a.get("translated")]
    print(f"\nStep1: news_pending フィルタ＋分類 ({len(pending)}件)")
    for i in range(0, len(pending), 10):
        batch = pending[i:i+10]
        print(f"  バッチ {i//10+1}: {len(batch)}件 →", end=" ", flush=True)
        kept = filter_and_classify(batch)
        print(f"{len(kept)}件通過")
        time.sleep(1)
    for a in articles:
        if a.get("category") == "news_pending" and not a.get("translated"):
            a["category"]   = "news_filtered"
            a["translated"] = True

    # Step2: TAT記事を複数イベントに分離
    tat_articles = [
        a for a in articles
        if a.get("category") == "events"
        and a.get("source_id") == "tat_events"
        and not a.get("translated")
    ]
    print(f"\nStep2: TAT複数イベント分離 ({len(tat_articles)}件の記事)")
    all_children = []
    for a in tat_articles:
        title_short = a["title_original"][:50]
        print(f"  分離中: {title_short}…", end=" ", flush=True)
        children = extract_tat_events(a)
        print(f"→ {len(children)}件のイベント")
        all_children.extend(children)
        a["translated"] = True
        time.sleep(1)

    for child in all_children:
        if child["id"] not in existing_ids:
            articles.append(child)
            existing_ids.add(child["id"])
    print(f"  子イベント合計: {len(all_children)}件")

    # Step3: events/mall_events 翻訳
    to_translate = [a for a in articles
                    if a.get("category") in ("events","mall_events") and not a.get("translated")]
    print(f"\nStep3: イベント翻訳 ({len(to_translate)}件)")
    for i in range(0, len(to_translate), BATCH_SIZE):
        batch = to_translate[i:i+BATCH_SIZE]
        print(f"  バッチ {i//BATCH_SIZE+1}: {len(batch)}件 →", end=" ", flush=True)
        translate_batch(batch)
        print(f"{sum(1 for a in batch if a.get('translated'))}件完了")
        if i + BATCH_SIZE < len(to_translate): time.sleep(1)

    # Step1b: ニュース翻訳
    news_todo = [a for a in articles
                 if a.get("category") in ("news_domestic","news_intl") and not a.get("translated")]
    print(f"\nStep1b: ニュース翻訳 ({len(news_todo)}件)")
    for i in range(0, len(news_todo), BATCH_SIZE):
        batch = news_todo[i:i+BATCH_SIZE]
        print(f"  バッチ {i//BATCH_SIZE+1}: {len(batch)}件 →", end=" ", flush=True)
        translate_batch(batch)
        print(f"{sum(1 for a in batch if a.get('translated'))}件完了")
        if i + BATCH_SIZE < len(news_todo): time.sleep(1)

    # news_filtered を除去してソート
    articles = [a for a in articles if a.get("category") != "news_filtered"]
    articles.sort(key=lambda a: a.get("published_at",""), reverse=True)

    ARTICLES_FILE.write_text(json.dumps(articles, ensure_ascii=False, indent=2), encoding="utf-8")
    cats = {}
    for a in articles:
        cats[a.get("category","?")] = cats.get(a.get("category","?"),0) + 1
    print(f"\n保存完了: {len(articles)}件 {cats}")


if __name__ == "__main__":
    main()
