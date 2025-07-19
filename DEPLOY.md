# Railway デプロイ手順

## 🚀 クイックデプロイ手順

### 1. Railway アカウント作成
1. https://railway.app にアクセス
2. 「Sign up with GitHub」でサインアップ

### 2. プロジェクトデプロイ
1. 「New Project」をクリック
2. 「Deploy from GitHub repo」を選択
3. `discord-ai-news-bot` リポジトリを選択
4. 自動でビルド・デプロイが開始

### 3. 環境変数設定
**Variables** タブで以下を追加：
```
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/1396002981291229324/HZBDfa1QpEp1SgD9QA_iwEHYC5A_DWj8Z3lB5BsBxiC2D8Ex2eQjvNpJdkmr1iqRROur
```

### 4. 設定確認
- **Service Type**: Worker (自動検出)
- **Start Command**: `python rss_discord_bot.py` (自動設定)
- **Python Version**: 3.11.9 (runtime.txt指定)

## ✅ デプロイ完了
- 自動で1時間間隔でAIニュース監視開始
- Discordに記事投稿確認
- Railway Dashboard でログ確認可能

## 💰 料金
- 月500時間まで無料
- RSS Bot の実行時間: 約720時間/月 (24時間x30日)
- **注意**: 無料枠を超える場合は月$5からの有料プラン必要