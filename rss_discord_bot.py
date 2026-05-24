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
        # 環境変数 SEEN_ARTICLES_PATH から既読ファイルパスを取得、デフォルトは "seen_articles.json"
        self.seen_articles_file = os.getenv('SEEN_ARTICLES_PATH', 'seen_articles.json')
        self.seen_articles = self.load_seen_articles()
        self.setup_logging()
    
    def load_config(self, config_file: str) -> Dict:
        config = {}
        
        # ローカル環境ではconfig.jsonを使用
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except FileNotFoundError:
            logging.warning(f"Config file {config_file} not found. Starting with default configuration.")
            config = {
                "rss_feeds": self.get_default_rss_feeds(),
                "check_interval_minutes": 60,
                "max_articles_per_feed": 2
            }
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON in config file {config_file}")
            raise
        
        # 環境変数からDISCORD_WEBHOOK_URLを最優先で読み込む（GitHub Secrets / VPS / Railway対応）
        webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        if webhook_url:
            config["discord_webhook_url"] = webhook_url
        elif "discord_webhook_url" not in config:
            logging.error("DISCORD_WEBHOOK_URL not set in environment or config file")
            raise ValueError("DISCORD_WEBHOOK_URL must be provided.")
            
        return config
    
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
            # 親ディレクトリが存在しない場合は作成（Actionsのキャッシュ保存等のため）
            dir_name = os.path.dirname(self.seen_articles_file)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            
            # バックアップ作成（拡張子を考慮した形式に変更）
            base, ext = os.path.splitext(self.seen_articles_file)
            backup_file = f"{base}_backup{ext}"
            if os.path.exists(self.seen_articles_file):
                import shutil
                try:
                    shutil.copy2(self.seen_articles_file, backup_file)
                except Exception as e:
                    logging.warning(f"Failed to create backup: {e}")
            
            with open(self.seen_articles_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.seen_articles), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Failed to save seen articles: {e}")
    
    def get_default_rss_feeds(self) -> List[Dict]:
        """GitHub Actions環境用のデフォルトRSSフィード設定（厳選されたフィードリスト）"""
        return [
            {"name": "🔬 OpenAI News", "url": "https://openai.com/news/rss.xml", "translate": True},
            {"name": "🔬 Anthropic News (Google News)", "url": "https://news.google.com/rss/search?q=Anthropic&hl=en-US&gl=US&ceid=US:en", "translate": True},
            {"name": "🔬 Google Research", "url": "https://research.google/blog/rss/", "translate": True},
            {"name": "🔬 Meta AI", "url": "https://ai.meta.com/blog/rss/", "translate": True},
            {"name": "🌐 VentureBeat AI", "url": "https://venturebeat.com/ai/feed/", "translate": True},
            {"name": "🇺🇸 WIRED – AI (Latest)", "url": "https://www.wired.com/feed/tag/ai/latest/rss", "translate": True},
            {"name": "🇺🇸 The Verge – Artificial Intelligence", "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "translate": True},
            {"name": "🧠 MIT Technology Review", "url": "https://www.technologyreview.com/feed/", "translate": True},
            {"name": "🇯🇵 ITmedia AI+", "url": "https://rss.itmedia.co.jp/rss/2.0/aiplus.xml"},
            {"name": "🇬🇧 The Guardian – Artificial Intelligence", "url": "https://www.theguardian.com/technology/artificialintelligenceai/rss", "translate": True},
            {"name": "🌐 OECD Digital", "url": "https://www.oecd.org/digital/rss.xml", "translate": True},
            {"name": "🏛️ 内閣府", "url": "https://www.cao.go.jp/rss/index.xml"},
            {"name": "🏛️ 総務省", "url": "https://www.soumu.go.jp/menu_news/rss/index.xml"},
            {"name": "🏛️ 経産省", "url": "https://www.meti.go.jp/rss/index.rdf"},
            {"name": "🏛️ デジタル庁", "url": "https://www.digital.go.jp/news/rss.xml"}
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
    
    def log_to_markdown(self, message: str, log_type: str = "INFO"):
        """ターミナル出力をMarkdownファイルに記録"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"## {timestamp} - {log_type}\n```\n{message}\n```\n\n"
            
            with open('terminal_log.md', 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            logging.error(f"Failed to log to markdown: {e}")
    
    def get_article_id(self, article) -> str:
        """Generate unique ID for article based on title, link, and published date"""
        # より一意性を高めるため公開日時も含める
        content = f"{article.get('title', '')}{article.get('link', '')}{article.get('published', '')}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def calculate_ai_regulation_score(self, title: str, summary: str = "") -> int:
        """AI法規制関連度をスコア計算（2点以上で投稿対象）"""
        text = f"{title} {summary}".lower()
        score = 0
        matched_keywords = []
        
        # AI技術関連キーワード（+2点）
        ai_tech_keywords = [
            "artificial intelligence", "machine learning", "generative ai",
            "large language model", "deep learning", "neural network",
            "ai", "人工知能", "生成ai", "機械学習", "chatgpt", "gpt", 
            "llm", "大規模言語モデル", "ディープラーニング", "自動化"
        ]
        
        # 法規制関連キーワード（+2点）- より具体的に
        regulation_keywords = [
            "regulation", "law", "policy", "guideline", "compliance", 
            "ethics", "governance", "framework", "standard",
            "規制", "法律", "法案", "政策", "ガイドライン", "倫理", 
            "コンプライアンス", "ルール", "指針", "基準"
        ]
        
        # セキュリティ・リスク関連（+2点）- 独立カテゴリに
        security_keywords = [
            "cybersecurity", "data breach", "privacy violation", "hacking",
            "vulnerability", "security flaw", "malware", "cyber attack",
            "悪用", "脆弱性", "セキュリティ", "サイバー攻撃", "マルウェア",
            "個人情報", "プライバシー", "情報漏洩"
        ]
        
        # 地域・機関名（+1点）- より具体的に
        region_keywords = [
            "european union", "united states", "eu commission", "us government",
            "nist", "ftc", "sec", "gdpr", "ai act", "白宮", "congress",
            "総務省", "経産省", "デジタル庁", "内閣府", "政府", "省庁",
            "欧州委員会", "米政府", "eu", "欧州", "ヨーロッパ", "アメリカ", "米国", "日本"
        ]
        
        # より具体的なマッチング（部分マッチを避ける）
        # AI技術キーワードチェック
        for keyword in ai_tech_keywords:
            if self._is_keyword_match(keyword, text):
                score += 2
                matched_keywords.append(f"AI:{keyword}")
                break
                
        # 法規制キーワードチェック
        for keyword in regulation_keywords:
            if self._is_keyword_match(keyword, text):
                score += 2
                matched_keywords.append(f"REG:{keyword}")
                break
                
        # セキュリティキーワードチェック
        for keyword in security_keywords:
            if self._is_keyword_match(keyword, text):
                score += 2
                matched_keywords.append(f"SEC:{keyword}")
                break
                
        # 地域キーワードチェック
        for keyword in region_keywords:
            if self._is_keyword_match(keyword, text):
                score += 1
                matched_keywords.append(f"REGION:{keyword}")
                break
        
        # デバッグ情報をログに出力
        if matched_keywords:
            logging.info(f"Matched keywords: {', '.join(matched_keywords)}")
        
        return score
    
    def _is_keyword_match(self, keyword: str, text: str) -> bool:
        """より精密なキーワードマッチング"""
        import re
        
        # 短いキーワード（3文字以下）は単語境界を使用
        if len(keyword) <= 3:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            return bool(re.search(pattern, text, re.IGNORECASE))
        
        # 長いキーワードは通常の部分マッチ
        return keyword.lower() in text.lower()
    
    def is_ai_regulation_related(self, article: Dict) -> bool:
        """AI法規制関連記事かどうか判定（スコア2点以上に緩和）"""
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
                        # 投稿対象記事は即座に見たものとしてマーク（重複防止）
                        self.seen_articles.add(article_id)
                    else:
                        score = self.calculate_ai_regulation_score(article['title'], article['summary'])
                        logging.info(f"Filtered out (score {score}): {article['title']}")
                        self.log_to_markdown(f"🚫 Filtered article (score {score}): {article['title']}", "FILTER")
                        # フィルターされた記事も見たものとしてマーク
                        self.seen_articles.add(article_id)
            
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
        processing_start = f"Starting RSS feed processing at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        logging.info("Starting RSS feed processing")
        self.log_to_markdown(processing_start, "START")
        
        for feed_config in self.config['rss_feeds']:
            feed_name = feed_config['name']
            feed_url = feed_config['url']
            
            feed_log = f"Processing feed: {feed_name}\nURL: {feed_url}"
            logging.info(f"Processing feed: {feed_name}")
            self.log_to_markdown(feed_log, "FEED")
            
            articles = self.parse_rss_feed(feed_url)
            
            for article in articles:
                # 記事IDが既にseen_articlesに追加されているかチェック
                if article['id'] in self.seen_articles:
                    message = self.format_article_message(article, feed_name, feed_config)
                    
                    if self.send_to_discord(message):
                        article_log = f"✅ Sent article from {feed_name}:\nTitle: {article['title']}\nLink: {article.get('link', 'No link')}"
                        logging.info(f"Sent article: {article['title']}")
                        self.log_to_markdown(article_log, "ARTICLE")
                        
                        # 送信後に即座に保存（個別保存で確実性向上）
                        self.save_seen_articles()
                    else:
                        error_log = f"❌ Failed to send article from {feed_name}:\nTitle: {article['title']}"
                        logging.error(f"Failed to send article: {article['title']}")
                        self.log_to_markdown(error_log, "ERROR")
                        # 送信失敗時はseen_articlesから削除（再試行可能にする）
                        self.seen_articles.discard(article['id'])
                    
                    time.sleep(1)  # Rate limiting
        
        self.save_seen_articles()
        completion_log = f"RSS feed processing completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        logging.info("RSS feed processing completed")
        self.log_to_markdown(completion_log, "COMPLETE")
    
    def run_once(self):
        """Run the bot once"""
        self.process_feeds()
    
    def run_forever(self):
        """Run the bot at XX:00 and XX:30 every 30 minutes"""
        logging.info("Starting RSS Discord Bot with 30-minute schedule (XX:00, XX:30)")
        last_execution = None
        
        while True:
            try:
                current_time = datetime.now()
                current_minute = current_time.minute
                current_key = f"{current_time.hour}:{current_minute:02d}"
                
                # XX:00またはXX:30の0分・30分に実行（重複実行防止）
                if (current_minute == 0 or current_minute == 30) and last_execution != current_key:
                    logging.info(f"Scheduled execution at {current_time.strftime('%H:%M')}")
                    self.process_feeds()
                    last_execution = current_key
                    time.sleep(60)  # 1分待機（同じ時間での再実行を防ぐ）
                else:
                    # 次の0分または30分まで待機
                    if current_minute < 30:
                        minutes_to_wait = 30 - current_minute
                    else:
                        minutes_to_wait = 60 - current_minute
                    
                    # ログ重複を避けるため、新しいスケジュールでのみログ出力
                    if last_execution != current_key:
                        logging.info(f"Waiting {minutes_to_wait} minutes until next scheduled run (XX:00 or XX:30)")
                    
                    time.sleep(min(60, minutes_to_wait * 60))  # 最大1分間隔でチェック
            
            except KeyboardInterrupt:
                logging.info("Bot stopped by user")
                break
            except Exception as e:
                logging.error(f"Unexpected error: {e}")
                time.sleep(60)  # Wait 1 minute before retrying


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="RSS Discord Bot")
    parser.add_argument("--once", action="store_true", help="Run the bot once and exit")
    args = parser.parse_args()
    
    bot = RSSDiscordBot()
    
    if args.once:
        bot.run_once()
    else:
        bot.run_forever()