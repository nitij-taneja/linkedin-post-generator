#!/usr/bin/env python3
"""
Medium Publisher Module for LinkedIn Post Generator
Publishes LinkedIn posts to Medium as drafts.
"""

import requests
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MediumPublisher:
    def __init__(self):
        self.token = os.environ.get('MEDIUM_INTEGRATION_TOKEN')
        if not self.token:
            raise ValueError("Missing MEDIUM_INTEGRATION_TOKEN")
        self.base_url = "https://api.medium.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.user_id = self._get_user_id()

    def _get_user_id(self):
        response = requests.get(f"{self.base_url}/me", headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch user ID: {response.text}")
        return response.json()['data']['id']

    def publish_post(self, title, content, tags=None, publish_status="draft"):
        payload = {
            "title": title,
            "contentFormat": "html",
            "content": f"<p>{content.replace('\n', '<br>')}</p>",
            "tags": tags or ["AI", "Machine Learning"],
            "publishStatus": publish_status
        }

        url = f"{self.base_url}/users/{self.user_id}/posts"
        response = requests.post(url, json=payload, headers=self.headers)
        if response.status_code == 201:
            logger.info(f"Medium post published: {response.json()['data']['url']}")
        else:
            logger.error(f"Failed to publish to Medium: {response.text}")
