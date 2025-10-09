# Quick Start: Watch Finder with Drag & Drop

## 30-Second Setup

1. **Get ImgBB API Key** (free forever):
   ```
   https://api.imgbb.com/
   → Click "Get API Key"
   → Sign up (no credit card)
   → Copy your key
   ```

2. **Add to .env file**:
   ```bash
   echo "IMGBB_API_KEY=your_key_here" >> .env
   ```

3. **Done!** ✅

## Usage

```bash
python3 watch_prices.py
```

When prompted, **drag and drop** your image file into the terminal!

## That's It!

The script will:
- ✅ Upload your image to ImgBB (with proper .jpg/.png extension)
- ✅ Search 1688 for similar products
- ✅ Compare with AI
- ✅ Save best match to `Watched_prices.csv`

## Works With:
- ✅ Local files (drag & drop)
- ✅ Online URLs (paste)
- ✅ Files with spaces in names
- ✅ Multiple images (separate with `|||`)

**Full guide:** `LOCAL_IMAGE_USAGE.md`

