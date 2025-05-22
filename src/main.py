import os
import sys
import json
import logging
import argparse
from datetime import datetime, timedelta
import shutil

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.email_fetcher import EmailFetcher
from src.research_fetcher import ResearchFetcher
from src.post_generator import PostGenerator
from src.telegram_delivery import TelegramDelivery

def cleanup_old_posts(directory, days_old=20):
    cutoff = datetime.now() - timedelta(days=days_old)
    deleted = 0
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            path = os.path.join(directory, filename)
            if os.path.isfile(path):
                created = datetime.fromtimestamp(os.path.getctime(path))
                if created < cutoff:
                    os.remove(path)
                    deleted += 1
    logger.info(f"Cleaned up {deleted} old post files from {directory}")

def strip_markdown(text):
    return text.replace('**', '').replace('__', '')

def save_posts_to_github(posts, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    analytics_dir = os.path.join(output_dir, '../analytics')
    images_dir = os.path.join(output_dir, '../images')
    os.makedirs(analytics_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)
    saved_files = []

    for i, post in enumerate(posts):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        md_file = f"post_{timestamp}_{i+1}.md"
        md_path = os.path.join(output_dir, md_file)

        try:
            clean_content = strip_markdown(post['content'])
            
            # Handle image if present
            image_path = post.get('image_path')
            image_filename = None
            if image_path and os.path.exists(image_path):
                image_filename = f"image_{timestamp}_{i+1}{os.path.splitext(image_path)[1]}"
                image_dest = os.path.join(images_dir, image_filename)
                shutil.copy(image_path, image_dest)
                logger.info(f"Copied image to {image_dest}")

            with open(md_path, 'w') as f:
                f.write(f"# LinkedIn Post Draft {i+1}\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"Source: {post['source_type']} - {post['source_title']}\n\n")
                
                # Add image reference if available
                if image_filename:
                    relative_path = f"../images/{image_filename}"
                    f.write(f"![Post Image]({relative_path})\n\n")
                
                f.write("## Content\n\n")
                f.write(clean_content)
                f.write("\n\n")
                if post['source_link']:
                    f.write(f"Original source: {post['source_link']}\n")

            analytics = {
                'timestamp': datetime.now().isoformat(),
                'source_type': post['source_type'],
                'source_title': post['source_title'],
                'source_link': post.get('source_link', ''),
                'hashtags': post.get('hashtags', []),
                'content_length': len(clean_content),
                'has_image': image_filename is not None,
                'image_path': f"../images/{image_filename}" if image_filename else None,
                'mentions': ['Avi Chawla', 'Akshay Pachaar'] if 'avi' in post['source_title'].lower() else [],
                'formatting': {
                    'emojis': True,
                    'bullets': '-' in clean_content
                }
            }
            json_path = os.path.join(analytics_dir, f"analytics_{timestamp}_{i+1}.json")
            with open(json_path, 'w') as jf:
                json.dump(analytics, jf, indent=2)

            saved_files.append(md_path)
            logger.info(f"Saved post to {md_path} and analytics to {json_path}")

        except Exception as e:
            logger.error(f"Error saving post: {e}")
    return saved_files

def setup_assets_directories():
    """Set up necessary directories for assets and stock images"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assets_dir = os.path.join(base_dir, 'assets')
    stock_images_dir = os.path.join(assets_dir, 'stock_images')
    generated_images_dir = os.path.join(assets_dir, 'generated_images')
    
    # Create directories if they don't exist
    for directory in [assets_dir, stock_images_dir, generated_images_dir]:
        os.makedirs(directory, exist_ok=True)
    
    # Create category subdirectories
    for category in ['technology', 'business', 'data_science', 'ai', 'machine_learning']:
        os.makedirs(os.path.join(stock_images_dir, category), exist_ok=True)
    
    logger.info(f"Set up asset directories at {assets_dir}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str)
    parser.add_argument('--output-dir', type=str, default='posts')
    parser.add_argument('--skip-email', action='store_true')
    parser.add_argument('--skip-telegram', action='store_true')
    parser.add_argument('--emails-only', action='store_true')
    parser.add_argument('--skip-images', action='store_true')
    args = parser.parse_args()

    config_path = args.config or os.path.join(os.path.dirname(__file__), '../config/sources.json')
    output_dir = os.path.abspath(args.output_dir)

    logger.info(f"Starting LinkedIn Post Generator with config: {config_path}")
    cleanup_old_posts(output_dir)
    setup_assets_directories()

    try:
        if not os.environ.get('GROQ_API_KEY'):
            logger.error("GROQ_API_KEY not set")
            return 1

        if not args.skip_telegram and (not os.environ.get('TELEGRAM_BOT_TOKEN') or not os.environ.get('TELEGRAM_CHAT_ID')):
            logger.warning("Telegram credentials not set, skipping Telegram delivery")
            args.skip_telegram = True

        email_fetcher = EmailFetcher(config_path)
        research_fetcher = ResearchFetcher(config_path)
        post_generator = PostGenerator(config_path)

        email_data = []
        if not args.skip_email:
            if os.environ.get('EMAIL_USERNAME') and os.environ.get('EMAIL_PASSWORD'):
                email_data = email_fetcher.fetch_emails(
                    os.environ['EMAIL_USERNAME'],
                    os.environ['EMAIL_PASSWORD']
                )
            else:
                logger.warning("Email credentials not set")

        research_data = {}
        if not args.emails_only:
            research_data = research_fetcher.fetch_all_research()
        else:
            logger.info("Skipping research sources — generating email-only posts")

        # Only 1 post per run
        posts = post_generator.generate_posts(email_data, research_data)
        posts = posts[:1]

        if not posts:
            logger.warning("No posts generated")
            return 0

        saved_files = save_posts_to_github(posts, output_dir)

        if not args.skip_telegram:
            telegram_delivery = TelegramDelivery(config_path)
            telegram_delivery.deliver_posts(posts)

        return 0

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
