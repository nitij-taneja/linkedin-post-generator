#!/usr/bin/env python3
"""
Main Module for LinkedIn Post Generator

This module orchestrates the entire LinkedIn post generation process.
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'linkedin_post_generator.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import project modules
from src.email_fetcher import EmailFetcher
from src.research_fetcher import ResearchFetcher
from src.post_generator import PostGenerator
from src.telegram_delivery import TelegramDelivery

def save_posts_to_github(posts, output_dir):
    """
    Save generated posts to GitHub repository as markdown files.
    
    Args:
        posts (list): List of dictionaries containing post data
        output_dir (str): Directory to save posts
        
    Returns:
        list: List of saved file paths
    """
    os.makedirs(output_dir, exist_ok=True)
    saved_files = []
    
    for i, post in enumerate(posts):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"post_{timestamp}_{i+1}.md"
        filepath = os.path.join(output_dir, filename)
        
        try:
            with open(filepath, 'w') as f:
                f.write(f"# LinkedIn Post Draft {i+1}\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"Source: {post['source_type']} - {post['source_title']}\n\n")
                f.write("## Content\n\n")
                f.write(post['content'])
                f.write("\n\n")
                
                if post['source_link']:
                    f.write(f"Original source: {post['source_link']}\n")
                    
            saved_files.append(filepath)
            logger.info(f"Saved post to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving post to file: {e}")
            
    return saved_files

def main():
    """Main function to run the LinkedIn post generator."""
    parser = argparse.ArgumentParser(description='LinkedIn Post Generator')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--output-dir', type=str, default='posts', help='Directory to save posts')
    parser.add_argument('--skip-email', action='store_true', help='Skip email fetching')
    parser.add_argument('--skip-telegram', action='store_true', help='Skip Telegram delivery')
    args = parser.parse_args()
    
    # Determine config path
    config_path = args.config
    if not config_path:
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'sources.json')
        
    # Determine output directory
    output_dir = args.output_dir
    if not os.path.isabs(output_dir):
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), output_dir)
        
    logger.info(f"Starting LinkedIn Post Generator with config: {config_path}")
    
    try:
        # Check required environment variables
        if not args.skip_telegram and (not os.environ.get('TELEGRAM_BOT_TOKEN') or not os.environ.get('TELEGRAM_CHAT_ID')):
            logger.warning("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set, skipping Telegram delivery")
            args.skip_telegram = True
            
        if not os.environ.get('GROQ_API_KEY'):
            logger.error("GROQ_API_KEY environment variable not set")
            return 1
            
        # Initialize components
        email_fetcher = EmailFetcher(config_path)
        research_fetcher = ResearchFetcher(config_path)
        post_generator = PostGenerator(config_path)
        
        # Fetch content
        email_data = []
        if not args.skip_email:
            if os.environ.get('EMAIL_USERNAME') and os.environ.get('EMAIL_PASSWORD'):
                email_data = email_fetcher.fetch_emails(
                    os.environ.get('EMAIL_USERNAME'),
                    os.environ.get('EMAIL_PASSWORD')
                )
                logger.info(f"Fetched {len(email_data)} emails")
            else:
                logger.warning("EMAIL_USERNAME or EMAIL_PASSWORD not set, skipping email fetching")
                
        research_data = research_fetcher.fetch_all_research()
        logger.info(f"Fetched research data from {len(research_data)} sources")
        
        # Generate posts
        posts = post_generator.generate_posts(email_data, research_data)
        logger.info(f"Generated {len(posts)} LinkedIn posts")
        
        if not posts:
            logger.warning("No posts were generated")
            return 0
            
        # Save posts to GitHub
        saved_files = save_posts_to_github(posts, output_dir)
        logger.info(f"Saved {len(saved_files)} posts to GitHub")
        
        # Deliver posts via Telegram
        if not args.skip_telegram:
            telegram_delivery = TelegramDelivery(config_path)
            success = telegram_delivery.deliver_posts(posts)
            if success:
                logger.info("Successfully delivered posts via Telegram")
            else:
                logger.error("Failed to deliver posts via Telegram")
                
        return 0
        
    except Exception as e:
        logger.error(f"Error running LinkedIn Post Generator: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
