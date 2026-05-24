"""情報収集ソース設定"""

SOURCES = [
    # ── 日本語サイト ─────────────────────────────────────────────────
    {
        "id": "thaich_news",
        "name": "タイランドハイパーリンクス",
        "type": "rss",
        "url": "https://www.thaich.net/news/rss.xml",
        "category": "ja_news",
        "max_items": 20,
        "lang": "ja",
    },
    {
        "id": "xbomber_news",
        "name": "X-BOMBER Thailand",
        "type": "rss",
        "url": "https://x-bomberth.com/feed/",
        "category": "ja_news",
        "max_items": 20,
        "lang": "ja",
    },

    # ── タイ語ニュース ────────────────────────────────────────────────
    {
        "id": "thairath_general",
        "name": "ไทยรัฐ（タイラット）",
        "type": "rss",
        "url": "https://www.thairath.co.th/rss/news.xml",
        "category": "news_pending",
        "max_items": 20,
        "lang": "th",
    },
    {
        "id": "khaosod_general",
        "name": "ข่าวสด（カーオソット）",
        "type": "rss",
        "url": "https://www.khaosod.co.th/feed",
        "category": "news_pending",
        "max_items": 20,
        "lang": "th",
    },
    {
        "id": "matichon_general",
        "name": "มติชน（マティチョン）",
        "type": "rss",
        "url": "https://www.matichon.co.th/feed",
        "category": "news_pending",
        "max_items": 15,
        "lang": "th",
    },
    {
        "id": "sanook_news",
        "name": "สนุก！ニュース",
        "type": "rss",
        "url": "https://news.sanook.com/rss/news.xml",
        "category": "news_pending",
        "max_items": 15,
        "lang": "th",
    },
    {
        "id": "kapook_news",
        "name": "กระปุก（カプック）",
        "type": "rss",
        "url": "https://news.kapook.com/rss.xml",
        "category": "news_pending",
        "max_items": 15,
        "lang": "th",
    },
    {
        "id": "dailynews",
        "name": "เดลินิวส์（デーリーニュース）",
        "type": "rss",
        "url": "https://www.dailynews.co.th/feed/",
        "category": "news_pending",
        "max_items": 15,
        "lang": "th",
    },

    # ── イベント情報（英語・本文取得して複数イベント分離） ───────────
    {
        "id": "tat_events",
        "name": "TAT公式イベント",
        "type": "rss_fulltext",
        "url": "https://www.tatnews.org/category/thailand-events-festivals/feed/",
        "category": "events",
        "max_items": 10,
        "lang": "en",
    },
    {
        # BK Magazineの「things to do this weekend」記事
        # 毎週木〜金に投稿。具体的な日程・会場・詳細が本文に含まれる最良ソース
        "id": "bk_events",
        "name": "BK Magazine イベント",
        "type": "rss_fulltext",
        "url": "https://bk.asia-city.com/things-to-do/more-event-news/feed",
        "category": "events",
        "max_items": 5,   # まとめ記事なので少数で十分
        "lang": "en",
    },
    {
        "id": "coconuts_bkk",
        "name": "Coconuts Bangkok",
        "type": "rss_fulltext",
        "url": "https://coconuts.co/bangkok/feed/",
        "category": "events",
        "max_items": 10,
        "lang": "en",
        # イベント記事とニュース混在のためフィルタで選別
    },
    {
        "id": "nation_events",
        "name": "Nation Thailand イベント",
        "type": "rss_fulltext",
        "url": "https://www.nationthailand.com/feed/rss",
        "category": "events",
        "max_items": 10,
        "lang": "en",
    },

    # ── モールイベント（Googleニュース検索RSS + 本文取得） ─────────
    # Googleニュース経由は本文も取得して日程抽出精度を上げる
    {
        "id": "iconsiam_gnews",
        "name": "ICONSIAM イベント",
        "type": "rss_fulltext",
        "url": "https://news.google.com/rss/search?q=ICONSIAM+%E0%B8%81%E0%B8%B4%E0%B8%88%E0%B8%81%E0%B8%A3%E0%B8%A3%E0%B8%A1+2026&hl=th&gl=TH&ceid=TH:th",
        "category": "mall_events",
        "max_items": 8,
        "lang": "th",
    },
    {
        "id": "centralworld_gnews",
        "name": "CentralWorld イベント",
        "type": "rss_fulltext",
        "url": "https://news.google.com/rss/search?q=CentralWorld+%E0%B8%81%E0%B8%B4%E0%B8%88%E0%B8%81%E0%B8%A3%E0%B8%A3%E0%B8%A1+2026&hl=th&gl=TH&ceid=TH:th",
        "category": "mall_events",
        "max_items": 8,
        "lang": "th",
    },
    {
        "id": "siamparagon_gnews",
        "name": "Siam Paragon イベント",
        "type": "rss_fulltext",
        "url": "https://news.google.com/rss/search?q=Siam+Paragon+%E0%B8%81%E0%B8%B4%E0%B8%88%E0%B8%81%E0%B8%A3%E0%B8%A3%E0%B8%A1+2026&hl=th&gl=TH&ceid=TH:th",
        "category": "mall_events",
        "max_items": 8,
        "lang": "th",
    },
    {
        "id": "emdistrict_gnews",
        "name": "EmQuartier / EmSphere イベント",
        "type": "rss_fulltext",
        "url": "https://news.google.com/rss/search?q=EmQuartier+EmSphere+%E0%B8%81%E0%B8%B4%E0%B8%88%E0%B8%81%E0%B8%A3%E0%B8%A3%E0%B8%A1+2026&hl=th&gl=TH&ceid=TH:th",
        "category": "mall_events",
        "max_items": 8,
        "lang": "th",
    },
    {
        "id": "onebangkok_gnews",
        "name": "One Bangkok イベント",
        "type": "rss_fulltext",
        "url": "https://news.google.com/rss/search?q=%22One+Bangkok%22+%E0%B8%81%E0%B8%B4%E0%B8%88%E0%B8%81%E0%B8%A3%E0%B8%A3%E0%B8%A1+2026&hl=th&gl=TH&ceid=TH:th",
        "category": "mall_events",
        "max_items": 8,
        "lang": "th",
    },
]

# translate.py で複数イベント分離を行うソースID
MULTI_EVENT_SOURCES = {"tat_events", "bk_events"}

# イベント記事かどうか本文でフィルタするソースID（ニュース混在ソース）
FILTER_FOR_EVENTS_SOURCES = {"coconuts_bkk", "nation_events"}

CATEGORY_LABELS = {
    "ja_news":       "日本語サイト",
    "news_domestic": "国内ニュース",
    "news_intl":     "国際ニュース",
    "events":        "イベント・祭り",
    "mall_events":   "モールイベント",
}
