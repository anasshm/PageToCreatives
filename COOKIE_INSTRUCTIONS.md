# How to Export Chrome Cookies for Douyin

The script needs your Chrome cookies to access Douyin without login. Here are **3 easy methods**:

---

## Method 1: Quick Export (Easiest - 2 minutes)

### Using Cookie-Editor Extension

1. **Install the extension:**
   - Go to: https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm
   - Click "Add to Chrome"

2. **Open Douyin in Chrome:**
   - Go to: https://www.douyin.com
   - Browse around for a few seconds (no need to login)

3. **Export cookies:**
   - Click the Cookie-Editor icon in Chrome toolbar
   - Click "Export" button at the bottom
   - Click "Copy to clipboard"

4. **Save to file:**
   ```bash
   cd "/Users/zak/Downloads/Find all products in Douyin page"
   ```
   
   Then create a file called `chrome_cookies_raw.json` and paste the cookies.

5. **Convert to Playwright format:**
   ```bash
   python3 convert_cookies.py
   ```

6. **Done!** Run your script:
   ```bash
   python3 find_product_videos.py
   ```

---

## Method 2: EditThisCookie Extension

1. Install "EditThisCookie" extension from Chrome Web Store
2. Go to douyin.com in Chrome
3. Click the cookie icon
4. Click "Export" (bottom left)
5. Save as `chrome_cookies_raw.json`
6. Run: `python3 convert_cookies.py`

---

## Method 3: Automatic Export (Advanced)

**Note:** Chrome must be completely closed for this to work.

1. **Close Chrome completely** (Quit, not just close windows)

2. Run the export script:
   ```bash
   python3 export_chrome_cookies.py
   ```

3. If successful, you'll get `douyin_cookies.json` automatically!

---

## How to Use Cookies

Once you have `douyin_cookies.json`, the script will automatically use it:

```bash
python3 find_product_videos.py
```

You'll see:
```
✅ Loading cookies from douyin_cookies.json
```

No more login prompts! 🎉

---

## Troubleshooting

### "No cookies found"
- Make sure you visited douyin.com in Chrome first
- Browse around the site for a few seconds
- Try again

### "Chrome database locked"
- Completely quit Chrome (Cmd+Q)
- Try the export script again

### Still getting login prompt?
- Delete `douyin_cookies.json`
- Visit douyin.com in Chrome (in regular mode, not incognito)
- Export cookies again using Method 1

---

## Files You'll Have

- `douyin_cookies.json` - Final cookies file (used by script)
- `chrome_cookies_raw.json` - Raw export (temporary)
- `ref.png` - Your product reference image
- `matching_videos.csv` - Results

---

Need help? The script will auto-save cookies after a successful run if you solve the CAPTCHA during the 30-second wait!
