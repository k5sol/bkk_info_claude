# BKK Journal — バンコク情報キュレーションサイト

タイ語ニュース・イベント情報を Claude API で日本語化し、
GitHub Pages に自動公開する静的サイトです。

## ディレクトリ構成

```
bangkok-curation/
├── .github/
│   └── workflows/
│       └── update.yml          # GitHub Actions（6時間ごと自動実行）
├── scripts/
│   ├── sources_config.py       # 情報収集ソース設定
│   ├── fetch_sources.py        # RSS取得 + スクレイピング
│   ├── dedupe.py               # 重複除去・マージ
│   ├── translate.py            # Claude API で日本語翻訳
│   └── build_site.py           # 静的HTML生成
├── templates/
│   └── index.html.j2           # Jinja2 HTMLテンプレート
├── data/                       # (自動生成・gitignore不要)
│   ├── raw_articles.json       # 収集した生データ
│   └── articles.json           # 翻訳済みデータ（キャッシュ）
├── docs/                       # GitHub Pages のソースディレクトリ
│   ├── index.html              # 公開サイト（自動生成）
│   └── articles.json           # JSON API（自動生成）
└── requirements.txt
```

## セットアップ手順

### 1. リポジトリの作成と初期設定

```bash
git init bangkok-curation
cd bangkok-curation
# このリポジトリの全ファイルをコピー
git add -A
git commit -m "initial commit"
git remote add origin https://github.com/<your-username>/bangkok-curation.git
git push -u origin main
```

### 2. GitHub Secrets の設定

GitHubリポジトリの **Settings → Secrets and variables → Actions** で:

| Secret名 | 値 |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic Console から取得した APIキー |

### 3. GitHub Pages の設定

**Settings → Pages** で:
- Source: `Deploy from a branch`
- Branch: `main` / `docs`
- → **Save**

### 4. 初回手動実行

**Actions → Update Bangkok Curation Site → Run workflow**

数分後に `https://<your-username>.github.io/bangkok-curation/` で閲覧可能になります。

## カスタマイズ

### 収集ソースの追加・削除

`scripts/sources_config.py` の `SOURCES` リストを編集します。

RSSフィードの場合:
```python
{
    "id": "mynews",         # 一意のID
    "name": "メディア名",
    "type": "rss",
    "url": "https://example.com/feed.xml",
    "category": "news",    # news / events / mall_events
    "max_items": 10,
}
```

### 更新頻度の変更

`.github/workflows/update.yml` の cron を変更します:
```yaml
- cron: '0 */6 * * *'   # 6時間ごと
- cron: '0 */3 * * *'   # 3時間ごと
- cron: '0 8,20 * * *'  # 毎日8時・20時
```

### 保持日数の変更

`scripts/dedupe.py` の `KEEP_DAYS = 7` を変更します。

## API コスト目安

Claude Haiku 4.5 使用時:
- 1記事あたり約 0.5〜1円
- 1日4回更新 × 1回50記事 = 約 200〜400円/月

翻訳済みキャッシュがあるため、差分のみ翻訳され実際にはもっと安くなります。
