import os
import json
import sys
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load project configuration
PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

OUTPUT_DIR = PROJECT_ROOT / "output"
LOG_DIR = PROJECT_ROOT / "logs"
CONFIG_DIR = PROJECT_ROOT / "config"

# Setup logging
LOG_FILE = LOG_DIR / f"rendering_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import rendering libraries
try:
    from PIL import Image, ImageDraw, ImageFont
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    logger.warning("Pillow not installed. Install with: pip install pillow")

try:
    import subprocess
    FFMPEG_AVAILABLE = subprocess.run(["ffmpeg", "-version"], capture_output=True).returncode == 0
except:
    FFMPEG_AVAILABLE = False
    logger.warning("FFmpeg not installed. Install from: https://ffmpeg.org/download.html")

logger.info("=" * 70)
logger.info("INSTAGRAM CONTENT RENDERING STARTED")
logger.info("=" * 70)

# Find the most recent generated stories file
story_files = sorted(OUTPUT_DIR.glob("generated_stories_*.json"), reverse=True)

if not story_files:
    logger.error("No generated stories found. Run generate.py first.")
    sys.exit(1)

latest_story_file = story_files[0]
logger.info(f"Loading stories from: {latest_story_file}")

with open(latest_story_file) as f:
    stories = json.load(f)

logger.info(f"Found {len(stories)} stories to render")

# ============================================================================
# PNG IMAGE GENERATION
# ============================================================================

def create_instagram_image(story_data, filename):
    """Create a 1080x1920px Instagram reel cover image"""
    if not PILLOW_AVAILABLE:
        logger.warning(f"Skipping PNG creation - Pillow not available")
        return False
    
    try:
        # Create image (1080x1920px for Instagram Reels)
        width, height = 1080, 1920
        
        # Color scheme by region
        region_colors = {
            "USA": "#0066CC",           # Blue
            "India": "#FF6B35",         # Orange
            "China": "#DC143C",         # Crimson
            "Rest of World": "#00A86B"  # Green
        }
        
        bg_color = region_colors.get(story_data["region"], "#333333")
        # Convert hex to RGB
        bg_color = tuple(int(bg_color[i:i+2], 16) for i in (1, 3, 5))
        
        # Create image
        img = Image.new('RGB', (width, height), bg_color)
        draw = ImageDraw.Draw(img)
        
        # Try to use a nice font, fall back to default
        try:
            title_font = ImageFont.truetype("arial.ttf", 60)
            text_font = ImageFont.truetype("arial.ttf", 40)
            small_font = ImageFont.truetype("arial.ttf", 30)
        except:
            title_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Add region label at top
        region_y = 50
        draw.text((540, region_y), story_data["region"], fill=(255, 255, 255), font=title_font, anchor="mm")
        
        # Add headline (wrapped)
        headline_y = 400
        headline = story_data["headline"]
        # Simple text wrapping
        words = headline.split()
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            if len(" ".join(current_line)) > 30:
                lines.append(" ".join(current_line[:-1]))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))
        
        line_height = 100
        for i, line in enumerate(lines[:4]):  # Max 4 lines
            draw.text((540, headline_y + i * line_height), line, fill=(255, 255, 255), font=text_font, anchor="mm")
        
        # Add content preview at bottom
        content_preview = story_data["content"][:100] + "..."
        draw.text((540, 1700), content_preview, fill=(200, 200, 200), font=small_font, anchor="mm")
        
        # Add source at very bottom
        draw.text((540, 1850), story_data["source"], fill=(150, 150, 150), font=small_font, anchor="mm")
        
        # Save image
        img_path = OUTPUT_DIR / filename
        img.save(img_path)
        logger.info(f"   PNG created: {filename}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating PNG: {e}")
        return False

# ============================================================================
# MP4 VIDEO GENERATION
# ============================================================================

def create_instagram_video(image_path, video_filename, duration=3):
    """Create MP4 video from image using FFmpeg"""
    if not FFMPEG_AVAILABLE:
        logger.warning(f"Skipping MP4 creation - FFmpeg not available")
        return False
    
    try:
        video_path = OUTPUT_DIR / video_filename
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output file
            "-loop", "1",
            "-i", str(image_path),
            "-c:v", "libx264",
            "-preset", "medium",
            "-t", str(duration),
            "-pix_fmt", "yuv420p",
            str(video_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"   MP4 created: {video_filename}")
            return True
        else:
            logger.error(f"FFmpeg error: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error creating MP4: {e}")
        return False

# ============================================================================
# RENDER ALL STORIES
# ============================================================================

rendered_count = 0
png_files = []
mp4_files = []

for idx, story in enumerate(stories, 1):
    region = story["region"].lower().replace(" ", "_")
    story_num = idx
    
    # Generate filenames
    png_filename = f"post_{region}_{story_num}.png"
    mp4_filename = f"reel_{region}_{story_num}.mp4"
    
    logger.info(f"[{idx}/{len(stories)}] Rendering {story['region']} story...")
    
    # Create PNG
    if create_instagram_image(story, png_filename):
        png_files.append(png_filename)
        
        # Create MP4 from PNG
        if create_instagram_video(OUTPUT_DIR / png_filename, mp4_filename, duration=3):
            mp4_files.append(mp4_filename)
            rendered_count += 1
        else:
            logger.warning(f"   Failed to create MP4 for {png_filename}")
    else:
        logger.warning(f"   Failed to create PNG for story {idx}")

logger.info("=" * 70)
logger.info(f"Rendering complete!")
logger.info(f"  - PNG files created: {len(png_files)}")
logger.info(f"  - MP4 files created: {len(mp4_files)}")
logger.info(f"  - Total rendered: {rendered_count}/{len(stories)}")
logger.info(f"  - Stored in: {OUTPUT_DIR}")
logger.info("=" * 70)

# Save rendering manifest
manifest = {
    "timestamp": datetime.now().isoformat(),
    "total_stories": len(stories),
    "rendered_stories": rendered_count,
    "png_files": png_files,
    "mp4_files": mp4_files,
    "output_directory": str(OUTPUT_DIR)
}

manifest_file = OUTPUT_DIR / f"rendering_manifest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(manifest_file, "w") as f:
    json.dump(manifest, f, indent=2)

logger.info(f"Rendering manifest saved: {manifest_file.name}")

print(json.dumps({
    "status": "success" if rendered_count == len(stories) else "partial",
    "rendered": rendered_count,
    "total": len(stories),
    "png_files": png_files,
    "mp4_files": mp4_files
}, indent=2))
