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
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error(f"Config file {config_file} not found")
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
        """Generate unique ID for article based on title and link"""
        content = f"{article.get('title', '')}{article.get('link', '')}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def calculate_ai_regulation_score(self, title: str, summary: str = "") -> int:
        """AI法規制関連度をスコア計算（3点以上で投稿対象）"""
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
                    else:
                        score = self.calculate_ai_regulation_score(article['title'], article['summary'])
                        logging.info(f"Filtered out (score {score}): {article['title']}")
                        self.log_to_markdown(f"🚫 Filtered article (score {score}): {article['title']}", "FILTER")
            
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
                message = self.format_article_message(article, feed_name, feed_config)
                
                if self.send_to_discord(message):
                    self.seen_articles.add(article['id'])
                    article_log = f"✅ Sent article from {feed_name}:\nTitle: {article['title']}\nLink: {article.get('link', 'No link')}"
                    logging.info(f"Sent article: {article['title']}")
                    self.log_to_markdown(article_log, "ARTICLE")
                else:
                    error_log = f"❌ Failed to send article from {feed_name}:\nTitle: {article['title']}"
                    logging.error(f"Failed to send article: {article['title']}")
                    self.log_to_markdown(error_log, "ERROR")
                
                time.sleep(1)  # Rate limiting
        
        self.save_seen_articles()
        completion_log = f"RSS feed processing completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        logging.info("RSS feed processing completed")
        self.log_to_markdown(completion_log, "COMPLETE")
    
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