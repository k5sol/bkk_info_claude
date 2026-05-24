#!/usr/bin/env python3
"""
translate.py
Step1 : news_pending フィルタ＋国内/国際 分類
Step2 : 複数イベント記事（TAT/BK）を本文から個別イベントに分離
Step2b: Coconuts/Nation などニュース混在ソースからイベント記事のみ選別
Step3 : mall_events を本文付きで翻訳＋日程抽出
Step3b: events 単体を翻訳＋日程抽出
Step4 : ニュース翻訳
ja_news: スキップ（そのまま転記）
"""
import json, os, sys, time, hashlib
from pathlib import Path
import anthropic

DATA_DIR      = Path(__file__).parent.parent / "data"
ARTICLES_FILE = DATA_DIR / "articles.json"
BATCH_SIZE    = 5

client_instance = None

# sources_config から定数を読み込む
sys.path.insert(0, str(Path(__file__).parent))
from sources_config import MULTI_EVENT_SOURCES, FILTER_FOR_EVENTS_SOURCES


def _clean_json(text: str) -> str:
    text = text.strip()
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return text.strip()


def _api(prompt: str, system: str, max_tokens: int = 2048) -> str:
    msg = client_instance.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


# ── Step1: ニュースフィルタ＋分類 ─────────────────────────────────────────
FILTER_SYS = """\
バンコク在住の日本人向け情報キュレーター。JSONのみ返答。
【除外】タイと無関係な海外スポーツ/商品紹介・書籍レビュー・広告/
        タイと無関係な海外政治・社会/占い・宝くじ/成人向けコンテンツ
【掲載】タイ国内の政治・経済・社会・交通・生活/タイと他国の関係/
        外国人観光客向け情報/タイに影響する国際ニュース
分類: news_domestic（タイ国内）/ news_intl（国際・他国との関係）
"""

def filter_and_classify(articles: list[dict]) -> list[dict]:
    if not articles:
        return []
    items = "\n\n---\n\n".join(
        f'ID: {a["id"]}\nTITLE: {a["title_original"]}\nSUMMARY: {a["summary_original"][:300]}'
        for a in articles
    )
    prompt = (
        "以下の記事を選別・分類し、掲載すべき記事のみJSON配列で返してください。\n"
        '[{"id":"...","category":"news_domestic または news_intl"}, ...]\n\n'
        f"記事:\n{items}"
    )
    try:
        raw = _clean_json(_api(prompt, FILTER_SYS, 1024))
        allowed = {r["id"]: r["category"] for r in json.loads(raw)}
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
        print(f"    フィルタエラー: {e} → 全件 news_domestic")
        for a in articles:
            a["category"] = "news_domestic"
        return articles


# ── Step2: 複数イベント分離（TAT / BK Magazine など） ─────────────────────
MULTI_SYS = """\
タイのイベント情報抽出の専門家。記事本文から個々のイベントを全て抽出しJSONのみ返す。
固有名詞はカタカナ＋英語名。日付はISO 8601。イベントが多くても全て列挙。
イベント記事でない（ニュース・レストランレビューなど）場合は [] を返す。
"""

def extract_multi_events(article: dict) -> list[dict]:
    body = article.get("body_original") or ""
    text = body if len(body) > 200 else article.get("summary_original", "")
    if not text:
        return []

    chunks = [text[i:i+2500] for i in range(0, len(text), 2500)]
    all_events: list[dict] = []
    seen_titles: set[str] = set()

    for chunk_idx, chunk in enumerate(chunks):
        prompt = f"""\
記事（パート{chunk_idx+1}/{len(chunks)}）からイベントを全て抽出してください。
元記事ID: "{article['id']}"

JSON配列（イベントなければ[]）:
[{{
  "id": "元ID_{chunk_idx*20+1}",
  "title_ja": "イベント名（日本語）",
  "summary_ja": "2〜3文の説明",
  "event_start": "YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS or null",
  "event_end": "同上 or null",
  "event_venue": "開催場所（施設名＋エリア）or null",
  "event_admission": "無料 / 金額 / null"
}}]

記事タイトル: {article['title_original']}
本文:
{chunk}
"""
        for attempt in range(2):
            try:
                events = json.loads(_clean_json(_api(prompt, MULTI_SYS, 4096)))
                for ev in events:
                    title = ev.get("title_ja", "")
                    if not title or title in seen_titles:
                        continue
                    seen_titles.add(title)
                    child_id = hashlib.sha256(
                        f"{article['id']}_{len(all_events)+1}".encode()
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
                        "body_original":   "",
                    })
                break
            except Exception as e:
                print(f"    エラー chunk{chunk_idx+1} attempt{attempt+1}: {e}")
                time.sleep(1)
        if len(chunks) > 1:
            time.sleep(0.5)

    return all_events


# ── Step2b: Coconuts/Nation からイベント記事のみ選別 ───────────────────────
SELECT_SYS = """\
バンコクのイベント情報キュレーター。JSONのみ返答。
以下の記事リストのうち、バンコクで行われるイベント・コンサート・展示会・祭り・
マーケット・スポーツイベントに関する記事のみ選別してください。
ニュース・レストランレビュー・旅行ガイド・広告は除外。
"""

def select_event_articles(articles: list[dict]) -> list[dict]:
    if not articles:
        return []
    items = "\n\n---\n\n".join(
        f'ID: {a["id"]}\nTITLE: {a["title_original"]}\nSUMMARY: {a["summary_original"][:200]}'
        for a in articles
    )
    prompt = (
        "以下からイベント記事のみをJSON配列で返してください。\n"
        '[{"id":"..."}, ...]\n\n'
        f"記事:\n{items}"
    )
    try:
        raw = _clean_json(_api(prompt, SELECT_SYS, 512))
        allowed = {r["id"] for r in json.loads(raw)}
        kept = [a for a in articles if a["id"] in allowed]
        print(f"    イベント選別: {len(articles)}件 → {len(kept)}件")
        return kept
    except Exception as e:
        print(f"    選別エラー: {e} → 全件通過")
        return articles


# ── Step3: イベント翻訳＋日程抽出 ─────────────────────────────────────────
EVENT_SYS = """\
タイ語/英語→日本語翻訳・イベント情報抽出。JSONのみ返答。
固有名詞はカタカナ＋英語名。日付はISO 8601。通貨はバーツ表記。
body（本文）がある場合は本文から日程・会場を優先して抽出すること。
"""

def translate_events(articles: list[dict]) -> None:
    items = []
    for a in articles:
        body = (a.get("body_original") or "")[:1500]
        body_part = f"\n本文:\n{body}" if body else ""
        items.append(
            f'ID: {a["id"]}\n'
            f'TITLE: {a["title_original"]}\n'
            f'SUMMARY: {a["summary_original"][:400]}'
            f'{body_part}'
        )
    prompt = (
        "以下のイベント記事を日本語に翻訳し、開催日程・会場・入場料も抽出してください。\n"
        'JSON配列: [{"id":"...","title_ja":"...","summary_ja":"2〜4文",'
        '"event_start":"YYYY-MM-DD or null","event_end":"同 or null",'
        '"event_venue":"日本語会場名 or null","event_admission":"無料/金額/null"}, ...]\n\n'
        f"記事:\n{'\\n\\n---\\n\\n'.join(items)}"
    )
    _call_and_apply(articles, prompt, EVENT_SYS)


# ── Step4: ニュース翻訳 ────────────────────────────────────────────────────
NEWS_SYS = """\
タイ語/英語→日本語翻訳。JSONのみ返答。
固有名詞はカタカナ＋英語名。通貨はバーツ表記。要約は2〜4文。
"""

def translate_news(articles: list[dict]) -> None:
    items = [
        f'ID: {a["id"]}\nTITLE: {a["title_original"]}\nSUMMARY: {a["summary_original"][:400]}'
        for a in articles
    ]
    prompt = (
        "以下のニュース記事を日本語に翻訳してください。\n"
        'JSON配列: [{"id":"...","title_ja":"...","summary_ja":"..."}, ...]\n\n'
        f"記事:\n{'\\n\\n---\\n\\n'.join(items)}"
    )
    _call_and_apply(articles, prompt, NEWS_SYS)


def _call_and_apply(articles: list[dict], prompt: str, system: str) -> None:
    for attempt in range(3):
        try:
            results = {r["id"]: r for r in json.loads(_clean_json(_api(prompt, system)))}
            for a in articles:
                r = results.get(a["id"])
                if r:
                    a["title_ja"]        = r.get("title_ja", a.get("title_original", ""))
                    a["summary_ja"]      = r.get("summary_ja", "")
                    a["event_start"]     = r.get("event_start", a.get("event_start"))
                    a["event_end"]       = r.get("event_end",   a.get("event_end"))
                    a["event_venue"]     = r.get("event_venue", a.get("event_venue"))
                    a["event_admission"] = r.get("event_admission", a.get("event_admission"))
                    a["translated"]      = True
            return
        except json.JSONDecodeError as e:
            print(f"    JSON解析エラー attempt{attempt+1}: {e}")
            time.sleep(2)
        except anthropic.RateLimitError:
            time.sleep(10 * (attempt + 1))
        except Exception as e:
            print(f"    APIエラー: {e}")
            time.sleep(3)


# ── メイン ────────────────────────────────────────────────────────────────
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

    # ja_news: そのまま転記
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
    pending = [a for a in articles
               if a.get("category") == "news_pending" and not a.get("translated")]
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

    # Step2: 複数イベント分離（TAT / BK Magazine）
    multi_ev_articles = [
        a for a in articles
        if a.get("source_id") in MULTI_EVENT_SOURCES and not a.get("translated")
    ]
    print(f"\nStep2: 複数イベント分離 ({len(multi_ev_articles)}件の記事)")
    if not multi_ev_articles:
        print("  ※ 対象記事なし")
    all_children: list[dict] = []
    for a in multi_ev_articles:
        src = a.get("source_id", "")
        print(f"  [{src}] {a['title_original'][:50]}…", end=" ", flush=True)
        children = extract_multi_events(a)
        print(f"→ {len(children)}件")
        all_children.extend(children)
        a["translated"] = True
        time.sleep(1)
    for child in all_children:
        if child["id"] not in existing_ids:
            articles.append(child)
            existing_ids.add(child["id"])
    print(f"  子イベント合計: {len(all_children)}件")

    # Step2b: Coconuts/Nation からイベント記事を選別
    filter_ev_articles = [
        a for a in articles
        if a.get("source_id") in FILTER_FOR_EVENTS_SOURCES and not a.get("translated")
    ]
    if filter_ev_articles:
        print(f"\nStep2b: イベント記事選別 ({len(filter_ev_articles)}件)")
        kept = select_event_articles(filter_ev_articles)
        kept_ids = {a["id"] for a in kept}
        for a in filter_ev_articles:
            if a["id"] not in kept_ids:
                a["category"]   = "news_filtered"
                a["translated"] = True

    # Step3: mall_events 翻訳
    mall_todo = [a for a in articles
                 if a.get("category") == "mall_events" and not a.get("translated")]
    print(f"\nStep3: モールイベント翻訳 ({len(mall_todo)}件)")
    for i in range(0, len(mall_todo), BATCH_SIZE):
        batch = mall_todo[i:i+BATCH_SIZE]
        print(f"  バッチ {i//BATCH_SIZE+1}: {len(batch)}件 →", end=" ", flush=True)
        translate_events(batch)
        print(f"{sum(1 for a in batch if a.get('translated'))}件完了")
        if i + BATCH_SIZE < len(mall_todo):
            time.sleep(1)

    # Step3b: events 単体翻訳
    ev_todo = [a for a in articles
               if a.get("category") == "events"
               and not a.get("translated")
               and not a.get("split_from")]
    if ev_todo:
        print(f"\nStep3b: events単体翻訳 ({len(ev_todo)}件)")
        for i in range(0, len(ev_todo), BATCH_SIZE):
            batch = ev_todo[i:i+BATCH_SIZE]
            print(f"  バッチ {i//BATCH_SIZE+1}: {len(batch)}件 →", end=" ", flush=True)
            translate_events(batch)
            print(f"{sum(1 for a in batch if a.get('translated'))}件完了")
            if i + BATCH_SIZE < len(ev_todo):
                time.sleep(1)

    # Step4: ニュース翻訳
    news_todo = [a for a in articles
                 if a.get("category") in ("news_domestic", "news_intl")
                 and not a.get("translated")]
    print(f"\nStep4: ニュース翻訳 ({len(news_todo)}件)")
    for i in range(0, len(news_todo), BATCH_SIZE):
        batch = news_todo[i:i+BATCH_SIZE]
        print(f"  バッチ {i//BATCH_SIZE+1}: {len(batch)}件 →", end=" ", flush=True)
        translate_news(batch)
        print(f"{sum(1 for a in batch if a.get('translated'))}件完了")
        if i + BATCH_SIZE < len(news_todo):
            time.sleep(1)

    # 除外記事を取り除いてソート
    articles = [a for a in articles if a.get("category") != "news_filtered"]
    articles.sort(key=lambda a: a.get("published_at", ""), reverse=True)

    ARTICLES_FILE.write_text(
        json.dumps(articles, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    cats: dict[str, int] = {}
    for a in articles:
        cats[a.get("category", "?")] = cats.get(a.get("category", "?"), 0) + 1
    ev_with_date = sum(
        1 for a in articles
        if a.get("category") in ("events", "mall_events") and a.get("event_start")
    )
    print(f"\n保存完了: {len(articles)}件 {cats}")
    print(f"カレンダー表示可能イベント: {ev_with_date}件")


if __name__ == "__main__":
    main()
