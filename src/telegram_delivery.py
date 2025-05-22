#!/usr/bin/env python3
"""
Telegram Delivery Module for LinkedIn Post Generator
Handles sending posts and images to Telegram channels.
"""

import os
import json
import logging
import requests
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TelegramDelivery:
    """Class to deliver LinkedIn posts via Telegram."""
    
    def __init__(self, config_path=None):
        """
        Initialize the TelegramDelivery with configuration.
        
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
        
        # Telegram API configuration
        self.bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        
        if not self.bot_token or not self.chat_id:
            logger.warning("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID environment variables not set")

    def _load_config(self):
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}

    def deliver_posts(self, posts):
        """
        Deliver LinkedIn posts to Telegram with images.
        
        Args:
            posts (list): List of dictionaries containing post data
            
        Returns:
            bool: True if delivery was successful, False otherwise
        """
        if not self.bot_token or not self.chat_id:
            logger.error("Cannot deliver posts: Telegram credentials not set")
            return False
            
        success_count = 0
        
        # Send a header message
        header = f"📊 *LinkedIn Post Drafts* - {datetime.now().strftime('%Y-%m-%d')} 📊\n\n"
        header += f"Generated {len(posts)} new LinkedIn post drafts for you to review and post.\n"
        header += "Copy and paste these directly to LinkedIn when ready to post."
        
        self._send_message(header)
        
        # Send each post
        for i, post in enumerate(posts):
            try:
                # Clean up post content - remove image prompt if present
                content = self._clean_post_content(post['content'])
                
                # Format message
                message = f"*Draft #{i+1}*\n"
                message += f"Source: {post['source_type']} - {post['source_title']}\n\n"
                message += "```\n"  # Code block for easy copying
                message += content
                message += "\n```\n\n"
                
                if post.get('source_link'):
                    message += f"Original source: {post['source_link']}"
                
                # Check if post has an image
                image_path = post.get('image_path')
                
                if image_path and os.path.exists(image_path):
                    # Send image with caption (shortened version of message due to caption limits)
                    caption = f"*Draft #{i+1}*\n"
                    caption += f"Source: {post['source_type']} - {post['source_title']}"
                    success = self._send_photo_with_caption(image_path, caption[:1024])  # Telegram caption limit
                    
                    # Also send the full message with code block for easy copying
                    self._send_message(message)
                else:
                    # Send text only
                    success = self._send_message(message)
                
                if success:
                    success_count += 1
                    logger.info(f"Delivered post {i+1} to Telegram")
            except Exception as e:
                logger.error(f"Error delivering post {i+1}: {e}")
        
        # Send summary
        if success_count > 0:
            summary = f"✅ Successfully delivered {success_count} of {len(posts)} LinkedIn post drafts."
            self._send_message(summary)
            
        return success_count > 0

    def _clean_post_content(self, content):
        """
        Remove image prompts from post content.
        
        Args:
            content (str): Original post content
            
        Returns:
            str: Cleaned post content
        """
        # Remove lines containing "Image:" or "image prompt"
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            if not any(phrase in line.lower() for phrase in ["image:", "image prompt", "(note:"]):
                cleaned_lines.append(line)
                
        return '\n'.join(cleaned_lines)

    def _send_message(self, text):
        """
        Send a text message to Telegram.
        
        Args:
            text (str): Message to send
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, data=data)
            
            if response.status_code == 200:
                logger.info("Message sent successfully to Telegram")
                return True
            else:
                logger.error(f"Failed to send message to Telegram: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending message to Telegram: {e}")
            return False

    def _send_photo_with_caption(self, photo_path, caption):
        """
        Send photo with caption to Telegram.
        
        Args:
            photo_path (str): Path to the photo file
            caption (str): Caption for the photo
            
        Returns:
            bool: True if photo was sent successfully, False otherwise
        """
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"
            
            with open(photo_path, 'rb') as photo:
                files = {'photo': photo}
                data = {
                    'chat_id': self.chat_id,
                    'caption': caption,
                    'parse_mode': 'Markdown'
                }
                
                response = requests.post(url, data=data, files=files)
                
            if response.status_code == 200:
                logger.info("Photo sent successfully to Telegram")
                return True
            else:
                logger.error(f"Failed to send photo to Telegram: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending photo to Telegram: {e}")
            return False
            
    def test_connection(self):
        """
        Test the Telegram connection by sending a test message.
        
        Returns:
            bool: True if test was successful, False otherwise
        """
        if not self.bot_token or not self.chat_id:
            logger.error("Cannot test connection: Telegram credentials not set")
            return False
            
        test_message = "🔄 *LinkedIn Post Generator* - Connection Test\n\n"
        test_message += "This is a test message to verify that the LinkedIn Post Generator can successfully deliver posts to Telegram."
        
        return self._send_message(test_message)

if __name__ == "__main__":
    # Example usage
    import sys
    
    # Check if credentials are set
    if not os.environ.get('TELEGRAM_BOT_TOKEN') or not os.environ.get('TELEGRAM_CHAT_ID'):
        print("Please set the TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
        sys.exit(1)
        
    # Test Telegram delivery
    delivery = TelegramDelivery()
    success = delivery.test_connection()
    
    if success:
        print("✅ Telegram connection test successful!")
    else:
        print("❌ Telegram connection test failed. Check your credentials and try again.")
