# 🧹 Remove Duplicates Script (Visual Similarity)

Clean up CSV files by removing duplicate videos using **visual similarity detection**.

Detects duplicates even when thumbnail URLs differ but the images look identical!

## ⚠️ First Time Setup:

Install the new dependency:
```bash
pip3 install imagehash
```

## Usage:

### Method 1: Interactive (drag and drop)
```bash
python3 remove_duplicates.py
```
Then drag and drop your CSV file when prompted.

### Method 2: Command line (exact duplicates only)
```bash
python3 remove_duplicates.py Matches/GAMEBOY.csv
```

### Method 3: With similarity threshold
```bash
python3 remove_duplicates.py Matches/GAMEBOY.csv Matches/GAMEBOY_clean.csv 5
```

**Threshold values:**
- `0` = Exact duplicates only (default)
- `5` = Very similar images
- `10` = Similar images (may catch different products)

## What it does:

1. ✅ Reads your CSV file
2. ✅ Downloads each thumbnail image
3. ✅ Computes perceptual hash (fingerprint) for each image
4. ✅ Identifies visually duplicate videos (even with different URLs!)
5. ✅ Keeps the **first occurrence** of each unique image
6. ✅ Removes all visual duplicates
7. ✅ Saves to new file (`_unique.csv` suffix by default)

## Example:

```bash
$ python3 remove_duplicates.py Matches/GAMEBOY.csv

🧹 CSV Duplicate Remover (Visual Similarity)
==================================================

📄 Enter CSV file path: Matches/GAMEBOY.csv
💾 Output file (press Enter for auto-name): 
🎯 Similarity threshold (0=exact, 5=very similar, press Enter=0): 

🔍 Detecting duplicates (threshold: 0)

📖 Reading: Matches/GAMEBOY.csv
🖼️  Analyzing thumbnails for visual duplicates...
  [1] Checking thumbnail...
  [5] 🔍 Duplicate found (diff=0)
  [12] 🔍 Duplicate found (diff=0)
  [38] Checking thumbnail...

💾 Writing: Matches/GAMEBOY_unique.csv

✅ Done!
==================================================
📊 Original videos: 38
✅ Unique videos: 12
🗑️  Visual duplicates removed: 26
📉 Reduction: 68.4%
==================================================
📄 Output saved to: Matches/GAMEBOY_unique.csv
```

## How It Works:

The script uses **perceptual hashing** (image fingerprinting) to detect duplicates:

1. Downloads each thumbnail image
2. Converts to a hash (fingerprint) that represents the visual content
3. Compares hashes to find identical or similar images
4. Removes duplicates even if URLs are different

**Why this is better than URL comparison:**
- Same video can have different thumbnail URLs over time
- Douyin sometimes changes CDN URLs but keeps same image
- Detects true visual duplicates, not just URL duplicates

## Input CSV Format:

Works with any CSV containing:
- `video_url` column
- `thumbnail_url` column (downloads and analyzes the actual image)
- `likes` column (optional)
- `index` column (optional)

## Output:

Creates a new CSV with:
- Same format as input
- Only visually unique videos
- Updated count in header comments
- Added "# Duplicates Removed (Visual): X" comment
- "# Download Errors: X" (if any thumbnails couldn't be downloaded)

## Notes:

- ✅ Original file is **never modified** (safe!)
- ✅ Duplicates detected by **comparing actual images**, not URLs
- ✅ Keeps the first occurrence of each unique image
- ✅ Works with both Matches and Research CSV files
- ✅ If a thumbnail can't be downloaded, it's kept (safe fallback)
- ⚡ Downloads thumbnails on-the-fly (may take a few seconds per file)

## Advanced: Similarity Threshold

- `0` (default): Only exact visual matches
- `5`: Catches very similar images (slight compression differences)
- `10`: Catches similar images (may include different angles/crops)
- `15+`: May catch different products (not recommended)

**Recommended:** Start with `0` for exact duplicates only.
