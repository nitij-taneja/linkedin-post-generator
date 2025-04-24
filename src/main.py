#!/usr/bin/env python3
"""
Main Module for LinkedIn Post Generator
Adds post file cleanup (older than 20 days) and analytics JSON recording.
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, timedelta

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modules
from src.email_fetcher import EmailFetcher
from src.research_fetcher import ResearchFetcher
from src.post_generator import PostGenerator
from src.telegram_delivery import TelegramDelivery

def cleanup_old_posts(directory, days_old=20):
    cutoff = datetime.now() - timedelta(days=days_old)
    deleted = 0
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            path = os.path.join(directory, filename)
            if os.path.isfile(path):
                created = datetime.fromtimestamp(os.path.getctime(path))
                if created < cutoff:
                    os.remove(path)
                    deleted += 1
    logger.info(f"Cleaned up {deleted} old post files from {directory}")

def save_posts_to_github(posts, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    analytics_dir = os.path.join(output_dir, '../analytics')
    os.makedirs(analytics_dir, exist_ok=True)

    saved_files = []
    for i, post in enumerate(posts):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        md_file = f"post_{timestamp}_{i+1}.md"
        md_path = os.path.join(output_dir, md_file)

        try:
            with open(md_path, 'w') as f:
                f.write(f"# LinkedIn Post Draft {i+1}\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"Source: {post['source_type']} - {post['source_title']}\n\n")
                f.write("## Content\n\n")
                f.write(post['content'])
                f.write("\n\n")
                if post['source_link']:
                    f.write(f"Original source: {post['source_link']}\n")

            # Save analytics JSON
            analytics = {
                'timestamp': datetime.now().isoformat(),
                'source_type': post['source_type'],
                'source_title': post['source_title'],
                'source_link': post.get('source_link', ''),
                'hashtags': post.get('hashtags', []),
                'content_length': len(post['content']),
                'mentions': ['Avi Chawla', 'Akshay Pachaar'] if 'avi' in post['source_title'].lower() else [],
                'formatting': {
                    'emojis': True,
                    'bullets': '-' in post['content']
                }
            }
            json_path = os.path.join(analytics_dir, f"analytics_{timestamp}_{i+1}.json")
            with open(json_path, 'w') as jf:
                json.dump(analytics, jf, indent=2)

            saved_files.append(md_path)
            logger.info(f"Saved post to {md_path} and analytics to {json_path}")

        except Exception as e:
            logger.error(f"Error saving post: {e}")
    return saved_files

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str)
    parser.add_argument('--output-dir', type=str, default='posts')
    parser.add_argument('--skip-email', action='store_true')
    parser.add_argument('--skip-telegram', action='store_true')
    args = parser.parse_args()

    config_path = args.config or os.path.join(os.path.dirname(__file__), '../config/sources.json')
    output_dir = os.path.abspath(args.output_dir)

    logger.info(f"Starting LinkedIn Post Generator with config: {config_path}")
    cleanup_old_posts(output_dir)

    try:
        if not os.environ.get('GROQ_API_KEY'):
            logger.error("GROQ_API_KEY not set")
            return 1

        if not args.skip_telegram and (not os.environ.get('TELEGRAM_BOT_TOKEN') or not os.environ.get('TELEGRAM_CHAT_ID')):
            logger.warning("Telegram credentials not set, skipping Telegram delivery")
            args.skip_telegram = True

        email_fetcher = EmailFetcher(config_path)
        research_fetcher = ResearchFetcher(config_path)
        post_generator = PostGenerator(config_path)

        email_data = []
        if not args.skip_email:
            if os.environ.get('EMAIL_USERNAME') and os.environ.get('EMAIL_PASSWORD'):
                email_data = email_fetcher.fetch_emails(
                    os.environ['EMAIL_USERNAME'],
                    os.environ['EMAIL_PASSWORD']
                )
            else:
                logger.warning("Email credentials not set")

        research_data = research_fetcher.fetch_all_research()
        posts = post_generator.generate_posts(email_data, research_data)

        if not posts:
            logger.warning("No posts generated")
            return 0

        saved_files = save_posts_to_github(posts, output_dir)

        if not args.skip_telegram:
            telegram_delivery = TelegramDelivery(config_path)
            telegram_delivery.deliver_posts(posts)

        return 0

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main())
