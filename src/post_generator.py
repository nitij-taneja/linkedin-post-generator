#!/usr/bin/env python3
"""
Post Generator Module for LinkedIn Post Generator
Enhanced with advanced prompting, diversity in tone, LLM-augmented context, hyperlink support,
free image generation capabilities, random topic generation, and enriched technical content.
"""

import json
import os
import logging
import requests
from datetime import datetime
import random
import re
import base64

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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

        self.api_key = os.environ.get('GROQ_API_KEY')
        self.api_endpoint = os.environ.get('GROQ_ENDPOINT', 'https://api.groq.com/openai/v1/chat/completions')
        if not self.api_key:
            logger.warning("GROQ_API_KEY environment variable not set")
            
        from src.image_generator import ImageGenerator
        self.image_generator = ImageGenerator(config_path)

    def _load_config(self):
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}

    def generate_posts(self, email_data, research_data, max_posts=3, emails_only=False):
        posts = []
        content_items = self._prepare_content(email_data, research_data, emails_only)
        random.shuffle(content_items)
        for item in content_items:
            post = self._generate_post(item)
            if post:
                image_path, cleaned_content = self.image_generator.generate_image_for_post(
                    post['content'], 
                    item['title'],
                    self._determine_category(item),
                    item.get('has_equations', False),
                    item.get('has_architecture', False)
                )
                post['content'] = cleaned_content
                if image_path:
                    post['image_path'] = image_path
                posts.append(post)
            if len(posts) >= max_posts:
                break
        logger.info(f"Generated {len(posts)} LinkedIn posts from email/research")
        return posts

    def generate_random_posts(self, topics):
        posts = []
        for topic in topics:
            post = self._generate_post(topic, is_random_topic=True)
            if post:
                image_path, cleaned_content = self.image_generator.generate_image_for_post(
                    post['content'], 
                    topic['title'],
                    topic.get('category', 'technology'),
                    topic.get('has_equations', False),
                    topic.get('has_architecture', False)
                )
                post['content'] = cleaned_content
                if image_path:
                    post['image_path'] = image_path
                posts.append(post)
        logger.info(f"Generated {len(posts)} LinkedIn posts from random topics")
        return posts

    def _determine_category(self, item):
        title = item.get('title', '').lower()
        content = item.get('content', '').lower()
        if any(term in title or term in content for term in ['nlp', 'language model', 'transformer']):
            return 'nlp'
        elif any(term in title or term in content for term in ['mlops', 'deployment', 'monitoring']):
            return 'mlops'
        elif any(term in title or term in content for term in ['machine learning', 'ml', 'neural network', 'deep learning']):
            return 'machine_learning'
        elif any(term in title or term in content for term in ['ai', 'artificial intelligence']):
            return 'ai'
        elif any(term in title or term in content for term in ['data science', 'data analysis', 'statistics']):
            return 'data_science'
        elif any(term in title or term in content for term in ['business', 'strategy', 'management']):
            return 'business'
        else:
            return 'technology'

    def _prepare_content(self, email_data, research_data, emails_only=False):
        content_items = []
        for email in email_data:
            content_items.append({
                'type': 'email',
                'title': email.get('subject', ''),
                'content': email.get('body', ''),
                'source': email.get('from', ''),
                'date': email.get('date', '')
            })
        if not emails_only:
            for source, items in research_data.items():
                for item in items:
                    content_items.append({
                        'type': 'research',
                        'title': item.get('title', ''),
                        'content': item.get('summary', ''),
                        'authors': item.get('authors', []),
                        'link': item.get('link', ''),
                        'source': source,
                        'date': item.get('published', ''),
                        'has_equations': True,
                        'has_architecture': True
                    })
        return content_items

    def _generate_post(self, content_item, is_random_topic=False):
        if not self.api_key:
            logger.error("Cannot generate post: GROQ_API_KEY not set")
            return None

        prompt = self._create_prompt(content_item, is_random_topic)

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
                        'content': 'You are a helpful assistant.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'temperature': 0.7,
                'max_tokens': 1500
            }

            response = requests.post(self.api_endpoint, headers=headers, json=data, timeout=180)
            if response.status_code == 200:
                result = response.json()
                post_content = result['choices'][0]['message']['content']
                if len(post_content) < 100 or "error" in post_content.lower():
                    logger.warning(f"Generated post seems too short or contains error: {post_content[:100]}...")
                    return None
                return {
                    'content': post_content,
                    'source_type': content_item.get('type', 'random_topic'),
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

    def _contains_image_references(self, content):
        return bool(re.search(r'<img|!\[.*?\]\(.*?\)', content))

    def _create_prompt(self, item, is_random_topic=False):
        include_emojis = self.post_preferences.get('include_emojis', True)
        include_hashtags = self.post_preferences.get('include_hashtags', True)
        max_hashtags = self.post_preferences.get('max_hashtags', 10)

        mention_avi = "Avi Chawla (https://www.linkedin.com/in/avi-chawla/)"
        mention_akshay = "Akshay Pachaar (https://www.linkedin.com/in/akshay-pachaar/)"
        mention_bhavishya = "Bhavishya Pandit (https://www.linkedin.com/in/bhavishyapandit/)"

        if is_random_topic:
            topic = item
            return f"""
            Create a detailed and insightful LinkedIn post about the following technical topic:

            TOPIC: {topic['title']}
            CATEGORY: {topic['category']}
            DESCRIPTION: {topic['content']}
            TECHNICAL LEVEL: {topic['technical_level']}

            Instructions:
            - Explain the core concepts clearly and concisely.
            - If the topic involves mathematics ({topic['has_equations']}), include relevant equations in LaTeX format.
            - If the topic involves architecture or process ({topic['has_architecture']}), describe it in detail for a diagram.
            - Add examples, analogies, comparisons.
            - End with a question or CTA.
            - Include {max_hashtags} hashtags.
            - On a new line at the very end, add an "Image: [description]" instruction.
            """

        if item['type'] == 'email':
            source = item.get('source', '').lower()
            content_sample = item['content'][:2500]
            title = item['title']

            if 'avi' in source and 'dailydoseofds' in source:
                return f"""
                Write a concise LinkedIn post from {mention_avi} and {mention_akshay}.

                TITLE: {title}
                CONTENT SNIPPET: {content_sample}

                Instructions:
                - Focus on 1-2 technical takeaways.
                - Use LaTeX for math if needed.
                - Describe diagrams.
                - Include emojis, {max_hashtags} hashtags.
                - Link {mention_avi} and {mention_akshay}.
                - End with: "Image: [description]"
                """

            elif 'wtf in tech' in source or 'bhavishya' in source:
                return f"""
                Draft a LinkedIn post based on {mention_bhavishya}'s newsletter.

                TITLE: {title}
                EXCERPT: {content_sample}

                Instructions:
                - Explain 1-2 concepts clearly.
                - Add a mini-lesson or equation.
                - Include emojis, {max_hashtags} hashtags.
                - End: "Credits to {mention_bhavishya} 👏"
                - "Image: [description]"
                """

            else:
                return f"""
                Write a LinkedIn post from this email.

                TITLE: {item['title']}
                BODY: {item['content'][:2000]}

                - Explain 1-2 technical ideas.
                - Add emojis and {max_hashtags} hashtags.
                - End with: "Image: [technical illustration]"
                """

        elif item['type'] == 'research':
            authors = ', '.join(item.get('authors', [])[:3])
            if len(item.get('authors', [])) > 3:
                authors += ' et al.'
            summary = item['content'][:2500]
            return f"""
            Create a technical LinkedIn post about this paper.

            TITLE: {item['title']}
            SUMMARY: {summary}
            AUTHORS: {authors}
            LINK: {item.get('link', '')}

            - Explain problem, solution, results.
            - Use LaTeX math.
            - Describe architecture for diagram.
            - Include emojis, {max_hashtags} hashtags.
            - "Image: [detailed diagram]"
            """

        return f"""
        Write a crisp LinkedIn post.

        TITLE: {item['title']}
        BODY: {item['content'][:1800]}

        - Hook, idea, insight.
        - Emojis and {max_hashtags} hashtags.
        - End: "Image: [technical illustration]"
        """

    def convert_latex_to_mathjax(self, text):
        text = re.sub(r'\$\$(.*?)\$\$', r'\\[\1\\]', text, flags=re.DOTALL)
        text = re.sub(r'\$(.*?)\$', r'\\(\1\\)', text, flags=re.DOTALL)
        return text
