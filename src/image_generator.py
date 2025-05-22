#!/usr/bin/env python3
"""
Image Generator Module for LinkedIn Post Generator
Provides enhanced image generation capabilities using self-hosted models and open-source tools.
"""

import os
import logging
import requests
import random
import shutil
import subprocess
import base64
import json
import re
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math

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
        
        # Create category subdirectories
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
        prompt, post_content_cleaned = self._extract_image_prompt(post_content, post_title)
        
        # Generate a unique filename
        timestamp = random.randint(10000, 99999)
        output_filename = f"image_{timestamp}.png"
        output_path = os.path.join(self.generated_images_dir, output_filename)
        
        # Determine if this is a technical post that needs a diagram
        is_technical = self.is_technical_topic(prompt)
        is_architecture = any(term in prompt.lower() for term in ['architecture', 'diagram', 'flow', 'model'])
        
        # Generate image with appropriate method
        if is_technical and is_architecture:
            # Generate a technical diagram for architecture/model posts
            success = self.generate_technical_diagram(prompt, output_path)
        else:
            # Use the fallback chain for other types of images
            success = self.generate_image_with_fallbacks(prompt, output_path, category)
        
        if success:
            return output_path, post_content_cleaned
        return None, post_content

    def _extract_image_prompt(self, post_content, post_title):
        """Extract a suitable image prompt from post content and remove it from the content"""
        # Look for explicit image prompt at the end of the post
        image_prompt_pattern = r'(?:Image:|image prompt:?)\s*(.*?)(?:\(Note:.*?\)|$)'
        match = re.search(image_prompt_pattern, post_content, re.IGNORECASE | re.DOTALL)
        
        cleaned_content = post_content
        
        if match:
            prompt = match.group(1).strip()
            # Remove the image prompt from the content
            cleaned_content = re.sub(image_prompt_pattern, '', post_content, flags=re.IGNORECASE | re.DOTALL).strip()
        else:
            # Start with the title as base
            prompt = post_title
            
            # Look for technical terms
            technical_terms = re.findall(r'\b(neural network|machine learning|AI|artificial intelligence|algorithm|data science|NLP|computer vision|deep learning)\b', post_content, re.IGNORECASE)
            if technical_terms:
                prompt += f" about {', '.join(set(technical_terms[:3]))}"
        
        # Add style guidance
        prompt += ", professional LinkedIn style, high quality, digital art"
        
        return prompt, cleaned_content

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
        
        # If all else fails, use a stock image or generate an enhanced text-based image
        if self.use_stock_image(output_path, category):
            logger.info(f"Using stock image: {output_path}")
            return True
        else:
            # Final fallback: generate an enhanced text-based image
            return self.generate_enhanced_text_image(prompt, output_path)

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
            'AI', 'artificial intelligence', 'deep learning', 'NLP', 'computer vision',
            'model', 'reasoning', 'transformer', 'attention', 'embedding', 'vector'
        ]
        
        return any(keyword.lower() in prompt.lower() for keyword in technical_keywords)

    def generate_diagram_code_from_prompt(self, prompt):
        """Generate Mermaid diagram code based on prompt"""
        prompt_lower = prompt.lower()
        
        # Check for specific model architectures
        if 'reasoner' in prompt_lower or 'reasoning' in prompt_lower:
            return """
            flowchart LR
                Input[User Query] --> Retriever[Knowledge Retriever]
                Retriever --> KB[(Knowledge Base)]
                KB --> Retriever
                Retriever --> Adapter[LoRA Adapter]
                Adapter --> Reasoner[Reasoning Module]
                Reasoner --> Output[Reasoned Response]
                
                subgraph "Open-Reasoner-Zero Architecture"
                Retriever
                Adapter
                Reasoner
                end
            """
        elif 'neural network' in prompt_lower or 'deep learning' in prompt_lower:
            return """
            flowchart LR
                Input[Input Layer] --> H1[Hidden Layer 1]
                H1 --> H2[Hidden Layer 2]
                H2 --> H3[Hidden Layer 3]
                H3 --> Output[Output Layer]
                
                subgraph "Neural Network Architecture"
                H1
                H2
                H3
                end
                
                style Input fill:#f9f,stroke:#333,stroke-width:2px
                style Output fill:#bbf,stroke:#333,stroke-width:2px
                style H1 fill:#dfd,stroke:#333,stroke-width:2px
                style H2 fill:#dfd,stroke:#333,stroke-width:2px
                style H3 fill:#dfd,stroke:#333,stroke-width:2px
            """
        elif 'transformer' in prompt_lower or 'attention' in prompt_lower:
            return """
            flowchart TD
                Input[Input Embeddings] --> SA[Self-Attention]
                SA --> Norm1[Layer Norm]
                Norm1 --> FF[Feed Forward]
                FF --> Norm2[Layer Norm]
                Norm2 --> Output[Output Probabilities]
                
                subgraph "Transformer Block"
                SA
                Norm1
                FF
                Norm2
                end
                
                style Input fill:#f9f,stroke:#333,stroke-width:2px
                style Output fill:#bbf,stroke:#333,stroke-width:2px
            """
        elif 'workflow' in prompt_lower or 'process' in prompt_lower:
            return """
            flowchart TD
                A[Start] --> B{Process Data}
                B -->|Success| C[Generate Insights]
                B -->|Failure| D[Error Handling]
                C --> E[Present Results]
                D --> A
                E --> F[End]
                
                style A fill:#f9f,stroke:#333,stroke-width:2px
                style F fill:#bbf,stroke:#333,stroke-width:2px
                style B fill:#fdd,stroke:#333,stroke-width:2px
                style C fill:#dfd,stroke:#333,stroke-width:2px
                style D fill:#fdd,stroke:#333,stroke-width:2px
                style E fill:#dfd,stroke:#333,stroke-width:2px
            """
        elif 'architecture' in prompt_lower or 'system' in prompt_lower:
            return """
            flowchart LR
                User([User]) -->|Request| API[API Gateway]
                API -->|Query| DB[(Database)]
                DB -->|Data| API
                API -->|Response| User
                API -->|Log| Monitor[Monitoring]
                
                subgraph "Backend Services"
                API
                DB
                Monitor
                end
                
                style User fill:#f9f,stroke:#333,stroke-width:2px
                style API fill:#dfd,stroke:#333,stroke-width:2px
                style DB fill:#bbf,stroke:#333,stroke-width:2px
                style Monitor fill:#ffd,stroke:#333,stroke-width:2px
            """
        else:
            # Default diagram
            return """
            flowchart TD
                A[Input] --> B[Process]
                B --> C[Output]
                B --> D[Feedback]
                D --> B
                
                style A fill:#f9f,stroke:#333,stroke-width:2px
                style B fill:#dfd,stroke:#333,stroke-width:2px
                style C fill:#bbf,stroke:#333,stroke-width:2px
                style D fill:#ffd,stroke:#333,stroke-width:2px
            """

    def generate_technical_diagram(self, prompt, output_path):
        """Generate a technical diagram based on the prompt"""
        # First try Mermaid.js
        diagram_code = self.generate_diagram_code_from_prompt(prompt)
        if self.generate_diagram(diagram_code, output_path):
            return True
            
        # If Mermaid fails, create a custom diagram
        return self.generate_custom_technical_diagram(prompt, output_path)

    def generate_custom_technical_diagram(self, prompt, output_path):
        """Generate a custom technical diagram using PIL"""
        try:
            # Create a canvas
            width, height = 1200, 800
            background_color = (250, 250, 255)
            
            # Create image with a slight gradient background
            image = Image.new('RGB', (width, height), background_color)
            draw = ImageDraw.Draw(image)
            
            # Create gradient background
            for y in range(height):
                r = int(250 - (y / height) * 20)
                g = int(250 - (y / height) * 15)
                b = int(255 - (y / height) * 5)
                for x in range(width):
                    draw.point((x, y), fill=(r, g, b))
            
            # Try to load a font, use default if not available
            try:
                title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 40)
                box_font = ImageFont.truetype("DejaVuSans.ttf", 30)
                arrow_font = ImageFont.truetype("DejaVuSans.ttf", 20)
            except IOError:
                title_font = ImageFont.load_default()
                box_font = title_font
                arrow_font = title_font
            
            # Extract title from prompt
            title = prompt.split(',')[0]
            if len(title) > 50:
                title = title[:47] + "..."
            
            # Draw title
            draw.text((width/2, 60), title, fill=(30, 50, 100), font=title_font, anchor="mm")
            
            # Determine diagram type based on prompt
            prompt_lower = prompt.lower()
            
            if 'neural network' in prompt_lower or 'deep learning' in prompt_lower:
                self._draw_neural_network(draw, width, height, box_font, arrow_font)
            elif 'transformer' in prompt_lower or 'attention' in prompt_lower:
                self._draw_transformer(draw, width, height, box_font, arrow_font)
            elif 'reasoner' in prompt_lower or 'reasoning' in prompt_lower:
                self._draw_reasoner(draw, width, height, box_font, arrow_font)
            elif 'workflow' in prompt_lower or 'process' in prompt_lower:
                self._draw_workflow(draw, width, height, box_font, arrow_font)
            else:
                self._draw_generic_architecture(draw, width, height, box_font, arrow_font)
            
            # Add a subtle border
            draw.rectangle([(10, 10), (width-10, height-10)], outline=(200, 200, 220), width=2)
            
            # Save the image
            image.save(output_path)
            return True
        except Exception as e:
            logger.error(f"Error generating custom technical diagram: {e}")
            return False

    def _draw_neural_network(self, draw, width, height, box_font, arrow_font):
        """Draw a neural network diagram"""
        # Define layers
        layers = [
            {"name": "Input Layer", "nodes": 4, "color": (230, 230, 250)},
            {"name": "Hidden Layer 1", "nodes": 6, "color": (220, 240, 220)},
            {"name": "Hidden Layer 2", "nodes": 6, "color": (220, 240, 220)},
            {"name": "Output Layer", "nodes": 3, "color": (220, 230, 250)}
        ]
        
        # Calculate positions
        layer_width = width / (len(layers) + 1)
        max_nodes = max(layer['nodes'] for layer in layers)
        node_radius = min(20, (height - 200) / (2 * max_nodes))
        
        # Draw layers and connections
        layer_centers = []
        
        for i, layer in enumerate(layers):
            x = layer_width * (i + 1)
            layer_centers.append(x)
            
            # Draw layer label
            draw.text((x, 130), layer['name'], fill=(50, 50, 80), font=box_font, anchor="mm")
            
            # Draw nodes
            node_positions = []
            node_spacing = (height - 200) / (layer['nodes'] + 1)
            
            for j in range(layer['nodes']):
                y = 200 + node_spacing * (j + 1)
                node_positions.append((x, y))
                
                # Draw node
                draw.ellipse([(x-node_radius, y-node_radius), (x+node_radius, y+node_radius)], 
                             fill=layer['color'], outline=(100, 100, 150), width=2)
            
            # Connect to previous layer
            if i > 0:
                prev_positions = [(layer_centers[i-1], 200 + (height - 200) / (layers[i-1]['nodes'] + 1) * (j + 1)) 
                                 for j in range(layers[i-1]['nodes'])]
                
                # Draw connections
                for start_pos in prev_positions:
                    for end_pos in node_positions:
                        draw.line([start_pos, end_pos], fill=(180, 180, 220), width=1)

    def _draw_transformer(self, draw, width, height, box_font, arrow_font):
        """Draw a transformer architecture diagram"""
        # Define components
        components = [
            {"name": "Input Embeddings", "color": (230, 220, 250)},
            {"name": "Multi-Head Attention", "color": (220, 240, 220)},
            {"name": "Add & Normalize", "color": (250, 230, 220)},
            {"name": "Feed Forward", "color": (220, 240, 220)},
            {"name": "Add & Normalize", "color": (250, 230, 220)},
            {"name": "Output Probabilities", "color": (220, 230, 250)}
        ]
        
        # Calculate positions
        box_width = 300
        box_height = 60
        box_spacing = (height - 200) / (len(components) + 1)
        
        # Draw components and connections
        for i, component in enumerate(components):
            x = width / 2
            y = 200 + box_spacing * (i + 1)
            
            # Draw box
            draw.rectangle([(x-box_width/2, y-box_height/2), (x+box_width/2, y+box_height/2)], 
                          fill=component['color'], outline=(100, 100, 150), width=2)
            
            # Draw label
            draw.text((x, y), component['name'], fill=(50, 50, 80), font=box_font, anchor="mm")
            
            # Draw connection to next component
            if i < len(components) - 1:
                next_y = 200 + box_spacing * (i + 2)
                draw.line([(x, y+box_height/2), (x, next_y-box_height/2)], fill=(100, 100, 150), width=2)
                
                # Draw arrow
                arrow_y = (y+box_height/2 + next_y-box_height/2) / 2
                draw.polygon([(x, arrow_y+10), (x-7, arrow_y-5), (x+7, arrow_y-5)], fill=(100, 100, 150))
        
        # Draw "Transformer Block" label
        draw.text((width-150, height/2), "Transformer Block", fill=(80, 80, 120), font=arrow_font, anchor="mm")
        draw.line([(width-250, height/2-100), (width-250, height/2+100)], fill=(180, 180, 220), width=2)

    def _draw_reasoner(self, draw, width, height, box_font, arrow_font):
        """Draw a reasoning architecture diagram"""
        # Define components
        components = [
            {"name": "User Query", "x": 200, "y": height/2, "color": (230, 220, 250)},
            {"name": "Knowledge Retriever", "x": 450, "y": height/2, "color": (220, 240, 220)},
            {"name": "Knowledge Base", "x": 450, "y": height/2 + 150, "color": (250, 230, 220)},
            {"name": "LoRA Adapter", "x": 700, "y": height/2, "color": (220, 240, 220)},
            {"name": "Reasoning Module", "x": 950, "y": height/2, "color": (220, 240, 220)},
            {"name": "Reasoned Response", "x": 1100, "y": height/2, "color": (220, 230, 250)}
        ]
        
        # Calculate box dimensions
        box_width = 180
        box_height = 60
        
        # Draw components and connections
        for i, component in enumerate(components):
            x, y = component["x"], component["y"]
            
            # Draw special shape for Knowledge Base
            if component["name"] == "Knowledge Base":
                # Draw cylinder for database
                draw.ellipse([(x-box_width/2, y-box_height/2), (x+box_width/2, y-box_height/2+20)], 
                            fill=component["color"], outline=(100, 100, 150), width=2)
                draw.rectangle([(x-box_width/2, y-box_height/2+10), (x+box_width/2, y+box_height/2-10)], 
                              fill=component["color"], outline=(100, 100, 150), width=2)
                draw.ellipse([(x-box_width/2, y+box_height/2-20), (x+box_width/2, y+box_height/2)], 
                            fill=component["color"], outline=(100, 100, 150), width=2)
            else:
                # Draw regular box
                draw.rectangle([(x-box_width/2, y-box_height/2), (x+box_width/2, y+box_height/2)], 
                              fill=component["color"], outline=(100, 100, 150), width=2)
            
            # Draw label
            draw.text((x, y), component["name"], fill=(50, 50, 80), font=box_font, anchor="mm")
        
        # Draw connections
        connections = [
            (0, 1), # User Query to Knowledge Retriever
            (1, 2), # Knowledge Retriever to Knowledge Base
            (2, 1), # Knowledge Base to Knowledge Retriever
            (1, 3), # Knowledge Retriever to LoRA Adapter
            (3, 4), # LoRA Adapter to Reasoning Module
            (4, 5)  # Reasoning Module to Reasoned Response
        ]
        
        for start_idx, end_idx in connections:
            start = components[start_idx]
            end = components[end_idx]
            
            # Determine connection points
            if start["y"] == end["y"]:
                # Horizontal connection
                start_x = start["x"] + box_width/2
                start_y = start["y"]
                end_x = end["x"] - box_width/2
                end_y = end["y"]
            else:
                # Vertical connection
                if start["y"] < end["y"]:
                    start_x = start["x"]
                    start_y = start["y"] + box_height/2
                    end_x = end["x"]
                    end_y = end["y"] - box_height/2
                else:
                    start_x = start["x"]
                    start_y = start["y"] - box_height/2
                    end_x = end["x"]
                    end_y = end["y"] + box_height/2
            
            # Draw line
            draw.line([(start_x, start_y), (end_x, end_y)], fill=(100, 100, 150), width=2)
            
            # Draw arrow
            if start_idx != 2:  # Skip arrow for Knowledge Base to Knowledge Retriever
                angle = math.atan2(end_y - start_y, end_x - start_x)
                arrow_x = end_x - 15 * math.cos(angle)
                arrow_y = end_y - 15 * math.sin(angle)
                
                draw.polygon([
                    (end_x, end_y),
                    (arrow_x - 7 * math.sin(angle), arrow_y + 7 * math.cos(angle)),
                    (arrow_x + 7 * math.sin(angle), arrow_y - 7 * math.cos(angle))
                ], fill=(100, 100, 150))
        
        # Draw "Open-Reasoner-Zero Architecture" label
        draw.text((width/2, height-80), "Open-Reasoner-Zero Architecture", fill=(80, 80, 120), font=box_font, anchor="mm")

    def _draw_workflow(self, draw, width, height, box_font, arrow_font):
        """Draw a workflow diagram"""
        # Define components
        components = [
            {"name": "Start", "x": width/2, "y": 180, "color": (230, 220, 250)},
            {"name": "Process Data", "x": width/2, "y": 300, "color": (220, 240, 220)},
            {"name": "Generate Insights", "x": width/2 - 250, "y": 420, "color": (220, 240, 220)},
            {"name": "Error Handling", "x": width/2 + 250, "y": 420, "color": (250, 220, 220)},
            {"name": "Present Results", "x": width/2 - 250, "y": 540, "color": (220, 240, 220)},
            {"name": "End", "x": width/2 - 250, "y": 660, "color": (220, 230, 250)}
        ]
        
        # Calculate box dimensions
        box_width = 180
        box_height = 60
        
        # Draw components
        for component in components:
            x, y = component["x"], component["y"]
            
            # Draw special shape for decision
            if component["name"] == "Process Data":
                # Draw diamond for decision
                draw.polygon([
                    (x, y - box_height/2),
                    (x + box_width/2, y),
                    (x, y + box_height/2),
                    (x - box_width/2, y)
                ], fill=component["color"], outline=(100, 100, 150), width=2)
            else:
                # Draw regular box with rounded corners
                draw.rounded_rectangle(
                    [(x-box_width/2, y-box_height/2), (x+box_width/2, y+box_height/2)],
                    radius=15, fill=component["color"], outline=(100, 100, 150), width=2
                )
            
            # Draw label
            draw.text((x, y), component["name"], fill=(50, 50, 80), font=box_font, anchor="mm")
        
        # Draw connections
        connections = [
            (0, 1, ""),  # Start to Process Data
            (1, 2, "Success"),  # Process Data to Generate Insights
            (1, 3, "Failure"),  # Process Data to Error Handling
            (2, 4, ""),  # Generate Insights to Present Results
            (4, 5, ""),  # Present Results to End
            (3, 0, "")   # Error Handling to Start
        ]
        
        for start_idx, end_idx, label in connections:
            start = components[start_idx]
            end = components[end_idx]
            
            # Draw line
            if start_idx == 1 and end_idx == 2:  # Process Data to Generate Insights
                # Draw angled line
                mid_x = (start["x"] + end["x"]) / 2
                draw.line([(start["x"] - box_width/4, start["y"] + box_height/4), 
                          (mid_x, start["y"] + box_height/4),
                          (mid_x, end["y"] - box_height/2)], 
                          fill=(100, 100, 150), width=2)
                draw.line([(mid_x, end["y"] - box_height/2), (end["x"], end["y"] - box_height/2)],
                          fill=(100, 100, 150), width=2)
                
                # Draw label
                draw.text((mid_x + 20, start["y"] + box_height/4 - 15), 
                         label, fill=(80, 80, 120), font=arrow_font, anchor="mm")
                
                # Draw arrow
                draw.polygon([
                    (end["x"], end["y"] - box_height/2),
                    (end["x"] - 10, end["y"] - box_height/2 - 7),
                    (end["x"] - 10, end["y"] - box_height/2 + 7)
                ], fill=(100, 100, 150))
                
            elif start_idx == 1 and end_idx == 3:  # Process Data to Error Handling
                # Draw angled line
                mid_x = (start["x"] + end["x"]) / 2
                draw.line([(start["x"] + box_width/4, start["y"] + box_height/4), 
                          (mid_x, start["y"] + box_height/4),
                          (mid_x, end["y"] - box_height/2)], 
                          fill=(100, 100, 150), width=2)
                draw.line([(mid_x, end["y"] - box_height/2), (end["x"], end["y"] - box_height/2)],
                          fill=(100, 100, 150), width=2)
                
                # Draw label
                draw.text((mid_x - 20, start["y"] + box_height/4 - 15), 
                         label, fill=(80, 80, 120), font=arrow_font, anchor="mm")
                
                # Draw arrow
                draw.polygon([
                    (end["x"], end["y"] - box_height/2),
                    (end["x"] - 10, end["y"] - box_height/2 - 7),
                    (end["x"] - 10, end["y"] - box_height/2 + 7)
                ], fill=(100, 100, 150))
                
            elif start_idx == 3 and end_idx == 0:  # Error Handling to Start
                # Draw curved line back to start
                draw.line([(start["x"] + box_width/2, start["y"]), 
                          (start["x"] + box_width/2 + 50, start["y"]),
                          (start["x"] + box_width/2 + 50, end["y"]),
                          (end["x"] + box_width/2, end["y"])], 
                          fill=(100, 100, 150), width=2)
                
                # Draw arrow
                draw.polygon([
                    (end["x"] + box_width/2, end["y"]),
                    (end["x"] + box_width/2 - 7, end["y"] - 10),
                    (end["x"] + box_width/2 + 7, end["y"] - 10)
                ], fill=(100, 100, 150))
                
            else:
                # Draw straight line
                draw.line([(start["x"], start["y"] + box_height/2), (end["x"], end["y"] - box_height/2)], 
                         fill=(100, 100, 150), width=2)
                
                # Draw arrow
                draw.polygon([
                    (end["x"], end["y"] - box_height/2),
                    (end["x"] - 7, end["y"] - box_height/2 - 10),
                    (end["x"] + 7, end["y"] - box_height/2 - 10)
                ], fill=(100, 100, 150))

    def _draw_generic_architecture(self, draw, width, height, box_font, arrow_font):
        """Draw a generic system architecture diagram"""
        # Define components
        components = [
            {"name": "User", "x": 200, "y": height/2, "color": (230, 220, 250), "type": "actor"},
            {"name": "API Gateway", "x": 450, "y": height/2, "color": (220, 240, 220), "type": "component"},
            {"name": "Service 1", "x": 700, "y": height/2 - 100, "color": (220, 240, 220), "type": "component"},
            {"name": "Service 2", "x": 700, "y": height/2 + 100, "color": (220, 240, 220), "type": "component"},
            {"name": "Database", "x": 950, "y": height/2, "color": (220, 230, 250), "type": "database"}
        ]
        
        # Calculate box dimensions
        box_width = 160
        box_height = 60
        
        # Draw components
        for component in components:
            x, y = component["x"], component["y"]
            
            if component["type"] == "actor":
                # Draw actor (person)
                # Head
                draw.ellipse([(x-20, y-box_height/2-30), (x+20, y-box_height/2+10)], 
                            fill=component["color"], outline=(100, 100, 150), width=2)
                # Body
                draw.line([(x, y-box_height/2+10), (x, y+10)], fill=(100, 100, 150), width=2)
                # Arms
                draw.line([(x-30, y-20), (x+30, y-20)], fill=(100, 100, 150), width=2)
                # Legs
                draw.line([(x, y+10), (x-20, y+box_height/2)], fill=(100, 100, 150), width=2)
                draw.line([(x, y+10), (x+20, y+box_height/2)], fill=(100, 100, 150), width=2)
                
                # Draw label
                draw.text((x, y+box_height/2+15), component["name"], fill=(50, 50, 80), font=box_font, anchor="mm")
                
            elif component["type"] == "database":
                # Draw cylinder for database
                draw.ellipse([(x-box_width/2, y-box_height/2), (x+box_width/2, y-box_height/2+20)], 
                            fill=component["color"], outline=(100, 100, 150), width=2)
                draw.rectangle([(x-box_width/2, y-box_height/2+10), (x+box_width/2, y+box_height/2-10)], 
                              fill=component["color"], outline=(100, 100, 150), width=2)
                draw.ellipse([(x-box_width/2, y+box_height/2-20), (x+box_width/2, y+box_height/2)], 
                            fill=component["color"], outline=(100, 100, 150), width=2)
                
                # Draw label
                draw.text((x, y), component["name"], fill=(50, 50, 80), font=box_font, anchor="mm")
                
            else:
                # Draw regular component box
                draw.rounded_rectangle(
                    [(x-box_width/2, y-box_height/2), (x+box_width/2, y+box_height/2)],
                    radius=10, fill=component["color"], outline=(100, 100, 150), width=2
                )
                
                # Draw label
                draw.text((x, y), component["name"], fill=(50, 50, 80), font=box_font, anchor="mm")
        
        # Draw connections
        connections = [
            (0, 1, "Request"),  # User to API Gateway
            (1, 2, ""),  # API Gateway to Service 1
            (1, 3, ""),  # API Gateway to Service 2
            (2, 4, ""),  # Service 1 to Database
            (3, 4, ""),  # Service 2 to Database
            (1, 0, "Response")  # API Gateway to User
        ]
        
        for start_idx, end_idx, label in connections:
            start = components[start_idx]
            end = components[end_idx]
            
            # Determine connection points
            if start_idx == 0 and end_idx == 1:  # User to API Gateway
                start_x = start["x"] + 30
                start_y = start["y"] - 10
                end_x = end["x"] - box_width/2
                end_y = end["y"] - 10
                
                # Draw line
                draw.line([(start_x, start_y), (end_x, end_y)], fill=(100, 100, 150), width=2)
                
                # Draw label
                mid_x = (start_x + end_x) / 2
                mid_y = (start_y + end_y) / 2 - 15
                draw.text((mid_x, mid_y), label, fill=(80, 80, 120), font=arrow_font, anchor="mm")
                
                # Draw arrow
                draw.polygon([
                    (end_x, end_y),
                    (end_x - 10, end_y - 7),
                    (end_x - 10, end_y + 7)
                ], fill=(100, 100, 150))
                
            elif start_idx == 1 and end_idx == 0:  # API Gateway to User
                start_x = start["x"] - box_width/2
                start_y = start["y"] + 10
                end_x = end["x"] + 30
                end_y = end["y"] + 10
                
                # Draw line
                draw.line([(start_x, start_y), (end_x, end_y)], fill=(100, 100, 150), width=2)
                
                # Draw label
                mid_x = (start_x + end_x) / 2
                mid_y = (start_y + end_y) / 2 + 15
                draw.text((mid_x, mid_y), label, fill=(80, 80, 120), font=arrow_font, anchor="mm")
                
                # Draw arrow
                draw.polygon([
                    (end_x, end_y),
                    (end_x - 10, end_y - 7),
                    (end_x - 10, end_y + 7)
                ], fill=(100, 100, 150))
                
            elif (start_idx == 1 and end_idx == 2) or (start_idx == 1 and end_idx == 3):
                # API Gateway to Services
                start_x = start["x"] + box_width/2
                start_y = start["y"]
                end_x = end["x"] - box_width/2
                end_y = end["y"]
                
                # Draw line
                draw.line([(start_x, start_y), (end_x, end_y)], fill=(100, 100, 150), width=2)
                
                # Draw arrow
                angle = math.atan2(end_y - start_y, end_x - start_x)
                draw.polygon([
                    (end_x, end_y),
                    (end_x - 10 * math.cos(angle) - 7 * math.sin(angle), end_y - 10 * math.sin(angle) + 7 * math.cos(angle)),
                    (end_x - 10 * math.cos(angle) + 7 * math.sin(angle), end_y - 10 * math.sin(angle) - 7 * math.cos(angle))
                ], fill=(100, 100, 150))
                
            elif (start_idx == 2 and end_idx == 4) or (start_idx == 3 and end_idx == 4):
                # Services to Database
                start_x = start["x"] + box_width/2
                start_y = start["y"]
                end_x = end["x"] - box_width/2
                end_y = end["y"]
                
                # Draw line
                draw.line([(start_x, start_y), (end_x, end_y)], fill=(100, 100, 150), width=2)
                
                # Draw arrow
                angle = math.atan2(end_y - start_y, end_x - start_x)
                draw.polygon([
                    (end_x, end_y),
                    (end_x - 10 * math.cos(angle) - 7 * math.sin(angle), end_y - 10 * math.sin(angle) + 7 * math.cos(angle)),
                    (end_x - 10 * math.cos(angle) + 7 * math.sin(angle), end_y - 10 * math.sin(angle) - 7 * math.cos(angle))
                ], fill=(100, 100, 150))
        
        # Draw "System Architecture" label
        draw.text((width/2, height-60), "System Architecture", fill=(80, 80, 120), font=box_font, anchor="mm")

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
                "-b", "transparent",
                "-t", "neutral"
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

    def generate_enhanced_text_image(self, prompt, output_path):
        """Generate an enhanced text-based image as final fallback"""
        try:
            # Create a visually appealing image with text
            width, height = 1200, 800
            
            # Create base image with gradient background
            image = Image.new('RGB', (width, height), (240, 245, 250))
            draw = ImageDraw.Draw(image)
            
            # Create gradient background
            for y in range(height):
                r = int(240 - (y / height) * 20)
                g = int(245 - (y / height) * 15)
                b = int(250 - (y / height) * 5)
                for x in range(width):
                    draw.point((x, y), fill=(r, g, b))
            
            # Try to load fonts
            try:
                title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 48)
                subtitle_font = ImageFont.truetype("DejaVuSans.ttf", 36)
                body_font = ImageFont.truetype("DejaVuSans.ttf", 24)
            except IOError:
                title_font = ImageFont.load_default()
                subtitle_font = title_font
                body_font = title_font
            
            # Extract title from prompt (first sentence or first 50 chars)
            title = prompt.split('.')[0]
            if len(title) > 50:
                title = title[:47] + "..."
                
            # Create a subtitle from keywords in the prompt
            keywords = re.findall(r'\b(AI|ML|data|neural|network|machine learning|deep learning|technology|business|analytics)\b', 
                                 prompt, re.IGNORECASE)
            subtitle = "Exploring " + ", ".join(set(keywords[:3])) if keywords else "Professional Insights"
            
            # Draw decorative elements
            # Top banner
            draw.rectangle([0, 0, width, 120], fill=(30, 60, 110, 180))
            
            # Side accent
            draw.rectangle([0, 0, 80, height], fill=(30, 60, 110, 100))
            
            # Bottom accent
            draw.rectangle([0, height-60, width, height], fill=(30, 60, 110, 100))
            
            # Draw circular elements for visual interest
            for i in range(5):
                x = random.randint(100, width-100)
                y = random.randint(200, height-200)
                size = random.randint(30, 100)
                opacity = random.randint(30, 80)
                color = (30, 60, 110, opacity)
                draw.ellipse((x-size, y-size, x+size, y+size), fill=color)
            
            # Draw title
            draw.text((width/2, 60), title, fill=(255, 255, 255), font=title_font, anchor="mm")
            
            # Draw subtitle
            draw.text((width/2, 180), subtitle, fill=(30, 60, 110), font=subtitle_font, anchor="mm")
            
            # Draw decorative line
            draw.line([(width/4, 220), (width*3/4, 220)], fill=(30, 60, 110), width=3)
            
            # Add some relevant text based on the prompt
            if 'AI' in prompt or 'artificial intelligence' in prompt.lower():
                body_text = "Artificial Intelligence Insights & Innovations"
            elif 'data' in prompt.lower():
                body_text = "Data Science & Analytics Perspectives"
            elif 'business' in prompt.lower():
                body_text = "Business Strategy & Leadership"
            else:
                body_text = "Professional Technology Insights"
                
            draw.text((width/2, height/2), body_text, fill=(50, 70, 120), font=subtitle_font, anchor="mm")
            
            # Add attribution
            draw.text((width/2, height-30), "LinkedIn Professional Content", fill=(255, 255, 255), font=body_font, anchor="mm")
            
            # Apply subtle blur to soften the image
            image = image.filter(ImageFilter.GaussianBlur(radius=0.5))
            
            # Save the image
            image.save(output_path)
            return True
        except Exception as e:
            logger.error(f"Error generating enhanced text image: {e}")
            return False
