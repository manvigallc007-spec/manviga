# Instagram Rendering Setup Guide

This guide explains how to set up and run the PNG image and MP4 video rendering for Instagram posts.

## Prerequisites

### 1. Python Pillow (for PNG generation)
Already in `requirements.txt`. Install with:
```bash
pip install Pillow==10.0.0
```

### 2. FFmpeg (for MP4 video generation)
FFmpeg is required to convert PNG images to MP4 videos.

#### Windows Installation

**Option A: Using Chocolatey (Recommended)**
```bash
choco install ffmpeg
```

**Option B: Using Scoop**
```bash
scoop install ffmpeg
```

**Option C: Manual Download**
1. Visit https://ffmpeg.org/download.html
2. Download Windows build
3. Extract to a folder (e.g., `C:\ffmpeg`)
4. Add to system PATH:
   - Press `Win + X` → "System"
   - Click "Advanced system settings"
   - Click "Environment Variables"
   - Under "System variables", select "Path" → Edit
   - Add: `C:\ffmpeg\bin`
   - Click OK and restart terminal

**Verify Installation:**
```bash
ffmpeg -version
```

## Complete Workflow

### Step 1: Install Dependencies
```bash
cd c:\Users\sport\Manviga\instagram-posting
pip install -r requirements.txt
```

### Step 2: Generate Story Content
Creates 10 geo-balanced stories (3 USA, 3 India, 2 China, 2 ROW):
```bash
python src/generate.py
```

**Output**: `output/generated_stories_YYYYMMDD_HHMMSS.json`

### Step 3: Render PNG Images and MP4 Videos
Converts stories to visual content:
```bash
python src/render.py
```

**Output**:
- PNG files: `output/post_usa_1.png`, `output/post_india_1.png`, etc. (1080x1920px)
- MP4 files: `output/reel_usa_1.mp4`, `output/reel_india_1.mp4`, etc. (3 seconds each)
- Manifest: `output/rendering_manifest_YYYYMMDD_HHMMSS.json`

### Step 4: Post to Instagram
Uploads rendered content to Instagram:
```bash
python src/poster.py
```

**Output**: `output/instagram_posts_YYYYMMDD_HHMMSS.json` with Post IDs

## Quick Start Script

Run the complete workflow in one go:
```bash
cd c:\Users\sport\Manviga\instagram-posting

echo "Step 1: Generate stories..."
python src/generate.py

echo "Step 2: Render PNG and MP4..."
python src/render.py

echo "Step 3: Post to Instagram..."
python src/poster.py

echo "All done!"
```

## PNG Image Specifications

- **Resolution**: 1080x1920px (Instagram Reels standard)
- **Color Scheme**: 
  - USA: Blue (#0066CC)
  - India: Orange (#FF6B35)
  - China: Crimson (#DC143C)
  - Rest of World: Green (#00A86B)
- **Content**: Region, headline, preview, source
- **Format**: PNG

## MP4 Video Specifications

- **Codec**: H.264 (libx264)
- **Resolution**: 1080x1920px
- **Duration**: 3 seconds per video
- **Frame Rate**: 30fps (default)
- **Pixel Format**: YUV420p (compatible with Instagram)
- **Preset**: Medium quality

## Rendered Files Location

All files stored in `instagram-posting/output/`:
```
output/
├── post_usa_1.png
├── post_usa_2.png
├── post_usa_3.png
├── post_india_1.png
├── post_india_2.png
├── post_india_3.png
├── post_china_1.png
├── post_china_2.png
├── post_row_1.png
├── post_row_2.png
├── reel_usa_1.mp4
├── reel_usa_2.mp4
├── reel_usa_3.mp4
├── reel_india_1.mp4
├── reel_india_2.mp4
├── reel_india_3.mp4
├── reel_china_1.mp4
├── reel_china_2.mp4
├── reel_row_1.mp4
├── reel_row_2.mp4
├── rendering_manifest_YYYYMMDD_HHMMSS.json
└── ...
```

## Logs

Rendering logs stored in `instagram-posting/logs/`:
- `rendering_YYYYMMDD_HHMMSS.log` - Complete rendering activity log

## Troubleshooting

### FFmpeg Not Found
```
Error: FFmpeg not installed
```
**Solution**: Install FFmpeg following the instructions above, then restart terminal.

### Pillow ImportError
```
ModuleNotFoundError: No module named 'PIL'
```
**Solution**: 
```bash
pip install Pillow==10.0.0
```

### Image File Too Large
If PNG files are very large, FFmpeg will take longer to convert. This is normal.

### MP4 Not Created
If step 3 shows "Skipping MP4 creation - FFmpeg not available":
1. Verify FFmpeg is installed: `ffmpeg -version`
2. Check if FFmpeg is in system PATH
3. Restart terminal after adding to PATH

### Different Image Output
Pillow's font rendering may vary by system. Install TrueType fonts if desired.

## Production Tips

- **Batch Processing**: Render multiple story batches in sequence
- **Storage**: Keep output files for archive/analytics
- **Monitoring**: Review rendering logs for any issues
- **Fallback**: PNG files are created even if MP4 conversion fails
- **Performance**: MP4 rendering takes ~5-10 seconds per video

## Performance

Typical rendering times:
- PNG generation: ~2 seconds per image (10 images = ~20 seconds)
- MP4 conversion: ~5-10 seconds per video (10 videos = ~50-100 seconds)
- **Total**: ~1-2 minutes for 10 complete stories

## Next Steps

After rendering:
1. Review generated PNG and MP4 files
2. Run poster.py to upload to Instagram
3. Configure 2-hour schedule in `SCHEDULE_SETUP.md`
4. Monitor logs for quality and performance
