# Thumbnail Backup Tool - Usage Guide

Backup your Douyin thumbnail URLs to Cloudinary for permanent storage.

## Why Use This?

Douyin thumbnail URLs expire after a certain time. This tool uploads all thumbnails to Cloudinary (permanent cloud storage) and adds backup URLs to your CSV files.

## Setup (One-Time)

### 1. Install Dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Get Cloudinary Credentials

1. Sign up for free at: https://cloudinary.com/users/register/free
2. Go to your dashboard: https://cloudinary.com/console
3. Copy these three values:
   - **Cloud Name**
   - **API Key**
   - **API Secret**

### 3. Add Credentials to .env File

Open `.env` file and replace the placeholders:

```bash
CLOUDINARY_CLOUD_NAME=your_actual_cloud_name
CLOUDINARY_API_KEY=your_actual_api_key
CLOUDINARY_API_SECRET=your_actual_api_secret
```

**Done!** You only need to do this once.

---

## How to Use

### 1. Run the Script

```bash
python3 backup_thumbnails.py
```

### 2. Drag and Drop Your CSV

When prompted, drag and drop your Research CSV file (e.g., `Research/MS4wLjABAAAA...csv`)

### 3. Wait for Completion

The script will:
- ✅ Upload each thumbnail to Cloudinary
- ✅ Add a `backup_thumbnail_url` column with permanent URLs
- ✅ Save to a new file: `{original_name}_backed.csv`
- ✅ Show a progress summary

### 4. Get Your Result

Find your backed-up CSV at:
```
Research/MS4wLjABAAAA..._backed.csv
```

---

## What It Does

**Before:**
```csv
video_url,thumbnail_url,likes,index
https://...,https://p3-pc-sign.douyinpic.com/...(expires),1.2K,1
```

**After:**
```csv
video_url,thumbnail_url,likes,index,backup_thumbnail_url
https://...,https://p3-pc-sign.douyinpic.com/...(expires),1.2K,1,https://res.cloudinary.com/...(permanent)
```

---

## Features

✅ **Preserves CSV structure** - Keeps all comments and data intact  
✅ **Smart retry** - Automatically retries failed uploads (up to 3 times)  
✅ **Progress tracking** - Shows real-time upload progress  
✅ **Failure detection** - Stops if 10+ consecutive failures occur  
✅ **Summary report** - Shows successful/failed uploads at the end  
✅ **Skip duplicates** - Won't re-upload if backup URL already exists  

---

## Cloudinary Free Tier Limits

- **Storage:** 25 GB
- **Bandwidth:** 25 GB/month
- **Transformations:** 25,000/month
- **Perfect for:** Thousands of thumbnails

---

## Troubleshooting

### "Cloudinary credentials not found"
→ Make sure you added your credentials to `.env` file

### "10 consecutive failures detected"
→ Possible causes:
  - API quota exceeded (wait or upgrade plan)
  - Network issues (check internet connection)
  - Invalid credentials (verify in .env)

### "Failed" in backup_thumbnail_url column
→ Individual thumbnail couldn't be downloaded/uploaded (URL may be invalid)

---

## Example Run

```bash
$ python3 backup_thumbnails.py

🔄 Douyin Thumbnail Backup Tool
==================================================
✅ Cloudinary configured successfully

📂 Drag and drop CSV file here (or enter path): Research/MS4wLjABAAAA...csv
📂 Processing CSV: Research/MS4wLjABAAAA...csv
✅ Loaded 306 rows from CSV
➕ Adding 'backup_thumbnail_url' column

🔄 Uploading thumbnails to Cloudinary...
==================================================
  [1/306] Uploading thumbnail...
  [1/306] ✅ Success
  [2/306] Uploading thumbnail...
  [2/306] ✅ Success
  ...
  [306/306] ✅ Success

✅ Backup complete!
📄 Saved to: Research/MS4wLjABAAAA..._backed.csv

📊 SUMMARY
==================================================
✅ Successful uploads: 304
❌ Failed uploads: 2
📁 Total rows: 306
==================================================

🎉 Backup completed successfully!
```

---

## Tips

💡 **Backup all your Research files** to protect against link expiration  
💡 **Re-run anytime** - Already backed-up rows will be skipped  
💡 **Free tier is generous** - Can store thousands of thumbnails  

---

## Questions?

- Cloudinary Dashboard: https://cloudinary.com/console
- Cloudinary Docs: https://cloudinary.com/documentation

