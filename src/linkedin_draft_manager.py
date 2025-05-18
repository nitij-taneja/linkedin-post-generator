#!/usr/bin/env python3
"""
LinkedIn Draft Manager for Post Generator
This module handles generating drafts for LinkedIn and managing their posting status.
"""

import json
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LinkedInDraftManager:
    """Class for generating and managing LinkedIn post drafts."""

    def __init__(self, config_path=None):
        """
        Initialize the LinkedInDraftManager with configuration.
        
        Args:
            config_path (str, optional): Path to the configuration file.
                If None, uses default config path.
        """
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'config',
            'communities.json'
        )
        self.config = self._load_config()

    def _load_config(self):
        """Load community and draft configurations from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load LinkedIn community config: {e}")
            return {}

    def format_draft_for_linkedin(self, post):
        """
        Prepare a draft for LinkedIn's editor.
        Args:
            post (dict): Post data containing content and other details
        Returns:
            str: Formatted post content for LinkedIn
        """
        formatted_post = f"**{post['source_title']}**\n\n"
        formatted_post += f"Source: {post['source_type']} - {post['source_title']}\n"
        formatted_post += f"Link: {post.get('source_link', '')}\n\n"
        formatted_post += post['content']
        # Mention the author directly in the post
        formatted_post += f"\n\nTagging: {self.format_mentions()}"
        return formatted_post

    def format_mentions(self):
        """Formats author mentions as inline hyperlinks."""
        mention_avi = "[Avi Chawla](https://www.linkedin.com/in/avi-chawla/)"
        mention_akshay = "[Akshay Pachaar](https://www.linkedin.com/in/akshay-pachaar/)"
        mention_bhavishya = "[Bhavishya Pandit](https://www.linkedin.com/in/bhavishyapandit/)"
        return f"{mention_avi}, {mention_akshay}, {mention_bhavishya}"

    def create_draft(self, post, community=None):
        """
        Create a LinkedIn draft.
        Optionally assign it to a specific community for approval.
        Args:
            post (dict): Post content and metadata
            community (str, optional): Community ID to assign the post
        """
        draft_content = self.format_draft_for_linkedin(post)
        draft = {
            'content': draft_content,
            'community': community if community else "None"
        }
        # Here we would send the draft to LinkedIn or browser extension
        # For now, we save the draft as a local file
        draft_filename = f"draft_{post['generated_at']}.txt"
        draft_path = os.path.join('drafts', draft_filename)
        
        os.makedirs('drafts', exist_ok=True)
        
        with open(draft_path, 'w') as draft_file:
            draft_file.write(draft_content)

        logger.info(f"Draft saved at {draft_path}")
        return draft

    def post_to_community(self, post, community):
        """
        Post a draft to a LinkedIn community (mock).
        Args:
            post (dict): Post content and metadata
            community (str): Community ID to send the post to
        """
        # Assuming approval and post are successful
        logger.info(f"Post successfully sent to community {community}")
        return True
