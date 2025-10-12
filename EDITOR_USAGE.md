# Douyin Page Extractor - Usage Guide

## What It Does

The **Douyin Page Extractor** is a simple tool that scrolls Douyin pages and collects ALL video data without any comparison or filtering. Unlike the other tools that compare videos to a reference image, this just collects everything.

## Features

- ✅ **No reference image needed** - Just provide URLs
- ✅ **No AI processing** - Fast and simple data collection
- ✅ **Multiple URLs** - Process many pages in one run
- ✅ **Custom output folder** - Save CSVs wherever you want
- ✅ **Same format as Research folder** - Compatible with existing tools

## What Data Is Collected

For each video found:
- `video_url` - Link to the video
- `thumbnail_url` - Image URL of the video thumbnail
- `likes` - Number of likes (or "N/A" if not available)
- `index` - Position in the list

## How to Use

### 1. Run the Script

```bash
python3 douyin_editor.py
```

### 2. Enter Output Folder

When prompted, enter the folder path where you want CSVs saved:
- Press ENTER for current directory
- Or enter a path like: `Research` or `/path/to/folder`

### 3. Enter Douyin URLs

Enter your Douyin page URLs one per line:
```
https://www.douyin.com/user/MS4wLjABAAAA...
https://www.douyin.com/user/MS4wLjABAAAA...
https://www.douyin.com/user/MS4wLjABAAAA...
```

Press ENTER on an empty line when done.

### 4. Complete CAPTCHA

If Douyin shows a CAPTCHA on the first page, solve it manually in the browser.
Then press ENTER to continue.

### 5. Wait for Collection

The script will:
- Scroll each page to load all videos (max 30 minutes per page)
- Extract all video data
- Save to separate CSV files (one per URL)

## Output Files

Each URL creates one CSV file named after the user ID:
```
MS4wLjABAAAA2SclwWoJbswXgCZpyna9GsKfzZLX9BaezyT7J0B7dr-WIdSBBCIKEobBVBNwgOzJ.csv
MS4wLjABAAAA2SclwWoJbswXgCZpyna9GsKfzZLX9BaezyT7J0B7dr-WIdSBBCIKEobBVBNwgOzJ_1.csv
```

If a file exists, it auto-increments: `_1`, `_2`, etc.

### CSV Format

```csv
# Source Page: https://www.douyin.com/user/...
# Total Videos: 1234
# Date: 2025-10-12 20:30:15
video_url,thumbnail_url,likes,index
https://www.douyin.com/video/...,https://p3-pc-sign.douyinpic.com/...,29,1
https://www.douyin.com/video/...,https://p3-pc-sign.douyinpic.com/...,18,2
...
```

## Example Usage

```bash
$ python3 douyin_editor.py

📝 Douyin Video Editor - Simple Data Collection
==================================================

📁 Where should the CSV files be saved?
Enter folder path (or press ENTER for current directory): Research

✅ Output folder: /Users/zak/Downloads/Find all products in Douyin page/Research

🌐 Enter Douyin page URLs (one per line)
Press ENTER on an empty line when done:
https://www.douyin.com/user/MS4wLjABAAAA2SclwWoJbswXgCZpyna9GsKfzZLX9BaezyT7J0B7dr-WIdSBBCIKEobBVBNwgOzJ
  ✅ Added page 1: https://www.douyin.com/user/MS4wLjABAAAA2SclwWoJbswXgCZpyna9GsKfzZLX...
https://www.douyin.com/user/MS4wLjABAAAAVNqeVHcemjKYdYYLB3_VqdBMS9kXTksLUrsbDS3N0ts
  ✅ Added page 2: https://www.douyin.com/user/MS4wLjABAAAAVNqeVHcemjKYdYYLB3_VqdBMS9kXT...

✅ Ready to process 2 pages

[Browser opens, scrolling happens, data is collected...]

🎉 All Done!
==================================================
📊 Total pages processed: 2/2
📁 Output folder: /Users/zak/Downloads/Find all products in Douyin page/Research

📄 CSV Files Created:
  - Research/MS4wLjABAAAA2SclwWoJbswXgCZpyna9GsKfzZLX9BaezyT7J0B7dr-WIdSBBCIKEobBVBNwgOzJ.csv
  - Research/MS4wLjABAAAAVNqeVHcemjKYdYYLB3_VqdBMS9kXTksLUrsbDS3N0ts.csv
==================================================
```

## Tips

- **First run**: Complete the CAPTCHA when prompted
- **Cookies saved**: After first run, future runs won't need CAPTCHA
- **Time limit**: Each page scrolls for max 30 minutes (configurable in code)
- **Browser visible**: Browser stays visible so you can monitor progress
- **Interruption**: Press Ctrl+C to stop at any time

## Difference from Other Tools

| Tool | Purpose | Requires Reference Image | Uses AI | Output |
|------|---------|-------------------------|---------|--------|
| `find_product_videos.py` | Find matching products | ✅ Yes | ✅ Yes | Matches + Research |
| `find_product_videos_multi.py` | Find across multiple pages | ✅ Yes | ✅ Yes | Matches + Research |
| `douyin_watch_scraper.py` | Collect unique watches | ❌ No | ✅ Yes | Deduplicated watches |
| **`douyin_editor.py`** | **Collect ALL videos** | **❌ No** | **❌ No** | **All videos (fast)** |

## Technical Details

- **No API key needed** - No Gemini API usage
- **Fast** - Only scrolling and extracting, no AI processing
- **Memory efficient** - Processes one page at a time
- **Uses Playwright** - Same browser automation as other tools
- **Cookies support** - Reuses saved cookies from `douyin_cookies.json`

## Troubleshooting

**No videos found?**
- Make sure you completed the CAPTCHA
- Check if the URL is valid
- Try scrolling manually first to see if videos load

**CAPTCHA keeps appearing?**
- Delete `douyin_cookies.json` and try again
- Complete CAPTCHA more carefully

**Browser crashes?**
- Reduce time limit in code (line 28: `max_duration_minutes`)
- Process fewer URLs at once

## Need Help?

This tool is the simplest version - just data collection. If you need:
- Product matching → Use `find_product_videos.py`
- Deduplication → Use `douyin_watch_scraper.py`
- Multi-page product search → Use `find_product_videos_multi.py`

