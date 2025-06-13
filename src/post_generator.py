#!/usr/bin/env python3
"""
Post Generator Module for LinkedIn Post Generator
Creates technically rich, domain-specific LinkedIn posts with equations and diagrams.
"""

import os
import json
import logging
import random
import re
from datetime import datetime
import requests
from typing import Dict, List, Tuple, Optional, Any

# Import local modules
# These will be imported from the same directory in the actual implementation
# from .image_generator import ImageGenerator
# from .equation_generator import EquationGenerator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PostGenerator:
    """Class to generate LinkedIn posts with technical depth and domain specificity."""
    
    def __init__(self, config_path=None, api_key=None, api_endpoint=None):
        """
        Initialize the PostGenerator with configuration.
        
        Args:
            config_path (str, optional): Path to the configuration file.
                If None, uses default config path.
            api_key (str, optional): API key for LLM service.
                If None, uses environment variable.
            api_endpoint (str, optional): API endpoint for LLM service.
                If None, uses environment variable.
        """
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'config',
            'sources.json'
        )
        self.config = self._load_config()
        
        self.api_key = api_key or os.environ.get('GROQ_API_KEY')
        self.api_endpoint = api_endpoint or os.environ.get('GROQ_ENDPOINT', 'https://api.groq.com/openai/v1/chat/completions')
        
        if not self.api_key:
            logger.warning("API key not provided. Post generation may fail.")
        
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.posts_dir = os.path.join(self.base_dir, 'posts')
        self.images_dir = os.path.join(self.base_dir, 'images')
        self.analytics_dir = os.path.join(self.base_dir, 'analytics')
        
        os.makedirs(self.posts_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.analytics_dir, exist_ok=True)
        
        # Technical domains and their specific characteristics
        self.technical_domains = {
            "machine_learning": {
                "concepts": ["neural networks", "deep learning", "supervised learning", "unsupervised learning", 
                            "reinforcement learning", "feature engineering", "model evaluation", "hyperparameter tuning"],
                "equations": ["loss functions", "gradient descent", "backpropagation", "activation functions", 
                             "regularization terms", "probability distributions"],
                "architectures": ["CNN", "RNN", "LSTM", "GRU", "Transformer", "VAE", "GAN", "ResNet"],
                "metrics": ["accuracy", "precision", "recall", "F1-score", "ROC-AUC", "log loss", "perplexity"]
            },
            "data_science": {
                "concepts": ["statistical analysis", "hypothesis testing", "data visualization", "feature selection",
                            "dimensionality reduction", "clustering", "regression", "classification"],
                "equations": ["statistical tests", "correlation coefficients", "regression formulas", "distance metrics",
                             "information criteria", "entropy measures"],
                "architectures": ["data pipelines", "ETL processes", "data warehousing", "OLAP cubes"],
                "metrics": ["R-squared", "adjusted R-squared", "MSE", "RMSE", "MAE", "silhouette score"]
            },
            "nlp": {
                "concepts": ["tokenization", "embeddings", "language modeling", "sentiment analysis", "named entity recognition",
                            "machine translation", "text classification", "question answering"],
                "equations": ["TF-IDF", "cosine similarity", "perplexity", "BLEU score", "cross-entropy"],
                "architectures": ["BERT", "GPT", "T5", "RoBERTa", "XLNet", "ELECTRA", "BART"],
                "metrics": ["BLEU", "ROUGE", "METEOR", "perplexity", "F1-score", "accuracy"]
            },
            "mlops": {
                "concepts": ["continuous integration", "continuous deployment", "model versioning", "feature stores",
                            "model monitoring", "A/B testing", "model registry", "experiment tracking"],
                "equations": ["monitoring metrics", "drift detection", "service level objectives"],
                "architectures": ["CI/CD pipelines", "model serving", "feature stores", "monitoring systems"],
                "metrics": ["latency", "throughput", "availability", "model drift", "data drift"]
            },
            "ai": {
                "concepts": ["artificial general intelligence", "expert systems", "knowledge representation",
                            "reasoning", "planning", "natural language understanding", "computer vision", "robotics"],
                "equations": ["utility functions", "search algorithms", "decision theory", "game theory"],
                "architectures": ["agent-based systems", "knowledge graphs", "neural-symbolic systems", "multi-agent systems"],
                "metrics": ["task completion", "reasoning accuracy", "human evaluation metrics"]
            }
        }
        
    def _load_config(self):
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def generate_posts(self, sources, num_posts=3, random_topics=False):
        """
        Generate LinkedIn posts from various sources.
        
        Args:
            sources (list): List of source dictionaries with type, title, content, etc.
            num_posts (int, optional): Number of posts to generate. Defaults to 3.
            random_topics (bool, optional): Whether to include random technical topics. Defaults to False.
            
        Returns:
            list: List of generated post dictionaries.
        """
        posts = []
        
        # Import modules here to avoid circular imports
        from image_generator import ImageGenerator
        from equation_generator import EquationGenerator
        
        image_generator = ImageGenerator()
        equation_generator = EquationGenerator()
        
        # Process each source
        for source in sources[:num_posts]:
            try:
                source_type = source.get('type', 'unknown')
                source_title = source.get('title', 'Untitled')
                source_content = source.get('content', '')
                source_link = source.get('link', '')
                
                # Determine the most appropriate category based on content
                category = self._determine_category(source_content, source_title)
                
                # Generate post with technical depth
                post_content = self._generate_post_with_technical_depth(
                    source_type, source_title, source_content, category
                )
                
                # Process equations in the post
                has_equations = '$' in post_content
                if has_equations:
                    post_content, equation_images = equation_generator.process_content_with_equations(post_content)
                else:
                    equation_images = []
                
                # Generate image for the post
                has_architecture = any(term in post_content.lower() for term in 
                                      ['architecture', 'framework', 'model', 'system', 'pipeline', 'workflow'])
                image_path, cleaned_content = image_generator.generate_image_for_post(
                    post_content, source_title, category, has_equations, has_architecture
                )
                
                # Save post to file
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                safe_title = re.sub(r'[^\w-]', '_', source_title.lower().replace(' ', '_'))[:30]
                post_file = os.path.join(self.posts_dir, f"post_{safe_title}_{timestamp}.md")
                
                with open(post_file, 'w') as f:
                    f.write(f"# {source_title}\n\n")
                    f.write(cleaned_content)
                    if source_link:
                        f.write(f"\n\nOriginal source: {source_link}")
                
                # Save image path for reference
                if image_path:
                    # Copy or move image to images directory if needed
                    image_filename = os.path.basename(image_path)
                    final_image_path = os.path.join(self.images_dir, image_filename)
                    
                    # Only copy if source and destination are different
                    if image_path != final_image_path:
                        import shutil
                        shutil.copy2(image_path, final_image_path)
                    
                    # Use the final path in the post dictionary
                    image_path = final_image_path
                
                # Create post dictionary
                post = {
                    'source_type': source_type,
                    'source_title': source_title,
                    'content': cleaned_content,
                    'image_path': image_path,
                    'post_file': post_file,
                    'source_link': source_link,
                    'category': category,
                    'equation_images': equation_images
                }
                
                posts.append(post)
                logger.info(f"Generated post for {source_title}")
                
                # Save analytics data
                self._save_analytics(post, source)
                
            except Exception as e:
                logger.error(f"Error generating post for {source.get('title', 'unknown')}: {e}", exc_info=True)
        
        return posts
    
    def _determine_category(self, content, title):
        """
        Determine the most appropriate category based on content and title.
        
        Args:
            content (str): Source content.
            title (str): Source title.
            
        Returns:
            str: Category name.
        """
        text = (content + " " + title).lower()
        
        # Define category keywords
        categories = {
            "ai": ["artificial intelligence", "ai ", "machine intelligence", "intelligent systems", "cognitive computing"],
            "machine_learning": ["machine learning", "ml ", "deep learning", "neural network", "supervised learning", "unsupervised learning"],
            "data_science": ["data science", "data analysis", "statistics", "data visualization", "big data", "data mining"],
            "nlp": ["natural language processing", "nlp ", "text analysis", "language model", "sentiment analysis", "named entity recognition"],
            "mlops": ["mlops", "ml ops", "machine learning operations", "model deployment", "model monitoring", "ci/cd", "devops for ml"],
            "technology": ["technology", "tech ", "software", "hardware", "programming", "coding", "development"],
            "business": ["business", "management", "leadership", "strategy", "marketing", "finance", "entrepreneurship"]
        }
        
        # Count keyword matches for each category
        scores = {category: 0 for category in categories}
        for category, keywords in categories.items():
            for keyword in keywords:
                scores[category] += text.count(keyword)
        
        # Return the category with the highest score, or default to "technology"
        max_score = max(scores.values())
        if max_score > 0:
            for category, score in scores.items():
                if score == max_score:
                    return category
        
        return "technology"  # Default category
    
    def _generate_post_with_technical_depth(self, source_type, title, content, category):
        """
        Generate a LinkedIn post with technical depth and domain specificity.
        
        Args:
            source_type (str): Type of source (email, research, etc.).
            title (str): Title of the source.
            content (str): Content of the source.
            category (str): Determined category of the content.
            
        Returns:
            str: Generated LinkedIn post content.
        """
        # Prepare domain-specific elements to include in the prompt
        domain_elements = self._get_domain_specific_elements(category)
        
        # Create a system prompt that encourages technical depth and domain specificity
        system_prompt = self._create_technical_system_prompt(category, domain_elements)
        
        # Create a user prompt with the source information
        user_prompt = self._create_technical_user_prompt(source_type, title, content, category, domain_elements)
        
        # Generate the post using the LLM API
        post_content = self._generate_with_llm(system_prompt, user_prompt)
        
        # If LLM API fails, use a fallback method
        if not post_content:
            post_content = self._fallback_post_generation(source_type, title, content, category)
        
        return post_content
    
    def _get_domain_specific_elements(self, category):
        """
        Get domain-specific elements for a given category.
        
        Args:
            category (str): Category name.
            
        Returns:
            dict: Domain-specific elements.
        """
        # Get domain elements from the technical_domains dictionary
        domain = self.technical_domains.get(category, {})
        if not domain:
            # Fallback to technology if category not found
            domain = self.technical_domains.get("ai", {})
        
        # Select random elements from each category to include
        elements = {
            "concepts": random.sample(domain.get("concepts", []), min(3, len(domain.get("concepts", [])))),
            "equations": random.sample(domain.get("equations", []), min(2, len(domain.get("equations", [])))),
            "architectures": random.sample(domain.get("architectures", []), min(2, len(domain.get("architectures", [])))),
            "metrics": random.sample(domain.get("metrics", []), min(2, len(domain.get("metrics", []))))
        }
        
        return elements
    
    def _create_technical_system_prompt(self, category, domain_elements):
        """
        Create a system prompt that encourages technical depth and domain specificity.
        
        Args:
            category (str): Category name.
            domain_elements (dict): Domain-specific elements.
            
        Returns:
            str: System prompt.
        """
        system_prompt = f"""You are an expert in {category.replace('_', ' ')} with deep technical knowledge. 
Your task is to create a LinkedIn post that demonstrates technical depth, domain expertise, and educational value.

Follow these guidelines:
1. Include precise technical terminology and concepts relevant to {category.replace('_', ' ')}.
2. Incorporate mathematical equations using LaTeX syntax ($ for inline, $$ for block equations).
3. Explain complex ideas clearly with examples or analogies.
4. Structure the post with a clear introduction, technical body, and conclusion.
5. Include a diagram or architecture description where appropriate.
6. Add 2-3 relevant hashtags at the end.
7. Keep the post under 3000 characters for LinkedIn's limits.

Specifically, try to incorporate some of these domain-specific elements:
- Concepts: {', '.join(domain_elements['concepts'])}
- Equations related to: {', '.join(domain_elements['equations'])}
- Architectures or frameworks: {', '.join(domain_elements['architectures'])}
- Metrics or evaluation methods: {', '.join(domain_elements['metrics'])}

At the end of your post, include an image prompt for generating a relevant technical diagram or visualization.
Format: "Image: [detailed description for image generation]"
"""
        return system_prompt
    
    def _create_technical_user_prompt(self, source_type, title, content, category, domain_elements):
        """
        Create a user prompt with the source information.
        
        Args:
            source_type (str): Type of source (email, research, etc.).
            title (str): Title of the source.
            content (str): Content of the source.
            category (str): Determined category of the content.
            domain_elements (dict): Domain-specific elements.
            
        Returns:
            str: User prompt.
        """
        # Truncate content if it's too long
        max_content_length = 4000
        if len(content) > max_content_length:
            content = content[:max_content_length] + "..."
        
        user_prompt = f"""Create a technically rich LinkedIn post based on this {source_type}:

Title: {title}

Content: {content}

Make sure to:
1. Include at least one mathematical equation using LaTeX ($ for inline, $$ for block).
2. Incorporate technical concepts like {', '.join(domain_elements['concepts'][:2])}.
3. Reference relevant architectures or frameworks.
4. Explain the technical significance and implications.
5. End with a thought-provoking question to engage readers.
6. Include an image prompt at the end describing a technical diagram or visualization that would enhance the post.

The post should be educational, technically accurate, and engaging for a professional {category.replace('_', ' ')} audience on LinkedIn.
"""
        return user_prompt
    
    def _generate_with_llm(self, system_prompt, user_prompt):
        """
        Generate content using the LLM API.
        
        Args:
            system_prompt (str): System prompt.
            user_prompt (str): User prompt.
            
        Returns:
            str: Generated content, or None if failed.
        """
        if not self.api_key:
            logger.warning("API key not provided. Skipping LLM generation.")
            return None
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "llama3-70b-8192",  # Use a capable model for technical content
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 4000
            }
            
            response = requests.post(self.api_endpoint, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            return content
        
        except Exception as e:
            logger.error(f"Error generating content with LLM: {e}", exc_info=True)
            return None
    
    def _fallback_post_generation(self, source_type, title, content, category):
        """
        Fallback method for post generation when LLM API fails.
        
        Args:
            source_type (str): Type of source (email, research, etc.).
            title (str): Title of the source.
            content (str): Content of the source.
            category (str): Determined category of the content.
            
        Returns:
            str: Generated post content.
        """
        # Extract key sentences from the content
        sentences = re.split(r'[.!?]', content)
        key_sentences = [s.strip() for s in sentences if len(s.strip()) > 40][:5]
        
        # Create a simple post structure
        post = f"""Here's a draft LinkedIn post based on {source_type} - {title}:

**{title}** 

{' '.join(key_sentences)}

#{'#'.join(category.split('_'))} #ProfessionalDevelopment #TechTrends

Image: A technical diagram illustrating the key concepts from {title}.
"""
        return post
    
    def _save_analytics(self, post, source):
        """
        Save analytics data for the generated post.
        
        Args:
            post (dict): Generated post dictionary.
            source (dict): Source dictionary.
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            analytics_file = os.path.join(self.analytics_dir, f"analytics_{timestamp}.json")
            
            analytics_data = {
                "timestamp": timestamp,
                "source_type": post['source_type'],
                "source_title": post['source_title'],
                "category": post['category'],
                "has_image": bool(post.get('image_path')),
                "has_equations": bool(post.get('equation_images')),
                "content_length": len(post['content']),
                "source_length": len(source.get('content', '')),
                "post_file": post['post_file']
            }
            
            with open(analytics_file, 'w') as f:
                json.dump(analytics_data, f, indent=2)
            
            logger.info(f"Saved analytics data to {analytics_file}")
        
        except Exception as e:
            logger.error(f"Error saving analytics data: {e}", exc_info=True)

if __name__ == "__main__":
    # Test the post generator
    generator = PostGenerator()
    
    # Example source
    test_source = {
        "type": "research",
        "title": "Advances in Transformer Architecture for NLP",
        "content": "Transformer models have revolutionized natural language processing with their self-attention mechanism. Recent advances include more efficient attention mechanisms, parameter sharing techniques, and specialized architectures for specific tasks. These improvements have led to better performance on benchmarks while reducing computational requirements.",
        "link": "https://example.com/transformer-research"
    }
    
    # Generate a post
    posts = generator.generate_posts([test_source])
    
    # Print the generated post
    if posts:
        print(posts[0]['content'])
        print(f"Image path: {posts[0].get('image_path')}")
        print(f"Post file: {posts[0].get('post_file')}")
