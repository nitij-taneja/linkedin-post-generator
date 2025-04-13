#!/usr/bin/env python3
"""
Post Generator Module for LinkedIn Post Generator

This module handles generating LinkedIn posts using the Groq API
based on content from emails and research APIs.
"""

import json
import os
import logging
import requests
from datetime import datetime
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PostGenerator:
    """Class to generate LinkedIn posts using Groq API."""
    
    def __init__(self, config_path=None):
        """
        Initialize the PostGenerator with configuration.
        
        Args:
            config_path (str, optional): Path to the configuration file.
                If None, uses default config path.
        """
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'config',
            'sources.json'
        )
        self.config = self._load_config()
        self.post_preferences = self.config.get('post_preferences', {})
        
        # Groq API configuration
        self.api_key = os.environ.get('GROQ_API_KEY')
        self.api_endpoint = os.environ.get('GROQ_ENDPOINT', 'https://api.groq.com/v1/chat/completions')
        
        if not self.api_key:
            logger.warning("GROQ_API_KEY environment variable not set")
            
    def _load_config(self):
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
            
    def generate_posts(self, email_data, research_data):
        """
        Generate LinkedIn posts based on email and research data.
        
        Args:
            email_data (list): List of dictionaries containing email data
            research_data (dict): Dictionary containing research data from various sources
            
        Returns:
            list: List of generated LinkedIn posts
        """
        posts_per_day = self.post_preferences.get('posts_per_day', 3)
        topics = self.post_preferences.get('topics', ['ai', 'datascience'])
        
        # Combine and prepare content for post generation
        content_items = self._prepare_content(email_data, research_data)
        
        # Shuffle and select items for today's posts
        random.shuffle(content_items)
        selected_items = content_items[:posts_per_day]
        
        # Generate posts for selected items
        posts = []
        for item in selected_items:
            post = self._generate_post(item)
            if post:
                posts.append(post)
                
        logger.info(f"Generated {len(posts)} LinkedIn posts")
        return posts
        
    def _prepare_content(self, email_data, research_data):
        """
        Prepare content items from email and research data.
        
        Args:
            email_data (list): List of dictionaries containing email data
            research_data (dict): Dictionary containing research data from various sources
            
        Returns:
            list: List of content items for post generation
        """
        content_items = []
        
        # Process email data
        for email in email_data:
            content_items.append({
                'type': 'email',
                'title': email.get('subject', ''),
                'content': email.get('body', ''),
                'source': email.get('from', ''),
                'date': email.get('date', '')
            })
            
        # Process research data
        for source, items in research_data.items():
            for item in items:
                content_items.append({
                    'type': 'research',
                    'title': item.get('title', ''),
                    'content': item.get('summary', ''),
                    'authors': item.get('authors', []),
                    'link': item.get('link', ''),
                    'source': source,
                    'date': item.get('published', '')
                })
                
        return content_items
        
    def _generate_post(self, content_item):
        """
        Generate a LinkedIn post for a content item using Groq API.
        
        Args:
            content_item (dict): Dictionary containing content item data
            
        Returns:
            dict: Dictionary containing generated post data
        """
        if not self.api_key:
            logger.error("Cannot generate post: GROQ_API_KEY not set")
            return None
            
        # Prepare prompt based on content type
        prompt = self._create_prompt(content_item)
        
        try:
            # Call Groq API
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': 'llama3-70b-8192',
                'messages': [
                    {
                        'role': 'system',
                        'content': 'You are a professional LinkedIn content creator specializing in AI, data science, and technology topics. Your posts are insightful, educational, and engaging, with a professional tone that includes appropriate emojis and hashtags.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'temperature': 0.7,
                'max_tokens': 1024
            }
            
            response = requests.post(self.api_endpoint, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                post_content = result['choices'][0]['message']['content']
                
                # Create post object
                post = {
                    'content': post_content,
                    'source_type': content_item['type'],
                    'source_title': content_item['title'],
                    'source_link': content_item.get('link', ''),
                    'generated_at': datetime.now().isoformat()
                }
                
                return post
            else:
                logger.error(f"Groq API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating post: {e}")
            return None
            
    def _create_prompt(self, content_item):
        """
        Create a prompt for the Groq API based on content item.
        
        Args:
            content_item (dict): Dictionary containing content item data
            
        Returns:
            str: Prompt for Groq API
        """
        include_emojis = self.post_preferences.get('include_emojis', True)
        include_hashtags = self.post_preferences.get('include_hashtags', True)
        max_hashtags = self.post_preferences.get('max_hashtags', 10)
        
        if content_item['type'] == 'email':
            prompt = f"""
Create a professional LinkedIn post based on the following newsletter content:

TITLE: {content_item['title']}
CONTENT: {content_item['content'][:2000]}  # Limit content length
SOURCE: {content_item['source']}

Requirements:
1. Create an engaging, educational LinkedIn post about the key insights from this newsletter
2. Use a professional tone with clear structure (intro, key points, conclusion)
3. Include an emoji-rich headline
4. Break down complex concepts into numbered points
5. Include a "Why it matters" section
6. Properly credit the original source
7. Maximum length: 1300 characters
8. {"Include relevant emojis throughout the post" if include_emojis else "Do not use emojis"}
9. {"Add {max_hashtags} relevant hashtags at the end" if include_hashtags else "Do not include hashtags"}

Focus on AI, data science, and technology topics from the content.
"""
        else:  # Research content
            authors = ', '.join(content_item.get('authors', [])[:3])
            if len(content_item.get('authors', [])) > 3:
                authors += ' et al.'
                
            prompt = f"""
Create a professional LinkedIn post based on the following research:

TITLE: {content_item['title']}
SUMMARY: {content_item['content'][:2000]}  # Limit content length
AUTHORS: {authors}
SOURCE: {content_item['source']}
LINK: {content_item.get('link', '')}

Requirements:
1. Create an engaging, educational LinkedIn post about this research
2. Use a professional tone with clear structure (intro, key points, conclusion)
3. Include an emoji-rich headline
4. Break down the research into 3-5 numbered key points
5. Include a "Why it matters" section
6. Properly credit the researchers and include the link
7. Maximum length: 1300 characters
8. {"Include relevant emojis throughout the post" if include_emojis else "Do not use emojis"}
9. {"Add {max_hashtags} relevant hashtags at the end" if include_hashtags else "Do not include hashtags"}

Focus on explaining the significance and applications of this research in AI, data science, or technology.
"""
        
        return prompt

if __name__ == "__main__":
    # Example usage
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.email_fetcher import EmailFetcher
    from src.research_fetcher import ResearchFetcher
    
    # Check if API key is set
    if not os.environ.get('GROQ_API_KEY'):
        print("Please set the GROQ_API_KEY environment variable")
        sys.exit(1)
        
    # Fetch content
    email_fetcher = EmailFetcher()
    research_fetcher = ResearchFetcher()
    
    # For testing, use empty email data
    email_data = []
    research_data = research_fetcher.fetch_all_research()
    
    # Generate posts
    generator = PostGenerator()
    posts = generator.generate_posts(email_data, research_data)
    
    # Print generated posts
    for i, post in enumerate(posts):
        print(f"\n--- Post {i+1} ---")
        print(f"Based on: {post['source_title']}")
        print(f"Source: {post['source_type']}")
        if post['source_link']:
            print(f"Link: {post['source_link']}")
        print("\nContent:")
        print(post['content'])
