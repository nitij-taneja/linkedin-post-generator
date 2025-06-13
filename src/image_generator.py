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
            \'config\
obots.txt', \'sources.json\'
        )
        self.config = self._load_config()
        
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assets_dir = os.path.join(self.base_dir, \'assets\
obots.txt')
        self.stock_images_dir = os.path.join(self.assets_dir, \'stock_images\
obots.txt')
        self.generated_images_dir = os.path.join(self.assets_dir, \'generated_images\
obots.txt')
        
        os.makedirs(self.assets_dir, exist_ok=True)
        os.makedirs(self.stock_images_dir, exist_ok=True)
        os.makedirs(self.generated_images_dir, exist_ok=True)
        
        self.sd_api_url = os.environ.get(\'SD_API_URL\
obots.txt', \'\
obots.txt')
        self.hf_api_url = os.environ.get(\'HF_API_URL\
obots.txt', \'\
obots.txt')
        
        self.diagram_templates = {
            \'neural_network\
obots.txt': """
            graph TD
                Input[Input Layer] --> H1[Hidden Layer 1]
                H1 --> H2[Hidden Layer 2]
                H2 --> Output[Output Layer]
                classDef default fill:#f9f,stroke:#333,stroke-width:2px;
                classDef inputNode fill:#lightgrey,stroke:#333,stroke-width:2px;
                classDef hiddenNode fill:#lightblue,stroke:#333,stroke-width:2px;
                classDef outputNode fill:#lightgreen,stroke:#333,stroke-width:2px;
                class Input inputNode;
                class H1,H2 hiddenNode;
                class Output outputNode;
            """,
            \'transformer\
obots.txt': """
            graph TD
                subgraph "Transformer Architecture"
                    direction LR
                    subgraph "Encoder Stack"
                        direction TB
                        Input[Input Embeddings] --> PE1[Positional Encoding]
                        PE1 --> MHA_Enc[Multi-Head Self-Attention]
                        MHA_Enc --> AddNorm_Enc1[Add & Norm]
                        AddNorm_Enc1 --> FFN_Enc[Feed Forward Network]
                        FFN_Enc --> AddNorm_Enc2[Add & Norm]
                        AddNorm_Enc2 --> Enc_Out[Encoder Output]
                    end
                    subgraph "Decoder Stack"
                        direction TB
                        Output_Prev[Previous Output Embeddings] --> PE2[Positional Encoding]
                        PE2 --> Masked_MHA_Dec[Masked Multi-Head Self-Attention]
                        Masked_MHA_Dec --> AddNorm_Dec1[Add & Norm]
                        AddNorm_Dec1 --> MHA_Cross[Multi-Head Cross-Attention]
                        Enc_Out --> MHA_Cross
                        MHA_Cross --> AddNorm_Dec2[Add & Norm]
                        AddNorm_Dec2 --> FFN_Dec[Feed Forward Network]
                        FFN_Dec --> AddNorm_Dec3[Add & Norm]
                        AddNorm_Dec3 --> Linear[Linear Layer]
                        Linear --> Softmax[Softmax]
                        Softmax --> Output_Probs[Output Probabilities]
                    end
                end
            """,
            \'reasoning_model\
obots.txt': """
            graph TD
                InputQuery[Input Query] --> KnowledgeRetriever[Knowledge Retriever]
                KnowledgeRetriever -- Fetches --> KnowledgeBase[(Knowledge Base)]
                KnowledgeRetriever --> RetrievedInfo[Retrieved Information]
                InputQuery --> LoRAAdapter[LoRA Adapter]
                RetrievedInfo --> LoRAAdapter
                LoRAAdapter --> ReasoningModule[Reasoning Module]
                ReasoningModule --> ReasonedOutput[Reasoned Output]
                subgraph "Reasoning Components"
                    LogicRules[Logic Rules]
                    InferenceEngine[Inference Engine]
                end
                ReasoningModule -. Uses .-> LogicRules
                ReasoningModule -. Employs .-> InferenceEngine
            """,
            \'mlops_pipeline\
obots.txt': """
            graph LR
                A[Data Ingestion] --> B(Data Validation)
                B --> C{Feature Engineering}
                C --> D[Model Training]
                D --> E(Model Evaluation)
                E --> F{Model Versioning}
                F --> G[Deployment]
                G --> H(Monitoring & Alerting)
                H --> I{Retraining Trigger}
                I -- Yes --> D
                I -- No --> H
            """,
            \'data_science_workflow\
obots.txt': """
            graph TD
                A[Problem Definition] --> B(Data Collection)
                B --> C{Data Cleaning & Preprocessing}
                C --> D[Exploratory Data Analysis (EDA)]
                D --> E{Feature Engineering}
                E --> F[Model Selection]
                F --> G(Model Training)
                G --> H{Model Evaluation}
                H --> I[Results Interpretation]
                I --> J(Deployment/Reporting)
            """,
            \'matryoshka_model\
obots.txt': """
            graph TD
                subgraph "Matryoshka AI Architecture"
                    CoreAI[Core AI Intelligence] --> Layer1[Platform Layer: APIs & Dev Tools]
                    Layer1 --> Layer2[Application Layer: User Apps]
                    Layer2 --> Layer3[Hardware Layer: Devices]
                    CoreAI -.-> ContextSharing[Context Sharing Fabric]
                    Layer1 -.-> ContextSharing
                    Layer2 -.-> ContextSharing
                    Layer3 -.-> ContextSharing
                end
                style CoreAI fill:#f96,stroke:#333,stroke-width:4px
                style Layer1 fill:#9cf,stroke:#333,stroke-width:2px
                style Layer2 fill:#9fc,stroke:#333,stroke-width:2px
                style Layer3 fill:#ff9,stroke:#333,stroke-width:2px
            """,
            \'guess_arena_framework\
obots.txt': """
            graph TD
                subgraph "GuessArena Framework"
                    LLM[Large Language Model] --> GameInteraction[Game-Based Interaction]
                    DomainKnowledge[Domain Knowledge Modeling] --> GameInteraction
                    GameInteraction --> ReasoningAssessment[Progressive Reasoning Assessment]
                    ReasoningAssessment --> EvaluationFidelity[Evaluation Fidelity]
                    GameInteraction -. Adversarial .-> LLM
                end
                style LLM fill:#f9f,stroke:#333,stroke-width:2px
                style DomainKnowledge fill:#9cf,stroke:#333,stroke-width:2px
                style GameInteraction fill:#9fc,stroke:#333,stroke-width:2px
                style ReasoningAssessment fill:#ff9,stroke:#333,stroke-width:2px
            """,
            \'recommendation_unlearning\
obots.txt': """
            graph TD
                subgraph "UnlearnRec Architecture"
                    UnlearningRequest[Unlearning Request] --> InfluenceEncoder[Influence Encoder]
                    ModelParams[Existing Model Parameters] --> InfluenceEncoder
                    subgraph "Influence Encoder"
                        GraphAttention[Graph Attention Module]
                        ModelUpdate[Model Update Module]
                        GraphAttention --> ModelUpdate
                    end
                    InfluenceEncoder --> UpdatedParams[Updated Model Parameters]
                    UpdatedParams --> FineTuning[Minimal Fine-Tuning]
                    FineTuning --> UnlearnedModel[Unlearned Recommender Model]
                end
                style InfluenceEncoder fill:#f96,stroke:#333,stroke-width:3px
            """,
            \'generic_flowchart\
obots.txt': """
            graph TD
                Start --> Step1[Step 1: Define Problem]
                Step1 --> Step2{Step 2: Gather Data}
                Step2 --> Step3[Step 3: Analyze Data]
                Step3 --> Step4{Step 4: Develop Solution}
                Step4 --> Step5[Step 5: Implement Solution]
                Step5 --> End[End]
            """
        }
        
    def _load_config(self):
        try:
            with open(self.config_path, \'r\
obots.txt') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def generate_image_for_post(self, content, title, category, has_equations=False, has_architecture=False):
        image_prompt, cleaned_content = self._extract_image_prompt(content)
        
        image_path = None
        # Prioritize diagram generation if architecture is mentioned or implied
        if has_architecture or any(term in title.lower() or term in image_prompt.lower() for term in [\'architecture\
obots.txt', \'model\
obots.txt', \'framework\
obots.txt', \'pipeline\
obots.txt', \'workflow\
obots.txt', \'system\
obots.txt', \'diagram\
obots.txt']):
            image_path = self._generate_diagram(image_prompt, title, category, content)
        
        # If no diagram, try equation image if relevant
        if not image_path and (has_equations or "equation" in image_prompt.lower() or "$" in content):
            image_path = self._generate_equation_image(content, image_prompt)
        
        # Fallback to AI generation or stock images
        if not image_path:
            if self.sd_api_url:
                image_path = self._generate_with_stable_diffusion(image_prompt, category)
            elif self.hf_api_url:
                image_path = self._generate_with_hugging_face(image_prompt, category)
        
        if not image_path or not os.path.exists(image_path):
            image_path = self._get_stock_image(category, image_prompt)
            
        if not image_path or not os.path.exists(image_path):
            image_path = self._create_custom_image(title, category, image_prompt)
            
        return image_path, cleaned_content
    
    def _extract_image_prompt(self, content):
        image_prompt = ""
        cleaned_lines = []
        lines = content.split(\'\n\
obots.txt')
        for line in lines:
            if line.lower().startswith("image:"):
                image_prompt = line[6:].strip()
            elif not any(phrase in line.lower() for phrase in ["image:", "image prompt", "(note:"]):
                cleaned_lines.append(line)
        cleaned_content = \'\n\
obots.txt'.join(cleaned_lines)
        if not image_prompt:
            # Basic prompt from title if no explicit prompt
            # This will be improved by the LLM in post_generator.py to be more specific
            image_prompt = f"Technical illustration related to the post content."
        return image_prompt, cleaned_content
    
    def _generate_diagram(self, prompt, title, category, post_content):
        try:
            diagram_type = self._determine_diagram_type(prompt, title, category, post_content)
            template_key = diagram_type if diagram_type in self.diagram_templates else \'generic_flowchart\
obots.txt'
            template = self.diagram_templates.get(template_key, self.diagram_templates[\'generic_flowchart\
obots.txt'])
            
            customized_template = self._customize_diagram_template(template, prompt, title, post_content, diagram_type)
            
            timestamp = datetime.now().strftime(\'%Y%m%d_%H%M%S\
obots.txt')
            safe_title = re.sub(r\'[^\w-]\[\]', \'_\
obots.txt', title.lower().replace(\' \
obots.txt', \'_\
obots.txt'))[:30]
            output_file = os.path.join(self.generated_images_dir, f"diagram_{safe_title}_{timestamp}.png")
            
            with tempfile.NamedTemporaryFile(mode=\'w\
obots.txt', suffix=\'.mmd\
obots.txt', delete=False) as temp_file:
                temp_file.write(customized_template)
                temp_file_path = temp_file.name
            
            try:
                subprocess.run(
                    [\'mmdc\
obots.txt', \'-i\
obots.txt', temp_file_path, \'-o\
obots.txt', output_file, \'-t\
obots.txt', \'forest\
obots.txt', \'-b\
obots.txt', \'transparent\
obots.txt', \'--width\
obots.txt', \'1000\
obots.txt', \'--height\
obots.txt', \'800\
obots.txt'],
                    check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                    logger.info(f"Generated diagram with Mermaid at {output_file}")
                    os.remove(temp_file_path)
                    return output_file
            except (subprocess.SubprocessError, FileNotFoundError) as e:
                logger.warning(f"Mermaid CLI failed: {e}. Output: {e.stdout if hasattr(e, \'stdout\
obots.txt') else \'N/A\
obots.txt'}, Error: {e.stderr if hasattr(e, \'stderr\
obots.txt') else \'N/A\
obots.txt'}. Trying PlantUML.")
                # Fallback to PlantUML or custom PIL diagram can be added here if needed
            finally:
                if os.path.exists(temp_file_path):
                     os.remove(temp_file_path)

            logger.warning(f"Failed to generate diagram with Mermaid for: {title}")
            return self._create_custom_diagram(diagram_type, title, prompt) # Fallback to PIL
            
        except Exception as e:
            logger.error(f"Error in _generate_diagram: {e}", exc_info=True)
            return self._create_custom_diagram(\'generic_flowchart\
obots.txt', title, prompt) # Fallback to PIL

    def _determine_diagram_type(self, prompt, title, category, post_content):
        text_corpus = f"{prompt.lower()} {title.lower()} {category.lower()} {post_content.lower()}"
        
        if any(term in text_corpus for term in [\'matryoshka\
obots.txt', \'hierarchical ai\
obots.txt', \'nested model\
obots.txt']):
            return \'matryoshka_model\
obots.txt'
        if any(term in text_corpus for term in [\'guessarena\
obots.txt', \'game-based evaluation\
obots.txt', \'adaptive framework\
obots.txt']):
            return \'guess_arena_framework\
obots.txt'
        if any(term in text_corpus for term in [\'unlearning\
obots.txt', \'recommendation unlearning\
obots.txt', \'influence encoder\
obots.txt', \'unlearnrec\
obots.txt']):
            return \'recommendation_unlearning\
obots.txt'
        if any(term in text_corpus for term in [\'transformer\
obots.txt', \'self-attention\
obots.txt', \'multi-head attention\
obots.txt', \'encoder-decoder\
obots.txt']):
            return \'transformer\
obots.txt'
        if any(term in text_corpus for term in [\'reasoning\
obots.txt', \'knowledge graph\
obots.txt', \'inference engine\
obots.txt', \'open-reasoner\
obots.txt']):
            return \'reasoning_model\
obots.txt'
        if any(term in text_corpus for term in [\'neural network\
obots.txt', \'deep learning\
obots.txt', \'hidden layer\
obots.txt', \'activation function\
obots.txt']):
            return \'neural_network\
obots.txt'
        if any(term in text_corpus for term in [\'mlops\
obots.txt', \'ci/cd pipeline\
obots.txt', \'model deployment\
obots.txt', \'monitoring\
obots.txt']):
            return \'mlops_pipeline\
obots.txt'
        if any(term in text_corpus for term in [\'data science\
obots.txt', \'data analysis\
obots.txt', \'workflow\
obots.txt', \'eda\
obots.txt', \'feature engineering\
obots.txt']):
            return \'data_science_workflow\
obots.txt'
        
        return \'generic_flowchart\
obots.txt' # Default

    def _customize_diagram_template(self, template, prompt, title, post_content, diagram_type):
        # This is a placeholder for more sophisticated template customization.
        # For now, it just returns the selected template.
        # Future improvements: Use NLP to extract entities and relationships from post_content
        # and dynamically modify the Mermaid code in the template.
        
        # Example: if diagram_type is 'transformer', try to find layer names or specific components in post_content
        # and replace generic names in the template.
        
        # Add title to the diagram if not already present in template
        if "title \"" not in template:
            escaped_title = title.replace(\'"\
obots.txt', \'\\"\
obots.txt') # Escape quotes for Mermaid title
            if "graph TD" in template or "graph LR" in template:
                template = template.replace("graph TD", f"graph TD\ntitle \"{escaped_title}\"")
                template = template.replace("graph LR", f"graph LR\ntitle \"{escaped_title}\"")
            else:
                # Add title at the beginning for other graph types if applicable
                template = f"title \"{escaped_title}\"\n{template}"
        return template

    # ... (rest of the _create_custom_diagram, _draw_... methods, _generate_equation_image, _generate_with_stable_diffusion, etc. remain largely the same for now)
    # Minor adjustments to _create_custom_diagram to use the new specific drawing functions if PIL is chosen.

    def _create_custom_diagram(self, diagram_type, title, prompt):
        try:
            timestamp = datetime.now().strftime(\'%Y%m%d_%H%M%S\
obots.txt')
            safe_title = re.sub(r\'[^\w-]\[\]', \'_\
obots.txt', title.lower().replace(\' \
obots.txt', \'_\
obots.txt'))[:30]
            output_file = os.path.join(self.generated_images_dir, f"custom_diagram_{safe_title}_{timestamp}.png")
            
            width, height = 1200, 900 # Increased height for better layout
            image = Image.new(\'RGB\
obots.txt', (width, height), color=(255, 255, 255))
            draw = ImageDraw.Draw(image)
            
            try:
                title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 36)
                node_font = ImageFont.truetype("DejaVuSans.ttf", 24)
                label_font = ImageFont.truetype("DejaVuSans.ttf", 20)
            except IOError:
                title_font = ImageFont.load_default()
                node_font = ImageFont.load_default()
                label_font = ImageFont.load_default()
            
            # Draw title for the image itself
            draw.text((width//2, 40), title, fill=(0, 0, 0), font=title_font, anchor="mm")
            
            # Call specific drawing function based on diagram_type
            if diagram_type == \'matryoshka_model\
obots.txt':
                self._draw_matryoshka_model(draw, width, height, node_font, label_font)
            elif diagram_type == \'guess_arena_framework\
obots.txt':
                self._draw_guess_arena_framework(draw, width, height, node_font, label_font)
            elif diagram_type == \'recommendation_unlearning\
obots.txt':
                self._draw_recommendation_unlearning(draw, width, height, node_font, label_font)
            elif diagram_type == \'neural_network\
obots.txt':
                self._draw_neural_network(draw, width, height, node_font, label_font)
            elif diagram_type == \'transformer\
obots.txt':
                self._draw_transformer(draw, width, height, node_font, label_font)
            elif diagram_type == \'reasoning_model\
obots.txt':
                self._draw_reasoning_model(draw, width, height, node_font, label_font)
            elif diagram_type == \'mlops_pipeline\
obots.txt':
                self._draw_mlops_pipeline(draw, width, height, node_font, label_font)
            elif diagram_type == \'data_science_workflow\
obots.txt':
                self._draw_data_science_flow(draw, width, height, node_font, label_font)
            else: # Fallback for generic or unknown types
                self._draw_generic_flowchart(draw, width, height, node_font, label_font, prompt)
            
            image.save(output_file)
            logger.info(f"Created custom PIL diagram at {output_file} for type {diagram_type}")
            return output_file
            
        except Exception as e:
            logger.error(f"Error creating custom PIL diagram: {e}", exc_info=True)
            return None

    # NEW PIL Drawing methods for specific diagrams
    def _draw_matryoshka_model(self, draw, width, height, node_font, label_font):
        core_ai = {"label": "Core AI Intelligence", "x": width/2, "y": height*0.2, "w": 300, "h": 80, "color": "#f96"}
        platform = {"label": "Platform Layer (APIs, Dev Tools)", "x": width/2, "y": height*0.4, "w": 400, "h": 70, "color": "#9cf"}
        app = {"label": "Application Layer (User Apps)", "x": width/2, "y": height*0.6, "w": 350, "h": 70, "color": "#9fc"}
        hardware = {"label": "Hardware Layer (Devices)", "x": width/2, "y": height*0.8, "w": 300, "h": 70, "color": "#ff9"}
        
        nodes = [core_ai, platform, app, hardware]
        for i in range(len(nodes) - 1):
            self._draw_arrow(draw, nodes[i]["x"], nodes[i]["y"] + nodes[i]["h"]/2, nodes[i+1]["x"], nodes[i+1]["y"] - nodes[i+1]["h"]/2)
        
        for node in nodes:
            self._draw_rounded_rect(draw, node["x"] - node["w"]/2, node["y"] - node["h"]/2, node["w"], node["h"], 10, node["color"])
            draw.text((node["x"], node["y"]), node["label"], fill=(0,0,0), font=label_font, anchor="mm")
        draw.text((width/2, height*0.95), "Matryoshka AI Architecture", fill=(0,0,0), font=node_font, anchor="mm")

    def _draw_guess_arena_framework(self, draw, width, height, node_font, label_font):
        llm = {"label": "Large Language Model (LLM)", "x": width/2, "y": height*0.2, "w": 300, "h": 70, "color": "#f9f"}
        game = {"label": "Game-Based Interaction", "x": width/2, "y": height*0.5, "w": 300, "h": 100, "color": "#9fc"}
        domain = {"label": "Domain Knowledge Modeling", "x": width*0.25, "y": height*0.5, "w": 250, "h": 70, "color": "#9cf"}
        reasoning = {"label": "Progressive Reasoning Assessment", "x": width*0.75, "y": height*0.5, "w": 300, "h": 70, "color": "#ff9"}
        fidelity = {"label": "Evaluation Fidelity", "x": width/2, "y": height*0.8, "w": 250, "h": 70, "color": "#ccc"}

        self._draw_arrow(draw, llm["x"], llm["y"] + llm["h"]/2, game["x"], game["y"] - game["h"]/2)
        self._draw_arrow(draw, domain["x"] + domain["w"]/2, domain["y"], game["x"] - game["w"]/2, game["y"])
        self._draw_arrow(draw, game["x"] + game["w"]/2, game["y"], reasoning["x"] - reasoning["w"]/2, reasoning["y"])
        self._draw_arrow(draw, reasoning["x"], reasoning["y"] + reasoning["h"]/2, fidelity["x"], fidelity["y"] - fidelity["h"]/2)
        self._draw_arrow(draw, game["x"], game["y"] - game["h"]/2, llm["x"], llm["y"] + llm["h"]/2, text="Adversarial") # Loop back

        for node in [llm, game, domain, reasoning, fidelity]:
            self._draw_rounded_rect(draw, node["x"] - node["w"]/2, node["y"] - node["h"]/2, node["w"], node["h"], 10, node["color"])
            draw.text((node["x"], node["y"]), node["label"], fill=(0,0,0), font=label_font, anchor="mm", align="center")
        draw.text((width/2, height*0.95), "GuessArena Framework", fill=(0,0,0), font=node_font, anchor="mm")

    def _draw_recommendation_unlearning(self, draw, width, height, node_font, label_font):
        req = {"label": "Unlearning Request", "x": width*0.2, "y": height*0.2, "w": 200, "h": 60, "color": "#9cf"}
        params = {"label": "Existing Model Params", "x": width*0.2, "y": height*0.4, "w": 200, "h": 60, "color": "#9cf"}
        enc = {"label": "Influence Encoder", "x": width*0.5, "y": height*0.3, "w": 250, "h": 120, "color": "#f96"}
        g_att = {"label": "Graph Attention Mod.", "x": width*0.5, "y": height*0.25, "w": 180, "h": 50, "color": "#ffc"}
        m_upd = {"label": "Model Update Mod.", "x": width*0.5, "y": height*0.35, "w": 180, "h": 50, "color": "#ffc"}
        upd_params = {"label": "Updated Params", "x": width*0.8, "y": height*0.3, "w": 200, "h": 60, "color": "#9fc"}
        fine_tune = {"label": "Minimal Fine-Tuning", "x": width*0.8, "y": height*0.5, "w": 200, "h": 60, "color": "#9fc"}
        final_model = {"label": "Unlearned Model", "x": width*0.8, "y": height*0.7, "w": 200, "h": 60, "color": "#6f6"}

        self._draw_arrow(draw, req["x"]+req["w"]/2, req["y"], enc["x"]-enc["w"]/2, enc["y"]-enc["h"]/4)
        self._draw_arrow(draw, params["x"]+params["w"]/2, params["y"], enc["x"]-enc["w"]/2, enc["y"]+enc["h"]/4)
        self._draw_arrow(draw, enc["x"]+enc["w"]/2, enc["y"], upd_params["x"]-upd_params["w"]/2, upd_params["y"])
        self._draw_arrow(draw, upd_params["x"], upd_params["y"]+upd_params["h"]/2, fine_tune["x"], fine_tune["y"]-fine_tune["h"]/2)
        self._draw_arrow(draw, fine_tune["x"], fine_tune["y"]+fine_tune["h"]/2, final_model["x"], final_model["y"]-final_model["h"]/2)
        
        # Draw main boxes
        for node in [req, params, enc, upd_params, fine_tune, final_model]:
            self._draw_rounded_rect(draw, node["x"] - node["w"]/2, node["y"] - node["h"]/2, node["w"], node["h"], 10, node["color"])
            draw.text((node["x"], node["y"]), node["label"], fill=(0,0,0), font=label_font, anchor="mm", align="center")
        
        # Draw boxes inside Influence Encoder
        for node in [g_att, m_upd]:
             self._draw_rounded_rect(draw, node["x"] - node["w"]/2, node["y"] - node["h"]/2, node["w"], node["h"], 5, node["color"], border_color="#aaa")
             draw.text((node["x"], node["y"]), node["label"], fill=(0,0,0), font=ImageFont.truetype("DejaVuSans.ttf", 18), anchor="mm", align="center")
        self._draw_arrow(draw, g_att["x"], g_att["y"]+g_att["h"]/2, m_upd["x"], m_upd["y"]-m_upd["h"]/2)

        draw.text((width/2, height*0.95), "UnlearnRec Architecture", fill=(0,0,0), font=node_font, anchor="mm")

    def _draw_generic_flowchart(self, draw, width, height, node_font, label_font, prompt):
        # Simplified generic flowchart based on prompt keywords
        keywords = re.findall(r\'\b[A-Z][a-z]+\w*\b\
obots.txt', prompt)[:5] # Extract up to 5 capitalized words as steps
        if not keywords:
            keywords = ["Start", "Process A", "Process B", "Decision", "End"]
        
        num_steps = len(keywords)
        step_h = 60
        step_w = 180
        y_center = height / 2
        total_width = num_steps * step_w + (num_steps -1) * 40
        start_x = (width - total_width) / 2 + step_w/2

        nodes = []
        for i, keyword in enumerate(keywords):
            nodes.append({"label": keyword, "x": start_x + i * (step_w + 40), "y": y_center, "w": step_w, "h": step_h, "color": "#9cf"})
        
        for i in range(len(nodes) - 1):
            self._draw_arrow(draw, nodes[i]["x"] + nodes[i]["w"]/2, nodes[i]["y"], nodes[i+1]["x"] - nodes[i+1]["w"]/2, nodes[i+1]["y"])

        for node in nodes:
            self._draw_rounded_rect(draw, node["x"] - node["w"]/2, node["y"] - node["h"]/2, node["w"], node["h"], 10, node["color"])
            draw.text((node["x"], node["y"]), node["label"], fill=(0,0,0), font=label_font, anchor="mm", align="center")
        draw.text((width/2, height*0.95), "Process Flowchart", fill=(0,0,0), font=node_font, anchor="mm")

    def _draw_rounded_rect(self, draw, x, y, w, h, r, color, border_color="#333"):
        draw.rectangle([(x+r, y), (x+w-r, y+h)], fill=color, outline=border_color)
        draw.rectangle([(x, y+r), (x+w, y+h-r)], fill=color, outline=border_color)
        draw.pieslice([(x, y), (x+2*r, y+2*r)], 180, 270, fill=color, outline=border_color)
        draw.pieslice([(x+w-2*r, y), (x+w, y+2*r)], 270, 360, fill=color, outline=border_color)
        draw.pieslice([(x, y+h-2*r), (x+2*r, y+h)], 90, 180, fill=color, outline=border_color)
        draw.pieslice([(x+w-2*r, y+h-2*r), (x+w, y+h)], 0, 90, fill=color, outline=border_color)

    def _draw_arrow(self, draw, x1, y1, x2, y2, color="#333", width=2, text=None, text_font=None):
        draw.line([(x1,y1), (x2,y2)], fill=color, width=width)
        angle = math.atan2(y2-y1, x2-x1)
        arrow_len = 15
        p1x = x2 - arrow_len * math.cos(angle - math.pi/6)
        p1y = y2 - arrow_len * math.sin(angle - math.pi/6)
        p2x = x2 - arrow_len * math.cos(angle + math.pi/6)
        p2y = y2 - arrow_len * math.sin(angle + math.pi/6)
        draw.polygon([(x2,y2), (p1x,p1y), (p2x,p2y)], fill=color)
        if text and text_font:
            mid_x = (x1+x2)/2
            mid_y = (y1+y2)/2 - 15 # Offset text above line
            draw.text((mid_x, mid_y), text, fill=color, font=text_font, anchor="mm")

    # Placeholder for _generate_equation_image, _generate_with_stable_diffusion, etc.
    # These will be refined in subsequent steps.
    def _generate_equation_image(self, content, prompt):
        logger.info("Equation image generation called, placeholder for now.")
        return self._create_custom_image(prompt, "equation", prompt) # Fallback to custom image

    def _generate_with_stable_diffusion(self, prompt, category):
        logger.info("Stable Diffusion called, placeholder for now.")
        return None # Fallback

    def _generate_with_hugging_face(self, prompt, category):
        logger.info("Hugging Face called, placeholder for now.")
        return None # Fallback

    def _get_stock_image(self, category, prompt):
        try:
            category_dir = os.path.join(self.stock_images_dir, category)
            if not os.path.exists(category_dir):
                os.makedirs(category_dir, exist_ok=True)
            
            images = [f for f in os.listdir(category_dir) if f.endswith((\'.jpg\
obots.txt', \'.jpeg\
obots.txt', \'.png\
obots.txt'))]
            if images:
                return os.path.join(category_dir, random.choice(images))
            else:
                # Create a placeholder if no stock images for this category
                placeholder_path = os.path.join(category_dir, f"{category}_stock_placeholder.png")
                self._create_custom_image(f"Stock image for {category}", category, prompt, output_path=placeholder_path)
                return placeholder_path if os.path.exists(placeholder_path) else None
        except Exception as e:
            logger.error(f"Error getting stock image: {e}")
            return None

    def _create_custom_image(self, title, category, prompt, output_path=None):
        # This is the general fallback if other methods fail or for stock placeholders
        try:
            timestamp = datetime.now().strftime(\'%Y%m%d_%H%M%S\
obots.txt')
            safe_title = re.sub(r\'[^\w-]\[\]', \'_\
obots.txt', title.lower().replace(\' \
obots.txt', \'_\
obots.txt'))[:30]
            if not output_path:
                output_file = os.path.join(self.generated_images_dir, f"custom_fallback_{safe_title}_{timestamp}.png")
            else:
                output_file = output_path

            width, height = 1000, 750
            image = Image.new(\'RGB\
obots.txt', (width, height), color=(230, 230, 250)) # Light lavender background
            draw = ImageDraw.Draw(image)
            try:
                font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 30)
                font_text = ImageFont.truetype("DejaVuSans.ttf", 22)
            except IOError:
                font_title = ImageFont.load_default()
                font_text = ImageFont.load_default()

            draw.text((width/2, 50), title, fill=(50,50,100), font=font_title, anchor="mm")
            # Wrap prompt text
            lines = []
            max_width = width - 100
            current_line = ""
            for word in prompt.split():
                if draw.textlength(current_line + word, font=font_text) <= max_width:
                    current_line += word + " "
                else:
                    lines.append(current_line.strip())
                    current_line = word + " "
            lines.append(current_line.strip())
            
            y_text = 100
            for line in lines[:5]: # Max 5 lines of prompt
                draw.text((width/2, y_text), line, fill=(70,70,120), font=font_text, anchor="mm")
                y_text += 30
            
            draw.text((width/2, height - 50), f"Category: {category.replace(\'_\
obots.txt', \' \
obots.txt').title()}", fill=(80,80,130), font=font_text, anchor="mm")
            image.save(output_file)
            logger.info(f"Created custom fallback image at {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"Error creating custom fallback image: {e}", exc_info=True)
            return None

    # Methods for drawing specific neural network, transformer, etc. for PIL fallback
    # These are simplified versions of the Mermaid diagrams for PIL rendering
    def _draw_neural_network(self, draw, width, height, node_font, label_font):
        # Simplified PIL drawing for a neural network
        layers = [ (width*0.2, 3), (width*0.45, 4), (width*0.7, 3), (width*0.9, 2) ] # x_pos, num_nodes
        node_r = 20
        for i in range(len(layers)-1):
            for n1 in range(layers[i][1]):
                y1 = height/2 - (layers[i][1]-1)*3*node_r/2 + n1*3*node_r
                for n2 in range(layers[i+1][1]):
                    y2 = height/2 - (layers[i+1][1]-1)*3*node_r/2 + n2*3*node_r
                    draw.line([(layers[i][0], y1), (layers[i+1][0], y2)], fill="#aaa", width=1)
        for x_pos, num_nodes in layers:
            for n in range(num_nodes):
                y_pos = height/2 - (num_nodes-1)*3*node_r/2 + n*3*node_r
                draw.ellipse([(x_pos-node_r, y_pos-node_r), (x_pos+node_r, y_pos+node_r)], fill="#9cf", outline="#333")
        draw.text((width/2, height*0.1), "Neural Network", fill="#000", font=node_font, anchor="mm")

    def _draw_transformer(self, draw, width, height, node_font, label_font):
        # Simplified PIL drawing for a Transformer
        enc_x, dec_x = width*0.3, width*0.7
        box_w, box_h = 150, 200
        self._draw_rounded_rect(draw, enc_x-box_w/2, height/2-box_h/2, box_w, box_h, 10, "#9fc")
        draw.text((enc_x, height/2), "Encoder", fill="#000", font=label_font, anchor="mm")
        self._draw_rounded_rect(draw, dec_x-box_w/2, height/2-box_h/2, box_w, box_h, 10, "#ff9")
        draw.text((dec_x, height/2), "Decoder", fill="#000", font=label_font, anchor="mm")
        self._draw_arrow(draw, enc_x+box_w/2, height/2, dec_x-box_w/2, height/2)
        draw.text((width/2, height*0.1), "Transformer Model", fill="#000", font=node_font, anchor="mm")

    def _draw_reasoning_model(self, draw, width, height, node_font, label_font):
        # Simplified PIL drawing for a Reasoning Model
        kq_x, adapt_x, reason_x = width*0.25, width*0.5, width*0.75
        box_w, box_h = 180, 70
        self._draw_rounded_rect(draw, kq_x-box_w/2, height*0.4-box_h/2, box_w, box_h, 10, "#9cf")
        draw.text((kq_x, height*0.4), "Knowledge Query", fill="#000", font=label_font, anchor="mm")
        self._draw_rounded_rect(draw, adapt_x-box_w/2, height*0.4-box_h/2, box_w, box_h, 10, "#f9c")
        draw.text((adapt_x, height*0.4), "Adapter", fill="#000", font=label_font, anchor="mm")
        self._draw_rounded_rect(draw, reason_x-box_w/2, height*0.4-box_h/2, box_w, box_h, 10, "#9fc")
        draw.text((reason_x, height*0.4), "Reasoning Engine", fill="#000", font=label_font, anchor="mm")
        self._draw_arrow(draw, kq_x+box_w/2, height*0.4, adapt_x-box_w/2, height*0.4)
        self._draw_arrow(draw, adapt_x+box_w/2, height*0.4, reason_x-box_w/2, height*0.4)
        draw.text((width/2, height*0.1), "Reasoning Architecture", fill="#000", font=node_font, anchor="mm")

    def _draw_mlops_pipeline(self, draw, width, height, node_font, label_font):
        # Simplified MLOps pipeline
        steps = ["Data", "Train", "Deploy", "Monitor"]
        step_w, step_h = 120, 60
        total_w = len(steps)*step_w + (len(steps)-1)*30
        start_x = (width-total_w)/2 + step_w/2
        for i, step in enumerate(steps):
            x = start_x + i*(step_w+30)
            self._draw_rounded_rect(draw, x-step_w/2, height/2-step_h/2, step_w, step_h, 10, "#ff9")
            draw.text((x, height/2), step, fill="#000", font=label_font, anchor="mm")
            if i > 0:
                prev_x = start_x + (i-1)*(step_w+30)
                self._draw_arrow(draw, prev_x+step_w/2, height/2, x-step_w/2, height/2)
        draw.text((width/2, height*0.1), "MLOps Pipeline", fill="#000", font=node_font, anchor="mm")

    def _draw_data_science_flow(self, draw, width, height, node_font, label_font):
        # Simplified Data Science Workflow
        steps = ["Define", "Collect", "Clean", "Analyze", "Model", "Deploy"]
        step_w, step_h = 100, 60
        total_w = len(steps)*step_w + (len(steps)-1)*20
        start_x = (width-total_w)/2 + step_w/2
        for i, step in enumerate(steps):
            x = start_x + i*(step_w+20)
            self._draw_rounded_rect(draw, x-step_w/2, height/2-step_h/2, step_w, step_h, 10, "#9f9")
            draw.text((x, height/2), step, fill="#000", font=label_font, anchor="mm")
            if i > 0:
                prev_x = start_x + (i-1)*(step_w+20)
                self._draw_arrow(draw, prev_x+step_w/2, height/2, x-step_w/2, height/2)
        draw.text((width/2, height*0.1), "Data Science Workflow", fill="#000", font=node_font, anchor="mm")

if __name__ == "__main__":
    generator = ImageGenerator()
    # Test Matryoshka
    image_path, _ = generator.generate_image_for_post(
        "Post about Google\'s AI Matryoshka. Image: A hierarchical diagram of the Matryoshka AI architecture.",
        "Google\'s AI Matryoshka Explained",
        "ai",
        has_architecture=True
    )
    print(f"Generated Matryoshka image: {image_path}")

    # Test GuessArena
    image_path, _ = generator.generate_image_for_post(
        "Evaluating LLMs with GuessArena. Image: Framework diagram of GuessArena showing LLM, Domain Knowledge, Game Interaction, and Reasoning Assessment.",
        "GuessArena Framework for LLM Evaluation",
        "ai",
        has_architecture=True
    )
    print(f"Generated GuessArena image: {image_path}")

    # Test UnlearnRec
    image_path, _ = generator.generate_image_for_post(
        "Pre-training for Recommendation Unlearning with UnlearnRec. Image: Architecture of UnlearnRec with Influence Encoder.",
        "UnlearnRec: Recommendation Unlearning",
        "machine_learning",
        has_architecture=True
    )
    print(f"Generated UnlearnRec image: {image_path}")
