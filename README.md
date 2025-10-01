# Douyin Product Video Finder

Find all videos containing a specific product in their thumbnails using AI-powered image comparison.

## Features

- ✅ Auto-scrolls Douyin pages to load all videos
- ✅ Extracts video thumbnails and URLs
- ✅ **Parallel processing** - Analyzes 50 videos simultaneously
- ✅ Uses Google Gemini 2.5 Flash AI for precise product matching
- ✅ Exports matching videos to `Matches/` folder (new file per run)
- ✅ **Organized research** - Saves non-matches by user ID to `Research/` folder
- ✅ **Overwrite strategy** - Latest data replaces old for each user
- ✅ Chrome cookie support to bypass login
- ✅ 30-minute time limit with progress tracking
- ✅ **~50x faster** than sequential processing

## Installation

1. Install Python dependencies:
```bash
pip3 install -r requirements.txt
```

2. Install Playwright browser:
```bash
python3 -m playwright install chromium
```

3. Set up your Gemini API key (optional - will prompt if not set):
```bash
# Create .env file
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

## Usage

1. **Place your reference product image** in the project directory and name it `ref.png`

2. **Run the script**:
```bash
python3 find_product_videos.py
```

The script will ask you for:
1. **Douyin page URL** - The user page or feed to search
2. **Output CSV filename** - Where to save results (default: `matching_videos.csv`)

## Example

```bash
# First, place your product image as ref.png
cp /path/to/your/product.jpg ref.png

# Then run the script
python3 find_product_videos.py

✅ Found reference image: ref.png
🌐 Enter Douyin page URL: https://www.douyin.com/user/MS4wLjABAAAA...
💾 Output CSV filename (press Enter for 'matching_videos.csv'): 
```

## Output

The script generates **two CSV files** per run:

### 1. Matches (saved to `Matches/` folder)
- Creates a **new file** for each run (e.g., `Matches/Neckadele.csv`)
- Contains only videos that match your product
- Columns: `video_url`, `thumbnail_url`, `index`

### 2. Research (saved to `Research/` folder)
- Saves non-matches to `Research/{user_id}.csv`
- **Overwrites** previous data for same user (not accumulative)
- Prevents 10k+ line files - each user has separate file
- Same structure: `video_url`, `thumbnail_url`, `index`
- Includes source page URLs in header comments

## Configuration

Edit `find_product_videos.py` to adjust:
- **Batch size**: Line 327 - Process N videos in parallel (default: 10)
- **Max workers**: Line 330 - Number of concurrent threads (default: 10)
- **Headless mode**: Change `headless=False` to `headless=True` in browser launch
- **Time limit**: Default is 30 minutes for scrolling
- **Scroll pause**: Delay between scrolls (default: 2 seconds)

## Tech Stack

- **Playwright** - Browser automation and scrolling
- **Google Gemini Flash** - AI image comparison
- **Pillow (PIL)** - Image processing
- **Requests** - Thumbnail downloading

## File Directory

- `find_product_videos.py` - Main script
- `requirements.txt` - Python dependencies
- `README.md` - This file
- `tag_images.py` - Legacy jewelry tagging script
- `tag_images_old.py` - Old version of tagging script
- `generate_tagged_master.py` - Gallery generator

## Error Handling

The script now provides **clear error reporting** to distinguish between:
- ❌ **No match** - Product not found (normal)
- 🚫 **Rate limit (429)** - API quota exceeded
- ❌ **API errors** - Server connection issues
- ⚠️  **Download failed** - Thumbnail download issues

### Error Summary Example:
```
⚠️  ERRORS ENCOUNTERED: 15 videos failed
==================================================
  🚫 Rate Limit (429): 12 videos
     → Your Gemini API quota is exceeded
     → Wait for quota reset or upgrade API plan
  ⚠️  Download Failed: 3 thumbnails
==================================================
⚠️  15 videos were skipped due to errors
💡 Consider re-running later or checking your API key
```

## Troubleshooting

### Rate limit errors (429)
- Your Gemini API quota is exhausted
- **Free tier**: 60 requests per minute (RPM)
- **Solution**: Wait for quota reset or upgrade to paid plan

### API connection errors
- Check your internet connection
- Verify your `GEMINI_API_KEY` is valid
- Check Google AI Studio status

### Can't download thumbnails
- Some thumbnails require authentication
- The script will skip failed downloads and continue

## Notes

- Uses Gemini 2.5 Flash Lite model (`gemini-2.5-flash-lite-preview-09-2025`)
- Browser runs in visible mode by default so you can monitor progress
- Respects Gemini API rate limits (1,000 RPM)
- Each comparison takes ~0.2-0.3 seconds to stay within limits

### File Organization

**Folder Structure:**
```
Matches/          # All match results
├── product1.csv
├── product2.csv
└── ...

Research/         # Non-matches by user ID
├── MS4wLjABAAAA6rykbXnNyLG1RCTlO2nhuOOljilzHfGAsyXu-Dl1PVc.csv
├── MS4wLjABAAAAHtxdmKXJfK7qVSv1yKywiwMh-pZvbc1VmoPGFHtrkho.csv
└── ...
```

**Benefits:**
- No growing file problem - each user has separate research file
- Re-running same user **overwrites** old data with latest
- Fast file access - no need to read 10k+ line files
- Clean organization - matches and research separated
