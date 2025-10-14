# Sequential Processing Update

## Date: October 14, 2025

## Summary
Updated `find_product_videos_multi.py` to process pages sequentially instead of all at once. This prevents data loss when Douyin blocks the scraper after ~1 hour of continuous scrolling.

## Problem Solved
**Before:** The script would:
1. Open all pages → Complete CAPTCHAs
2. Scroll ALL pages → Collect ALL videos
3. Analyze ALL videos at once
4. Save results

**Issue:** If Douyin blocked after scrolling 8k-10k videos for ~1 hour, all work was lost.

## Solution Implemented
**Now:** The script processes each page completely before moving to the next:
1. Open all pages → Complete CAPTCHAs
2. **For EACH page:**
   - Scroll and extract videos
   - Save raw videos to Research folder immediately
   - Analyze videos for matches
   - Save matches to Matches folder (append mode)
   - Close tab to free RAM
   - Move to next page

## Benefits
✅ **Progress saved after each page** - If blocked, previous pages are preserved
✅ **Same output format** - Research folder for all videos, Matches folder for matches
✅ **Better RAM management** - Tabs closed immediately after processing
✅ **Clear progress tracking** - Shows cumulative stats after each page
✅ **Fault tolerant** - Can resume manually by removing already-processed URLs

## Changes Made

### 1. New Helper Functions

#### `save_page_to_research(videos, page_url)`
- Saves raw extracted videos to Research folder immediately after scrolling
- Uses user_id from URL as filename (e.g., `MS4wLjABAAAA...csv`)
- Called right after extracting videos from each page

#### `analyze_videos(videos, model, reference_image)`
- Analyzes a batch of videos and returns (matches, non_matches)
- Uses ThreadPoolExecutor with 50 workers for parallel processing
- Shows progress and error statistics
- Extracted from the old bulk analysis code

#### `save_matches_incrementally(matches, output_csv, page_url, is_first_page, all_page_urls)`
- Appends matches to the Matches CSV file
- First page: writes header with source URLs
- Subsequent pages: appends in append mode
- Only saves if there are matches

### 2. Modified Phase 2 Processing Loop

**Old Flow:**
```python
for each page:
    scroll and extract videos
    accumulate all videos
    close tab

# Then analyze ALL videos at once
```

**New Flow:**
```python
for each page:
    scroll and extract videos          # Step 1
    save to Research folder            # Step 2 - IMMEDIATE SAVE
    analyze this page's videos         # Step 3
    save matches incrementally         # Step 4 - IMMEDIATE SAVE
    accumulate totals                  # Step 5
    close tab                          # Step 6
    show cumulative progress           # Step 7
```

### 3. Removed Bulk Analysis Section
- Deleted lines that collected all videos then analyzed them
- Analysis now happens per-page within the loop

### 4. Enhanced Progress Reporting
- Shows detailed progress after each page
- Cumulative statistics (total videos, matches, non-matches)
- Clear visual separators for each page
- Final summary with complete statistics

## Output Structure

### Research Folder
Each page's raw videos saved as: `Research/{user_id}.csv`
- Contains ALL extracted videos from that page
- Saved immediately after scrolling, before analysis
- Includes video_url, thumbnail_url, likes, index, source_page

### Matches Folder
Cumulative matches saved as: `Matches/{image_name}.csv`
- First page creates file with header
- Subsequent pages append matches
- All source URLs listed in header comments
- Only contains matching videos

## Usage
No changes to how you run the script:
```bash
python3 find_product_videos_multi.py
```

1. Enter reference image path
2. Enter multiple Douyin URLs (one per line, empty line to finish)
3. Complete CAPTCHAs in all tabs
4. Press ENTER to start sequential processing
5. Watch progress as each page is processed
6. Check results in Research/ and Matches/ folders

## Example Output
```
🔄 Phase 2: Sequential Processing (scroll → save → analyze → close)
============================================================

============================================================
📄 PROCESSING PAGE 1/3
🔗 URL: https://www.douyin.com/user/...
============================================================

⏬ Scrolling Page 1/3 with periodic extraction...
✅ Extracted 1500 videos from page 1
💾 Saving 1500 raw videos to Research/MS4wLjABAAAA...csv...
  ✅ Saved to Research/MS4wLjABAAAA...csv

🔎 Analyzing 1500 videos...
📦 Processing batch 1/30 (50 videos)...
...

📊 Page 1 Results:
   ✅ Matches: 25
   ❌ Non-matches: 1475

💾 Saving 25 matches to Matches/product.csv...
  ✅ Saved 25 matches

🗑️  Closing Page 1 to free RAM...
✅ Page 1 complete and closed

📈 CUMULATIVE PROGRESS:
   Pages processed: 1/3
   Total videos: 1500
   Total matches: 25
   Total non-matches: 1475
```

## Technical Notes
- Uses same Gemini API for image comparison
- ThreadPoolExecutor with 50 workers for parallel analysis
- Batch size: 50 videos per batch
- No changes to scrolling, extraction, or DOM cleanup logic
- Compatible with existing cookie handling

## Testing Recommendations
1. Test with 2-3 pages first
2. Verify Research folder populates after each page scroll
3. Verify Matches file updates after each page analysis
4. Confirm tabs close after each page
5. Test recovery: stop mid-run, check saved files

## Next Steps (If Needed)
- Add resume capability (skip already-processed URLs)
- Add page-level error recovery
- Add statistics export to JSON
- Add email notification when complete

