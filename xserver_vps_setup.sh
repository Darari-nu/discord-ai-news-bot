#!/bin/bash

# Xserver VPS自動セットアップスクリプト
# Discord RSS Bot のデプロイメント

set -e

# 色付き出力関数
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# SSH接続情報
VPS_IP="210.131.217.175"
VPS_USER="root"
VPS_PASSWORD="j-33008744444-"
DISCORD_WEBHOOK="https://discord.com/api/webhooks/1396002981291229324/HZBDfa1QpEp1SgD9QA_iwEHYC5A_DWj8Z3lB5BsBxiC2D8Ex2eQjvNpJdkmr1iqRROur"

log_info "=== Xserver VPS Discord RSS Bot セットアップ開始 ==="

# SSH接続テスト
log_info "SSH接続をテストしています..."
if ! sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$VPS_USER@$VPS_IP" "echo 'SSH接続成功'" 2>/dev/null; then
    log_error "SSH接続に失敗しました。以下を確認してください："
    echo "  - IPアドレス: $VPS_IP"
    echo "  - ユーザー名: $VPS_USER"
    echo "  - パスワード: $VPS_PASSWORD"
    echo ""
    echo "sshpassがインストールされていない場合："
    echo "  macOS: brew install hudochenkov/sshpass/sshpass"
    echo "  Ubuntu: sudo apt-get install sshpass"
    exit 1
fi

log_info "SSH接続成功！セットアップを開始します..."

# リモートセットアップスクリプトを作成
cat > /tmp/remote_setup.sh << 'EOF'
#!/bin/bash

set -e

echo "=== サーバー環境セットアップ開始 ==="

# システム更新
echo "システムを更新中..."
if command -v apt-get &> /dev/null; then
    apt-get update -y
    apt-get upgrade -y
    apt-get install -y python3 python3-pip python3-venv git curl
elif command -v yum &> /dev/null; then
    yum update -y
    yum install -y python3 python3-pip git curl
elif command -v dnf &> /dev/null; then
    dnf update -y
    dnf install -y python3 python3-pip git curl
fi

# Pythonバージョン確認
python3 --version

# 作業ディレクトリ作成
cd /opt
rm -rf discord-rss-bot
mkdir -p discord-rss-bot
cd discord-rss-bot

# Discord RSS Botコードを作成
cat > rss_discord_bot.py << 'PYTHON_EOF'
#!/usr/bin/env python3
import json
import time
import logging
import hashlib
import os
from datetime import datetime
from typing import List, Dict, Set

# Python 3.13 compatibility fix for feedparser
try:
    import cgi
except ImportError:
    # For Python 3.13+, create a minimal cgi module replacement
    import sys
    from types import ModuleType
    
    cgi = ModuleType('cgi')
    cgi.parse_header = lambda value: (value.split(';')[0].strip(), {})
    sys.modules['cgi'] = cgi

import feedparser
import requests

class RSSDiscordBot:
    def __init__(self, config_file: str = "config.json"):
        self.config = self.load_config(config_file)
        self.seen_articles_file = "seen_articles.json"
        self.seen_articles = self.load_seen_articles()
        self.setup_logging()
    
    def load_config(self, config_file: str) -> Dict:
        # 環境変数から設定を読み込む（VPS環境）
        webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        if webhook_url:
            return {
                "discord_webhook_url": webhook_url,
                "rss_feeds": self.get_default_rss_feeds(),
                "check_interval_minutes": 60,
                "max_articles_per_feed": 2
            }
        
        # config.jsonを使用
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error(f"Config file {config_file} not found and no DISCORD_WEBHOOK_URL env var")
            raise
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON in config file {config_file}")
            raise
    
    def load_seen_articles(self) -> Set[str]:
        try:
            with open(self.seen_articles_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(data)
        except FileNotFoundError:
            return set()
        except json.JSONDecodeError:
            logging.warning("Invalid JSON in seen articles file, starting fresh")
            return set()
    
    def save_seen_articles(self):
        try:
            with open(self.seen_articles_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.seen_articles), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Failed to save seen articles: {e}")
    
    def get_default_rss_feeds(self) -> List[Dict]:
        """VPS環境用のデフォルトRSSフィード設定"""
        return [
            {"name": "🚀 TechCrunch", "url": "https://techcrunch.com/feed/", "translate": True},
            {"name": "🇺🇸 Washington Post Tech", "url": "https://feeds.washingtonpost.com/rss/business/technology", "translate": True},
            {"name": "🇺🇸 Reuters (Google News)", "url": "https://news.google.com/rss/search?q=when:24h+allinurl:reuters.com&ceid=US:en&hl=en-US&gl=US", "translate": True},
            {"name": "🇪🇺 EURACTIV", "url": "https://www.euractiv.com/feed/", "translate": True},
            {"name": "🇪🇺 TechCrunch Europe", "url": "https://techcrunch.com/category/startups/europe/feed/", "translate": True},
            {"name": "🇯🇵 ITmedia AI+", "url": "https://rss.itmedia.co.jp/rss/2.0/aiplus.xml"},
            {"name": "🇯🇵 日経xTECH", "url": "https://xtech.nikkei.com/rss/index.rdf"},
            {"name": "🧠 MIT Technology Review", "url": "https://www.technologyreview.com/feed/", "translate": True},
            {"name": "🌐 VentureBeat AI", "url": "https://venturebeat.com/ai/feed/", "translate": True},
            {"name": "🌐 OECD Digital", "url": "https://www.oecd.org/digital/rss.xml", "translate": True},
            {"name": "🏛️ 内閣府", "url": "https://www.cao.go.jp/rss/index.xml"},
            {"name": "🏛️ 総務省", "url": "https://www.soumu.go.jp/menu_news/rss/index.xml"},
            {"name": "🏛️ 経産省", "url": "https://www.meti.go.jp/rss/index.rdf"},
            {"name": "🏛️ デジタル庁", "url": "https://www.digital.go.jp/news/rss.xml"},
            {"name": "🇯🇵 日本経済新聞 (Google News)", "url": "https://news.google.com/rss/search?q=site:nikkei.com&hl=ja&gl=JP&ceid=JP:ja"},
            {"name": "🇺🇸 Bloomberg Tech", "url": "https://feeds.bloomberg.com/technology/news.rss", "translate": True},
            {"name": "🇬🇧 BBC News – Technology", "url": "http://feeds.bbci.co.uk/news/technology/rss.xml", "translate": True},
            {"name": "🇬🇧 The Guardian – Artificial Intelligence", "url": "https://www.theguardian.com/technology/artificialintelligenceai/rss", "translate": True},
            {"name": "🇺🇸 WIRED – AI (Latest)", "url": "https://www.wired.com/feed/tag/ai/latest/rss", "translate": True},
            {"name": "🇺🇸 The Verge – Artificial Intelligence", "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "translate": True},
            {"name": "🇬🇧 The Register – AI/ML", "url": "https://www.theregister.com/software/ai_ml/headlines.atom", "translate": True},
            {"name": "🌐 AI Business", "url": "https://aibusiness.com/rss.xml", "translate": True},
            {"name": "🌐 Artificial Intelligence News", "url": "https://www.artificialintelligence-news.com/feed/rss/", "translate": True},
            {"name": "🌐 SiliconANGLE – AI", "url": "https://siliconangle.com/category/ai/feed", "translate": True},
            {"name": "🌐 TechRepublic – AI", "url": "https://www.techrepublic.com/rssfeeds/topic/artificial-intelligence/", "translate": True},
            {"name": "🌐 Futurism – Artificial Intelligence", "url": "https://futurism.com/categories/ai-artificial-intelligence/feed", "translate": True},
            {"name": "🔬 OpenAI News", "url": "https://openai.com/news/rss.xml", "translate": True},
            {"name": "🔬 Google Research", "url": "https://research.google/blog/rss/", "translate": True},
            {"name": "🔬 Meta AI", "url": "https://ai.meta.com/blog/rss/", "translate": True},
            {"name": "📰 WSJ Tech", "url": "https://feeds.content.dowjones.io/public/rss/wsj/tech/feed", "translate": True},
            {"name": "📚 arXiv AI Papers", "url": "http://export.arxiv.org/rss/cs.AI", "translate": True}
        ]
    
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('rss_bot.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    def get_article_id(self, article) -> str:
        """Generate unique ID for article based on title and link"""
        content = f"{article.get('title', '')}{article.get('link', '')}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def calculate_ai_regulation_score(self, title: str, summary: str = "") -> int:
        """AI法規制関連度をスコア計算（2点以上で投稿対象）"""
        text = f"{title} {summary}".lower()
        score = 0
        
        # AI技術関連キーワード（+2点）
        ai_tech_keywords = [
            "ai", "人工知能", "生成ai", "機械学習", "chatgpt", "gpt", 
            "llm", "大規模言語モデル", "ディープラーニング", "自動化",
            "artificial intelligence", "machine learning", "generative ai",
            "large language model", "deep learning", "neural network"
        ]
        
        # 法規制関連キーワード（+2点）
        regulation_keywords = [
            "規制", "法律", "法案", "政策", "ガイドライン", "倫理", 
            "コンプライアンス", "ルール", "指針", "基準",
            "悪用", "脆弱性", "セキュリティ", "リスク", "危険", "問題",
            "regulation", "law", "policy", "guideline", "compliance", 
            "ethics", "governance", "framework", "standard",
            "misuse", "vulnerability", "security", "risk", "danger", "malware"
        ]
        
        # 地域・機関名（+1点）
        region_keywords = [
            "eu", "欧州", "ヨーロッパ", "アメリカ", "米国", "日本", 
            "総務省", "経産省", "デジタル庁", "gdpr", "ai act",
            "european union", "united states", "nist", "ftc", "sec"
        ]
        
        # スコア計算
        for keyword in ai_tech_keywords:
            if keyword in text:
                score += 2
                break
                
        for keyword in regulation_keywords:
            if keyword in text:
                score += 2
                break
                
        for keyword in region_keywords:
            if keyword in text:
                score += 1
                break
        
        return score
    
    def is_ai_regulation_related(self, article: Dict) -> bool:
        """AI法規制関連記事かどうか判定（スコア2点以上）"""
        score = self.calculate_ai_regulation_score(
            article.get('title', ''), 
            article.get('summary', '')
        )
        return score >= 2
    
    def get_article_category(self, title: str, summary: str = "") -> str:
        """記事のカテゴリを判定"""
        text = f"{title} {summary}".lower()
        
        # カテゴリ判定用キーワード
        categories = []
        
        # AI技術
        ai_tech = ["ai", "人工知能", "chatgpt", "gpt", "機械学習", "ディープラーニング", 
                   "artificial intelligence", "machine learning", "neural network"]
        if any(keyword in text for keyword in ai_tech):
            categories.append("AI技術")
        
        # 法規制・政策
        regulation = ["規制", "法律", "政策", "ガイドライン", "行政指導", 
                     "regulation", "law", "policy", "governance"]
        if any(keyword in text for keyword in regulation):
            categories.append("法規制")
        
        # セキュリティ・リスク
        security = ["悪用", "脆弱性", "セキュリティ", "リスク", "危険", "マルウェア",
                   "security", "vulnerability", "risk", "malware", "misuse"]
        if any(keyword in text for keyword in security):
            categories.append("セキュリティ")
        
        # 政府・機関
        government = ["総務省", "経産省", "デジタル庁", "内閣府", "政府", "省庁",
                     "government", "ministry", "agency"]
        if any(keyword in text for keyword in government):
            categories.append("政府発表")
        
        # カテゴリが複数ある場合は結合、なければデフォルト
        if categories:
            return "・".join(categories)
        else:
            return "技術動向"
    
    def parse_rss_feed(self, feed_url: str) -> List[Dict]:
        try:
            feed = feedparser.parse(feed_url)
            if feed.bozo:
                logging.warning(f"RSS feed parsing warning for {feed_url}: {feed.bozo_exception}")
            
            articles = []
            max_articles = self.config.get('max_articles_per_feed', 5)
            
            for entry in feed.entries[:max_articles]:
                article_id = self.get_article_id(entry)
                
                if article_id not in self.seen_articles:
                    article = {
                        'id': article_id,
                        'title': entry.get('title', 'No title'),
                        'link': entry.get('link', ''),
                        'published': entry.get('published', ''),
                        'summary': entry.get('summary', '')
                    }
                    
                    # AI法規制関連度チェック
                    if self.is_ai_regulation_related(article):
                        score = self.calculate_ai_regulation_score(article['title'], article['summary'])
                        logging.info(f"AI regulation score {score}: {article['title']}")
                        articles.append(article)
                    else:
                        score = self.calculate_ai_regulation_score(article['title'], article['summary'])
                        logging.info(f"Filtered out (score {score}): {article['title']}")
            
            return articles
        
        except Exception as e:
            logging.error(f"Error parsing RSS feed {feed_url}: {e}")
            return []
    
    def send_to_discord(self, message: str) -> bool:
        try:
            webhook_url = self.config['discord_webhook_url']
            payload = {
                'content': message,
                'username': 'RSS Bot'
            }
            
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
            
            logging.info("Message sent to Discord successfully")
            return True
        
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to send message to Discord: {e}")
            return False
    
    def translate_text(self, text: str) -> str:
        try:
            # Google Translate API (無料版)
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                'client': 'gtx',
                'sl': 'en',
                'tl': 'ja',
                'dt': 't',
                'q': text
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            result = response.json()
            translated = result[0][0][0]
            
            return translated
        
        except Exception as e:
            logging.warning(f"Translation failed: {e}")
            return text  # 翻訳に失敗した場合は元のテキストを返す
    
    def format_article_message(self, article: Dict, feed_name: str, feed_config: Dict) -> str:
        title = article['title']
        link = article['link']
        summary = article.get('summary', '')
        
        # カテゴリを取得
        category = self.get_article_category(title, summary)
        
        # 翻訳が必要な場合
        if feed_config.get('translate', False):
            translated_title = self.translate_text(title)
            display_title = translated_title
            # X投稿用は元の英語タイトルを使用
            tweet_title = title
        else:
            display_title = title
            tweet_title = title
        
        # X(Twitter)への投稿リンクを作成（元のタイトルを使用）
        tweet_text = f"\n\n{tweet_title} {link}"
        x_intent_url = f"https://x.com/intent/post?text={requests.utils.quote(tweet_text)}"
        
        message = f"**{feed_name}** 【{category}】\n"
        message += f"📰 {display_title}\n"
        message += f"🔗 {link}\n"
        message += f"🐦 [Xに投稿]({x_intent_url})"
        
        return message
    
    def process_feeds(self):
        logging.info("Starting RSS feed processing")
        
        for feed_config in self.config['rss_feeds']:
            feed_name = feed_config['name']
            feed_url = feed_config['url']
            
            logging.info(f"Processing feed: {feed_name}")
            
            articles = self.parse_rss_feed(feed_url)
            
            for article in articles:
                message = self.format_article_message(article, feed_name, feed_config)
                
                if self.send_to_discord(message):
                    self.seen_articles.add(article['id'])
                    logging.info(f"Sent article: {article['title']}")
                else:
                    logging.error(f"Failed to send article: {article['title']}")
                
                time.sleep(1)  # Rate limiting
        
        self.save_seen_articles()
        logging.info("RSS feed processing completed")
    
    def run_once(self):
        """Run the bot once"""
        self.process_feeds()
    
    def run_forever(self):
        """Run the bot continuously with specified interval"""
        interval_minutes = self.config.get('check_interval_minutes', 60)
        interval_seconds = interval_minutes * 60
        
        logging.info(f"Starting RSS Discord Bot with {interval_minutes} minute intervals")
        
        while True:
            try:
                self.process_feeds()
                logging.info(f"Sleeping for {interval_minutes} minutes...")
                time.sleep(interval_seconds)
            
            except KeyboardInterrupt:
                logging.info("Bot stopped by user")
                break
            except Exception as e:
                logging.error(f"Unexpected error: {e}")
                time.sleep(60)  # Wait 1 minute before retrying


if __name__ == "__main__":
    import sys
    
    bot = RSSDiscordBot()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        bot.run_once()
    else:
        bot.run_forever()
PYTHON_EOF

# requirements.txtを作成
cat > requirements.txt << 'REQ_EOF'
feedparser==6.0.10
requests==2.31.0
REQ_EOF

# 仮想環境を作成してパッケージをインストール
echo "Python仮想環境を作成中..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# systemdサービスファイルを作成
cat > /etc/systemd/system/discord-rss-bot.service << 'SERVICE_EOF'
[Unit]
Description=Discord RSS Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/discord-rss-bot
Environment=DISCORD_WEBHOOK_URL=WEBHOOK_URL_PLACEHOLDER
ExecStart=/opt/discord-rss-bot/venv/bin/python /opt/discord-rss-bot/rss_discord_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE_EOF

echo "セットアップ完了！"
echo "Discord Webhook URLを設定してサービスを開始してください。"
EOF

# リモートサーバーにスクリプトをアップロードして実行
log_info "リモートサーバーにセットアップスクリプトを転送中..."
sshpass -p "$VPS_PASSWORD" scp -o StrictHostKeyChecking=no /tmp/remote_setup.sh "$VPS_USER@$VPS_IP:/tmp/"

log_info "リモートサーバーでセットアップを実行中..."
sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "chmod +x /tmp/remote_setup.sh && /tmp/remote_setup.sh"

# Discord Webhook URLを設定
log_info "Discord Webhook URLを設定中..."
sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "sed -i 's|WEBHOOK_URL_PLACEHOLDER|$DISCORD_WEBHOOK|' /etc/systemd/system/discord-rss-bot.service"

# systemdサービスを開始
log_info "Discord RSS Botサービスを開始中..."
sshpass -p "$VPS_PASSWORD" ssh -o StrictHostKeyChecking=no "$VPS_USER@$VPS_IP" "
    systemctl daemon-reload
    systemctl enable discord-rss-bot
    systemctl start discord-rss-bot
    systemctl status discord-rss-bot
"

log_info "=== セットアップ完了！ ==="
echo ""
echo "🎉 Discord RSS BotがXserver VPSで起動しました！"
echo ""
echo "📊 サービス管理コマンド："
echo "  ステータス確認: ssh root@$VPS_IP 'systemctl status discord-rss-bot'"
echo "  ログ確認:       ssh root@$VPS_IP 'journalctl -u discord-rss-bot -f'"
echo "  サービス停止:   ssh root@$VPS_IP 'systemctl stop discord-rss-bot'"
echo "  サービス開始:   ssh root@$VPS_IP 'systemctl start discord-rss-bot'"
echo ""
echo "🚀 ボットは60分間隔でAI法規制ニュースを監視・投稿します"