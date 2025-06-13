#!/usr/bin/env python3
"""
Random Topic Generator Module for LinkedIn Post Generator
Creates diverse technical topics for LinkedIn posts.
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
            'config',
            'sources.json'
        )
        self.config = self._load_config()
        
        # Define topic templates for different domains
        self.topic_templates = {
            "ai": [
                {
                    "title": "The Future of {ai_field}: {timeframe} Predictions",
                    "content": "Exploring the future developments in {ai_field} over the next {timeframe}. Key areas of advancement include {technique1}, {technique2}, and {application}. What implications will these have for {industry}?",
                    "requires_equations": False
                },
                {
                    "title": "Understanding {ai_model} Architecture",
                    "content": "A technical deep dive into the architecture of {ai_model}. We'll explore how it works, its key components including {component1} and {component2}, and how it achieves state-of-the-art performance in {task}.",
                    "requires_equations": True
                },
                {
                    "title": "{ai_technique} Explained: From Theory to Practice",
                    "content": "Breaking down {ai_technique} from its theoretical foundations to practical applications. We'll cover the mathematical principles, implementation challenges, and real-world use cases in {industry}.",
                    "requires_equations": True
                }
            ],
            "machine_learning": [
                {
                    "title": "Optimizing {ml_algorithm} for {application}",
                    "content": "A technical exploration of how to optimize {ml_algorithm} specifically for {application}. We'll cover hyperparameter tuning, feature engineering, and performance metrics like {metric1} and {metric2}.",
                    "requires_equations": True
                },
                {
                    "title": "From {basic_model} to {advanced_model}: Evolution of {ml_field}",
                    "content": "Tracing the evolution from {basic_model} to {advanced_model} in the field of {ml_field}. Key innovations, architectural changes, and performance improvements will be discussed.",
                    "requires_equations": False
                },
                {
                    "title": "The Mathematics Behind {ml_technique}",
                    "content": "Diving deep into the mathematical foundations of {ml_technique}. We'll explore the key equations, optimization methods, and theoretical guarantees that make this technique work.",
                    "requires_equations": True
                }
            ],
            "data_science": [
                {
                    "title": "{statistical_method} for {data_problem}: A Practical Guide",
                    "content": "A hands-on guide to applying {statistical_method} to solve {data_problem}. We'll walk through the methodology, implementation details, and interpretation of results using real-world examples.",
                    "requires_equations": True
                },
                {
                    "title": "Building Robust {data_pipeline} for {industry} Applications",
                    "content": "Best practices for designing and implementing robust {data_pipeline} specifically for {industry} applications. We'll cover architecture, scalability considerations, and common pitfalls to avoid.",
                    "requires_equations": False
                },
                {
                    "title": "Beyond {basic_metric}: Advanced Evaluation Methods for {model_type}",
                    "content": "Moving beyond simple metrics like {basic_metric} to more sophisticated evaluation approaches for {model_type}. We'll explore {advanced_metric1}, {advanced_metric2}, and their implications for model selection.",
                    "requires_equations": True
                }
            ],
            "nlp": [
                {
                    "title": "Improving {nlp_task} with {nlp_technique}",
                    "content": "A technical exploration of how {nlp_technique} can significantly improve performance on {nlp_task}. We'll examine the methodology, implementation details, and empirical results across multiple benchmarks.",
                    "requires_equations": True
                },
                {
                    "title": "From {classic_nlp} to {modern_nlp}: Evolution of Language Models",
                    "content": "Tracing the evolution from {classic_nlp} approaches to {modern_nlp} architectures. Key innovations, scaling laws, and performance breakthroughs will be discussed with technical depth.",
                    "requires_equations": False
                },
                {
                    "title": "The Mathematics of {nlp_concept}: Theory and Applications",
                    "content": "Diving deep into the mathematical foundations of {nlp_concept}. We'll explore the key equations, optimization techniques, and theoretical insights that drive modern NLP systems.",
                    "requires_equations": True
                }
            ],
            "mlops": [
                {
                    "title": "Building a {deployment_pattern} for {model_type} Models",
                    "content": "A technical guide to implementing {deployment_pattern} specifically for {model_type} models. We'll cover architecture, monitoring considerations, and performance optimization techniques.",
                    "requires_equations": False
                },
                {
                    "title": "From Development to Production: {mlops_technique} for Robust ML Systems",
                    "content": "Best practices for using {mlops_technique} to bridge the gap between development and production ML systems. We'll explore implementation details, common challenges, and success metrics.",
                    "requires_equations": False
                },
                {
                    "title": "Measuring {ml_system} Health: Beyond Basic Metrics",
                    "content": "Advanced approaches to monitoring and measuring the health of {ml_system} in production. We'll cover drift detection, performance degradation signals, and automated remediation strategies.",
                    "requires_equations": True
                }
            ]
        }
        
        # Define domain-specific variables to fill in templates
        self.domain_variables = {
            "ai": {
                "ai_field": ["Generative AI", "Reinforcement Learning", "Computer Vision", "Multimodal AI", "Explainable AI", "AI Ethics", "Federated Learning", "Neural-Symbolic AI"],
                "timeframe": ["5-Year", "10-Year", "Near-Term", "Long-Term"],
                "technique1": ["Transfer Learning", "Few-Shot Learning", "Self-Supervised Learning", "Neuro-Symbolic Integration", "Causal Inference", "Multi-Agent Systems"],
                "technique2": ["Knowledge Distillation", "Meta-Learning", "Continual Learning", "Adversarial Training", "Attention Mechanisms", "Graph Neural Networks"],
                "application": ["Healthcare Diagnostics", "Autonomous Systems", "Climate Modeling", "Drug Discovery", "Financial Forecasting", "Content Generation"],
                "industry": ["Healthcare", "Finance", "Manufacturing", "Retail", "Transportation", "Energy", "Education"],
                "ai_model": ["Transformer", "Diffusion Model", "Graph Neural Network", "Mixture of Experts", "Foundation Model", "Multimodal Architecture"],
                "component1": ["Attention Mechanism", "Residual Connections", "Normalization Layers", "Embedding Space", "Decoder Architecture"],
                "component2": ["Positional Encoding", "Cross-Attention", "Tokenization Strategy", "Loss Function", "Activation Function"],
                "task": ["Natural Language Understanding", "Image Generation", "Multimodal Reasoning", "Time Series Forecasting", "Recommendation"],
                "ai_technique": ["Self-Attention", "Diffusion Process", "Contrastive Learning", "Prompt Engineering", "Knowledge Distillation", "Reinforcement Learning from Human Feedback"]
            },
            "machine_learning": {
                "ml_algorithm": ["Random Forest", "Gradient Boosting", "Deep Neural Network", "Support Vector Machine", "Gaussian Process", "Ensemble Method"],
                "application": ["Anomaly Detection", "Time Series Forecasting", "Recommendation Systems", "Natural Language Processing", "Computer Vision", "Reinforcement Learning"],
                "metric1": ["AUC-ROC", "F1-Score", "Mean Average Precision", "BLEU Score", "Mean Squared Error"],
                "metric2": ["Precision-Recall Curve", "Log Loss", "R-Squared", "Spearman Correlation", "Matthews Correlation Coefficient"],
                "basic_model": ["Linear Regression", "Decision Tree", "Naive Bayes", "Logistic Regression", "K-Means"],
                "advanced_model": ["Transformer", "Graph Neural Network", "Variational Autoencoder", "Generative Adversarial Network", "Diffusion Model"],
                "ml_field": ["Natural Language Processing", "Computer Vision", "Reinforcement Learning", "Recommendation Systems", "Time Series Analysis"],
                "ml_technique": ["Backpropagation", "Gradient Descent", "Regularization", "Attention Mechanism", "Ensemble Learning", "Transfer Learning"]
            },
            "data_science": {
                "statistical_method": ["Bayesian Inference", "Time Series Analysis", "Causal Inference", "Dimensionality Reduction", "Bootstrapping", "MCMC Sampling"],
                "data_problem": ["Missing Data", "Class Imbalance", "Feature Selection", "Outlier Detection", "Bias Mitigation", "Distribution Shift"],
                "data_pipeline": ["ETL Process", "Feature Store", "Data Validation Framework", "Streaming Analytics", "Data Versioning System"],
                "industry": ["Healthcare", "Finance", "Retail", "Manufacturing", "Energy", "Transportation"],
                "basic_metric": ["Accuracy", "Mean Squared Error", "R-Squared", "Precision", "Recall"],
                "advanced_metric1": ["Calibration Curves", "Partial Dependence Plots", "SHAP Values", "Integrated Gradients", "Expected Calibration Error"],
                "advanced_metric2": ["Counterfactual Explanations", "Adversarial Robustness", "Fairness Metrics", "Concept Activation Vectors", "Influence Functions"],
                "model_type": ["Classification Models", "Regression Models", "Clustering Algorithms", "Recommendation Systems", "Anomaly Detectors"]
            },
            "nlp": {
                "nlp_task": ["Named Entity Recognition", "Question Answering", "Text Summarization", "Machine Translation", "Sentiment Analysis", "Topic Modeling"],
                "nlp_technique": ["Attention Mechanism", "Transfer Learning", "Contrastive Learning", "Prompt Engineering", "Knowledge Distillation", "Few-Shot Learning"],
                "classic_nlp": ["Bag-of-Words", "TF-IDF", "Word2Vec", "GloVe", "RNN", "LSTM"],
                "modern_nlp": ["BERT", "GPT", "T5", "RoBERTa", "BART", "XLNet"],
                "nlp_concept": ["Attention", "Tokenization", "Embeddings", "Fine-tuning", "Prompt Engineering", "In-context Learning"]
            },
            "mlops": {
                "deployment_pattern": ["Blue-Green Deployment", "Canary Release", "Shadow Deployment", "A/B Testing Framework", "Feature Flag System"],
                "model_type": ["Large Language Models", "Computer Vision Models", "Recommendation Systems", "Time Series Models", "Anomaly Detection Systems"],
                "mlops_technique": ["Continuous Training", "Model Versioning", "Feature Store", "Experiment Tracking", "Automated Model Evaluation"],
                "ml_system": ["Recommendation Engine", "Content Moderation System", "Fraud Detection Pipeline", "Forecasting Service", "Language Model API"]
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
    
    def generate_random_topics(self, num_topics=3):
        """
        Generate random technical topics for LinkedIn posts.
        
        Args:
            num_topics (int, optional): Number of topics to generate. Defaults to 3.
            
        Returns:
            list: List of topic dictionaries.
        """
        topics = []
        
        # Select random domains
        available_domains = list(self.topic_templates.keys())
        selected_domains = random.choices(available_domains, k=num_topics)
        
        for domain in selected_domains:
            try:
                # Select a random template for this domain
                template = random.choice(self.topic_templates[domain])
                
                # Fill in the template with domain-specific variables
                title = self._fill_template(template["title"], domain)
                content = self._fill_template(template["content"], domain)
                requires_equations = template["requires_equations"]
                
                # Create topic dictionary
                topic = {
                    "type": "random_topic",
                    "title": title,
                    "content": content,
                    "domain": domain,
                    "requires_equations": requires_equations,
                    "link": ""  # No external link for random topics
                }
                
                topics.append(topic)
                logger.info(f"Generated random topic: {title}")
                
            except Exception as e:
                logger.error(f"Error generating random topic for domain {domain}: {e}", exc_info=True)
        
        return topics
    
    def _fill_template(self, template, domain):
        """
        Fill in a template with domain-specific variables.
        
        Args:
            template (str): Template string with placeholders.
            domain (str): Domain name.
            
        Returns:
            str: Filled template.
        """
        result = template
        
        # Get domain-specific variables
        variables = self.domain_variables.get(domain, {})
        
        # Find all placeholders in the template
        placeholders = set(re.findall(r'\{([^}]+)\}', template))
        
        # Replace each placeholder with a random value from the corresponding variable list
        for placeholder in placeholders:
            if placeholder in variables:
                value = random.choice(variables[placeholder])
                result = result.replace(f"{{{placeholder}}}", value)
        
        return result

if __name__ == "__main__":
    # Test the random topic generator
    generator = RandomTopicGenerator()
    topics = generator.generate_random_topics(5)
    
    for i, topic in enumerate(topics):
        print(f"\nTopic {i+1}:")
        print(f"Title: {topic['title']}")
        print(f"Domain: {topic['domain']}")
        print(f"Content: {topic['content']}")
        print(f"Requires equations: {topic['requires_equations']}")
