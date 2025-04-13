#!/usr/bin/env python3
"""
Telegram Delivery Module for LinkedIn Post Generator

This module handles delivering generated LinkedIn posts to a Telegram bot.
"""

import json
import os
import logging
import requests
from datetime import datetime

# Configure logging
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
        Deliver LinkedIn posts to Telegram.
        
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
        
        self._send_telegram_message(header)
        
        # Send each post
        for i, post in enumerate(posts):
            try:
                message = f"*Draft #{i+1}*\n"
                message += f"Source: {post['source_type']} - {post['source_title']}\n\n"
                message += "```\n"  # Code block for easy copying
                message += post['content']
                message += "\n```\n\n"
                
                if post['source_link']:
                    message += f"Original source: {post['source_link']}"
                
                success = self._send_telegram_message(message)
                if success:
                    success_count += 1
                    
            except Exception as e:
                logger.error(f"Error delivering post {i+1}: {e}")
                
        # Send summary
        if success_count > 0:
            summary = f"✅ Successfully delivered {success_count} of {len(posts)} LinkedIn post drafts."
            self._send_telegram_message(summary)
            
        return success_count > 0
        
    def _send_telegram_message(self, message):
        """
        Send a message to Telegram.
        
        Args:
            message (str): Message to send
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
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
        
        return self._send_telegram_message(test_message)

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
