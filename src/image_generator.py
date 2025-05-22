#!/usr/bin/env python3
"""
Image Generator Module for LinkedIn Post Generator
Provides free image generation capabilities using self-hosted models and open-source tools.
"""

import os
import logging
import requests
import random
import shutil
import subprocess
import base64
import json
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import re

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ImageGenerator:
    def __init__(self, config_path=None):
        self.config_path = config_path
        self.config = self._load_config()
        
        # Set up directories
        self.assets_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'assets'
        )
        self.stock_images_dir = os.path.join(self.assets_dir, 'stock_images')
        self.generated_images_dir = os.path.join(self.assets_dir, 'generated_images')
        
        # Ensure directories exist
        for directory in [self.assets_dir, self.stock_images_dir, self.generated_images_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # Create subdirectories for different categories
        for category in ['technology', 'business', 'data_science', 'ai', 'machine_learning']:
            os.makedirs(os.path.join(self.stock_images_dir, category), exist_ok=True)
        
        # Get API endpoints from environment or config
        self.sd_api_url = os.environ.get('SD_API_URL', self.config.get('sd_api_url', 'http://localhost:7860/sdapi/v1/txt2img'))
        self.hf_api_url = os.environ.get('HF_API_URL', self.config.get('hf_api_url', 'https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5'))

    def _load_config(self):
        """Load configuration from file"""
        if not self.config_path:
            return {}
            
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}

    def generate_image_for_post(self, post_content, post_title, category="technology"):
        """Generate an appropriate image for a LinkedIn post"""
        # Extract image prompt from post content
        prompt = self._extract_image_prompt(post_content, post_title)
        
        # Generate a unique filename
        timestamp = random.randint(10000, 99999)
        output_filename = f"image_{timestamp}.png"
        output_path = os.path.join(self.generated_images_dir, output_filename)
        
        # Generate image with fallbacks
        success = self.generate_image_with_fallbacks(prompt, output_path, category)
        
        if success:
            return output_path
        return None

    def _extract_image_prompt(self, post_content, post_title):
        """Extract a suitable image prompt from post content"""
        # Start with the title as base
        prompt = post_title
        
        # Look for technical terms
        technical_terms = re.findall(r'\b(neural network|machine learning|AI|artificial intelligence|algorithm|data science|NLP|computer vision|deep learning)\b', post_content, re.IGNORECASE)
        if technical_terms:
            prompt += f" about {', '.join(set(technical_terms[:3]))}"
        
        # Add style guidance
        prompt += ", professional LinkedIn style, high quality, digital art"
        
        return prompt

    def generate_image_with_fallbacks(self, prompt, output_path, category="technology"):
        """Try multiple image generation methods with fallbacks"""
        logger.info(f"Generating image for prompt: {prompt}")
        
        # Try self-hosted Stable Diffusion first
        if self.generate_image_stable_diffusion(prompt, output_path):
            logger.info(f"Successfully generated image with Stable Diffusion: {output_path}")
            return True
            
        # Fallback to Hugging Face
        if self.generate_image_huggingface(prompt, output_path):
            logger.info(f"Successfully generated image with Hugging Face: {output_path}")
            return True
            
        # Check if it's a technical topic for diagram generation
        if self.is_technical_topic(prompt):
            diagram_code = self.generate_diagram_code_from_prompt(prompt)
            if self.generate_diagram(diagram_code, output_path):
                logger.info(f"Successfully generated diagram: {output_path}")
                return True
        
        # If all else fails, use a stock image or generate a text-based image
        if self.use_stock_image(output_path, category):
            logger.info(f"Using stock image: {output_path}")
            return True
        else:
            # Final fallback: generate a simple text-based image
            return self.generate_text_image(prompt, output_path)

    def generate_image_stable_diffusion(self, prompt, output_path):
        """Generate image using self-hosted Stable Diffusion API"""
        try:
            # Check if API is available
            try:
                base_url = self.sd_api_url.split('/sdapi')[0]
                response = requests.get(f"{base_url}/healthcheck", timeout=2)
                if response.status_code != 200:
                    logger.warning(f"Self-hosted Stable Diffusion API not available: {response.status_code}")
                    return False
            except requests.exceptions.RequestException:
                logger.warning("Self-hosted Stable Diffusion API not available")
                return False
                
            # Call the self-hosted API
            response = requests.post(
                self.sd_api_url,
                json={
                    "prompt": prompt,
                    "negative_prompt": "low quality, blurry, distorted, deformed, disfigured, watermark",
                    "width": 768,
                    "height": 768,
                    "steps": 30,
                    "cfg_scale": 7.5
                },
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'images' in result and result['images']:
                    # Decode base64 image
                    image_data = base64.b64decode(result['images'][0])
                    with open(output_path, 'wb') as f:
                        f.write(image_data)
                    return True
                else:
                    logger.error("No images in response")
                    return False
            else:
                logger.error(f"Image generation failed: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error generating image with Stable Diffusion: {e}")
            return False

    def generate_image_huggingface(self, prompt, output_path):
        """Generate image using Hugging Face community spaces"""
        try:
            # Some community spaces offer free inference with limitations
            response = requests.post(
                self.hf_api_url,
                headers={},  # No auth token needed for some community models
                json={"inputs": prompt},
                timeout=120
            )
            
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                return True
            else:
                logger.error(f"Hugging Face image generation failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error with Hugging Face: {e}")
            return False

    def is_technical_topic(self, prompt):
        """Determine if the prompt is about a technical topic"""
        technical_keywords = [
            'algorithm', 'neural network', 'machine learning', 'code', 'programming',
            'data structure', 'architecture', 'system design', 'workflow', 'process',
            'AI', 'artificial intelligence', 'deep learning', 'NLP', 'computer vision'
        ]
        
        return any(keyword.lower() in prompt.lower() for keyword in technical_keywords)

    def generate_diagram_code_from_prompt(self, prompt):
        """Generate Mermaid diagram code based on prompt"""
        # This is a simplified implementation - in production, you might use an LLM to generate this
        
        if 'workflow' in prompt.lower() or 'process' in prompt.lower():
            return """
            flowchart TD
                A[Start] --> B{Process Data}
                B -->|Success| C[Generate Insights]
                B -->|Failure| D[Error Handling]
                C --> E[Present Results]
                D --> A
                E --> F[End]
            """
        elif 'architecture' in prompt.lower() or 'system' in prompt.lower():
            return """
            flowchart LR
                User -->|Request| API
                API -->|Query| Database
                Database -->|Data| API
                API -->|Response| User
                API -->|Log| Monitoring
            """
        elif 'neural network' in prompt.lower() or 'deep learning' in prompt.lower():
            return """
            flowchart LR
                Input --> |Layer 1| H1[Hidden Layer 1]
                H1 --> |Layer 2| H2[Hidden Layer 2]
                H2 --> |Output Layer| Output
            """
        else:
            # Default diagram
            return """
            flowchart TD
                A[Input] --> B[Process]
                B --> C[Output]
                B --> D[Feedback]
                D --> B
            """

    def generate_diagram(self, diagram_code, output_path):
        """Generate diagram using Mermaid.js"""
        try:
            # Create temporary diagram file
            diagram_file = "temp_diagram.mmd"
            with open(diagram_file, 'w') as f:
                f.write(diagram_code)
            
            # Check if mmdc is available
            try:
                subprocess.run(["which", "mmdc"], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                logger.warning("Mermaid CLI not available, attempting to install")
                try:
                    subprocess.run(["npm", "install", "-g", "@mermaid-js/mermaid-cli"], check=True)
                except subprocess.CalledProcessError:
                    logger.error("Failed to install Mermaid CLI")
                    return False
            
            # Execute mmdc to convert to image
            subprocess.run([
                "mmdc",
                "-i", diagram_file,
                "-o", output_path,
                "-b", "transparent"
            ], check=True)
            
            # Clean up
            if os.path.exists(diagram_file):
                os.remove(diagram_file)
                
            return os.path.exists(output_path)
        except Exception as e:
            logger.error(f"Error generating diagram: {e}")
            return False

    def use_stock_image(self, output_path, category="technology"):
        """Use a stock image from the repository"""
        stock_images_dir = os.path.join(self.stock_images_dir, category)
        
        if not os.path.exists(stock_images_dir):
            logger.error(f"Stock images directory not found: {stock_images_dir}")
            return False
            
        # Get a random stock image
        images = [f for f in os.listdir(stock_images_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if not images:
            logger.error(f"No stock images found in {stock_images_dir}")
            return False
            
        selected_image = os.path.join(stock_images_dir, random.choice(images))
        shutil.copy(selected_image, output_path)
        return True

    def generate_text_image(self, prompt, output_path):
        """Generate a simple text-based image as final fallback"""
        try:
            # Create a simple image with text
            width, height = 800, 600
            background_color = (240, 240, 240)
            text_color = (30, 30, 30)
            
            # Create image
            image = Image.new('RGB', (width, height), background_color)
            draw = ImageDraw.Draw(image)
            
            # Try to load a font, use default if not available
            try:
                font = ImageFont.truetype("DejaVuSans.ttf", 32)
            except IOError:
                font = ImageFont.load_default()
            
            # Extract title from prompt (first sentence or first 50 chars)
            title = prompt.split('.')[0]
            if len(title) > 50:
                title = title[:47] + "..."
                
            # Draw title
            draw.text((width/2, height/4), title, fill=text_color, font=font, anchor="mm")
            
            # Draw decorative elements
            draw.rectangle([100, height/2-50, width-100, height/2+50], outline=(200, 200, 200))
            
            # Add attribution
            small_font = ImageFont.load_default()
            draw.text((width/2, height*3/4), "Generated for LinkedIn", fill=text_color, font=small_font, anchor="mm")
            
            # Save the image
            image.save(output_path)
            return True
        except Exception as e:
            logger.error(f"Error generating text image: {e}")
            return False
