#!/usr/bin/env python3
"""
Post Generator Module for LinkedIn Post Generator
Now includes personalized prompt logic for Daily Dose (Avi & Akshay) and improved formatting.
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
    def __init__(self, config_path=None):
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'config', 'sources.json'
        )
        self.config = self._load_config()
        self.post_preferences = self.config.get('post_preferences', {})

        # Groq API
        self.api_key = os.environ.get('GROQ_API_KEY')
        self.api_endpoint = os.environ.get('GROQ_ENDPOINT', 'https://api.groq.com/openai/v1/chat/completions')
        if not self.api_key:
            logger.warning("GROQ_API_KEY environment variable not set")

    def _load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}

    def generate_posts(self, email_data, research_data):
        posts_per_day = self.post_preferences.get('posts_per_day', 3)
        content_items = self._prepare_content(email_data, research_data)
        random.shuffle(content_items)
        selected_items = content_items[:posts_per_day]

        posts = []
        for item in selected_items:
            post = self._generate_post(item)
            if post:
                posts.append(post)
        logger.info(f"Generated {len(posts)} LinkedIn posts")
        return posts

    def _prepare_content(self, email_data, research_data):
        content_items = []
        for email in email_data:
            content_items.append({
                'type': 'email',
                'title': email.get('subject', ''),
                'content': email.get('body', ''),
                'source': email.get('from', ''),
                'date': email.get('date', '')
            })
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
        if not self.api_key:
            logger.error("Cannot generate post: GROQ_API_KEY not set")
            return None

        prompt = self._create_prompt(content_item)

        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            data = {
                'model': 'llama3-70b-8192',
                'messages': [
                    {
                        'role': 'system',
                        'content': (
                            "You are a professional LinkedIn content creator. "
                            "You write high-impact, concise posts on AI and data science, especially research or newsletter summaries."
                        )
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'temperature': 0.7,
                'max_tokens': 1024
            }

            response = requests.post(self.api_endpoint, headers=headers, json=data, timeout=120)
            if response.status_code == 200:
                result = response.json()
                post_content = result['choices'][0]['message']['content']
                return {
                    'content': post_content,
                    'source_type': content_item['type'],
                    'source_title': content_item['title'],
                    'source_link': content_item.get('link', ''),
                    'generated_at': datetime.now().isoformat()
                }
            else:
                logger.error(f"Groq API error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error generating post: {e}")
            return None

    def _create_prompt(self, item):
        include_emojis = self.post_preferences.get('include_emojis', True)
        include_hashtags = self.post_preferences.get('include_hashtags', True)
        max_hashtags = self.post_preferences.get('max_hashtags', 10)

        if item['type'] == 'email' and 'dailydoseofds.com' in item.get('source', '').lower():
            return f"""
You're writing a post based on a newsletter from Daily Dose of Data Science by Avi Chawla and Akshay Pachaar.

TITLE: {item['title']}
CONTENT: {item['content'][:1800]}

Instructions:
- Extract the 2 best ideas or facts
- Format clearly using line breaks or bullets
- Mention Avi and Akshay as curators
- Add 3+ relevant hashtags
- Use 2-3 emojis for attention
- End with "Follow Avi and Akshay for more insights"
- Max 1300 characters
"""

        elif item['type'] == 'research':
            authors = ', '.join(item.get('authors', [])[:3]) + (' et al.' if len(item.get('authors', [])) > 3 else '')
            return f"""
Summarize this AI research for a LinkedIn audience:

TITLE: {item['title']}
SUMMARY: {item['content'][:1800]}
AUTHORS: {authors}
SOURCE: {item['source']}
LINK: {item.get('link', '')}

Highlight:
- Key ideas
- Impact and use cases
- End with questions or future thoughts
- Include emojis and up to {max_hashtags} hashtags
- Max 1300 characters
"""
        else:
            return f"""
Write a brief, well-structured LinkedIn post:

TITLE: {item['title']}
CONTENT: {item['content'][:1800]}

- Include intro, value points, and CTA
- Use emojis and {max_hashtags} hashtags
- Max 1300 characters
"""
