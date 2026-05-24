"""情報収集ソース設定"""

SOURCES = [
    # ── 日本語サイト（翻訳不要・フィルタ不要） ──────────────────────
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

    # ── タイ語ニュース（国内/国際をClaudeが分類、無関係は除外） ─────
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

    # ── TAT公式イベント（英語・本文取得して複数イベント分離） ────────
    {
        "id": "tat_events",
        "name": "TAT公式イベント",
        "type": "rss_fulltext",          # 本文も取得する
        "url": "https://www.tatnews.org/category/thailand-events-festivals/feed/",
        "category": "events",
        "max_items": 15,
        "lang": "en",
    },

    # ── モールイベント（Google ニュース検索RSS） ──────────────────────
    {
        "id": "iconsiam_gnews",
        "name": "ICONSIAM イベント",
        "type": "rss",
        "url": "https://news.google.com/rss/search?q=ICONSIAM+event+OR+%E0%B8%AD%E0%B8%B2%E0%B8%84%E0%B8%B2%E0%B8%A3+%E0%B8%81%E0%B8%B4%E0%B8%88%E0%B8%81%E0%B8%A3%E0%B8%A3%E0%B8%A1&hl=th&gl=TH&ceid=TH:th",
        "category": "mall_events",
        "max_items": 10,
        "lang": "th",
    },
    {
        "id": "centralworld_gnews",
        "name": "CentralWorld イベント",
        "type": "rss",
        "url": "https://news.google.com/rss/search?q=CentralWorld+event+OR+%E0%B9%80%E0%B8%8B%E0%B9%87%E0%B8%99%E0%B8%97%E0%B8%A3%E0%B8%B1%E0%B8%A5%E0%B9%80%E0%B8%A7%E0%B8%B4%E0%B8%A5%E0%B8%94%E0%B9%8C+%E0%B8%81%E0%B8%B4%E0%B8%88%E0%B8%81%E0%B8%A3%E0%B8%A3%E0%B8%A1&hl=th&gl=TH&ceid=TH:th",
        "category": "mall_events",
        "max_items": 10,
        "lang": "th",
    },
    {
        "id": "siamparagon_gnews",
        "name": "Siam Paragon イベント",
        "type": "rss",
        "url": "https://news.google.com/rss/search?q=Siam+Paragon+event+OR+%E0%B8%AA%E0%B8%A2%E0%B8%B2%E0%B8%A1%E0%B8%9E%E0%B8%B2%E0%B8%A3%E0%B8%B2%E0%B8%81%E0%B8%AD%E0%B8%99+%E0%B8%81%E0%B8%B4%E0%B8%88%E0%B8%81%E0%B8%A3%E0%B8%A3%E0%B8%A1&hl=th&gl=TH&ceid=TH:th",
        "category": "mall_events",
        "max_items": 10,
        "lang": "th",
    },
    {
        "id": "emquartier_gnews",
        "name": "EmQuartier / EmSphere イベント",
        "type": "rss",
        "url": "https://news.google.com/rss/search?q=EmQuartier+OR+EmSphere+event+OR+%E0%B8%81%E0%B8%B4%E0%B8%88%E0%B8%81%E0%B8%A3%E0%B8%A3%E0%B8%A1&hl=th&gl=TH&ceid=TH:th",
        "category": "mall_events",
        "max_items": 10,
        "lang": "th",
    },
    {
        "id": "terminal21_gnews",
        "name": "Terminal 21 イベント",
        "type": "rss",
        "url": "https://news.google.com/rss/search?q=Terminal+21+Bangkok+event+OR+%E0%B8%81%E0%B8%B4%E0%B8%88%E0%B8%81%E0%B8%A3%E0%B8%A3%E0%B8%A1&hl=th&gl=TH&ceid=TH:th",
        "category": "mall_events",
        "max_items": 10,
        "lang": "th",
    },
    {
        "id": "onebangkok_gnews",
        "name": "One Bangkok イベント",
        "type": "rss",
        "url": "https://news.google.com/rss/search?q=%22One+Bangkok%22+event+OR+%E0%B8%81%E0%B8%B4%E0%B8%88%E0%B8%81%E0%B8%A3%E0%B8%A3%E0%B8%A1&hl=th&gl=TH&ceid=TH:th",
        "category": "mall_events",
        "max_items": 10,
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
