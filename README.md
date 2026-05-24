# BKK Journal — バンコク情報キュレーションサイト

タイ語ニュース・イベント情報を Claude API で日本語化し、
GitHub Pages に自動公開する静的サイトです。

## ディレクトリ構成

```
bangkok-curation/
├── .github/workflows/update.yml   # GitHub Actions（6時間ごと自動実行）
├── scripts/
│   ├── sources_config.py          # 収集ソース設定（ここを編集してカスタマイズ）
│   ├── fetch_sources.py           # RSS取得＋スクレイピング
│   ├── dedupe.py                  # 重複除去・古い記事の削除
│   ├── translate.py               # Claude API で日本語翻訳＋イベント情報抽出
│   └── build_site.py              # 静的HTML生成
├── templates/index.html.j2        # サイトHTMLテンプレート
├── data/
│   ├── raw_articles.json          # 収集した生データ（自動生成）
│   └── articles.json              # 翻訳済みキャッシュ（自動生成）
├── docs/
│   ├── index.html                 # 公開サイト（自動生成）
│   └── articles.json              # JSON（自動生成）
└── requirements.txt
```

## セットアップ手順

### 1. このリポジトリをGitHubにpush

```bash
cd bangkok-curation
git init
git add -A
git commit -m "initial commit"
git branch -M main
git remote add origin https://github.com/<your-username>/bangkok-curation.git
git push -u origin main
```

### 2. GitHub Secrets の登録

リポジトリの **Settings → Secrets and variables → Actions → New repository secret**

| Name | Value |
|------|-------|
| `ANTHROPIC_API_KEY` | Anthropic Console の APIキー |

### 3. GitHub Pages の有効化

リポジトリの **Settings → Pages**
- Source: **Deploy from a branch**
- Branch: `main` / folder: `/docs`
- **Save** をクリック

### 4. 初回手動実行

**Actions → Update Bangkok Curation Site → Run workflow → Run workflow**

数分後に `https://<your-username>.github.io/bangkok-curation/` で公開されます。

## ローカルでのテスト実行

```bash
pip install -r requirements.txt
python scripts/fetch_sources.py
python scripts/dedupe.py
ANTHROPIC_API_KEY=sk-ant-... python scripts/translate.py
python scripts/build_site.py
open docs/index.html
```

## カスタマイズ

`scripts/sources_config.py` の `SOURCES` リストを編集するだけでソースを追加・削除できます。

更新頻度は `.github/workflows/update.yml` の cron を変更してください。
