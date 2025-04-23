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
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'config',
            'sources.json'
        )
        self.config = self._load_config()
        self.post_preferences = self.config.get('post_preferences', {})

        # Groq API configuration
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
        topics = self.post_preferences.get('topics', ['ai', 'datascience'])

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
                            "You are a professional LinkedIn content strategist who crafts concise, engaging, "
                            "and thought-leading posts on AI, data science, and cutting-edge research. "
                            "You write like a domain expert with clarity, confidence, and purpose. "
                            "Your goal is to make technical content accessible, relevant, and share-worthy."
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

    def _create_prompt(self, content_item):
        include_emojis = self.post_preferences.get('include_emojis', True)
        include_hashtags = self.post_preferences.get('include_hashtags', True)
        max_hashtags = self.post_preferences.get('max_hashtags', 10)

        if content_item['type'] == 'email':
            return f"""
Create a concise, insightful, and engaging LinkedIn post based on the following newsletter:

📰 TITLE: {content_item['title']}
📩 CONTENT: {content_item['content'][:2000]}
✉️ SOURCE: {content_item['source']}

Guidelines:
- Start with a bold, emoji-driven attention hook
- Extract 2–3 valuable insights from the content
- Format them with bullets or short paragraphs
- Add a "Why this matters" perspective
- End with a CTA or reflection
- Credit the original newsletter author/source
- Max 1300 characters
- {"Add emojis and up to " + str(max_hashtags) + " relevant hashtags" if include_emojis else "No emojis"}
"""

        else:  # research
            authors = ', '.join(content_item.get('authors', [])[:3])
            if len(content_item.get('authors', [])) > 3:
                authors += ' et al.'

            return f"""
Create a compelling LinkedIn post that summarizes this new research in a way that sparks curiosity and adds value to an AI-savvy audience:

📘 TITLE: {content_item['title']}
📄 SUMMARY: {content_item['content'][:2000]}
👥 AUTHORS: {authors}
🔗 LINK: {content_item.get('link', '')}

Guidelines:
- Start with a strong, emoji-infused headline
- Highlight 3–5 key takeaways from the research
- Explain the practical impact or future potential
- Include a brief "Why this matters" section
- End with a forward-looking or community-involving statement
- Max 1300 characters
- {"Include emojis and up to " + str(max_hashtags) + " relevant hashtags" if include_emojis else "Do not use emojis"}
"""

if __name__ == "__main__":
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.email_fetcher import EmailFetcher
    from src.research_fetcher import ResearchFetcher

    if not os.environ.get('GROQ_API_KEY'):
        print("Please set the GROQ_API_KEY environment variable")
        sys.exit(1)

    email_fetcher = EmailFetcher()
    research_fetcher = ResearchFetcher()

    email_data = []  # You can replace with: email_fetcher.fetch_emails()
    research_data = research_fetcher.fetch_all_research()

    generator = PostGenerator()
    posts = generator.generate_posts(email_data, research_data)

    for i, post in enumerate(posts):
        print(f"\n--- Post {i+1} ---")
        print(f"Based on: {post['source_title']}")
        print(f"Source: {post['source_type']}")
        if post['source_link']:
            print(f"Link: {post['source_link']}")
        print("\nContent:")
        print(post['content'])
