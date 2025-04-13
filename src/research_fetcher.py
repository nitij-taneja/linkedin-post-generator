#!/usr/bin/env python3
"""
Research API Module for LinkedIn Post Generator

This module handles fetching trending research and news from various free APIs
like arXiv, HuggingFace, and PapersWithCode.
"""

import json
import os
import logging
import requests
from datetime import datetime, timedelta
import feedparser
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ResearchFetcher:
    """Class to fetch trending research from various APIs."""
    
    def __init__(self, config_path=None):
        """
        Initialize the ResearchFetcher with configuration.
        
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
        self.research_config = self.config.get('research_apis', {})
        
    def _load_config(self):
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def fetch_all_research(self):
        """
        Fetch research from all configured APIs.
        
        Returns:
            dict: Dictionary containing research data from all sources
        """
        research_data = {}
        
        # Fetch from arXiv if enabled
        if self.research_config.get('arxiv', {}).get('enabled', True):
            research_data['arxiv'] = self.fetch_arxiv()
            
        # Fetch from HuggingFace if enabled
        if self.research_config.get('huggingface', {}).get('enabled', True):
            research_data['huggingface'] = self.fetch_huggingface()
            
        # Fetch from PapersWithCode if enabled
        if self.research_config.get('papers_with_code', {}).get('enabled', True):
            research_data['papers_with_code'] = self.fetch_papers_with_code()
            
        return research_data
    
    def fetch_arxiv(self):
        """
        Fetch trending papers from arXiv.
        
        Returns:
            list: List of dictionaries containing paper data
        """
        arxiv_config = self.research_config.get('arxiv', {})
        categories = arxiv_config.get('categories', ['cs.AI', 'cs.CL', 'cs.LG'])
        max_results = arxiv_config.get('max_results', 10)
        sort_by = arxiv_config.get('sort_by', 'submittedDate')
        sort_order = arxiv_config.get('sort_order', 'descending')
        
        # Construct the query
        category_query = ' OR '.join([f'cat:{cat}' for cat in categories])
        query = f'({category_query}) AND submittedDate:[{self._get_date_range()}]'
        
        # Construct the API URL
        base_url = 'http://export.arxiv.org/api/query'
        params = {
            'search_query': query,
            'max_results': max_results,
            'sortBy': sort_by,
            'sortOrder': sort_order
        }
        
        try:
            # Use feedparser to parse the arXiv RSS feed
            response = requests.get(base_url, params=params)
            feed = feedparser.parse(response.text)
            
            papers = []
            for entry in feed.entries:
                paper = {
                    'title': entry.title,
                    'authors': [author.name for author in entry.authors],
                    'summary': entry.summary,
                    'link': entry.link,
                    'published': entry.published,
                    'categories': [tag.term for tag in entry.tags],
                    'source': 'arXiv'
                }
                papers.append(paper)
                
            logger.info(f"Successfully fetched {len(papers)} papers from arXiv")
            return papers
        except Exception as e:
            logger.error(f"Error fetching from arXiv: {e}")
            return []
    
    def fetch_huggingface(self):
        """
        Fetch trending models and datasets from HuggingFace.
        
        Returns:
            list: List of dictionaries containing model/dataset data
        """
        hf_config = self.research_config.get('huggingface', {})
        topics = hf_config.get('topics', ['nlp', 'computer-vision'])
        max_results = hf_config.get('max_results', 10)
        
        models = []
        
        try:
            # HuggingFace API doesn't have a formal trending endpoint,
            # so we'll use their models endpoint with filters
            base_url = 'https://huggingface.co/api/models'
            
            for topic in topics:
                params = {
                    'filter': topic,
                    'sort': 'downloads',
                    'direction': -1,
                    'limit': max_results // len(topics)
                }
                
                response = requests.get(base_url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    for model in data:
                        model_data = {
                            'title': model.get('modelId'),
                            'authors': [model.get('author')] if model.get('author') else [],
                            'summary': model.get('description', ''),
                            'link': f"https://huggingface.co/{model.get('modelId')}",
                            'downloads': model.get('downloads', 0),
                            'likes': model.get('likes', 0),
                            'tags': model.get('tags', []),
                            'source': 'HuggingFace'
                        }
                        models.append(model_data)
                else:
                    logger.warning(f"Failed to fetch HuggingFace models for topic {topic}: {response.status_code}")
                
                # Avoid rate limiting
                time.sleep(1)
                
            logger.info(f"Successfully fetched {len(models)} models from HuggingFace")
            return models
        except Exception as e:
            logger.error(f"Error fetching from HuggingFace: {e}")
            return []
    
    def fetch_papers_with_code(self):
        """
        Fetch trending papers from PapersWithCode.
        
        Returns:
            list: List of dictionaries containing paper data
        """
        pwc_config = self.research_config.get('papers_with_code', {})
        topics = pwc_config.get('topics', ['RAG', 'generative-ai'])
        max_results = pwc_config.get('max_results', 10)
        
        papers = []
        
        try:
            # PapersWithCode API
            base_url = 'https://paperswithcode.com/api/v1/papers/'
            params = {
                'ordering': '-date',
                'limit': max_results
            }
            
            response = requests.get(base_url, params=params)
            if response.status_code == 200:
                data = response.json()
                for paper in data.get('results', []):
                    # Check if paper matches any of our topics
                    paper_topics = [task.get('name', '').lower() for task in paper.get('tasks', [])]
                    if not any(topic.lower() in ' '.join(paper_topics) for topic in topics):
                        continue
                        
                    paper_data = {
                        'title': paper.get('title'),
                        'authors': [author.get('name') for author in paper.get('authors', [])],
                        'summary': paper.get('abstract', ''),
                        'link': paper.get('url'),
                        'published': paper.get('published'),
                        'topics': paper_topics,
                        'repository': paper.get('repository'),
                        'source': 'PapersWithCode'
                    }
                    papers.append(paper_data)
                    
                    # Stop once we have enough papers
                    if len(papers) >= max_results:
                        break
            else:
                logger.warning(f"Failed to fetch PapersWithCode papers: {response.status_code}")
                
            logger.info(f"Successfully fetched {len(papers)} papers from PapersWithCode")
            return papers
        except Exception as e:
            logger.error(f"Error fetching from PapersWithCode: {e}")
            return []
    
    def _get_date_range(self):
        """Get date range for arXiv query (last 7 days)."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        return f"{start_date.strftime('%Y%m%d')}* TO {end_date.strftime('%Y%m%d')}*"

if __name__ == "__main__":
    # Example usage
    fetcher = ResearchFetcher()
    research = fetcher.fetch_all_research()
    
    print("Research Summary:")
    for source, items in research.items():
        print(f"\n{source.upper()} ({len(items)} items):")
        for i, item in enumerate(items[:3]):  # Show first 3 items from each source
            print(f"  {i+1}. {item['title']}")
            print(f"     Authors: {', '.join(item['authors'][:3])}")
            print(f"     Link: {item['link']}")
