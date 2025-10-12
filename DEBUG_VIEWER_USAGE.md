# Watch Debug Viewer Usage

## Overview

The debug viewer helps you inspect and verify the watch deduplication results by showing:
- All watches grouped by fingerprint (same attributes)
- AI verification decisions (MATCH/NO/ERROR)
- Visual duplicates grouped by phash
- Statistics and summaries

## How to Use

### 1. Generate the Debug Viewer

After running the watch scraper, generate the debug HTML viewer:

```bash
python debug_watch_database.py
```

This will:
- Read `processed_watches_db.json`
- Analyze all fingerprint and phash groups
- Generate `watch_debug_viewer.html`
- Automatically open it in your browser

### 2. Understanding the Viewer

#### Statistics Dashboard
At the top, you'll see:
- **Total Fingerprints**: All unique attribute combinations
- **Multi-Watch Fingerprints**: Fingerprints with 2+ watches (⚠️ potential duplicates)
- **Total Phashes**: All perceptual hashes
- **Multi-URL Phashes**: Phashes with 2+ URLs (visual duplicates)
- **AI Verifications**: Total AI comparison calls made
- **AI: Match**: AI confirmed duplicates
- **AI: Different**: AI said watches are different (kept as unique)
- **AI: Errors**: AI verification errors

#### Fingerprint Groups Section
Shows watches that share the same attributes:

**Color Coding:**
- 🔵 **Blue border** = Original watch (first seen with this fingerprint)
- 🟢 **Green border** = AI said "different watch" - kept as unique
- 🔴 **Red border** = AI confirmed "duplicate" - was filtered out
- 🟠 **Orange border** = AI verification error

**Badges:**
- `ORIGINAL` = First watch with these attributes
- `AI: Different` = Same attributes but AI detected different design
- `AI: Duplicate` = AI confirmed it's the same watch
- `ERROR_*` = AI verification failed

#### Phash Groups Section
Shows URLs with identical perceptual hashes (exact visual duplicates)

## What to Look For

### 🎯 Good Signs
- Most fingerprint groups have AI decision badges
- Green badges (`AI: Different`) show the system is catching false positives
- Red badges (`AI: Duplicate`) confirm true duplicates were caught

### ⚠️ Warning Signs
- Many fingerprint groups with 2+ watches but no AI verification
  - This means the old data doesn't have AI decisions yet
  - Re-run the scraper to populate AI verifications

### 🔴 Issues to Investigate
- Many `ERROR_*` badges = API issues or rate limits
- Watches that look identical but have `AI: Different` = might need review
- Watches that look different but have `AI: Duplicate` = false positive

## Troubleshooting

### "No AI verifications" in stats
The database was created before AI verification was added. Re-run `douyin_watch_scraper.py` to populate AI decisions.

### Can't see images in viewer
The viewer loads images directly from URLs. If thumbnails don't load:
- Check your internet connection
- URL might be expired or blocked
- Original image might have been removed

### Too many fingerprint groups
This is normal! The system groups watches by 8 attributes, so similar watches will share fingerprints. The AI verification step ensures only true duplicates are filtered.

## Tips

1. **Focus on Multi-Watch Fingerprints**: These are the interesting cases where AI verification matters

2. **Look for Green Badges**: These show cases where the old attribute-only system would have incorrectly filtered unique watches

3. **Review Orange/Error Badges**: These might need manual review or re-processing

4. **Check Phash Groups**: These are true visual duplicates and should always be filtered

## Next Steps

After reviewing the debug viewer:
1. If you see many false positives, adjust the AI prompt in `douyin_watch_scraper.py`
2. If you see many false negatives, consider adjusting the attribute extraction
3. Re-run the scraper to re-process with new settings

