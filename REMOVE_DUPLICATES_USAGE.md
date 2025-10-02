# 🧹 Remove Duplicates Script

Clean up CSV files by removing duplicate videos (same thumbnail URL).

## Usage:

### Method 1: Interactive (drag and drop)
```bash
python3 remove_duplicates.py
```
Then drag and drop your CSV file when prompted.

### Method 2: Command line
```bash
python3 remove_duplicates.py Matches/GAMEBOY.csv
```

### Method 3: Specify output file
```bash
python3 remove_duplicates.py Matches/GAMEBOY.csv Matches/GAMEBOY_clean.csv
```

## What it does:

1. ✅ Reads your CSV file
2. ✅ Identifies duplicate videos (same `thumbnail_url`)
3. ✅ Keeps the **first occurrence** of each unique video
4. ✅ Removes all duplicates
5. ✅ Saves to new file (`_unique.csv` suffix by default)

## Example:

```bash
$ python3 remove_duplicates.py Matches/GAMEBOY.csv

🧹 CSV Duplicate Remover
==================================================

📖 Reading: Matches/GAMEBOY.csv
💾 Writing: Matches/GAMEBOY_unique.csv

✅ Done!
==================================================
📊 Original videos: 38
✅ Unique videos: 12
🗑️  Duplicates removed: 26
📉 Reduction: 68.4%
==================================================
📄 Output saved to: Matches/GAMEBOY_unique.csv
```

## Input CSV Format:

Works with any CSV containing:
- `video_url` column
- `thumbnail_url` column (used for duplicate detection)
- `likes` column (optional)
- `index` column (optional)

## Output:

Creates a new CSV with:
- Same format as input
- Only unique videos (by thumbnail)
- Updated count in header comments
- Added "# Duplicates Removed: X" comment

## Notes:

- Original file is **never modified** (safe!)
- Duplicates detected by comparing `thumbnail_url` values
- Keeps the first occurrence of each unique thumbnail
- Works with both Matches and Research CSV files
