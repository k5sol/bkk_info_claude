"""
情報収集ソース設定
各ソースの種別・URL・カテゴリを定義する
"""

SOURCES = [
    # ──────────────────────────────────────────────
    # タイ語ニュース RSS
    # ──────────────────────────────────────────────
    {
        "id": "thairath_general",
        "name": "ไทยรัฐ（タイラット）",
        "type": "rss",
        "url": "https://www.thairath.co.th/rss/news.xml",
        "category": "news",
        "max_items": 15,
    },
    {
        "id": "khaosod_general",
        "name": "ข่าวสด（カーオソット）",
        "type": "rss",
        "url": "https://www.khaosod.co.th/feed",
        "category": "news",
        "max_items": 15,
    },
    {
        "id": "matichon_general",
        "name": "มติชน（マティチョン）",
        "type": "rss",
        "url": "https://www.matichon.co.th/feed",
        "category": "news",
        "max_items": 10,
    },
    {
        "id": "sanook_news",
        "name": "สนุก！ニュース",
        "type": "rss",
        "url": "https://news.sanook.com/rss/news.xml",
        "category": "news",
        "max_items": 10,
    },
    {
        "id": "kapook_news",
        "name": "กระปุก（カプック）",
        "type": "rss",
        "url": "https://news.kapook.com/rss.xml",
        "category": "news",
        "max_items": 10,
    },
    {
        "id": "dailynews",
        "name": "เดลินิวส์（デーリーニュース）",
        "type": "rss",
        "url": "https://www.dailynews.co.th/feed/",
        "category": "news",
        "max_items": 10,
    },
    # ──────────────────────────────────────────────
    # イベント・フェスティバル情報（スクレイプ）
    # ──────────────────────────────────────────────
    {
        "id": "tat_events",
        "name": "TAT公式イベント",
        "type": "scrape",
        "url": "https://www.tatnews.org/category/thailand-events-festivals/feed/",
        "category": "events",
        "max_items": 20,
        # tatnewsはRSSも提供している
    },
    {
        "id": "iconsiam_events",
        "name": "ICONSIAM イベント",
        "type": "scrape",
        "url": "https://www.iconsiam.com/th/events",
        "category": "mall_events",
        "max_items": 10,
        "scrape_rules": {
            "item_selector": "article, .event-card, .promotion-item, [class*='event']",
            "title_selector": "h2, h3, .title",
            "date_selector": ".date, time, [class*='date']",
            "link_selector": "a",
            "image_selector": "img",
        },
    },
    {
        "id": "centralworld_events",
        "name": "CentralWorld イベント",
        "type": "scrape",
        "url": "https://www.centralworld.co.th/en/event/",
        "category": "mall_events",
        "max_items": 10,
        "scrape_rules": {
            "item_selector": ".event-item, .promotion-card, [class*='event']",
            "title_selector": "h2, h3, .title",
            "date_selector": ".date, time",
            "link_selector": "a",
            "image_selector": "img",
        },
    },
    {
        "id": "siamparagon_events",
        "name": "Siam Paragon イベント",
        "type": "scrape",
        "url": "https://www.siamparagon.co.th/events",
        "category": "mall_events",
        "max_items": 10,
        "scrape_rules": {
            "item_selector": "[class*='event'], article",
            "title_selector": "h2, h3, .event-title",
            "date_selector": ".date, time",
            "link_selector": "a",
            "image_selector": "img",
        },
    },
    {
        "id": "emdistrict_events",
        "name": "EmQuartier / EmSphere イベント",
        "type": "scrape",
        "url": "https://www.theemdistrict.com/events/",
        "category": "mall_events",
        "max_items": 10,
        "scrape_rules": {
            "item_selector": "[class*='event'], .card",
            "title_selector": "h2, h3",
            "date_selector": ".date, time",
            "link_selector": "a",
            "image_selector": "img",
        },
    },
]

# カテゴリの日本語ラベル
CATEGORY_LABELS = {
    "news":        "ニュース",
    "events":      "イベント・祭り",
    "mall_events": "ショッピングモール",
}
