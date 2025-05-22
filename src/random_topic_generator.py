#!/usr/bin/env python3
"""
Random Topic Generator Module for LinkedIn Post Generator
Generates diverse technical topics for AI, ML, Data Science, NLP, and MLOps posts.
"""

import os
import json
import logging
import random
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RandomTopicGenerator:
    """Class to generate random technical topics for LinkedIn posts."""
    
    def __init__(self, config_path=None):
        """
        Initialize the RandomTopicGenerator with configuration.
        
        Args:
            config_path (str, optional): Path to the configuration file.
                If None, uses default config path.
        """
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'config', 'sources.json'
        )
        self.config = self._load_config()
        
        # Define topic categories and specific topics
        self.topic_categories = {
            'ai': [
                {
                    'title': 'The Mathematics Behind Neural Networks',
                    'content': 'Exploring backpropagation, gradient descent, and activation functions in neural networks.',
                    'technical_level': 'high',
                    'has_equations': True,
                    'has_architecture': True
                },
                {
                    'title': 'Explainable AI: Making Black Box Models Transparent',
                    'content': 'Methods and techniques for interpreting complex AI models like LIME, SHAP, and attention visualization.',
                    'technical_level': 'medium',
                    'has_equations': False,
                    'has_architecture': True
                },
                {
                    'title': 'Reinforcement Learning: From Theory to Practice',
                    'content': 'Understanding Q-learning, policy gradients, and value functions in reinforcement learning.',
                    'technical_level': 'high',
                    'has_equations': True,
                    'has_architecture': True
                }
            ],
            'machine_learning': [
                {
                    'title': 'Decision Trees vs. Random Forests: A Mathematical Comparison',
                    'content': 'Analyzing the mathematical foundations of tree-based models and ensemble methods.',
                    'technical_level': 'high',
                    'has_equations': True,
                    'has_architecture': False
                },
                {
                    'title': 'Regularization Techniques in Machine Learning',
                    'content': 'Exploring L1, L2, Elastic Net, and Dropout regularization methods to prevent overfitting.',
                    'technical_level': 'high',
                    'has_equations': True,
                    'has_architecture': False
                },
                {
                    'title': 'Feature Engineering: The Art and Science',
                    'content': 'Techniques for creating, transforming, and selecting features to improve model performance.',
                    'technical_level': 'medium',
                    'has_equations': False,
                    'has_architecture': False
                }
            ],
            'data_science': [
                {
                    'title': 'Principal Component Analysis: A Visual Guide',
                    'content': 'Understanding dimensionality reduction through eigenvalues and eigenvectors.',
                    'technical_level': 'high',
                    'has_equations': True,
                    'has_architecture': False
                },
                {
                    'title': 'Bayesian Statistics for Data Scientists',
                    'content': 'Applying Bayes theorem and probabilistic thinking to data analysis problems.',
                    'technical_level': 'high',
                    'has_equations': True,
                    'has_architecture': False
                },
                {
                    'title': 'Time Series Forecasting: ARIMA vs. Prophet vs. LSTM',
                    'content': 'Comparing statistical and deep learning approaches to time series prediction.',
                    'technical_level': 'medium',
                    'has_equations': True,
                    'has_architecture': True
                }
            ],
            'nlp': [
                {
                    'title': 'Attention Mechanisms Explained: From Theory to Implementation',
                    'content': 'Deep dive into self-attention, multi-head attention, and their role in transformer architectures.',
                    'technical_level': 'high',
                    'has_equations': True,
                    'has_architecture': True
                },
                {
                    'title': 'Word Embeddings: Word2Vec, GloVe, and Beyond',
                    'content': 'Understanding vector representations of words and their semantic relationships.',
                    'technical_level': 'medium',
                    'has_equations': True,
                    'has_architecture': False
                },
                {
                    'title': 'The Mathematics of Language Models',
                    'content': 'Exploring the mathematical foundations of modern language models like transformers.',
                    'technical_level': 'high',
                    'has_equations': True,
                    'has_architecture': True
                }
            ],
            'mlops': [
                {
                    'title': 'Model Monitoring: Detecting Drift and Ensuring Reliability',
                    'content': 'Techniques for monitoring model performance and detecting data/concept drift in production.',
                    'technical_level': 'medium',
                    'has_equations': False,
                    'has_architecture': True
                },
                {
                    'title': 'CI/CD for Machine Learning: Best Practices',
                    'content': 'Implementing continuous integration and deployment pipelines for ML models.',
                    'technical_level': 'medium',
                    'has_equations': False,
                    'has_architecture': True
                },
                {
                    'title': 'A/B Testing for ML Models: Statistical Approaches',
                    'content': 'Statistical methods for properly evaluating model performance in production.',
                    'technical_level': 'high',
                    'has_equations': True,
                    'has_architecture': False
                }
            ]
        }
    
    def _load_config(self):
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def generate_topics(self, num_topics=1, categories=None):
        """
        Generate random technical topics for posts.
        
        Args:
            num_topics (int): Number of topics to generate
            categories (list): List of categories to choose from. If None, uses all categories.
            
        Returns:
            list: List of topic dictionaries
        """
        if not categories:
            categories = list(self.topic_categories.keys())
        
        # Validate categories
        valid_categories = [cat for cat in categories if cat in self.topic_categories]
        if not valid_categories:
            logger.warning(f"No valid categories found in {categories}. Using all categories.")
            valid_categories = list(self.topic_categories.keys())
        
        # Generate topics
        topics = []
        for _ in range(num_topics):
            # Select a random category
            category = random.choice(valid_categories)
            
            # Select a random topic from that category
            topic = random.choice(self.topic_categories[category])
            
            # Add category and timestamp
            topic_with_metadata = topic.copy()
            topic_with_metadata['category'] = category
            topic_with_metadata['generated_at'] = datetime.now().isoformat()
            
            topics.append(topic_with_metadata)
        
        return topics

if __name__ == "__main__":
    # Example usage
    generator = RandomTopicGenerator()
    topics = generator.generate_topics(num_topics=3)
    
    for i, topic in enumerate(topics):
        print(f"Topic {i+1}: {topic['title']}")
        print(f"Category: {topic['category']}")
        print(f"Technical Level: {topic['technical_level']}")
        print(f"Has Equations: {topic['has_equations']}")
        print(f"Has Architecture: {topic['has_architecture']}")
        print(f"Content: {topic['content']}")
        print()
