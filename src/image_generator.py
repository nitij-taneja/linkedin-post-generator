#!/usr/bin/env python3
"""
Image Generator Module for LinkedIn Post Generator
Creates diagrams, technical visualizations, and images for LinkedIn posts.
"""

import os
import json
import logging
import random
import re
import requests
import base64
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageColor
import io
import subprocess
import tempfile
import math

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ImageGenerator:
    """Class to generate images for LinkedIn posts."""
    
    def __init__(self, config_path=None):
        """
        Initialize the ImageGenerator with configuration.
        
        Args:
            config_path (str, optional): Path to the configuration file.
                If None, uses default config path.
        """
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'config', 'sources.json'
        )
        self.config = self._load_config()
        
        # Set up paths
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assets_dir = os.path.join(self.base_dir, 'assets')
        self.stock_images_dir = os.path.join(self.assets_dir, 'stock_images')
        self.generated_images_dir = os.path.join(self.assets_dir, 'generated_images')
        
        # Create directories if they don't exist
        os.makedirs(self.assets_dir, exist_ok=True)
        os.makedirs(self.stock_images_dir, exist_ok=True)
        os.makedirs(self.generated_images_dir, exist_ok=True)
        
        # External API configuration
        self.sd_api_url = os.environ.get('SD_API_URL', '')
        self.hf_api_url = os.environ.get('HF_API_URL', '')
        
        # Diagram templates
        self.diagram_templates = {
            'neural_network': """
            graph TD
                Input[Input Layer] --> H1[Hidden Layer 1]
                H1 --> H2[Hidden Layer 2]
                H2 --> Output[Output Layer]
                
                subgraph Activation Functions
                    ReLU[ReLU]
                    Sigmoid[Sigmoid]
                    Tanh[Tanh]
                end
                
                subgraph Training
                    Loss[Loss Function]
                    Backprop[Backpropagation]
                    Optimizer[Optimizer]
                end
            """,
            'transformer': """
            graph TD
                Input[Input Embeddings] --> PE[Positional Encoding]
                PE --> Encoder
                
                subgraph Encoder
                    SA1[Self-Attention]
                    FF1[Feed Forward]
                    Norm1[Layer Norm]
                    Norm2[Layer Norm]
                    SA1 --> Norm1
                    Norm1 --> FF1
                    FF1 --> Norm2
                end
                
                Encoder --> Decoder
                
                subgraph Decoder
                    SA2[Self-Attention]
                    CA[Cross-Attention]
                    FF2[Feed Forward]
                    Norm3[Layer Norm]
                    Norm4[Layer Norm]
                    Norm5[Layer Norm]
                    SA2 --> Norm3
                    Norm3 --> CA
                    CA --> Norm4
                    Norm4 --> FF2
                    FF2 --> Norm5
                end
                
                Decoder --> Output[Output Probabilities]
            """,
            'reasoning_model': """
            graph TD
                Input[Input Query] --> Retriever[Knowledge Retriever]
                Retriever --> KnowledgeBase[(Knowledge Base)]
                KnowledgeBase --> RetrievedInfo[Retrieved Information]
                RetrievedInfo --> Adapter[LoRA Adapter]
                Input --> Adapter
                Adapter --> Reasoner[Reasoning Module]
                Reasoner --> Output[Reasoned Output]
                
                subgraph Reasoning Process
                    LogicRules[Logic Rules]
                    Inference[Inference Engine]
                    Verification[Verification]
                end
            """,
            'mlops': """
            graph LR
                Dev[Development] --> Train[Training]
                Train --> Validate[Validation]
                Validate --> Package[Packaging]
                Package --> Deploy[Deployment]
                Deploy --> Monitor[Monitoring]
                Monitor --> Retrain[Retraining]
                Retrain --> Train
                
                subgraph CI/CD Pipeline
                    Tests[Automated Tests]
                    Version[Version Control]
                    Registry[Model Registry]
                end
                
                subgraph Monitoring
                    Drift[Drift Detection]
                    Alerts[Alerts]
                    Metrics[Performance Metrics]
                end
            """,
            'data_science': """
            graph TD
                Data[Raw Data] --> Clean[Data Cleaning]
                Clean --> EDA[Exploratory Analysis]
                EDA --> Feature[Feature Engineering]
                Feature --> Split[Train/Test Split]
                Split --> Model[Model Training]
                Model --> Evaluate[Evaluation]
                Evaluate --> Tune[Hyperparameter Tuning]
                Tune --> Deploy[Deployment]
                
                subgraph Metrics
                    Accuracy[Accuracy]
                    Precision[Precision]
                    Recall[Recall]
                    F1[F1 Score]
                end
            """
        }
        
    def _load_config(self):
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def generate_image_for_post(self, content, title, category, has_equations=False, has_architecture=False):
        """
        Generate an appropriate image for a LinkedIn post.
        
        Args:
            content (str): Post content
            title (str): Post title
            category (str): Post category (ai, machine_learning, data_science, etc.)
            has_equations (bool): Whether the post contains equations
            has_architecture (bool): Whether the post describes an architecture
            
        Returns:
            tuple: (image_path, cleaned_content)
        """
        # Extract image prompt if present
        image_prompt, cleaned_content = self._extract_image_prompt(content)
        
        # Determine the best image generation method based on content
        if has_architecture or "architecture" in image_prompt.lower() or "diagram" in image_prompt.lower():
            # Generate a diagram
            image_path = self._generate_diagram(image_prompt, title, category)
        elif has_equations or "equation" in image_prompt.lower() or "$" in content:
            # Generate an equation visualization
            image_path = self._generate_equation_image(content, image_prompt)
        elif self.sd_api_url:
            # Try Stable Diffusion if available
            image_path = self._generate_with_stable_diffusion(image_prompt, category)
        elif self.hf_api_url:
            # Try Hugging Face if available
            image_path = self._generate_with_hugging_face(image_prompt, category)
        else:
            # Fall back to stock images or generated placeholders
            image_path = self._get_stock_image(category, image_prompt)
            
        # If all else fails, create a custom image with text
        if not image_path or not os.path.exists(image_path):
            image_path = self._create_custom_image(title, category, image_prompt)
            
        return image_path, cleaned_content
    
    def _extract_image_prompt(self, content):
        """
        Extract image prompt from post content and clean the content.
        
        Args:
            content (str): Original post content
            
        Returns:
            tuple: (image_prompt, cleaned_content)
        """
        # Look for image prompt at the end of the content
        image_prompt = ""
        cleaned_lines = []
        
        lines = content.split('\n')
        for line in lines:
            if line.lower().startswith("image:"):
                image_prompt = line[6:].strip()
            elif not any(phrase in line.lower() for phrase in ["image:", "image prompt", "(note:"]):
                cleaned_lines.append(line)
                
        cleaned_content = '\n'.join(cleaned_lines)
        
        # If no explicit prompt found, generate one from title and content
        if not image_prompt:
            # Extract key phrases from content
            words = re.findall(r'\b\w{5,}\b', cleaned_content.lower())
            if words:
                top_words = [word for word in words if word not in ['about', 'would', 'could', 'should', 'their', 'there', 'these', 'those', 'other', 'another']][:5]
                image_prompt = f"Technical diagram about {', '.join(top_words)}"
            else:
                image_prompt = "Technical concept visualization"
        
        return image_prompt, cleaned_content
    
    def _generate_diagram(self, prompt, title, category):
        """
        Generate a diagram using Mermaid or PlantUML.
        
        Args:
            prompt (str): Image prompt
            title (str): Post title
            category (str): Post category
            
        Returns:
            str: Path to the generated diagram image
        """
        try:
            # Determine diagram type based on prompt and category
            diagram_type = self._determine_diagram_type(prompt, category)
            
            # Get the appropriate diagram template
            template = self.diagram_templates.get(diagram_type, self.diagram_templates['neural_network'])
            
            # Customize the template based on the prompt
            customized_template = self._customize_diagram_template(template, prompt, title)
            
            # Generate a unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = os.path.join(self.generated_images_dir, f"diagram_{diagram_type}_{timestamp}.png")
            
            # Create a temporary file for the Mermaid content
            with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False) as temp_file:
                temp_file.write(customized_template)
                temp_file_path = temp_file.name
            
            # Generate the diagram using Mermaid CLI
            try:
                subprocess.run(
                    ['mmdc', '-i', temp_file_path, '-o', output_file, '-t', 'forest', '-b', 'transparent'],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                # Check if the file was created successfully
                if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                    logger.info(f"Generated diagram at {output_file}")
                    return output_file
            except (subprocess.SubprocessError, FileNotFoundError) as e:
                logger.warning(f"Mermaid CLI failed: {e}. Trying PlantUML fallback.")
                
                # Try PlantUML as fallback
                try:
                    # Convert Mermaid to PlantUML (simplified conversion)
                    plantuml_content = f"@startuml\n{customized_template}\n@enduml"
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.puml', delete=False) as puml_file:
                        puml_file.write(plantuml_content)
                        puml_file_path = puml_file.name
                    
                    # Generate diagram using PlantUML
                    subprocess.run(
                        ['java', '-jar', 'tools/plantuml.jar', puml_file_path, '-o', self.generated_images_dir],
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    
                    # PlantUML output filename is based on input filename
                    plantuml_output = os.path.join(self.generated_images_dir, os.path.basename(puml_file_path).replace('.puml', '.png'))
                    
                    if os.path.exists(plantuml_output) and os.path.getsize(plantuml_output) > 0:
                        # Rename to our desired filename
                        os.rename(plantuml_output, output_file)
                        logger.info(f"Generated diagram with PlantUML at {output_file}")
                        return output_file
                except Exception as puml_error:
                    logger.warning(f"PlantUML fallback failed: {puml_error}")
            
            # If both Mermaid and PlantUML fail, create a custom diagram
            return self._create_custom_diagram(diagram_type, title, prompt)
            
        except Exception as e:
            logger.error(f"Error generating diagram: {e}")
            return None
    
    def _determine_diagram_type(self, prompt, category):
        """
        Determine the most appropriate diagram type based on prompt and category.
        
        Args:
            prompt (str): Image prompt
            category (str): Post category
            
        Returns:
            str: Diagram type
        """
        prompt_lower = prompt.lower()
        
        if any(term in prompt_lower for term in ['reason', 'reasoning', 'knowledge', 'lora']):
            return 'reasoning_model'
        elif any(term in prompt_lower for term in ['transform', 'attention', 'nlp', 'language model']):
            return 'transformer'
        elif any(term in prompt_lower for term in ['neural', 'deep learning', 'network', 'layer']):
            return 'neural_network'
        elif any(term in prompt_lower for term in ['mlops', 'deploy', 'pipeline', 'ci/cd', 'monitor']):
            return 'mlops'
        elif any(term in prompt_lower for term in ['data', 'feature', 'analysis', 'eda']):
            return 'data_science'
        elif category == 'nlp':
            return 'transformer'
        elif category == 'machine_learning':
            return 'neural_network'
        elif category == 'mlops':
            return 'mlops'
        elif category == 'data_science':
            return 'data_science'
        else:
            return 'neural_network'  # Default
    
    def _customize_diagram_template(self, template, prompt, title):
        """
        Customize a diagram template based on the prompt and title.
        
        Args:
            template (str): Base diagram template
            prompt (str): Image prompt
            title (str): Post title
            
        Returns:
            str: Customized diagram template
        """
        # Extract key terms from prompt and title
        key_terms = set()
        for text in [prompt, title]:
            # Find capitalized terms and technical terms
            terms = re.findall(r'\b[A-Z][a-zA-Z]+\b|\b[a-z]+(?:Net|Model|Flow|Layer|Function|Algorithm)\b', text)
            key_terms.update(terms)
        
        # Replace generic terms in the template with specific terms from the prompt/title
        customized = template
        
        # Replace node labels with more specific terms if available
        if key_terms:
            terms_list = list(key_terms)
            
            # Replace generic node labels with specific terms
            generic_labels = ['Input', 'Output', 'Model', 'Process', 'Data', 'Layer']
            for i, label in enumerate(generic_labels):
                if i < len(terms_list):
                    customized = re.sub(f'\\b{label}\\b', terms_list[i], customized, count=1)
        
        # Add a title to the diagram
        diagram_title = title.replace('"', '\\"')
        if "graph" in customized:
            title_line = f'    title "{diagram_title}"\n'
            customized = customized.replace('graph', f'graph\n{title_line}')
        
        return customized
    
    def _create_custom_diagram(self, diagram_type, title, prompt):
        """
        Create a custom diagram image when Mermaid/PlantUML fails.
        
        Args:
            diagram_type (str): Type of diagram
            title (str): Post title
            prompt (str): Image prompt
            
        Returns:
            str: Path to the generated image
        """
        try:
            # Generate a unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = os.path.join(self.generated_images_dir, f"custom_diagram_{diagram_type}_{timestamp}.png")
            
            # Create a blank image
            width, height = 1200, 800
            image = Image.new('RGB', (width, height), color=(255, 255, 255))
            draw = ImageDraw.Draw(image)
            
            # Try to load a font
            try:
                title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 40)
                node_font = ImageFont.truetype("DejaVuSans.ttf", 30)
                label_font = ImageFont.truetype("DejaVuSans.ttf", 24)
            except IOError:
                title_font = ImageFont.load_default()
                node_font = ImageFont.load_default()
                label_font = ImageFont.load_default()
            
            # Draw title
            draw.text((width//2, 50), title, fill=(0, 0, 0), font=title_font, anchor="mm")
            
            # Draw diagram based on type
            if diagram_type == 'neural_network':
                self._draw_neural_network(draw, width, height, node_font, label_font)
            elif diagram_type == 'transformer':
                self._draw_transformer(draw, width, height, node_font, label_font)
            elif diagram_type == 'reasoning_model':
                self._draw_reasoning_model(draw, width, height, node_font, label_font)
            elif diagram_type == 'mlops':
                self._draw_mlops_pipeline(draw, width, height, node_font, label_font)
            elif diagram_type == 'data_science':
                self._draw_data_science_flow(draw, width, height, node_font, label_font)
            
            # Save the image
            image.save(output_file)
            logger.info(f"Created custom diagram at {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Error creating custom diagram: {e}")
            return None
    
    def _draw_neural_network(self, draw, width, height, node_font, label_font):
        """Draw a neural network diagram."""
        # Define colors
        input_color = (70, 130, 180)  # Steel Blue
        hidden_color = (60, 179, 113)  # Medium Sea Green
        output_color = (255, 165, 0)   # Orange
        
        # Draw layers
        layers = [
            {"name": "Input Layer", "nodes": 4, "color": input_color, "x": width * 0.2},
            {"name": "Hidden Layer 1", "nodes": 6, "color": hidden_color, "x": width * 0.4},
            {"name": "Hidden Layer 2", "nodes": 6, "color": hidden_color, "x": width * 0.6},
            {"name": "Output Layer", "nodes": 3, "color": output_color, "x": width * 0.8}
        ]
        
        # Draw connections first (so they're behind the nodes)
        for i in range(len(layers) - 1):
            current_layer = layers[i]
            next_layer = layers[i + 1]
            
            for j in range(current_layer["nodes"]):
                y1 = height * 0.2 + j * (height * 0.6 / (current_layer["nodes"] - 1))
                
                for k in range(next_layer["nodes"]):
                    y2 = height * 0.2 + k * (height * 0.6 / (next_layer["nodes"] - 1))
                    draw.line([(current_layer["x"], y1), (next_layer["x"], y2)], fill=(200, 200, 200), width=1)
        
        # Draw nodes
        for layer in layers:
            # Draw layer label
            draw.text((layer["x"], height * 0.1), layer["name"], fill=(0, 0, 0), font=label_font, anchor="mm")
            
            # Draw nodes
            for i in range(layer["nodes"]):
                y = height * 0.2 + i * (height * 0.6 / (layer["nodes"] - 1))
                draw.ellipse([(layer["x"] - 30, y - 30), (layer["x"] + 30, y + 30)], fill=layer["color"], outline=(0, 0, 0))
    
    def _draw_transformer(self, draw, width, height, node_font, label_font):
        """Draw a transformer architecture diagram."""
        # Define colors
        input_color = (70, 130, 180)   # Steel Blue
        encoder_color = (60, 179, 113) # Medium Sea Green
        decoder_color = (255, 165, 0)  # Orange
        output_color = (255, 99, 71)   # Tomato
        
        # Draw main components
        components = [
            {"name": "Input", "color": input_color, "x": width * 0.2, "y": height * 0.3, "width": 150, "height": 80},
            {"name": "Encoder", "color": encoder_color, "x": width * 0.4, "y": height * 0.3, "width": 180, "height": 200},
            {"name": "Decoder", "color": decoder_color, "x": width * 0.7, "y": height * 0.3, "width": 180, "height": 200},
            {"name": "Output", "color": output_color, "x": width * 0.9, "y": height * 0.3, "width": 150, "height": 80}
        ]
        
        # Draw connections
        draw.line([(components[0]["x"] + components[0]["width"]/2, components[0]["y"]), 
                   (components[1]["x"] - components[1]["width"]/2, components[1]["y"])], 
                  fill=(0, 0, 0), width=3)
        
        draw.line([(components[1]["x"] + components[1]["width"]/2, components[1]["y"]), 
                   (components[2]["x"] - components[2]["width"]/2, components[2]["y"])], 
                  fill=(0, 0, 0), width=3)
        
        draw.line([(components[2]["x"] + components[2]["width"]/2, components[2]["y"]), 
                   (components[3]["x"] - components[3]["width"]/2, components[3]["y"])], 
                  fill=(0, 0, 0), width=3)
        
        # Draw components
        for comp in components:
            # Draw rounded rectangle
            x1 = comp["x"] - comp["width"]/2
            y1 = comp["y"] - comp["height"]/2
            x2 = comp["x"] + comp["width"]/2
            y2 = comp["y"] + comp["height"]/2
            
            # Draw rectangle with rounded corners
            radius = 20
            draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=comp["color"], outline=(0, 0, 0), width=2)
            draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=comp["color"], outline=(0, 0, 0), width=2)
            draw.pieslice([x1, y1, x1 + 2*radius, y1 + 2*radius], 180, 270, fill=comp["color"], outline=(0, 0, 0), width=2)
            draw.pieslice([x2 - 2*radius, y1, x2, y1 + 2*radius], 270, 0, fill=comp["color"], outline=(0, 0, 0), width=2)
            draw.pieslice([x1, y2 - 2*radius, x1 + 2*radius, y2], 90, 180, fill=comp["color"], outline=(0, 0, 0), width=2)
            draw.pieslice([x2 - 2*radius, y2 - 2*radius, x2, y2], 0, 90, fill=comp["color"], outline=(0, 0, 0), width=2)
            
            # Draw component name
            draw.text((comp["x"], comp["y"]), comp["name"], fill=(0, 0, 0), font=node_font, anchor="mm")
            
            # Add internal components for Encoder and Decoder
            if comp["name"] == "Encoder":
                internal_y = comp["y"] - comp["height"]/4
                draw.text((comp["x"], internal_y), "Self-Attention", fill=(0, 0, 0), font=label_font, anchor="mm")
                
                internal_y = comp["y"] + comp["height"]/4
                draw.text((comp["x"], internal_y), "Feed Forward", fill=(0, 0, 0), font=label_font, anchor="mm")
            
            elif comp["name"] == "Decoder":
                internal_y = comp["y"] - comp["height"]/3
                draw.text((comp["x"], internal_y), "Self-Attention", fill=(0, 0, 0), font=label_font, anchor="mm")
                
                internal_y = comp["y"]
                draw.text((comp["x"], internal_y), "Cross-Attention", fill=(0, 0, 0), font=label_font, anchor="mm")
                
                internal_y = comp["y"] + comp["height"]/3
                draw.text((comp["x"], internal_y), "Feed Forward", fill=(0, 0, 0), font=label_font, anchor="mm")
        
        # Draw title
        draw.text((width/2, height * 0.8), "Transformer Architecture", fill=(0, 0, 0), font=node_font, anchor="mm")
    
    def _draw_reasoning_model(self, draw, width, height, node_font, label_font):
        """Draw a reasoning model architecture diagram."""
        # Define colors
        input_color = (70, 130, 180)    # Steel Blue
        retriever_color = (60, 179, 113) # Medium Sea Green
        knowledge_color = (255, 165, 0)  # Orange
        adapter_color = (186, 85, 211)   # Medium Purple
        reasoner_color = (255, 99, 71)   # Tomato
        output_color = (30, 144, 255)    # Dodger Blue
        
        # Draw main components
        components = [
            {"name": "Input Query", "color": input_color, "x": width * 0.2, "y": height * 0.2, "width": 150, "height": 60},
            {"name": "Knowledge Retriever", "color": retriever_color, "x": width * 0.4, "y": height * 0.3, "width": 180, "height": 60},
            {"name": "Knowledge Base", "color": knowledge_color, "x": width * 0.4, "y": height * 0.5, "width": 180, "height": 60},
            {"name": "LoRA Adapter", "color": adapter_color, "x": width * 0.6, "y": height * 0.4, "width": 180, "height": 60},
            {"name": "Reasoning Module", "color": reasoner_color, "x": width * 0.8, "y": height * 0.4, "width": 180, "height": 60},
            {"name": "Reasoned Output", "color": output_color, "x": width * 0.9, "y": height * 0.6, "width": 150, "height": 60}
        ]
        
        # Draw connections
        arrows = [
            (0, 1), # Input to Retriever
            (1, 2), # Retriever to Knowledge Base
            (2, 3), # Knowledge Base to Adapter
            (0, 3), # Input to Adapter
            (3, 4), # Adapter to Reasoner
            (4, 5)  # Reasoner to Output
        ]
        
        for start, end in arrows:
            start_comp = components[start]
            end_comp = components[end]
            
            # Calculate start and end points
            if start_comp["y"] < end_comp["y"]:
                # Start is above end
                start_y = start_comp["y"] + start_comp["height"]/2
                end_y = end_comp["y"] - end_comp["height"]/2
            elif start_comp["y"] > end_comp["y"]:
                # Start is below end
                start_y = start_comp["y"] - start_comp["height"]/2
                end_y = end_comp["y"] + end_comp["height"]/2
            else:
                # Same level
                start_y = start_comp["y"]
                end_y = end_comp["y"]
                
            if start_comp["x"] < end_comp["x"]:
                # Start is left of end
                start_x = start_comp["x"] + start_comp["width"]/2
                end_x = end_comp["x"] - end_comp["width"]/2
            elif start_comp["x"] > end_comp["x"]:
                # Start is right of end
                start_x = start_comp["x"] - start_comp["width"]/2
                end_x = end_comp["x"] + end_comp["width"]/2
            else:
                # Same column
                start_x = start_comp["x"]
                end_x = end_comp["x"]
            
            # Draw arrow
            draw.line([(start_x, start_y), (end_x, end_y)], fill=(0, 0, 0), width=2)
            
            # Draw arrowhead
            arrow_size = 10
            angle = math.atan2(end_y - start_y, end_x - start_x)
            x1 = end_x - arrow_size * math.cos(angle - math.pi/6)
            y1 = end_y - arrow_size * math.sin(angle - math.pi/6)
            x2 = end_x - arrow_size * math.cos(angle + math.pi/6)
            y2 = end_y - arrow_size * math.sin(angle + math.pi/6)
            draw.polygon([(end_x, end_y), (x1, y1), (x2, y2)], fill=(0, 0, 0))
        
        # Draw components
        for comp in components:
            # Draw rounded rectangle
            x1 = comp["x"] - comp["width"]/2
            y1 = comp["y"] - comp["height"]/2
            x2 = comp["x"] + comp["width"]/2
            y2 = comp["y"] + comp["height"]/2
            
            # Draw rectangle with rounded corners
            radius = 15
            draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=comp["color"], outline=(0, 0, 0), width=2)
            draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=comp["color"], outline=(0, 0, 0), width=2)
            draw.pieslice([x1, y1, x1 + 2*radius, y1 + 2*radius], 180, 270, fill=comp["color"], outline=(0, 0, 0), width=2)
            draw.pieslice([x2 - 2*radius, y1, x2, y1 + 2*radius], 270, 0, fill=comp["color"], outline=(0, 0, 0), width=2)
            draw.pieslice([x1, y2 - 2*radius, x1 + 2*radius, y2], 90, 180, fill=comp["color"], outline=(0, 0, 0), width=2)
            draw.pieslice([x2 - 2*radius, y2 - 2*radius, x2, y2], 0, 90, fill=comp["color"], outline=(0, 0, 0), width=2)
            
            # Draw component name
            draw.text((comp["x"], comp["y"]), comp["name"], fill=(0, 0, 0), font=label_font, anchor="mm")
        
        # Draw title
        draw.text((width/2, height * 0.8), "Open-Reasoner-Zero Architecture", fill=(0, 0, 0), font=node_font, anchor="mm")
    
    def _draw_mlops_pipeline(self, draw, width, height, node_font, label_font):
        """Draw an MLOps pipeline diagram."""
        # Define colors
        dev_color = (70, 130, 180)     # Steel Blue
        train_color = (60, 179, 113)   # Medium Sea Green
        deploy_color = (255, 165, 0)   # Orange
        monitor_color = (255, 99, 71)  # Tomato
        
        # Draw main components in a circular flow
        components = [
            {"name": "Development", "color": dev_color, "x": width * 0.2, "y": height * 0.3},
            {"name": "Training", "color": train_color, "x": width * 0.4, "y": height * 0.3},
            {"name": "Validation", "color": train_color, "x": width * 0.6, "y": height * 0.3},
            {"name": "Deployment", "color": deploy_color, "x": width * 0.8, "y": height * 0.3},
            {"name": "Monitoring", "color": monitor_color, "x": width * 0.8, "y": height * 0.6},
            {"name": "Retraining", "color": train_color, "x": width * 0.2, "y": height * 0.6}
        ]
        
        # Draw arrows connecting components
        for i in range(len(components)):
            start = components[i]
            end = components[(i + 1) % len(components)]
            
            # Draw arrow
            draw.line([(start["x"], start["y"]), (end["x"], end["y"])], fill=(0, 0, 0), width=2)
            
            # Draw arrowhead
            arrow_size = 10
            angle = math.atan2(end["y"] - start["y"], end["x"] - start["x"])
            x1 = end["x"] - arrow_size * math.cos(angle - math.pi/6)
            y1 = end["y"] - arrow_size * math.sin(angle - math.pi/6)
            x2 = end["x"] - arrow_size * math.cos(angle + math.pi/6)
            y2 = end["y"] - arrow_size * math.sin(angle + math.pi/6)
            draw.polygon([(end["x"], end["y"]), (x1, y1), (x2, y2)], fill=(0, 0, 0))
        
        # Draw components
        for comp in components:
            # Draw circle
            radius = 50
            draw.ellipse([(comp["x"] - radius, comp["y"] - radius), 
                          (comp["x"] + radius, comp["y"] + radius)], 
                         fill=comp["color"], outline=(0, 0, 0), width=2)
            
            # Draw component name
            draw.text((comp["x"], comp["y"]), comp["name"], fill=(0, 0, 0), font=label_font, anchor="mm")
        
        # Draw CI/CD box
        ci_cd_x = width * 0.5
        ci_cd_y = height * 0.7
        ci_cd_width = width * 0.6
        ci_cd_height = height * 0.2
        
        # Draw box
        draw.rectangle([(ci_cd_x - ci_cd_width/2, ci_cd_y - ci_cd_height/2),
                        (ci_cd_x + ci_cd_width/2, ci_cd_y + ci_cd_height/2)],
                       outline=(100, 100, 100), width=2)
        
        # Draw title
        draw.text((ci_cd_x, ci_cd_y - ci_cd_height/2 + 20), "CI/CD Pipeline", fill=(0, 0, 0), font=label_font, anchor="mm")
        
        # Draw elements
        elements = ["Version Control", "Automated Tests", "Model Registry"]
        for i, element in enumerate(elements):
            element_x = ci_cd_x - ci_cd_width/3 + (i * ci_cd_width/3)
            element_y = ci_cd_y + 20
            draw.text((element_x, element_y), element, fill=(0, 0, 0), font=label_font, anchor="mm")
        
        # Draw title
        draw.text((width/2, height * 0.1), "MLOps Pipeline", fill=(0, 0, 0), font=node_font, anchor="mm")
    
    def _draw_data_science_flow(self, draw, width, height, node_font, label_font):
        """Draw a data science workflow diagram."""
        # Define colors
        data_color = (70, 130, 180)    # Steel Blue
        process_color = (60, 179, 113) # Medium Sea Green
        model_color = (255, 165, 0)    # Orange
        eval_color = (255, 99, 71)     # Tomato
        
        # Draw main components in a flow
        components = [
            {"name": "Raw Data", "color": data_color, "x": width * 0.1, "y": height * 0.3},
            {"name": "Data Cleaning", "color": process_color, "x": width * 0.25, "y": height * 0.3},
            {"name": "Feature Engineering", "color": process_color, "x": width * 0.4, "y": height * 0.3},
            {"name": "Model Training", "color": model_color, "x": width * 0.55, "y": height * 0.3},
            {"name": "Evaluation", "color": eval_color, "x": width * 0.7, "y": height * 0.3},
            {"name": "Deployment", "color": model_color, "x": width * 0.85, "y": height * 0.3}
        ]
        
        # Draw arrows connecting components
        for i in range(len(components) - 1):
            start = components[i]
            end = components[i + 1]
            
            # Draw arrow
            draw.line([(start["x"], start["y"]), (end["x"], end["y"])], fill=(0, 0, 0), width=2)
            
            # Draw arrowhead
            arrow_size = 10
            angle = math.atan2(end["y"] - start["y"], end["x"] - start["x"])
            x1 = end["x"] - arrow_size * math.cos(angle - math.pi/6)
            y1 = end["y"] - arrow_size * math.sin(angle - math.pi/6)
            x2 = end["x"] - arrow_size * math.cos(angle + math.pi/6)
            y2 = end["y"] - arrow_size * math.sin(angle + math.pi/6)
            draw.polygon([(end["x"], end["y"]), (x1, y1), (x2, y2)], fill=(0, 0, 0))
        
        # Draw components
        for comp in components:
            # Draw rectangle
            rect_width = 120
            rect_height = 60
            draw.rectangle([(comp["x"] - rect_width/2, comp["y"] - rect_height/2),
                            (comp["x"] + rect_width/2, comp["y"] + rect_height/2)],
                           fill=comp["color"], outline=(0, 0, 0), width=2)
            
            # Draw component name
            draw.text((comp["x"], comp["y"]), comp["name"], fill=(0, 0, 0), font=label_font, anchor="mm")
        
        # Draw metrics box
        metrics_x = width * 0.5
        metrics_y = height * 0.6
        metrics_width = width * 0.7
        metrics_height = height * 0.2
        
        # Draw box
        draw.rectangle([(metrics_x - metrics_width/2, metrics_y - metrics_height/2),
                        (metrics_x + metrics_width/2, metrics_y + metrics_height/2)],
                       outline=(100, 100, 100), width=2)
        
        # Draw title
        draw.text((metrics_x, metrics_y - metrics_height/2 + 20), "Evaluation Metrics", fill=(0, 0, 0), font=label_font, anchor="mm")
        
        # Draw metrics
        metrics = ["Accuracy", "Precision", "Recall", "F1 Score", "ROC AUC"]
        for i, metric in enumerate(metrics):
            metric_x = metrics_x - metrics_width/2 + 100 + (i * metrics_width/6)
            metric_y = metrics_y + 20
            draw.text((metric_x, metric_y), metric, fill=(0, 0, 0), font=label_font, anchor="mm")
        
        # Draw title
        draw.text((width/2, height * 0.1), "Data Science Workflow", fill=(0, 0, 0), font=node_font, anchor="mm")
    
    def _generate_equation_image(self, content, prompt):
        """
        Generate an image visualizing mathematical equations from the post.
        
        Args:
            content (str): Post content
            prompt (str): Image prompt
            
        Returns:
            str: Path to the generated image
        """
        try:
            # Extract equations from content
            equations = re.findall(r'\$\$(.*?)\$\$|\$(.*?)\$', content, re.DOTALL)
            equation_texts = []
            
            for eq in equations:
                if eq[0]:  # Display equation ($$...$$)
                    equation_texts.append(eq[0])
                elif eq[1]:  # Inline equation ($...$)
                    equation_texts.append(eq[1])
            
            # If no equations found, extract potential equations from the prompt
            if not equation_texts and "equation" in prompt.lower():
                # Look for equation-like text in the prompt
                potential_eq = re.search(r'equation[s]?.*?([\w\s\+\-\*\/\=\(\)\[\]\{\}\^\_\\\d]+)', prompt, re.IGNORECASE)
                if potential_eq:
                    equation_texts.append(potential_eq.group(1).strip())
            
            # If still no equations, use a placeholder
            if not equation_texts:
                equation_texts = ["f(x) = \\frac{1}{\\sqrt{2\\pi\\sigma^2}} e^{-\\frac{(x-\\mu)^2}{2\\sigma^2}}"]
            
            # Generate a unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = os.path.join(self.generated_images_dir, f"equation_{timestamp}.png")
            
            # Create a blank image
            width, height = 1200, 800
            image = Image.new('RGB', (width, height), color=(255, 255, 255))
            draw = ImageDraw.Draw(image)
            
            # Try to load a font
            try:
                title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 40)
                equation_font = ImageFont.truetype("DejaVuSans.ttf", 30)
            except IOError:
                title_font = ImageFont.load_default()
                equation_font = ImageFont.load_default()
            
            # Draw title
            title = "Mathematical Formulation"
            draw.text((width//2, 50), title, fill=(0, 0, 0), font=title_font, anchor="mm")
            
            # Draw equations (simple rendering, not actual LaTeX)
            y_pos = 150
            for i, eq_text in enumerate(equation_texts[:5]):  # Limit to 5 equations
                # Clean up the equation text
                eq_text = eq_text.strip().replace('\\', '\\\\')
                
                # Draw equation label
                label = f"Equation {i+1}:"
                draw.text((100, y_pos), label, fill=(0, 0, 0), font=equation_font, anchor="lt")
                
                # Draw equation (simplified representation)
                draw.text((250, y_pos), eq_text, fill=(0, 0, 0), font=equation_font, anchor="lt")
                
                y_pos += 100
            
            # Draw a decorative border
            border_width = 5
            draw.rectangle([(border_width, border_width), (width - border_width, height - border_width)], 
                          outline=(70, 130, 180), width=border_width)
            
            # Save the image
            image.save(output_file)
            logger.info(f"Generated equation visualization at {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Error generating equation image: {e}")
            return None
    
    def _generate_with_stable_diffusion(self, prompt, category):
        """
        Generate an image using Stable Diffusion API.
        
        Args:
            prompt (str): Image prompt
            category (str): Post category
            
        Returns:
            str: Path to the generated image
        """
        if not self.sd_api_url:
            return None
            
        try:
            # Enhance the prompt for better results
            enhanced_prompt = f"Professional diagram of {prompt}, technical illustration, clean lines, minimalist, educational, {category}, high quality"
            
            # Generate a unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = os.path.join(self.generated_images_dir, f"sd_{category}_{timestamp}.png")
            
            # Call Stable Diffusion API
            response = requests.post(
                self.sd_api_url,
                json={
                    "prompt": enhanced_prompt,
                    "negative_prompt": "text, watermark, signature, blurry, low quality",
                    "width": 768,
                    "height": 768,
                    "num_inference_steps": 30,
                    "guidance_scale": 7.5
                },
                timeout=60
            )
            
            if response.status_code == 200:
                # Save the image
                image_data = base64.b64decode(response.json()["images"][0])
                with open(output_file, "wb") as f:
                    f.write(image_data)
                logger.info(f"Generated image with Stable Diffusion at {output_file}")
                return output_file
            else:
                logger.warning(f"Stable Diffusion API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating image with Stable Diffusion: {e}")
            return None
    
    def _generate_with_hugging_face(self, prompt, category):
        """
        Generate an image using Hugging Face API.
        
        Args:
            prompt (str): Image prompt
            category (str): Post category
            
        Returns:
            str: Path to the generated image
        """
        if not self.hf_api_url:
            return None
            
        try:
            # Enhance the prompt for better results
            enhanced_prompt = f"Professional diagram of {prompt}, technical illustration, clean lines, minimalist, educational, {category}, high quality"
            
            # Generate a unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = os.path.join(self.generated_images_dir, f"hf_{category}_{timestamp}.png")
            
            # Call Hugging Face API
            response = requests.post(
                self.hf_api_url,
                json={"inputs": enhanced_prompt},
                timeout=60
            )
            
            if response.status_code == 200:
                # Save the image
                with open(output_file, "wb") as f:
                    f.write(response.content)
                logger.info(f"Generated image with Hugging Face at {output_file}")
                return output_file
            else:
                logger.warning(f"Hugging Face API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating image with Hugging Face: {e}")
            return None
    
    def _get_stock_image(self, category, prompt):
        """
        Get a stock image for the given category.
        
        Args:
            category (str): Post category
            prompt (str): Image prompt
            
        Returns:
            str: Path to the stock image
        """
        try:
            # Ensure category directory exists
            category_dir = os.path.join(self.stock_images_dir, category)
            if not os.path.exists(category_dir):
                os.makedirs(category_dir, exist_ok=True)
                
                # Create a placeholder image if directory is empty
                placeholder_path = os.path.join(category_dir, f"{category}_placeholder.jpg")
                self._create_placeholder_image(placeholder_path, category)
            
            # Get list of images in the category directory
            images = [f for f in os.listdir(category_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
            
            if not images:
                # Create a placeholder image if no images found
                placeholder_path = os.path.join(category_dir, f"{category}_placeholder.jpg")
                self._create_placeholder_image(placeholder_path, category)
                images = [f"{category}_placeholder.jpg"]
            
            # Select a random image
            image_path = os.path.join(category_dir, random.choice(images))
            logger.info(f"Selected stock image: {image_path}")
            return image_path
            
        except Exception as e:
            logger.error(f"Error getting stock image: {e}")
            return None
    
    def _create_placeholder_image(self, path, category):
        """
        Create a placeholder image for a category.
        
        Args:
            path (str): Path to save the image
            category (str): Category name
        """
        try:
            # Create a blank image
            width, height = 800, 600
            image = Image.new('RGB', (width, height), color=(240, 245, 250))
            draw = ImageDraw.Draw(image)
            
            # Draw border
            draw.rectangle([(20, 20), (width - 20, height - 20)], outline=(30, 90, 150), width=2)
            
            # Try to load a font
            try:
                font = ImageFont.truetype("DejaVuSans-Bold.ttf", 40)
            except IOError:
                font = ImageFont.load_default()
            
            # Draw category name
            category_display = category.replace('_', ' ').title()
            draw.text((width//2, height//2), category_display, fill=(30, 90, 150), font=font, anchor="mm")
            
            # Save the image
            image.save(path)
            logger.info(f"Created placeholder image at {path}")
            
        except Exception as e:
            logger.error(f"Error creating placeholder image: {e}")
    
    def _create_custom_image(self, title, category, prompt):
        """
        Create a custom image with text.
        
        Args:
            title (str): Post title
            category (str): Post category
            prompt (str): Image prompt
            
        Returns:
            str: Path to the generated image
        """
        try:
            # Generate a unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = os.path.join(self.generated_images_dir, f"custom_{category}_{timestamp}.png")
            
            # Create a blank image
            width, height = 1200, 800
            
            # Choose background color based on category
            bg_colors = {
                'ai': (240, 248, 255),  # Alice Blue
                'machine_learning': (240, 255, 240),  # Honeydew
                'data_science': (255, 240, 245),  # Lavender Blush
                'nlp': (255, 250, 240),  # Floral White
                'mlops': (240, 255, 255),  # Azure
                'technology': (245, 245, 245),  # White Smoke
                'business': (245, 255, 250)   # Mint Cream
            }
            bg_color = bg_colors.get(category, (240, 248, 255))
            
            image = Image.new('RGB', (width, height), color=bg_color)
            draw = ImageDraw.Draw(image)
            
            # Try to load fonts
            try:
                title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 40)
                subtitle_font = ImageFont.truetype("DejaVuSans.ttf", 30)
                body_font = ImageFont.truetype("DejaVuSans.ttf", 24)
            except IOError:
                title_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()
                body_font = ImageFont.load_default()
            
            # Draw title
            title_text = title if len(title) < 50 else title[:47] + "..."
            draw.text((width//2, 80), title_text, fill=(0, 0, 0), font=title_font, anchor="mm")
            
            # Draw prompt as subtitle
            prompt_text = prompt if len(prompt) < 60 else prompt[:57] + "..."
            draw.text((width//2, 150), prompt_text, fill=(60, 60, 60), font=subtitle_font, anchor="mm")
            
            # Draw category
            category_display = category.replace('_', ' ').title()
            draw.text((width//2, height - 80), f"Category: {category_display}", fill=(60, 60, 60), font=body_font, anchor="mm")
            
            # Draw decorative elements based on category
            if category == 'ai' or category == 'machine_learning':
                self._draw_neural_network_decoration(draw, width, height)
            elif category == 'nlp':
                self._draw_text_decoration(draw, width, height)
            elif category == 'data_science':
                self._draw_chart_decoration(draw, width, height)
            elif category == 'mlops':
                self._draw_pipeline_decoration(draw, width, height)
            else:
                self._draw_tech_decoration(draw, width, height)
            
            # Draw border
            border_width = 5
            border_colors = {
                'ai': (70, 130, 180),  # Steel Blue
                'machine_learning': (60, 179, 113),  # Medium Sea Green
                'data_science': (186, 85, 211),  # Medium Purple
                'nlp': (255, 165, 0),  # Orange
                'mlops': (255, 99, 71),  # Tomato
                'technology': (30, 144, 255),  # Dodger Blue
                'business': (46, 139, 87)   # Sea Green
            }
            border_color = border_colors.get(category, (70, 130, 180))
            
            draw.rectangle([(border_width, border_width), (width - border_width, height - border_width)], 
                          outline=border_color, width=border_width)
            
            # Save the image
            image.save(output_file)
            logger.info(f"Created custom image at {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Error creating custom image: {e}")
            return None
    
    def _draw_neural_network_decoration(self, draw, width, height):
        """Draw a neural network decoration on the image."""
        # Draw nodes and connections
        nodes = [
            {"x": width * 0.3, "y": height * 0.4, "r": 20},
            {"x": width * 0.3, "y": height * 0.5, "r": 20},
            {"x": width * 0.3, "y": height * 0.6, "r": 20},
            
            {"x": width * 0.5, "y": height * 0.35, "r": 20},
            {"x": width * 0.5, "y": height * 0.45, "r": 20},
            {"x": width * 0.5, "y": height * 0.55, "r": 20},
            {"x": width * 0.5, "y": height * 0.65, "r": 20},
            
            {"x": width * 0.7, "y": height * 0.4, "r": 20},
            {"x": width * 0.7, "y": height * 0.5, "r": 20},
            {"x": width * 0.7, "y": height * 0.6, "r": 20}
        ]
        
        # Draw connections
        for i in range(3):
            for j in range(4):
                draw.line([(nodes[i]["x"], nodes[i]["y"]), (nodes[3 + j]["x"], nodes[3 + j]["y"])], 
                         fill=(200, 200, 200), width=2)
        
        for i in range(4):
            for j in range(3):
                draw.line([(nodes[3 + i]["x"], nodes[3 + i]["y"]), (nodes[7 + j]["x"], nodes[7 + j]["y"])], 
                         fill=(200, 200, 200), width=2)
        
        # Draw nodes
        for node in nodes:
            draw.ellipse([(node["x"] - node["r"], node["y"] - node["r"]), 
                         (node["x"] + node["r"], node["y"] + node["r"])], 
                        fill=(70, 130, 180), outline=(0, 0, 0), width=1)
    
    def _draw_text_decoration(self, draw, width, height):
        """Draw a text/NLP decoration on the image."""
        # Draw text bubbles
        bubbles = [
            {"x": width * 0.3, "y": height * 0.4, "w": 100, "h": 60, "text": "Input"},
            {"x": width * 0.5, "y": height * 0.5, "w": 120, "h": 60, "text": "Process"},
            {"x": width * 0.7, "y": height * 0.6, "w": 100, "h": 60, "text": "Output"}
        ]
        
        # Draw connections
        for i in range(len(bubbles) - 1):
            draw.line([(bubbles[i]["x"] + bubbles[i]["w"]/2, bubbles[i]["y"]), 
                      (bubbles[i+1]["x"] - bubbles[i+1]["w"]/2, bubbles[i+1]["y"])], 
                     fill=(200, 200, 200), width=2)
        
        # Draw bubbles
        for bubble in bubbles:
            # Draw rounded rectangle
            x1 = bubble["x"] - bubble["w"]/2
            y1 = bubble["y"] - bubble["h"]/2
            x2 = bubble["x"] + bubble["w"]/2
            y2 = bubble["y"] + bubble["h"]/2
            
            # Draw rectangle with rounded corners
            radius = 15
            draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=(255, 165, 0), outline=(0, 0, 0), width=1)
            draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=(255, 165, 0), outline=(0, 0, 0), width=1)
            draw.pieslice([x1, y1, x1 + 2*radius, y1 + 2*radius], 180, 270, fill=(255, 165, 0), outline=(0, 0, 0), width=1)
            draw.pieslice([x2 - 2*radius, y1, x2, y1 + 2*radius], 270, 0, fill=(255, 165, 0), outline=(0, 0, 0), width=1)
            draw.pieslice([x1, y2 - 2*radius, x1 + 2*radius, y2], 90, 180, fill=(255, 165, 0), outline=(0, 0, 0), width=1)
            draw.pieslice([x2 - 2*radius, y2 - 2*radius, x2, y2], 0, 90, fill=(255, 165, 0), outline=(0, 0, 0), width=1)
            
            # Draw text
            try:
                font = ImageFont.truetype("DejaVuSans.ttf", 20)
            except IOError:
                font = ImageFont.load_default()
            
            draw.text((bubble["x"], bubble["y"]), bubble["text"], fill=(0, 0, 0), font=font, anchor="mm")
    
    def _draw_chart_decoration(self, draw, width, height):
        """Draw a chart decoration for data science."""
        # Draw bar chart
        chart_x = width * 0.5
        chart_y = height * 0.5
        chart_width = width * 0.4
        chart_height = height * 0.3
        
        # Draw axes
        draw.line([(chart_x - chart_width/2, chart_y + chart_height/2), 
                  (chart_x + chart_width/2, chart_y + chart_height/2)], 
                 fill=(0, 0, 0), width=2)  # X-axis
        
        draw.line([(chart_x - chart_width/2, chart_y - chart_height/2), 
                  (chart_x - chart_width/2, chart_y + chart_height/2)], 
                 fill=(0, 0, 0), width=2)  # Y-axis
        
        # Draw bars
        bar_width = chart_width / 6
        bar_colors = [(186, 85, 211), (70, 130, 180), (60, 179, 113), (255, 165, 0)]
        
        for i in range(4):
            bar_height = random.uniform(0.3, 0.9) * chart_height
            bar_x = chart_x - chart_width/2 + (i + 1) * bar_width
            bar_y = chart_y + chart_height/2 - bar_height
            
            draw.rectangle([(bar_x, chart_y + chart_height/2), 
                           (bar_x + bar_width*0.8, bar_y)], 
                          fill=bar_colors[i], outline=(0, 0, 0), width=1)
    
    def _draw_pipeline_decoration(self, draw, width, height):
        """Draw a pipeline decoration for MLOps."""
        # Draw pipeline stages
        stages = [
            {"x": width * 0.2, "y": height * 0.5, "text": "Build"},
            {"x": width * 0.4, "y": height * 0.5, "text": "Test"},
            {"x": width * 0.6, "y": height * 0.5, "text": "Deploy"},
            {"x": width * 0.8, "y": height * 0.5, "text": "Monitor"}
        ]
        
        # Draw connections
        for i in range(len(stages) - 1):
            draw.line([(stages[i]["x"] + 50, stages[i]["y"]), 
                      (stages[i+1]["x"] - 50, stages[i+1]["y"])], 
                     fill=(200, 200, 200), width=3)
            
            # Draw arrowhead
            arrow_size = 10
            end_x = stages[i+1]["x"] - 50
            end_y = stages[i+1]["y"]
            angle = 0  # Horizontal line
            x1 = end_x - arrow_size * math.cos(angle - math.pi/6)
            y1 = end_y - arrow_size * math.sin(angle - math.pi/6)
            x2 = end_x - arrow_size * math.cos(angle + math.pi/6)
            y2 = end_y - arrow_size * math.sin(angle + math.pi/6)
            draw.polygon([(end_x, end_y), (x1, y1), (x2, y2)], fill=(200, 200, 200))
        
        # Draw stages
        for stage in stages:
            # Draw rectangle
            rect_width = 80
            rect_height = 50
            draw.rectangle([(stage["x"] - rect_width/2, stage["y"] - rect_height/2),
                           (stage["x"] + rect_width/2, stage["y"] + rect_height/2)],
                          fill=(255, 99, 71), outline=(0, 0, 0), width=1)
            
            # Draw text
            try:
                font = ImageFont.truetype("DejaVuSans.ttf", 20)
            except IOError:
                font = ImageFont.load_default()
            
            draw.text((stage["x"], stage["y"]), stage["text"], fill=(0, 0, 0), font=font, anchor="mm")
    
    def _draw_tech_decoration(self, draw, width, height):
        """Draw a generic tech decoration."""
        # Draw a circuit-like pattern
        lines = [
            [(width * 0.2, height * 0.4), (width * 0.4, height * 0.4)],
            [(width * 0.4, height * 0.4), (width * 0.4, height * 0.6)],
            [(width * 0.4, height * 0.6), (width * 0.6, height * 0.6)],
            [(width * 0.6, height * 0.6), (width * 0.6, height * 0.4)],
            [(width * 0.6, height * 0.4), (width * 0.8, height * 0.4)]
        ]
        
        for line in lines:
            draw.line(line, fill=(30, 144, 255), width=3)
        
        # Draw nodes at junctions
        junctions = [(width * 0.4, height * 0.4), (width * 0.4, height * 0.6), 
                     (width * 0.6, height * 0.6), (width * 0.6, height * 0.4)]
        
        for junction in junctions:
            draw.ellipse([(junction[0] - 10, junction[1] - 10), 
                         (junction[0] + 10, junction[1] + 10)], 
                        fill=(30, 144, 255), outline=(0, 0, 0), width=1)

if __name__ == "__main__":
    # Example usage
    generator = ImageGenerator()
    image_path, _ = generator.generate_image_for_post(
        "This is a post about neural networks and deep learning. Image: Neural network architecture with input, hidden, and output layers.",
        "Understanding Neural Networks",
        "machine_learning",
        has_equations=True,
        has_architecture=True
    )
    
    print(f"Generated image: {image_path}")
