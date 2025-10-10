# Douyin Watch Scraper - Usage Guide

## Overview

The Douyin Watch Scraper is a tool that scrapes Douyin user pages and extracts only **unique watches** using a hybrid deduplication approach:

1. **Perceptual Hash** - Fast elimination of exact/near-duplicate images
2. **AI Multi-Product Filter** - Removes images with multiple products
3. **AI Attribute Extraction** - Identifies watch characteristics
4. **Fingerprint Matching** - Compares against historical database

## Quick Start

```bash
python3 douyin_watch_scraper.py
```

The script will prompt you for:
1. Gemini API key (if not set in `.env`)
2. Douyin page URL
3. CAPTCHA completion (if shown)

## Workflow

### Step 1: Enter Douyin URL

```
🌐 Enter Douyin page URL: https://www.douyin.com/user/MS4wLjABAAAA...
```

### Step 2: Complete CAPTCHA (if shown)

The browser will open and load the page. If Douyin shows a CAPTCHA:
- Complete it manually
- Press ENTER when done

### Step 3: Auto-Scrolling

The script will automatically scroll through the entire page, loading all videos (max 30 minutes).

### Step 4: Processing

Each video thumbnail goes through the deduplication pipeline:

```
[1/150] ⏭️  SKIP - Duplicate image (phash)
[2/150] ⏭️  SKIP - Multiple products
[3/150] ✅ UNIQUE WATCH - round|gold|white|roman|leather|brown
[4/150] ⏭️  SKIP - Duplicate watch (attributes)
```

### Step 5: Results

At the end, you'll see statistics:

```
🎉 Processing Complete!
📊 STATISTICS:
   Total videos processed: 150
   ✅ Unique watches found: 45
   ⏭️  Duplicate images (phash): 30
   ⏭️  Multiple products filtered: 25
   ⏭️  Duplicate watches (attributes): 40
   ⚠️  Errors: 10
📄 Results saved to: watch_sources.csv
💾 Database updated: processed_watches_db.json
```

## Output Files

### 1. watch_sources.csv

Contains unique watches with full attributes:

| Column | Description |
|--------|-------------|
| video_url | Douyin video URL |
| thumbnail_url | Watch image URL |
| likes | Video likes count |
| case_shape | round, square, rectangular, oval, triangular, other |
| case_color | gold, silver, rose-gold, black, other |
| dial_color | white, black, gold, blue, pink, other |
| dial_markers | roman, arabic, minimalist, crystals, mixed, other |
| strap_type | metal-bracelet, leather, fabric, other |
| strap_color | gold, silver, black, brown, tan, pink, other |
| fingerprint | Unique identifier (e.g., "round\|gold\|white\|roman\|leather\|brown") |
| phash | Perceptual hash value |

**Example:**
```csv
video_url,thumbnail_url,likes,case_shape,case_color,dial_color,dial_markers,strap_type,strap_color,fingerprint,phash
https://www.douyin.com/video/123...,https://...,1.2w,round,gold,white,roman,leather,brown,round|gold|white|roman|leather|brown,abc123def456
```

### 2. processed_watches_db.json

Persistent database that tracks all processed watches:

```json
{
  "phashes": ["abc123def456", "def789ghi012", ...],
  "fingerprints": {
    "round|gold|white|roman|leather|brown": {
      "first_seen": "2025-10-10",
      "thumbnail_url": "https://...",
      "count": 1
    },
    ...
  }
}
```

This database is **updated after each run** and prevents re-processing the same watches across multiple scraping sessions.

## Deduplication Logic

### Filter 1: Perceptual Hash

- Uses `imagehash` library with pHash algorithm
- Eliminates exact and near-duplicate images instantly
- **When triggered:** Same watch image uploaded multiple times

### Filter 2: Multiple Products

- AI analyzes image to count distinct watch/jewelry products
- Eliminates images showing 2+ different products
- **When triggered:** Comparison images, product collages, catalog pages

### Filter 3: Attribute Fingerprint

- AI extracts 6 key attributes from the watch
- Generates a unique fingerprint string
- Compares against historical database
- **When triggered:** Same watch model from different angles/photos

## Understanding Watch Fingerprints

A fingerprint like `round|gold|white|roman|leather|brown` means:

- **Case shape:** Round
- **Case color:** Gold
- **Dial color:** White
- **Dial markers:** Roman numerals
- **Strap type:** Leather
- **Strap color:** Brown

Two watches with the same fingerprint are considered **the same product** even if photographed differently.

## Tips for Best Results

### 1. API Rate Limits

The script uses Gemini AI extensively. If you hit rate limits:
- **Free tier:** 60 requests per minute
- **Solution:** Wait for quota reset or upgrade to paid plan
- The script will retry automatically on rate limit errors

### 2. Running Multiple Times

The database is persistent, so:
- **First run:** Processes all unique watches
- **Second run (same page):** Should find 0 new unique watches
- **Different pages:** Only processes watches not in database

### 3. CSV File Naming

The script auto-increments filenames:
- `watch_sources.csv` (first run)
- `watch_sources1.csv` (second run)
- `watch_sources2.csv` (third run)
- etc.

### 4. Database Management

To reset the database and start fresh:
```bash
rm processed_watches_db.json
```

## Troubleshooting

### Problem: "No videos found on page"

**Solution:** 
- Make sure the URL is a Douyin user page with videos
- Complete CAPTCHA if shown
- Check your internet connection

### Problem: "Rate limit hit"

**Solution:**
- Your Gemini API quota is exhausted
- Wait for quota reset (usually next minute)
- Or upgrade to paid API plan

### Problem: "Too many errors"

**Solution:**
- Check Gemini API key is valid
- Verify internet connection stable
- Some thumbnails may be inaccessible - this is normal

### Problem: "Duplicate fingerprint but different watches"

This can happen if two watches are **very similar** (e.g., same design in different colors). The current attributes don't distinguish:
- Size variations (32mm vs 36mm)
- Minor color shades (light gold vs dark gold)
- Brand logos

**Solution:** These watches will be treated as duplicates. If you need finer granularity, the fingerprint logic can be adjusted.

## Advanced Usage

### Batch Processing Multiple Pages

```bash
# Create a script to process multiple Douyin pages
for url in "https://..." "https://..." "https://..."; do
    python3 douyin_watch_scraper.py <<< "$url"
done
```

### Filtering CSV Results

After scraping, you can filter the CSV by attributes:

```bash
# Find all gold watches
grep ",gold," watch_sources.csv

# Find watches with Roman numerals
grep "roman" watch_sources.csv

# Find rectangular leather watches
grep "rectangular.*leather" watch_sources.csv
```

### Integration with watch_prices.py

After scraping unique watches, you can feed them to `watch_prices.py` for 1688 sourcing:

1. Extract thumbnail URLs from `watch_sources.csv`
2. Use them as input to `watch_prices.py`
3. Get 1688 supplier links with pricing

## Statistics Interpretation

```
📊 STATISTICS:
   Total videos processed: 150        ← All thumbnails from page
   ✅ Unique watches found: 45         ← New watches added to CSV
   ⏭️  Duplicate images (phash): 30   ← Exact/near-duplicate images
   ⏭️  Multiple products filtered: 25  ← Images with 2+ products
   ⏭️  Duplicate watches (attributes): 40  ← Same watch, different photo
   ⚠️  Errors: 10                      ← API errors, download failures
```

**Note:** Numbers may not add up to total due to database matches (watches already processed in previous runs).

## Next Steps

After scraping unique watches:

1. **Verify Results** - Open `watch_sources.csv` and check the watches
2. **Manual Review** - Review thumbnail URLs to confirm accuracy
3. **Source on 1688** - Use `watch_prices.py` to find suppliers
4. **Iterate** - Run on more Douyin pages to build watch database

## Need Help?

- Check that all requirements are installed: `pip3 install -r requirements.txt`
- Verify Playwright browser is installed: `python3 -m playwright install chromium`
- Ensure Gemini API key is valid and has quota remaining
- Check README.md for general troubleshooting tips

