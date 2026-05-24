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

    # ── TAT公式イベント（本文も取得して複数イベント分離） ───────────
    # RSSが取得できない場合のフォールバックとして複数URLを設定
    {
        "id": "tat_events",
        "name": "TAT公式イベント",
        "type": "rss_fulltext",
        "url": "https://www.tatnews.org/category/thailand-events-festivals/feed/",
        "category": "events",
        "max_items": 10,
        "lang": "en",
    },

    # ── モールイベント（Googleニュース検索RSS + 本文取得） ─────────
    # Googleニュース経由は要約が短いため本文も取得する
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
        "id": "emquartier_gnews",
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

CATEGORY_LABELS = {
    "ja_news":       "日本語サイト",
    "news_domestic": "国内ニュース",
    "news_intl":     "国際ニュース",
    "events":        "イベント・祭り",
    "mall_events":   "モールイベント",
}
