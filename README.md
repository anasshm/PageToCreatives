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
- ✅ **Thumbnail backup** - Save expiring URLs to Bunny.net for permanent storage (~$1-10/month)

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
- Columns: `video_url`, `thumbnail_url`, `likes`, `index`

### 2. Research (saved to `Research/` folder)
- Saves non-matches to `Research/{user_id}.csv`
- **Overwrites** previous data for same user (not accumulative)
- Prevents 10k+ line files - each user has separate file
- Same structure: `video_url`, `thumbnail_url`, `likes`, `index`
- Includes source page URLs in header comments

**CSV Format:**
```csv
video_url,thumbnail_url,likes,index
https://www.douyin.com/video/123...,https://...,1.2w,1
https://www.douyin.com/video/456...,https://...,8520,2
https://www.douyin.com/video/789...,https://...,N/A,3
```

**Note:** Likes are shown in Douyin's format (e.g., "1.2w" for 12,000 or "N/A" if unavailable)

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

## Thumbnail Backup Tool

**Problem:** Douyin thumbnail URLs expire after some time.  
**Solution:** Backup thumbnails to Bunny.net (permanent, affordable cloud storage).

### Quick Start

1. **One-time setup:**
   ```bash
   # Dependencies already installed in requirements.txt
   
   # Get Bunny.net account at https://bunny.net
   # Create storage zone and add credentials to .env file
   # See BUNNY_SETUP.md for detailed instructions
   ```

2. **Backup a Research CSV:**
   ```bash
   python3 backup_thumbnails.py
   # Drag and drop your CSV when prompted
   ```

3. **Result:**
   - Creates `Backed_{filename}.csv` with new `backup_thumbnail_url` column
   - All thumbnails permanently stored on Bunny.net CDN
   - Shows summary: successful/failed uploads

**Features:**
- ✅ Preserves all CSV data and comments
- ✅ Adds permanent CDN backup URLs
- ✅ Smart retry on failures (up to 3 attempts)
- ✅ Parallel uploads (10 concurrent)
- ✅ Skips already backed-up images
- ✅ Cost-effective: ~$1-10/month (vs $90/month for Cloudinary)
  - 100GB storage: ~$1/month
  - 500GB storage: ~$5/month

**See detailed guide:** `BUNNY_SETUP.md`

## Watch Finder Tool (1688 Product Search)

Search for similar products on 1688.com using reference images!

### Features

- ✅ **Support for local images** - Drag and drop files or use URLs
- ✅ **Automatic image upload** - Local files uploaded to ImgBB with proper extensions
- ✅ **AI-powered matching** - Gemini compares all products
- ✅ **Parallel processing** - Analyzes 50 products at once
- ✅ **Proper image URLs** - ImgBB returns URLs with `.jpg`/`.png` extensions

### Quick Setup (First Time Only)

For local file uploads, get a free ImgBB API key (30 seconds):
1. Go to https://api.imgbb.com/
2. Click "Get API Key" → Sign up (free forever)
3. Copy your API key
4. Add to `.env` file: `IMGBB_API_KEY=your_key_here`

### Quick Start

```bash
python3 watch_prices.py
```

**When prompted, you can:**
- Paste an online image URL
- **Drag and drop a local image file**
- Use multiple images (separate with `|||`)

### Example with Local Files

```bash
python3 watch_prices.py

Image URL(s) or path(s): /path/to/watch.jpg
# Or drag and drop your file into the terminal!

# First time with local files:
🔑 ImgBB API Key Setup (FREE - takes 30 seconds!)
1. Go to: https://api.imgbb.com/
2. Click 'Get API Key'...
```

### Multiple Images

```bash
# Mix URLs and local files:
|||https://example.com/watch1.jpg|||./Watches/A1.png|||/path/to/watch2.jpg
```

**Output:** Results saved to `Watched_prices.csv`

**See detailed guide:** `LOCAL_IMAGE_USAGE.md`

## Watch Deduplication Tool (Douyin Watch Scraper)

Scrape Douyin pages and extract only **unique watches** using AI-powered deduplication!

### Features

- ✅ **Hybrid deduplication** - Perceptual hash + AI attribute extraction
- ✅ **Multi-product filtering** - Auto-eliminates images with multiple products
- ✅ **AI attribute extraction** - Identifies case shape, colors, dial markers, strap type
- ✅ **Persistent database** - Tracks all processed watches across runs
- ✅ **Parallel processing** - 50 watches analyzed simultaneously
- ✅ **Auto-scrolling** - Loads all videos from Douyin page

### How It Works

1. **Perceptual Hash Filter** - Fast elimination of exact/near-duplicate images
2. **AI Filter 1** - Eliminates images with multiple products
3. **AI Filter 2** - Extracts watch attributes (case, dial, strap details)
4. **Fingerprint Check** - Compares attributes against historical database
5. **Result** - Only truly unique watches saved to CSV

### Quick Start

```bash
python3 douyin_watch_scraper.py

# Enter Douyin page URL when prompted
# Complete CAPTCHA if shown
# Press ENTER to start scraping
```

### Output Files

1. **`watch_sources.csv`** - Unique watches with attributes
   - Columns: video_url, thumbnail_url, likes, case_shape, case_color, dial_color, dial_markers, strap_type, strap_color, fingerprint, phash
   - Auto-increments filename (watch_sources1.csv, watch_sources2.csv, etc.)

2. **`processed_watches_db.json`** - Persistent deduplication database
   - Tracks perceptual hashes and watch fingerprints
   - Updated after each run
   - Prevents re-processing same watches across multiple runs

### Example

```bash
python3 douyin_watch_scraper.py

🌐 Enter Douyin page URL: https://www.douyin.com/user/MS4wLjABAAAA...

# After scraping...
🎉 Processing Complete!
📊 STATISTICS:
   Total videos processed: 150
   ✅ Unique watches found: 45
   ⏭️  Duplicate images (phash): 30
   ⏭️  Multiple products filtered: 25
   ⏭️  Duplicate watches (attributes): 40
   ⚠️  Errors: 10
```

### Deduplication Logic

**Same Watch = Same Fingerprint**

A watch fingerprint is generated from:
- Case shape (round, square, rectangular, oval, triangular)
- Case color/material (gold, silver, rose-gold, black)
- Dial color (white, black, gold, blue, pink)
- Dial markers (roman, arabic, minimalist, crystals, mixed)
- Strap type (metal-bracelet, leather, fabric)
- Strap color (gold, silver, black, brown, tan, pink)

**Example:** Two images of the same gold rectangular watch with Roman numerals will generate the same fingerprint and be treated as duplicates, even from different angles.

**See detailed guide:** `WATCH_SCRAPER_USAGE.md`

## File Directory

- `find_product_videos.py` - Main product finder script
- `douyin_watch_scraper.py` - Watch deduplication scraper (outputs watch_sources.csv)
- `watch_prices.py` - 1688 product finder with drag-and-drop support
- `backup_thumbnails.py` - Thumbnail backup to Bunny.net
- `tag_research_videos.py` - Tag research videos with product taxonomy
- `generate_research_gallery.py` - Generate gallery from research videos
- `generate_tagged_research_gallery.py` - Generate tagged gallery
- `consolidate_watch_prices.py` - Consolidate watch prices from multiple CSVs
- `generate_master_watch_gallery.py` - Generate master watch gallery
- `tag_and_merge_watch_pages.py` - Tag and merge watch pages
- `requirements.txt` - Python dependencies
- `README.md` - This file
- `BUNNY_SETUP.md` - Bunny.net setup guide (NEW)
- `WATCH_SCRAPER_USAGE.md` - Watch scraper detailed guide
- `LOCAL_IMAGE_USAGE.md` - Watch finder local image guide
- `BACKUP_THUMBNAILS_USAGE.md` - Detailed backup tool guide (legacy Cloudinary)
- `BACKUP_QUICK_START.txt` - Quick setup instructions (legacy)
- `TAGGING_USAGE.md` - Video tagging guide
- `FILTER_IMPROVEMENTS.md` - Filter improvements documentation
- `product_taxonomy.json` - Product category taxonomy
- `processed_watches_db.json` - Watch deduplication database (auto-created)

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
