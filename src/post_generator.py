#!/usr/bin/env python3
"""
Post Generator Module for LinkedIn Post Generator
Enhanced with advanced prompting, diversity in tone, LLM-augmented context, hyperlink support,
and free image generation capabilities.
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

        self.api_key = os.environ.get('GROQ_API_KEY')
        self.api_endpoint = os.environ.get('GROQ_ENDPOINT', 'https://api.groq.com/openai/v1/chat/completions')
        if not self.api_key:
            logger.warning("GROQ_API_KEY environment variable not set")
            
        # Initialize image generator
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
                # Generate image for the post and clean content
                image_path, cleaned_content = self.image_generator.generate_image_for_post(
                    post['content'], 
                    item['title'],
                    self._determine_category(item)
                )
                
                # Update post with cleaned content and image path
                post['content'] = cleaned_content
                if image_path:
                    post['image_path'] = image_path
                
                posts.append(post)
            if len(posts) >= max_posts:
                break
        logger.info(f"Generated {len(posts)} LinkedIn posts")
        return posts

    def _determine_category(self, item):
        """Determine the category for image generation based on content"""
        title = item.get('title', '').lower()
        content = item.get('content', '').lower()
        
        if any(term in title or term in content for term in ['machine learning', 'ml', 'neural network', 'deep learning']):
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
                            "You are a LinkedIn content strategist. You create engaging, educational, and fresh posts with technical precision and human relatability."
                        )
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'temperature': 0.75,
                'max_tokens': 1300
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

    def _contains_image_references(self, content):
        return bool(re.search(r'<img|!\[.*?\]\(.*?\)', content))

    def _create_prompt(self, item):
        include_emojis = self.post_preferences.get('include_emojis', True)
        include_hashtags = self.post_preferences.get('include_hashtags', True)
        max_hashtags = self.post_preferences.get('max_hashtags', 10)

        mention_avi = "Avi Chawla (https://www.linkedin.com/in/avi-chawla/)"
        mention_akshay = "Akshay Pachaar (https://www.linkedin.com/in/akshay-pachaar/)"
        mention_bhavishya = "Bhavishya Pandit (https://www.linkedin.com/in/bhavishyapandit/)"

        if item['type'] == 'email':
            source = item.get('source', '').lower()
            content_sample = item['content'][:2000]
            title = item['title']
            has_images = self._contains_image_references(item['content'])

            if 'avi' in source and 'dailydoseofds' in source:
                return f"""
You're writing a concise but thoughtful LinkedIn post based on a technical newsletter.

TITLE: {title}
CONTENT SNIPPET: {content_sample}

Instructions:
- Avoid repeating generic intros, vary tone across posts
- Pull 2–3 technical insights and expand with analogies or implications
- Highlight practical applications or pain points it addresses
- {'Describe any diagram or image insight in text.' if has_images else ''}
- Add emojis, hashtags, and link to {mention_avi} and {mention_akshay} using inline mentions
- Max 3000 characters, avoid markdown (*, **)
- At the end of your post, on a new line, add "Image: [brief description for image generation]" - this will be removed from the final post"""

            elif 'wtf in tech' in source or 'bhavishya' in source:
                return f"""
Draft an educational and snappy post based on this newsletter by {mention_bhavishya}.

TITLE: {title}
EXCERPT: {content_sample}

Instructions:
- Vary your opening lines: story, question, or bold claim
- Pick 2–3 questions/solutions and explain their real-world relevance
- Include a mini-lesson or definition for one key term or method
- {'Summarize any attached image or diagram as text if found.' if has_images else ''}
- Add emojis and 5+ hashtags
- End with: "Credits to {mention_bhavishya} for curating this 👏"
- Avoid markdown styling, make it LinkedIn-ready
- At the end of your post, on a new line, add "Image: [brief description for image generation]" - this will be removed from the final post"""

        elif item['type'] == 'research':
            authors = ', '.join(item.get('authors', [])[:3]) + (' et al.' if len(item.get('authors', [])) > 3 else '')
            summary = item['content'][:2000]
            prompt = f"""
Summarize this research post for LinkedIn in a way that's engaging to an AI-curious audience.

TITLE: {item['title']}
SUMMARY: {summary}
AUTHORS: {authors}
LINK: {item.get('link', '')}

Instructions:
- Explain what this research does and why it matters
- Extract mathematical or algorithmic insight, if any (e.g. equations, attention weights)
- Describe intuition or pseudocode if space allows
- Define key terms (e.g. VolovNet, LoRA, retrieval augmentation)
- Include diagrams or flow explanation if relevant (describe it textually)
- Link to the paper and tag the authors (if known)
- End with a question or next-step insight
- Keep <3000 characters, avoid markdown
- Emojis & hashtags welcomed
- At the end of your post, on a new line, add "Image: A diagram showing the architecture of the proposed model" - this will be removed from the final post"""

            if len(item['content']) < 500:
                prompt += "\nNote: The summary is short. Enrich it by expanding on known methods, use-cases, or simplified pseudocode."

            return prompt

        else:
            return f"""
Write a crisp LinkedIn post:

TITLE: {item['title']}
BODY: {item['content'][:1800]}

- Open with a hook (question, story, emoji)
- Break down 2–3 main ideas
- Add 15 relevant hashtags
- End with an invite for feedback or discussion
- No markdown (*, **)
- At the end of your post, on a new line, add "Image: [brief description for image generation]" - this will be removed from the final post"""

    def convert_latex_to_mathjax(self, text):
        text = re.sub(r'\$\$(.*?)\$\$', r'\\[\1\\]', text, flags=re.DOTALL)
        text = re.sub(r'\$(.*?)\$', r'\\(\1\\)', text, flags=re.DOTALL)
        return text
