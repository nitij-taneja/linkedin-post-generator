#!/usr/bin/env python3
"""
Equation Generator Module for LinkedIn Post Generator
Creates high-quality equation images and LaTeX code for LinkedIn posts.
"""

import os
import re
import logging
import tempfile
import subprocess
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
from matplotlib import rc
rc('text', usetex=True)  # Enable LaTeX rendering

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EquationGenerator:
    """Class to generate equation images and LaTeX code for LinkedIn posts."""
    
    def __init__(self, output_dir=None):
        """
        Initialize the EquationGenerator.
        
        Args:
            output_dir (str, optional): Directory to save equation images.
                If None, uses default directory.
        """
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.output_dir = output_dir or os.path.join(self.base_dir, 'assets', 'equations')
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Check if LaTeX is installed
        self.has_latex = self._check_latex_installed()
        if not self.has_latex:
            logger.warning("LaTeX not found. Will use matplotlib for equation rendering.")
    
    def _check_latex_installed(self):
        """Check if LaTeX is installed on the system."""
        try:
            subprocess.run(['pdflatex', '--version'], 
                          stdout=subprocess.PIPE, 
                          stderr=subprocess.PIPE, 
                          check=False)
            return True
        except FileNotFoundError:
            return False
    
    def extract_equations(self, content):
        """
        Extract LaTeX equations from post content.
        
        Args:
            content (str): Post content with LaTeX equations.
            
        Returns:
            tuple: (cleaned_content, equations_dict)
                - cleaned_content: Content with equation placeholders
                - equations_dict: Dictionary mapping placeholders to equations
        """
        # Extract inline equations $...$
        inline_pattern = r'\$([^$]+)\$'
        inline_equations = re.findall(inline_pattern, content)
        
        # Extract block equations $$...$$
        block_pattern = r'\$\$([^$]+)\$\$'
        block_equations = re.findall(block_pattern, content)
        
        # Create a dictionary to store equations and their placeholders
        equations_dict = {}
        cleaned_content = content
        
        # Replace inline equations with placeholders
        for i, eq in enumerate(inline_equations):
            placeholder = f"[EQUATION_INLINE_{i}]"
            equations_dict[placeholder] = {'type': 'inline', 'latex': eq}
            cleaned_content = cleaned_content.replace(f"${eq}$", placeholder, 1)
        
        # Replace block equations with placeholders
        for i, eq in enumerate(block_equations):
            placeholder = f"[EQUATION_BLOCK_{i}]"
            equations_dict[placeholder] = {'type': 'block', 'latex': eq}
            cleaned_content = cleaned_content.replace(f"$${eq}$$", placeholder, 1)
        
        return cleaned_content, equations_dict
    
    def generate_equation_images(self, equations_dict):
        """
        Generate images for all equations in the dictionary.
        
        Args:
            equations_dict (dict): Dictionary mapping placeholders to equations.
            
        Returns:
            dict: Updated dictionary with image paths added.
        """
        for placeholder, eq_info in equations_dict.items():
            latex = eq_info['latex']
            eq_type = eq_info['type']
            
            # Generate image
            image_path = self._generate_equation_image(latex, eq_type)
            
            if image_path:
                eq_info['image_path'] = image_path
            else:
                logger.warning(f"Failed to generate image for equation: {latex}")
        
        return equations_dict
    
    def _generate_equation_image(self, latex, eq_type):
        """
        Generate an image for a LaTeX equation.
        
        Args:
            latex (str): LaTeX equation string.
            eq_type (str): 'inline' or 'block'.
            
        Returns:
            str: Path to the generated image, or None if failed.
        """
        try:
            # Clean the LaTeX string for filename
            safe_name = re.sub(r'[^\w]', '_', latex)[:30]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = os.path.join(self.output_dir, f"eq_{safe_name}_{timestamp}.png")
            
            # Try using matplotlib (works without LaTeX installation)
            fig = plt.figure(figsize=(10, 2) if eq_type == 'inline' else (10, 3))
            plt.axis('off')
            plt.tight_layout()
            
            # Add $ or $$ back for matplotlib rendering
            if eq_type == 'inline':
                render_latex = f"${latex}$"
            else:
                render_latex = f"$${latex}$$"
            
            plt.text(0.5, 0.5, render_latex, 
                    size=18 if eq_type == 'inline' else 22,
                    ha='center', va='center')
            
            plt.savefig(output_file, bbox_inches='tight', pad_inches=0.1, dpi=200, transparent=True)
            plt.close(fig)
            
            # Check if the image was created successfully
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                logger.info(f"Generated equation image at {output_file}")
                return output_file
            else:
                logger.warning(f"Failed to generate equation image with matplotlib")
                return self._create_fallback_equation_image(latex, eq_type)
        
        except Exception as e:
            logger.error(f"Error generating equation image: {e}", exc_info=True)
            return self._create_fallback_equation_image(latex, eq_type)
    
    def _create_fallback_equation_image(self, latex, eq_type):
        """
        Create a fallback image for an equation using PIL.
        
        Args:
            latex (str): LaTeX equation string.
            eq_type (str): 'inline' or 'block'.
            
        Returns:
            str: Path to the generated image, or None if failed.
        """
        try:
            # Clean the LaTeX string for filename
            safe_name = re.sub(r'[^\w]', '_', latex)[:30]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = os.path.join(self.output_dir, f"eq_fallback_{safe_name}_{timestamp}.png")
            
            # Create a simple image with the LaTeX code
            width = 800
            height = 150 if eq_type == 'inline' else 250
            image = Image.new('RGB', (width, height), color=(255, 255, 255))
            draw = ImageDraw.Draw(image)
            
            try:
                font = ImageFont.truetype("DejaVuSans.ttf", 24)
                title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 28)
            except IOError:
                font = ImageFont.load_default()
                title_font = ImageFont.load_default()
            
            # Draw title
            draw.text((width/2, 30), "LaTeX Equation", fill=(0, 0, 0), font=title_font, anchor="mm")
            
            # Draw the LaTeX code
            draw.text((width/2, height/2), latex, fill=(0, 0, 0), font=font, anchor="mm")
            
            # Draw instructions
            draw.text((width/2, height-30), "Copy the LaTeX code above to use in your post", 
                     fill=(100, 100, 100), font=font, anchor="mm")
            
            image.save(output_file)
            logger.info(f"Created fallback equation image at {output_file}")
            return output_file
        
        except Exception as e:
            logger.error(f"Error creating fallback equation image: {e}", exc_info=True)
            return None
    
    def replace_equations_with_images_and_latex(self, content, equations_dict):
        """
        Replace equation placeholders with image references and LaTeX code.
        
        Args:
            content (str): Content with equation placeholders.
            equations_dict (dict): Dictionary mapping placeholders to equations with image paths.
            
        Returns:
            str: Content with equations replaced by image references and LaTeX code.
        """
        result = content
        
        for placeholder, eq_info in equations_dict.items():
            latex = eq_info['latex']
            eq_type = eq_info['type']
            image_path = eq_info.get('image_path')
            
            if image_path:
                # Format for LinkedIn: Image reference + LaTeX code
                if eq_type == 'inline':
                    replacement = f"[Equation: ${latex}$]"
                else:
                    replacement = f"\n\n[Equation: ${latex}$]\n\n"
                
                result = result.replace(placeholder, replacement)
            else:
                # Fallback to original LaTeX if image generation failed
                if eq_type == 'inline':
                    result = result.replace(placeholder, f"${latex}$")
                else:
                    result = result.replace(placeholder, f"$${latex}$$")
        
        return result
    
    def process_content_with_equations(self, content):
        """
        Process content to handle equations properly for LinkedIn.
        
        Args:
            content (str): Original post content with LaTeX equations.
            
        Returns:
            tuple: (processed_content, equation_images)
                - processed_content: Content with equations formatted for LinkedIn
                - equation_images: List of paths to equation images
        """
        # Extract equations
        cleaned_content, equations_dict = self.extract_equations(content)
        
        # Generate images for equations
        equations_dict = self.generate_equation_images(equations_dict)
        
        # Replace placeholders with formatted equations
        processed_content = self.replace_equations_with_images_and_latex(cleaned_content, equations_dict)
        
        # Collect image paths
        equation_images = [eq_info['image_path'] for eq_info in equations_dict.values() 
                          if 'image_path' in eq_info]
        
        return processed_content, equation_images
    
    def create_equation_reference_guide(self, equations_dict):
        """
        Create a reference guide for equations in the post.
        
        Args:
            equations_dict (dict): Dictionary of equations.
            
        Returns:
            str: Path to the reference guide image.
        """
        if not equations_dict:
            return None
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = os.path.join(self.output_dir, f"equation_reference_{timestamp}.png")
            
            # Count equations
            num_equations = len(equations_dict)
            
            # Create image
            width = 800
            height = 150 + num_equations * 100
            image = Image.new('RGB', (width, height), color=(255, 255, 255))
            draw = ImageDraw.Draw(image)
            
            try:
                title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 28)
                font = ImageFont.truetype("DejaVuSans.ttf", 20)
                code_font = ImageFont.truetype("DejaVuSansMono.ttf", 18)
            except IOError:
                title_font = ImageFont.load_default()
                font = ImageFont.load_default()
                code_font = ImageFont.load_default()
            
            # Draw title
            draw.text((width/2, 40), "Equation Reference Guide", fill=(0, 0, 0), font=title_font, anchor="mm")
            draw.text((width/2, 80), "Copy these LaTeX equations for your own posts", 
                     fill=(80, 80, 80), font=font, anchor="mm")
            
            # Draw each equation and its LaTeX code
            y_pos = 150
            for i, (placeholder, eq_info) in enumerate(equations_dict.items()):
                latex = eq_info['latex']
                eq_type = eq_info['type']
                
                # Draw equation number
                draw.text((50, y_pos), f"Equation {i+1}:", fill=(0, 0, 0), font=font)
                
                # Draw LaTeX code
                draw.text((50, y_pos + 30), f"LaTeX: ${latex}$", fill=(50, 50, 150), font=code_font)
                
                # Draw separator
                draw.line([(50, y_pos + 70), (width - 50, y_pos + 70)], fill=(200, 200, 200), width=1)
                
                y_pos += 100
            
            image.save(output_file)
            logger.info(f"Created equation reference guide at {output_file}")
            return output_file
        
        except Exception as e:
            logger.error(f"Error creating equation reference guide: {e}", exc_info=True)
            return None

if __name__ == "__main__":
    # Test the equation generator
    generator = EquationGenerator()
    
    # Test content with equations
    test_content = """
    # Understanding Neural Networks
    
    Neural networks use the following activation function:
    
    $$\\sigma(x) = \\frac{1}{1 + e^{-x}}$$
    
    The weight update rule is $w_{t+1} = w_t - \\alpha \\nabla J(w_t)$ where $\\alpha$ is the learning rate.
    
    The loss function is defined as:
    
    $$J(\\theta) = -\\frac{1}{m} \\sum_{i=1}^{m} [y^{(i)} \\log(h_\\theta(x^{(i)})) + (1-y^{(i)}) \\log(1-h_\\theta(x^{(i)}))]$$
    """
    
    processed_content, equation_images = generator.process_content_with_equations(test_content)
    print("Processed content:")
    print(processed_content)
    print("\nEquation images:")
    for img in equation_images:
        print(img)
