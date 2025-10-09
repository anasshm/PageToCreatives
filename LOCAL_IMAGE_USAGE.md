# Local Image Support for Watch Finder

## Overview

The `watch_prices.py` script now supports **local image files** in addition to online URLs!

## Quick Setup (First Time Only)

If you want to use local files, you'll need a **free ImgBB API key** (takes 30 seconds):

1. Go to https://api.imgbb.com/
2. Click "Get API Key"
3. Sign up with email (free forever, no credit card)
4. Copy your API key
5. Paste it when the script asks, or add to `.env` file:
   ```
   IMGBB_API_KEY=your_key_here
   ```

**Why?** Local files need to be uploaded to get a public URL for the 1688 search. ImgBB gives us permanent URLs with proper `.jpg`/`.png` extensions.

## How It Works

When you provide a local file path:
1. The script validates the file exists and is a valid image
2. Asks for your ImgBB API key (only first time)
3. Uploads the image to ImgBB to get a public URL with proper extension
4. Uses that URL for product search on 1688
5. Processes results normally

## Usage

### Single Local File

```bash
python watch_prices.py
# When prompted, enter:
/path/to/your/watch.jpg
```

Or drag and drop the file into the terminal!

### Multiple Local Files

```bash
python watch_prices.py
# When prompted, enter:
|||/path/to/watch1.jpg|||/path/to/watch2.jpg|||/path/to/watch3.jpg
```

### Mixed URLs and Local Files

You can mix both URLs and local file paths:

```bash
python watch_prices.py
# When prompted, enter:
|||https://example.com/watch.jpg|||/path/to/local/watch.png|||https://another-url.com/watch.jpg
```

## Drag and Drop Support

### macOS/Linux Terminal

1. Run the script: `python watch_prices.py`
2. When prompted for "Image URL(s) or path(s):"
3. **Drag and drop** your image file(s) from Finder into the terminal
4. The terminal will automatically paste the full file path (with escaped spaces - this is handled automatically!)
5. Press Enter

**For multiple files:**
- Type `|||` before each file
- Drag first file → type `|||` → drag second file → type `|||` → drag third file
- Press Enter

**Note:** macOS terminals escape spaces in paths with backslashes (e.g., `Screenshot\ 2025-10-09\ at\ 10.55.13\ PM.png`). The script automatically handles this, so just drag and drop without worrying about it!

### Example Terminal Session

```
🔗 Enter image URL(s) or local file path(s):
   - For single input: paste one URL or file path
   - For multiple inputs: separate with |||
   
Image URL(s) or path(s): /Users/you/Downloads/watch.jpg

✅ Found 1 input(s) to process
   1. [File] /Users/you/Downloads/watch.jpg

📝 Preparing input 1/1
📁 Local file detected: /Users/you/Downloads/watch.jpg
📝 Normalized path: /Users/you/Downloads/watch.jpg
✅ Valid image: (800, 600), JPEG
📤 Uploading local image to ImgBB...
✅ Image uploaded successfully: https://i.ibb.co/abc123/watch.jpg
```

## Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- WebP (.webp)
- BMP (.bmp)
- TIFF (.tiff)

## Notes

### About ImgBB
- **Free forever** - No credit card, no paid plans needed
- **Permanent storage** - Images never expire
- **Proper URLs** - Returns URLs with `.jpg`, `.png` etc extensions
- **Fast uploads** - Usually takes 1-2 seconds per image
- **Privacy** - Images are unlisted (not searchable, only accessible via direct link)

### Tips for Best Results
- Use online URLs when possible (no upload needed)
- For local files, get your ImgBB API key first
- Save API key to `.env` to avoid re-entering it
- Browser version works great with ImgBB URLs

## Tips

1. **File paths with spaces:** They work fine! Just drag and drop or use quotes:
   ```
   "/path/with spaces/to/image.jpg"
   # Or with escaped spaces (from drag-and-drop):
   /path/with\ spaces/to/image.jpg
   ```
   Both formats are automatically handled by the script.

2. **Relative paths:** Work too!
   ```
   ./Watches/A1.png
   ../images/watch.jpg
   ```

3. **Home directory:** Use `~` shortcut
   ```
   ~/Downloads/watch.jpg
   ```

4. **Check file exists:** If you get "File not found", double-check the path

5. **For best results:** Use the browser version (`watch_prices.py`) with ImgBB uploaded images

## Troubleshooting

### "Invalid API v1 key"
- Your ImgBB API key is incorrect or expired
- Get a new key from https://api.imgbb.com/
- Make sure you copied the full key (no extra spaces)

### "File not found"
- Check the file path is correct
- Try dragging and dropping the file instead of typing the path
- Make sure the file hasn't been moved or deleted

### "Invalid image file"
- Verify the file is actually an image
- Try opening it in an image viewer first
- Convert to JPEG or PNG if using an uncommon format

### "ImgBB upload failed"
- Check your internet connection
- Verify your API key is correct
- Try again in a few minutes (rare rate limits)
- If persistent, get a new API key

## Output

Results are saved to: **`Watched_prices.csv`**

The CSV includes:
- Original reference image URL (or ImgBB URL if uploaded from local file)
- Best matching 1688 product URL
- Product image URL
- Price
- Similarity score

