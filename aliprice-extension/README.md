# AliPrice Image Search Extension with AI Comparison

A Chrome extension that adds a right-click context menu option to search any image on AliPrice, then automatically compares products using Google's Gemini AI and generates a CSV report.

## Features

✅ Right-click any image to search on AliPrice
✅ Automatically scrolls to load ~100 products
✅ AI-powered image comparison using Gemini API
✅ Scores products based on Shape, Strap, Dial, and Color
✅ Downloads comparison results as CSV file

## Installation

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable **Developer mode** (toggle in the top-right corner)
3. Click **Load unpacked**
4. Select the `aliprice-extension` folder
5. The extension is now installed!

## Usage

1. Navigate to any webpage with images (e.g., Douyin, social media, etc.)
2. Right-click on a watch/product image
3. Select **"Search on AliPrice"** from the context menu
4. A new tab will open with AliPrice search results
5. **Wait 10 seconds** - the extension will automatically:
   - Scroll the page to load products
   - Extract the reference image and product images
   - Compare each product using AI
   - Download a CSV file with scores

## How It Works

### Step 1: Image Search
- Captures the image URL when you right-click
- URL-encodes the image link
- Opens AliPrice search: `https://www.aliprice.com/Index/searchByImage.html?image=[ENCODED_URL]`

### Step 2: Auto-Scroll & Extract
- Waits 10 seconds for page load
- Scrolls 10 times to load ~100 products
- Extracts reference image from `.imgsearch-banner-box`
- Extracts product images from `li.image_li` containers

### Step 3: AI Comparison
- Converts images to base64
- Sends to Gemini API for comparison
- Scores each product on:
  - **SHAPE** (35% weight)
  - **STRAP** (25% weight)
  - **DIAL** (25% weight)
  - **COLOR** (15% weight)

### Step 4: CSV Export
- Generates CSV with all product scores
- Downloads automatically with timestamp
- Format: `aliprice_comparison_YYYY-MM-DDTHH-MM-SS.csv`

## CSV Columns

- `reference_image_url` - Original reference image
- `product_number` - Product index
- `final_score` - Weighted total score (0-100)
- `shape_score` - Shape similarity (0-100)
- `strap_score` - Strap similarity (0-100)
- `dial_score` - Dial similarity (0-100)
- `color_score` - Color similarity (0-100)
- `price` - Product price
- `1688_url` - Product page URL
- `1688_product_image_url` - Product image URL

## Files

- `manifest.json` - Extension configuration (Manifest V3)
- `background.js` - Service worker with Gemini API integration
- `content.js` - Content script for page interaction
- `README.md` - This file

## Permissions

- `contextMenus` - Add right-click menu option
- `downloads` - Download CSV files
- `activeTab` - Access current tab
- `scripting` - Inject content script
- `host_permissions` - Access AliPrice and image URLs

## Notes

- This extension is for **personal use only** (API key is hardcoded)
- Comparison may take several minutes for 100 products
- Check browser console for progress logs
- Results are saved to your Downloads folder

