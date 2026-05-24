# Discord RSS Bot - Claude Assistant Guide

## 🤖 このファイルについて
このファイルは、Claude（AI Assistant）が Discord RSS Bot プロジェクトを効率的にサポートするための設定・記録ファイルです。

---

## 📋 プロジェクト情報

### 🎯 **プロジェクト概要**
- **名前**: Discord RSS Bot for AI Regulation News
- **目的**: AI法規制関連ニュースの自動収集・Discord投稿
- **言語**: Python 3.11+
- **主要機能**: RSS監視、自動翻訳、Discord Webhook投稿、重複防止

### 📍 **プロジェクト構造**
```
/Users/watanabehidetaka/Claudecode/News_Discord_BOT/discord-rss-bot/
├── rss_discord_bot.py       # メインアプリケーション
├── config.json             # 設定ファイル（Webhook URL、RSS一覧）
├── requirements.txt        # Python依存関係
├── run_mac.sh             # Mac実行スクリプト
├── test_mac.sh            # テスト実行スクリプト
├── rss_bot.log           # 実行ログ（テキスト）
├── terminal_log.md       # 実行ログ（Markdown）
├── conversation_log.md   # 会話記録
├── seen_articles.json    # 投稿済み記事管理
└── CLAUDE.md            # このファイル
```

---

## ⚙️ 重要な設定情報

### 🔗 **Discord Webhook URL**
```
https://discord.com/api/webhooks/1396002981291229324/HZBDfa1QpEp1SgD9QA_iwEHYC5A_DWj8Z3lB5BsBxiC2D8Ex2eQjvNpJdkmr1iqRROur
```

### 📊 **現在の設定**
- **実行間隔**: 30分
- **フィード毎記事数**: 2記事まで
- **翻訳機能**: 英語記事→日本語（Google Translate API）

### 🗂️ **対象RSS分野**
- **🇺🇸 アメリカ**: 技術政策、AI規制
- **🇪🇺 ヨーロッパ**: EU AI Act、デジタル政策
- **🇯🇵 日本**: 政府機関、技術メディア
- **🌐 国際機関**: OECD、学術機関

---

## 🔧 よく使うコマンド

### 📱 **テスト実行**
```bash
./test_mac.sh
```

### 🔄 **継続実行**
```bash
./run_mac.sh
```

### 🛑 **停止**
```
Ctrl + C
```

### 📁 **ログ確認**
```bash
# テキストログ
tail -f rss_bot.log

# Markdownログ
open terminal_log.md
```

### 💬 **重要：ターミナル会話ログの管理**
- ユーザーとの**このターミナルでのやりとり**を`conversation_log.md`に必ず記録する
- 会話の流れ、決定事項、問題解決過程を時系列で記録  
- 新しい要求や機能追加があった場合、即座に会話ログを更新
- これにより次回のClaude起動時に文脈を継承可能

---

## 🔍 トラブルシューティング

### ✅ **動作確認済みRSS**
- 🚀 TechCrunch: `https://techcrunch.com/feed/`
- 🧠 MIT Technology Review: `https://www.technologyreview.com/feed/`

### ❌ **問題のあるRSS**
- Reuters: RSS提供終了（2020年）→ Google News代替必要
- EURACTIV: アクセス制限→メインフィード使用
- ITmedia AI+: 正式URL要確認
- 日経xTECH: 公式RSS URL要確認
- 政府機関: XMLフォーマットエラー

### 🔧 **修正予定URL**
```json
"🇺🇸 Reuters Tech": "https://news.google.com/rss/search?q=when:24h+allinurl:reuters.com&ceid=US:en&hl=en-US&gl=US",
"🇪🇺 EURACTIV Digital": "https://www.euractiv.com/feed/",
"🇯🇵 ITmedia AI+": "https://rss.itmedia.co.jp/rss/2.0/aiplus.xml",
"🇯🇵 日経xTECH": "https://xtech.nikkei.com/rss/index.rdf"
```

---

## 📈 パフォーマンス情報

### 📊 **現在の成功率**
- **テスト済み**: 15フィード中3フィードが正常動作 (20%)
- **目標**: 80%以上の成功率達成

### ⏱️ **実行時間**
- **RSS取得**: 1-10秒/フィード
- **翻訳処理**: 1-3秒/記事
- **Discord投稿**: 1秒/記事（レート制限）

---

## 🎯 実行すべきタスク

### 🔥 **高優先度**
1. ❌ RSS URL修正（代替URL実装）
2. ❌ 成功率向上テスト
3. ❌ 継続実行開始

### 📋 **中優先度**
- Google Search API統合検討
- エラーハンドリング強化
- 記事フィルタリング機能

### 💡 **将来の改善案**
- AI要約機能追加
- 記事カテゴリ分類
- 複数Discord チャンネル対応

---

## 🔐 セキュリティ注意事項

### ⚠️ **機密情報**
- `config.json` - Webhook URLが含まれるため Git 除外済み
- `.gitignore` でWebhook URL保護済み

### 🛡️ **ベストプラクティス**
- Webhook URLの再共有禁止
- 定期的な依存関係アップデート
- ログファイルの定期クリーンアップ

---

## 📚 参考情報

### 🔗 **重要なリンク**
- [Discord Webhook Guide](https://support.discord.com/hc/ja/articles/228383668)
- [RSS 2.0 Specification](https://www.rssboard.org/rss-specification)
- [Google Translate API](https://cloud.google.com/translate)

### 📖 **技術仕様**
- **Python**: 3.11+ (3.13対応済み)
- **主要ライブラリ**: feedparser, requests
- **RSS形式**: RSS 2.0
- **文字エンコード**: UTF-8

---

## 🤝 Claude Assistant のための注意事項

### ✅ **実行時の確認ポイント**
1. `config.json` のWebhook URL設定確認
2. `venv` 仮想環境の状態確認
3. RSS URL の有効性確認
4. ログファイルのエラー内容確認

### 🚫 **避けるべき操作**
- Webhook URL の変更・削除
- `seen_articles.json` の手動編集
- 本番実行中の設定変更

### 📝 **推奨される作業フロー**
1. 現在の設定状況確認
2. テスト実行での動作確認
3. 問題特定・修正
4. 再テスト・動作確認
5. 継続実行開始

---

## 🚫 デプロイ状況の正確な記録

### 📍 **現在の稼働状況**
- **Railway**: ❌ 停止済み（または未デプロイ）
- **Xserver VPS**: 🔒 セキュリティ強化によりClaude外部アクセス不可
  - IP: 210.131.217.175
  - User: root  
  - 稼働状況: 不明（SSH接続制限により確認不可）
- **ローカル環境**: ✅ 開発・テスト用として動作

### ⚠️ **重要：Claude Assistant制限事項**
- Xserver VPSへのSSH接続は認証強化により不可
- Railway CLI未認証状態
- 本番環境の直接確認・操作は不可
- デプロイ作業はユーザー自身で実行が必要

---

## 🐛 Railway CLI デプロイ問題解決記録

### ❌ **遭遇したエラーと解決方法**

#### 1. **環境変数設定問題**
```bash
# ❌ 間違い（CLI 4.5系では認識されない）
export RAILWAY_API_TOKEN="xxxx"

# ✅ 正解
export RAILWAY_TOKEN="xxxx"
```

#### 2. **Bash subshell問題**
```bash
# ❌ 問題：毎回subshellで変数が消える
railway whoami  # → Unauthorized

# ✅ 解決：永続ファイルに設定
mkdir -p ~/.railway
echo '{"user":{"token":"xxxx"},"version":1}' > ~/.railway/config.json
```

#### 3. **CLI config.json スキーマ問題**
```json
// ❌ 動かないスキーマ
{"token": "xxxx"}

// ✅ CLI 4.5系が期待するスキーマ  
{
  "user": {
    "token": "xxxx"
  },
  "version": 1
}
```

#### 4. **認証エラーの根本原因**
```bash
# エラー: Unable to parse config file, regenerating
# 原因: CLI 4.5系のスキーマ不一致
# 解決: railway logout → 正しいスキーマで再設定
```

### ✅ **最終的な成功手順**
1. `npm uninstall -g @railway/cli && npm i -g @railway/cli@latest`
2. `railway logout || true` 
3. 正しいスキーマでconfig.json作成
4. `railway whoami` で認証確認
5. `railway init --name discord-ai-news-bot`
6. `railway up` でデプロイ成功

### 🎯 **TDD検証項目**
- [x] `jq '.user.token' ~/.railway/config.json` → UUID返却
- [x] `railway whoami` → メールアドレス返却  
- [x] `railway init` → プロジェクト作成成功
- [x] `railway up` → デプロイ成功

---

## 📅 更新履歴

### 2025-07-19
- ✅ プロジェクト開始
- ✅ 基本機能実装・テスト完了
- ✅ AI法規制RSS 32フィード追加
- ✅ ログ機能強化（Markdown対応）
- ✅ 会話記録機能追加
- ✅ Claude.md作成
- ✅ Xserver VPS セットアップスクリプト作成

### 2025-08-14
- 🔍 デプロイ状況調査・記録修正
- ❌ Railway未稼働確認（停止済みまたは未デプロイ）
- 🔒 Xserver VPS セキュリティ強化によりClaude外部アクセス制限
- 📝 CLAUDE.md デプロイ状況正確化

---

*最終更新: 2025-08-14*