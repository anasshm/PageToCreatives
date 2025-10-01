# Douyin Product Video Finder

Find all videos containing a specific product in their thumbnails using AI-powered image comparison.

## Features

- ✅ Auto-scrolls Douyin pages to load all videos
- ✅ Extracts video thumbnails and URLs
- ✅ **Parallel processing** - Analyzes 50 videos simultaneously
- ✅ Uses Google Gemini 2.5 Flash AI for precise product matching
- ✅ Exports matching videos to CSV (new file per run)
- ✅ **Accumulative research.csv** - Saves all non-matches for analysis
- ✅ **Smart deduplication** - Prevents re-processing same pages
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

### 1. Matches File (e.g., `Neckadele.csv`)
- Creates a **new file** for each run
- Contains only videos that match your product
- Columns: `video_url`, `thumbnail_url`, `index`

### 2. Research File (`research.csv`)
- **Accumulative** - keeps growing with each run
- Contains all non-matching videos
- Automatically prevents duplicates by checking if page was already processed
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

## Troubleshooting

### No videos found
- The Douyin page structure may have changed. Check browser console for errors.
- Try adjusting the CSS selector in `extract_videos_from_page()` function.

### Rate limit errors
- The script will automatically retry with exponential backoff.
- If persistent, increase the delay in line 317.

### Can't download thumbnails
- Some thumbnails may require authentication or have anti-bot measures.
- The script will skip failed downloads and continue.

## Notes

- Uses Gemini 2.5 Flash Lite model (`gemini-2.5-flash-lite-preview-09-2025`)
- Browser runs in visible mode by default so you can monitor progress
- Respects Gemini API rate limits (1,000 RPM)
- Each comparison takes ~0.2-0.3 seconds to stay within limits

### Duplicate Prevention

- The script checks `research.csv` for previously processed page URLs
- If a page was already analyzed, matches are still saved to a new file
- Non-matches from duplicate pages are **skipped** to avoid bloating research.csv
- This allows you to re-run the same page with different product images without polluting your research data
