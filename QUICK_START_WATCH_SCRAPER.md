# Quick Start: Douyin Watch Scraper

## 1. Prerequisites

```bash
# Install dependencies (if not already done)
pip3 install -r requirements.txt

# Install Playwright browser
python3 -m playwright install chromium

# Set up Gemini API key in .env file (optional)
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

## 2. Run the Script

```bash
python3 douyin_watch_scraper.py
```

## 3. Provide Input

```
🌐 Enter Douyin page URL: [paste Douyin user page URL]
```

Example: `https://www.douyin.com/user/MS4wLjABAAAA...`

## 4. Complete CAPTCHA (if shown)

- Browser will open automatically
- If CAPTCHA appears, solve it manually
- Press ENTER when done

## 5. Wait for Processing

The script will:
- Auto-scroll to load all videos (~30 seconds)
- Extract thumbnails
- Analyze each watch with AI filters
- Show progress in real-time

## 6. Review Results

After completion:
- **CSV file:** `watch_sources.csv` (or `watch_sources1.csv` if file exists)
- **Database:** `processed_watches_db.json` (updated)
- **Statistics:** Printed to console

## Example Output

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
```

## Output CSV Columns

- `video_url` - Douyin video link
- `thumbnail_url` - Watch image URL
- `likes` - Video engagement
- `case_shape`, `case_color`, `dial_color`, `dial_markers`, `strap_type`, `strap_color`
- `fingerprint` - Unique watch ID
- `phash` - Image hash

## What Gets Filtered Out?

✅ **Eliminated automatically:**
- Duplicate images (same photo uploaded multiple times)
- Images with 2+ products (comparison shots)
- Same watch from different angles
- Watches already in database from previous runs

✅ **Kept in results:**
- Unique watches never seen before
- Same watch design in different colors (different SKUs)

## Next Steps

1. **Verify results:** Open `watch_sources.csv` in Excel/Sheets
2. **Check thumbnails:** Visit `thumbnail_url` to see images
3. **Source on 1688:** Use thumbnail URLs with `watch_prices.py`

## Troubleshooting

### Rate Limit Error
```
🚫 RATE LIMIT
```
**Solution:** Wait 1 minute or upgrade Gemini API plan

### No Videos Found
```
❌ No videos found on page!
```
**Solution:** Verify URL is a Douyin user page with videos

### API Key Error
```
❌ Error configuring Gemini API
```
**Solution:** Check `GEMINI_API_KEY` in `.env` or enter manually

## Tips

- **First run:** Start with small page (10-20 videos) to test
- **Database:** Delete `processed_watches_db.json` to reset
- **Multiple pages:** Run script multiple times with different URLs
- **Gemini quota:** Free tier = 60 requests/minute

## Documentation

- **Full guide:** See `WATCH_SCRAPER_USAGE.md`
- **Implementation details:** See `IMPLEMENTATION_SUMMARY.md`
- **Main README:** See `README.md`

## Support

If you encounter issues:
1. Check that all dependencies are installed
2. Verify Gemini API key is valid
3. Ensure internet connection is stable
4. Review error messages in console
5. Check detailed guide for specific error solutions

