# 🏷️ AI Tagging System - Usage Guide

Complete guide to using the AI-powered product tagging system for your Douyin research videos.

---

## 📋 What You Get

After setup, you'll have:
- ✅ **Structured tags** for all products (shape, color, material, style)
- ✅ **Smart search** with synonym support (search "fourleaf" → finds "clover")
- ✅ **Automatic pairing** to match necklaces with earrings
- ✅ **Multi-filter search** by product type, likes, index, and tags
- ✅ **Fast processing** - 50 videos processed simultaneously

---

## 🚀 Quick Start (3 Steps)

### Step 1: Tag Your Videos (First Time)

Run the tagging script on your Research CSV:

```bash
python3 tag_research_videos.py "Research last OCT6.csv"
```

**You'll be asked:**
- Test mode? (y/n) → Type `y` to tag only 100 videos first (recommended)
- API key if not already set in .env

**What happens:**
- Downloads each thumbnail
- Uses Gemini AI to analyze and tag
- Saves results to `Research last OCT6_tagged.json`
- Takes ~2-3 minutes for 100 videos (test mode)

### Step 2: Generate Gallery

Create the interactive HTML gallery:

```bash
python3 generate_tagged_research_gallery.py "Research last OCT6_tagged.json"
```

**Output:**
- Creates `tagged_research_gallery.html`
- Open in your browser to start searching!

### Step 3: Use the Gallery

Open `tagged_research_gallery.html` and:

1. **Search by tag**: Type "clover", "butterfly", "fourleaf", etc.
2. **Filter by product type**: Select necklace, earring, etc.
3. **Filter by likes/index**: Set min/max ranges
4. **Find pairs**: Click "Find Pairs" to see matching sets

---

## 🎯 Example Workflows

### Workflow 1: Find All Clover Products

```
1. Open tagged_research_gallery.html
2. Type "clover" in search box
3. Click "Search"
→ See ALL clover products (necklaces, earrings, rings)
```

**Smart search finds:**
- "clover" ✅
- "fourleaf" ✅
- "four-leaf" ✅
- "quatrefoil" ✅
- "shamrock" ✅

### Workflow 2: Find Black Gold Clover Necklaces

```
1. Search: "clover"
2. Product Type: "necklace"
3. Additional search: "black" and "gold"
4. Click "Apply Filters"
→ See only black/gold clover necklaces
```

### Workflow 3: Find Matching Earrings for Your Necklace

```
1. Find your necklace (e.g., clover-black-gold)
2. Note the pairing key tag
3. Product Type: "earring"
4. Search by the same pairing key
→ See all matching earrings!
```

**Or use the automatic way:**
```
1. Click "Find Pairs" button
→ Automatically shows matching sets!
```

---

## 🔧 Configuration

### Tagging Settings (Already Configured)

- **AI Model**: `gemini-2.5-flash-lite-preview-09-2025` (same as find_product_videos.py)
- **Parallel Processing**: 50 videos at once
- **Batch Size**: 50 videos per batch
- **Rate Limit**: Respects Gemini API limits

### Taxonomy (product_taxonomy.json)

Contains all valid tags organized by category:

**Shapes:**
- clover, butterfly, leaf, star, heart, flower, shell, circle, bow, crown, cross

**Product Types:**
- necklace, earring, ring, bracelet, watch, brooch

**Materials:**
- pearl, mother-of-pearl, crystal, diamond, enamel, resin

**Metal Colors:**
- gold, silver, rose-gold, two-tone

**Colors:**
- black, white, red, blue, green, pink, purple, yellow, brown, multicolor

**Styles:**
- luxury, vintage, modern, statement, delicate

### Customize Taxonomy

Edit `product_taxonomy.json` to add:
- New shapes
- Synonyms for existing tags
- New materials or colors

```json
{
  "shapes": {
    "your-shape": {
      "primary": "your-shape",
      "synonyms": ["synonym1", "synonym2"],
      "description": "Description"
    }
  }
}
```

---

## 📊 Tag Structure

Each video gets tagged with:

```json
{
  "product_type": "necklace",
  "primary_shape": "clover",
  "secondary_shapes": ["circle"],
  "primary_color": "black",
  "secondary_colors": [],
  "metal_color": "gold",
  "materials": ["enamel", "crystal"],
  "style": "luxury",
  "size": "small",
  "pairing_key": "clover-black-gold"
}
```

**Pairing Key Format:**
`{primary_shape}-{primary_color}-{metal_color}`

Example: `clover-black-gold`

This allows automatic matching of necklaces and earrings!

---

## 🎨 Gallery Features

### 1. Smart Search
- Type any tag or synonym
- Shows expansion: "Also searching: clover, fourleaf, quatrefoil..."
- Searches all tag categories (shape, color, material, etc.)

### 2. Multi-Filter
- **Product Type**: Filter by necklace, earring, etc.
- **Likes Range**: Min/max likes
- **Index Range**: Min/max index
- All filters work together!

### 3. Find Pairs
- Automatically groups products with same pairing key
- Shows largest groups first
- Perfect for finding matching sets

### 4. Visual Tags
- Each product shows colored tags:
  - 🔵 Blue = Shape tags
  - 🟣 Purple = Product type
  - ⚫ Gray = Color tags
  - 🟢 Green = Material tags
  - 🔴 Red = Pairing key

### 5. Pagination
- 100 products per page
- Fast loading (doesn't crash browser)
- Smooth navigation

---

## 💡 Tips & Tricks

### Tip 1: Start with Test Mode
```bash
# Tag only 100 videos first
python3 tag_research_videos.py "Research last OCT6.csv"
# When asked: y for test mode
```

Check the results, adjust taxonomy if needed, then run full tagging.

### Tip 2: Use Multiple Search Terms
```
Search: "clover black"
→ Finds products tagged with BOTH clover AND black
```

### Tip 3: Save Common Searches
Bookmark the gallery HTML with your filters applied!

### Tip 4: Re-tag When Needed
If you update the taxonomy, re-run tagging:
```bash
python3 tag_research_videos.py "Research last OCT6.csv"
# New tags will overwrite old ones
```

---

## 🔍 Troubleshooting

### "Rate limit error (429)"
- You hit Gemini API quota
- **Solution**: Wait a few minutes, then resume
- Free tier: 60 requests per minute

### "Download failed" for thumbnails
- Some Douyin URLs expire
- **Solution**: Normal, script will skip and continue

### Search returns no results
- Check spelling
- Try synonyms (e.g., "fourleaf" instead of "clover")
- Check if videos are actually tagged (test mode only tags 100)

### Gallery loads slowly
- Normal for 50K videos
- Pagination helps (100 per page)
- Use filters to reduce results

---

## 📈 Performance

### Tagging Speed
- **Test mode (100 videos)**: ~2-3 minutes
- **Full dataset (50K videos)**: ~2-3 hours
- **Parallel processing**: 50 videos at once

### API Costs
- Gemini 2.5 Flash Lite: Free tier available
- Approximately 1 API call per video
- 50K videos = 50K API calls

---

## 🎯 Example Tag Results

### Example 1: Black Clover Necklace
```json
{
  "product_type": "necklace",
  "primary_shape": "clover",
  "primary_color": "black",
  "metal_color": "gold",
  "materials": ["enamel", "crystal"],
  "style": "luxury",
  "pairing_key": "clover-black-gold"
}
```

**Searchable by:**
- clover, fourleaf, quatrefoil, shamrock
- necklace, pendant
- black, noir
- gold, golden
- enamel

### Example 2: Pearl Drop Earrings
```json
{
  "product_type": "earring",
  "primary_shape": "shell",
  "primary_color": "white",
  "metal_color": "gold",
  "materials": ["pearl", "crystal"],
  "style": "luxury",
  "pairing_key": "shell-white-gold"
}
```

---

## 🔄 Full Workflow

```mermaid
Research CSV
    ↓
[Tag Videos]
    ↓
Tagged JSON
    ↓
[Generate Gallery]
    ↓
HTML Gallery
    ↓
[Search & Filter]
    ↓
Find Products!
```

---

## 📚 Related Files

- `product_taxonomy.json` - Tag vocabulary with synonyms
- `tag_research_videos.py` - AI tagging script
- `generate_tagged_research_gallery.py` - Gallery generator
- `tagged_research_gallery.html` - Interactive gallery (output)
- `Research last OCT6_tagged.json` - Tagged data (output)

---

## 🎉 You're Ready!

Start with test mode to tag 100 videos, then run full tagging when you're happy with the results!

```bash
# Step 1: Test with 100 videos
python3 tag_research_videos.py "Research last OCT6.csv"
# → Choose 'y' for test mode

# Step 2: Generate gallery
python3 generate_tagged_research_gallery.py "Research last OCT6_tagged.json"

# Step 3: Open tagged_research_gallery.html in browser
open tagged_research_gallery.html
```

Happy product hunting! 🚀

