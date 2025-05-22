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
    format=\'%(asctime)s - %(name)s - %(levelname)s - %(message)s\'
)
logger = logging.getLogger(__name__)

class PostGenerator:
    def __init__(self, config_path=None):
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            \'config\', \'sources.json\'
        )
        self.config = self._load_config()
        self.post_preferences = self.config.get(\'post_preferences\', {})

        self.api_key = os.environ.get(\'GROQ_API_KEY\')
        self.api_endpoint = os.environ.get(\'GROQ_ENDPOINT\', \'https://api.groq.com/openai/v1/chat/completions\')
        if not self.api_key:
            logger.warning("GROQ_API_KEY environment variable not set")
            
        # Initialize image generator
        from src.image_generator import ImageGenerator
        self.image_generator = ImageGenerator(config_path)

    def _load_config(self):
        try:
            with open(self.config_path, \'r\') as f:
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
                    post[\'content\'], 
                    item[\'title\'],
                    self._determine_category(item),
                    item.get(\'has_equations\', False),
                    item.get(\'has_architecture\', False)
                )
                
                # Update post with cleaned content and image path
                post[\'content\'] = cleaned_content
                if image_path:
                    post[\'image_path\'] = image_path
                
                posts.append(post)
            if len(posts) >= max_posts:
                break
        logger.info(f"Generated {len(posts)} LinkedIn posts from email/research")
        return posts

    def generate_random_posts(self, topics):
        """Generate posts based on randomly generated technical topics."""
        posts = []
        for topic in topics:
            post = self._generate_post(topic, is_random_topic=True)
            if post:
                # Generate image for the post and clean content
                image_path, cleaned_content = self.image_generator.generate_image_for_post(
                    post[\'content\'], 
                    topic[\'title\'],
                    topic.get(\'category\', \'technology\'),
                    topic.get(\'has_equations\', False),
                    topic.get(\'has_architecture\', False)
                )
                
                # Update post with cleaned content and image path
                post[\'content\'] = cleaned_content
                if image_path:
                    post[\'image_path\'] = image_path
                
                posts.append(post)
        logger.info(f"Generated {len(posts)} LinkedIn posts from random topics")
        return posts

    def _determine_category(self, item):
        """Determine the category for image generation based on content"""
        title = item.get(\'title\', \'\').lower()
        content = item.get(\'content\', \'\').lower()
        
        if any(term in title or term in content for term in [\'nlp\', \'language model\', \'transformer\']):
            return \'nlp\'
        elif any(term in title or term in content for term in [\'mlops\', \'deployment\', \'monitoring\']):
            return \'mlops\'
        elif any(term in title or term in content for term in [\'machine learning\', \'ml\', \'neural network\', \'deep learning\']):
            return \'machine_learning\'
        elif any(term in title or term in content for term in [\'ai\', \'artificial intelligence\']):
            return \'ai\'
        elif any(term in title or term in content for term in [\'data science\', \'data analysis\', \'statistics\']):
            return \'data_science\'
        elif any(term in title or term in content for term in [\'business\', \'strategy\', \'management\']):
            return \'business\'
        else:
            return \'technology\'

    def _prepare_content(self, email_data, research_data, emails_only=False):
        content_items = []
        for email in email_data:
            content_items.append({
                \'type\': \'email\',
                \'title\': email.get(\'subject\', \'\'),
                \'content\': email.get(\'body\', \'\'),
                \'source\': email.get(\'from\', \'\'),
                \'date\': email.get(\'date\', \'\')
            })
        if not emails_only:
            for source, items in research_data.items():
                for item in items:
                    content_items.append({
                        \'type\': \'research\',
                        \'title\': item.get(\'title\', \'\'),
                        \'content\': item.get(\'summary\', \'\'),
                        \'authors\': item.get(\'authors\', []),
                        \'link\': item.get(\'link\', \'\'),
                        \'source\': source,
                        \'date\': item.get(\'published\', \'\'),
                        \'has_equations\': True, # Assume research might have equations
                        \'has_architecture\': True # Assume research might have architecture
                    })
        return content_items

    def _generate_post(self, content_item, is_random_topic=False):
        if not self.api_key:
            logger.error("Cannot generate post: GROQ_API_KEY not set")
            return None

        prompt = self._create_prompt(content_item, is_random_topic)

        try:
            headers = {
                \'Authorization\': f\'Bearer {self.api_key}\',
                \'Content-Type\': \'application/json\'
            }

            data = {
                \'model\': \'llama3-70b-8192\',
                \'messages\': [
                    {
                        \'role\': \'system\',
                        \'content
ées
                    },
                    {
                        \'role\': \'user\',
                        \'content\': prompt
                    }
                ],
                \'temperature\': 0.7,
                \'max_tokens\': 1500 # Increased token limit for more detail
            }

            response = requests.post(self.api_endpoint, headers=headers, json=data, timeout=180)
            if response.status_code == 200:
                result = response.json()
                post_content = result[\'choices\'][0][\'message\'][\'content\']
                
                # Basic check for successful generation (not just an error message)
                if len(post_content) < 100 or "error" in post_content.lower():
                    logger.warning(f"Generated post seems too short or contains error: {post_content[:100]}...")
                    # Optionally, retry or return None
                    return None
                    
                return {
                    \'content\': post_content,
                    \'source_type\': content_item.get(\'type\', \'random_topic\'),
                    \'source_title\': content_item[\'title\'],
                    \'source_link\': content_item.get(\'link\', \'\'),
                    \'generated_at\': datetime.now().isoformat()
                }
            else:
                logger.error(f"Groq API error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error generating post: {e}")
            return None

    def _contains_image_references(self, content):
        return bool(re.search(r\'<img|!\[.*?\]\(.*?\)\', content))

    def _create_prompt(self, item, is_random_topic=False):
        include_emojis = self.post_preferences.get(\'include_emojis\', True)
        include_hashtags = self.post_preferences.get(\'include_hashtags\', True)
        max_hashtags = self.post_preferences.get(\'max_hashtags\', 10)

        mention_avi = "Avi Chawla (https://www.linkedin.com/in/avi-chawla/)"
        mention_akshay = "Akshay Pachaar (https://www.linkedin.com/in/akshay-pachaar/)"
        mention_bhavishya = "Bhavishya Pandit (https://www.linkedin.com/in/bhavishyapandit/)"

        system_prompt = (
            "You are a LinkedIn content strategist specializing in AI, Machine Learning, Data Science, NLP, and MLOps. "
            "You create highly engaging, technically accurate, and insightful posts for a knowledgeable audience. "
            "Your posts often include mathematical equations (using LaTeX format like $...$ or $$...$$), flowcharts, architecture diagrams, and comparisons with other techniques. "
            "You explain *how* things work, not just summarize. Use emojis and relevant hashtags. Avoid generic intros and markdown styling (*, **)."
        )

        if is_random_topic:
            topic = item
            prompt = f"""
            Create a detailed and insightful LinkedIn post about the following technical topic:

            TOPIC: {topic[\'title\']}
            CATEGORY: {topic[\'category\']}
            DESCRIPTION: {topic[\'content\']}
            TECHNICAL LEVEL: {topic[\'technical_level\']}

            Instructions:
            - Explain the core concepts clearly and concisely.
            - If the topic involves mathematics ({topic[\'has_equations\']}), include relevant equations in LaTeX format (e.g., $E=mc^2$, $$L = \sum (y_i - \hat{y}_i)^2$$).
            - If the topic involves architecture or process ({topic[\'has_architecture\']}), describe it in detail, suitable for generating a diagram or flowchart.
            - Provide practical examples, analogies, or comparisons to make it relatable.
            - Discuss the significance, applications, or challenges related to the topic.
            - Ensure technical accuracy and depth suitable for the specified level.
            - Include {max_hashtags} relevant hashtags.
            - End with an engaging question or call to action.
            - Keep the post under 3000 characters.
            - On a new line at the very end, add an "Image: [Detailed description for image/diagram generation based on the content, e.g., \'Flowchart of the Q-learning algorithm\', \'Architecture diagram of a Transformer model showing self-attention\']" instruction.
            """
            return prompt

        elif item[\'type\'] == \'email\':
            source = item.get(\'source\', \'\').lower()
            content_sample = item[\'content\'][:2500] # Slightly increased sample size
            title = item[\'title\']
            has_images = self._contains_image_references(item[\'content\'])

            if \'avi\' in source and \'dailydoseofds\' in source:
                return f"""
                Write a concise but technically insightful LinkedIn post based on this newsletter excerpt from {mention_avi} and {mention_akshay}.

                TITLE: {title}
                CONTENT SNIPPET: {content_sample}

                Instructions:
                - Focus on 1-2 key technical takeaways. Explain the \'how\' and \'why\'.
                - If equations or algorithms are mentioned, include them in LaTeX format.
                - If diagrams are present, describe them for image generation.
                - Add practical implications or compare with other methods.
                - Include emojis, {max_hashtags} hashtags, and link to {mention_avi} and {mention_akshay}.
                - Max 3000 characters, avoid markdown (*, **).
                - On a new line at the very end, add an "Image: [Description based on content/diagrams]" instruction.
                """

            elif \'wtf in tech\' in source or \'bhavishya\' in source:
                return f"""
                Draft an educational and snappy post based on this newsletter by {mention_bhavishya}.

                TITLE: {title}
                EXCERPT: {content_sample}

                Instructions:
                - Pick 1-2 key questions/solutions. Explain the underlying technical concepts.
                - Include a mini-lesson or definition for one key term or method, potentially with a simple equation (LaTeX).
                - If images/diagrams exist, describe them for image generation.
                - Add emojis and {max_hashtags} hashtags.
                - End with: "Credits to {mention_bhavishya} for curating this 👏"
                - Avoid markdown styling, make it LinkedIn-ready.
                - On a new line at the very end, add an "Image: [Description based on content/diagrams]" instruction.
                """
            else: # Generic email
                 return f"""
                Write a crisp LinkedIn post based on this email content:

                TITLE: {item[\'title\']}
                BODY: {item[\'content\'][:2000]}

                Instructions:
                - Extract 1-2 interesting technical points.
                - Explain the concepts clearly.
                - Add {max_hashtags} relevant hashtags and emojis.
                - End with an invite for feedback or discussion.
                - No markdown (*, **).
                - On a new line at the very end, add an "Image: [General relevant technical illustration]" instruction.
                """

        elif item[\'type\'] == \'research\':
            authors = \', \'.join(item.get(\'authors\', [])[:3]) + (\' et al.\' if len(item.get(\'authors\', [])) > 3 else \'\')
            summary = item[\'content\'][:2500]
            prompt = f"""
            Create a highly engaging and technically detailed LinkedIn post summarizing this research paper for an AI/ML audience.

            TITLE: {item[\'title\']}
            SUMMARY: {summary}
            AUTHORS: {authors}
            LINK: {item.get(\'link\', \'\')}

            Instructions:
            - Explain the core problem, the proposed solution, and key results.
            - Focus on the technical novelty: What specific algorithms, architectures, or mathematical concepts are introduced or improved?
            - Include relevant mathematical equations in LaTeX format (e.g., loss functions, update rules).
            - Describe the model architecture or experimental setup in detail, suitable for generating a diagram/flowchart.
            - Compare the approach to existing methods if possible.
            - Discuss the significance and potential impact of the research.
            - Define key terms clearly (e.g., VolovNet, LoRA, retrieval augmentation).
            - Link to the paper and tag authors if possible.
            - End with a thought-provoking question or future outlook.
            - Keep <3000 characters, avoid markdown.
            - Include emojis & {max_hashtags} relevant hashtags.
            - On a new line at the very end, add an "Image: [Detailed description of the model architecture, key equation visualization, or experimental setup flowchart]" instruction.
            """
            return prompt

        else: # Fallback for unknown types
            return f"""
            Write a crisp LinkedIn post:

            TITLE: {item[\'title\']}
            BODY: {item[\'content\'][:1800]}

            - Open with a hook (question, story, emoji).
            - Break down 1-2 main ideas.
            - Add {max_hashtags} relevant hashtags.
            - End with an invite for feedback or discussion.
            - No markdown (*, **).
            - On a new line at the very end, add an "Image: [General relevant technical illustration]" instruction.
            """

    def convert_latex_to_mathjax(self, text):
        # Basic conversion, might need refinement
        text = re.sub(r\'\$\$(.*?)\$\$\', r\'\\[\1\\]\', text, flags=re.DOTALL)
        text = re.sub(r\'\$(.*?)\$\', r\'\\(\1\\)\', text, flags=re.DOTALL)
        return text
