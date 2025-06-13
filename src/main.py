#!/usr/bin/env python3
"""
Main module for LinkedIn Post Generator
Orchestrates the entire post generation workflow.
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
import random
import re
import shutil
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import local modules
from post_generator import PostGenerator
from image_generator import ImageGenerator
from equation_generator import EquationGenerator
from random_topic_generator import RandomTopicGenerator
from telegram_delivery import TelegramDelivery

def setup_directories():
    """Create necessary directories if they don't exist."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(base_dir)
    
    directories = [
        os.path.join(project_dir, 'posts'),
        os.path.join(project_dir, 'images'),
        os.path.join(project_dir, 'assets'),
        os.path.join(project_dir, 'assets', 'stock_images'),
        os.path.join(project_dir, 'assets', 'generated_images'),
        os.path.join(project_dir, 'assets', 'equations'),
        os.path.join(project_dir, 'analytics'),
        os.path.join(project_dir, 'config')
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Ensured directory exists: {directory}")
    
    # Create default config if it doesn't exist
    config_path = os.path.join(project_dir, 'config', 'sources.json')
    if not os.path.exists(config_path):
        default_config = {
            "email_sources": [],
            "research_sources": [],
            "custom_sources": []
        }
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        logger.info(f"Created default config at {config_path}")
    
    return project_dir

def load_sources(config_path):
    """Load sources from configuration file."""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        sources = []
        
        # Process email sources
        for source in config.get('email_sources', []):
            sources.append({
                'type': 'email',
                'title': source.get('subject', 'Untitled Email'),
                'content': source.get('body', ''),
                'link': source.get('link', '')
            })
        
        # Process research sources
        for source in config.get('research_sources', []):
            sources.append({
                'type': 'research',
                'title': source.get('title', 'Untitled Research'),
                'content': source.get('abstract', ''),
                'link': source.get('url', '')
            })
        
        # Process custom sources
        for source in config.get('custom_sources', []):
            sources.append({
                'type': source.get('type', 'custom'),
                'title': source.get('title', 'Untitled Custom Source'),
                'content': source.get('content', ''),
                'link': source.get('link', '')
            })
        
        return sources
    
    except Exception as e:
        logger.error(f"Error loading sources: {e}", exc_info=True)
        return []

def fetch_email_sources():
    """Fetch sources from email."""
    # This is a placeholder for the actual email fetching logic
    # In a real implementation, this would connect to an email server
    # and fetch emails based on configuration
    
    logger.info("Fetching email sources")
    
    # Check if email credentials are provided
    email_username = os.environ.get('EMAIL_USERNAME')
    email_password = os.environ.get('EMAIL_PASSWORD')
    email_server = os.environ.get('EMAIL_SERVER')
    
    if not email_username or not email_password or not email_server:
        logger.warning("Email credentials not provided. Skipping email sources.")
        return []
    
    # Placeholder for email fetching logic
    # In a real implementation, this would use the email credentials
    # to connect to the email server and fetch emails
    
    # For now, return a placeholder email source
    return [{
        'type': 'email',
        'title': 'Latest AI Developments Newsletter',
        'content': 'This is a placeholder for email content that would be fetched from an actual email server.',
        'link': ''
    }]

def fetch_research_sources():
    """Fetch sources from research papers."""
    # This is a placeholder for the actual research paper fetching logic
    # In a real implementation, this would connect to research paper APIs
    # or scrape websites to fetch recent papers
    
    logger.info("Fetching research sources")
    
    # Placeholder for research paper fetching logic
    # In a real implementation, this would use APIs or web scraping
    # to fetch recent research papers
    
    # For now, return a placeholder research source
    return [{
        'type': 'research',
        'title': 'Recent Advances in Machine Learning',
        'content': 'This is a placeholder for research paper content that would be fetched from actual research sources.',
        'link': 'https://arxiv.org/abs/example'
    }]

def generate_posts(sources, num_posts=3, random_topics=False):
    """Generate LinkedIn posts from sources."""
    logger.info(f"Generating {num_posts} posts (random_topics={random_topics})")
    
    # Initialize generators
    post_generator = PostGenerator()
    
    # If random topics are requested, generate them
    if random_topics:
        topic_generator = RandomTopicGenerator()
        random_sources = topic_generator.generate_random_topics(num_posts)
        # Combine with other sources and shuffle
        all_sources = sources + random_sources
        random.shuffle(all_sources)
        sources = all_sources
    
    # Generate posts
    posts = post_generator.generate_posts(sources, num_posts=num_posts)
    
    return posts

def deliver_posts(posts):
    """Deliver posts to Telegram."""
    logger.info(f"Delivering {len(posts)} posts to Telegram")
    
    # Initialize delivery
    delivery = TelegramDelivery()
    
    # Deliver posts
    success = delivery.deliver_posts(posts)
    
    if success:
        logger.info("Successfully delivered posts to Telegram")
    else:
        logger.error("Failed to deliver posts to Telegram")
    
    return success

def save_posts_to_github(posts):
    """Save posts to GitHub repository for contribution streak."""
    logger.info(f"Saving {len(posts)} posts to GitHub repository")
    
    try:
        # Create a summary file with links to all posts
        timestamp = datetime.now().strftime('%Y-%m-%d')
        summary_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                   'posts', f"summary_{timestamp}.md")
        
        with open(summary_file, 'w') as f:
            f.write(f"# LinkedIn Posts - {timestamp}\n\n")
            for i, post in enumerate(posts):
                f.write(f"## Post {i+1}: {post['source_title']}\n\n")
                f.write(f"Source: {post['source_type']}\n\n")
                f.write(f"[View full post]({os.path.relpath(post['post_file'], os.path.dirname(summary_file))})\n\n")
                if post.get('image_path'):
                    f.write(f"![Post Image]({os.path.relpath(post['image_path'], os.path.dirname(summary_file))})\n\n")
                f.write("---\n\n")
        
        logger.info(f"Created summary file at {summary_file}")
        return True
    
    except Exception as e:
        logger.error(f"Error saving posts to GitHub: {e}", exc_info=True)
        return False

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Generate LinkedIn posts')
    parser.add_argument('--num-posts', type=int, default=3, help='Number of posts to generate')
    parser.add_argument('--random-topics', action='store_true', help='Include random technical topics')
    parser.add_argument('--no-delivery', action='store_true', help='Skip delivery to Telegram')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    return parser.parse_args()

def main():
    """Main function."""
    # Parse arguments
    args = parse_arguments()
    
    # Setup directories
    project_dir = setup_directories()
    
    # Determine config path
    config_path = args.config or os.path.join(project_dir, 'config', 'sources.json')
    
    # Load sources
    sources = load_sources(config_path)
    
    # Fetch additional sources
    email_sources = fetch_email_sources()
    research_sources = fetch_research_sources()
    
    # Combine all sources
    all_sources = sources + email_sources + research_sources
    
    # Generate posts
    posts = generate_posts(all_sources, num_posts=args.num_posts, random_topics=args.random_topics)
    
    # Deliver posts if requested
    if not args.no_delivery:
        deliver_posts(posts)
    
    # Save posts to GitHub
    save_posts_to_github(posts)
    
    logger.info("LinkedIn post generation completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())
