# 🚀 Setup Instructions

Quick setup guide for the Douyin Video Finder project.

## 📋 Prerequisites

- Python 3.8 or higher
- Git (for cloning the repository)
- Chrome browser (for cookie export)

## 🔧 Installation Steps

### 1. Clone the repository
```bash
git clone https://github.com/anasshm/PageToCreatives.git
cd PageToCreatives
```

### 2. Install Python dependencies
```bash
pip3 install -r requirements.txt
```

### 3. Install Playwright browsers
```bash
playwright install chromium
```

### 4. Set up your Google Gemini API key

Get your API key from: https://aistudio.google.com/app/apikey

Then set it as an environment variable:

**On macOS/Linux:**
```bash
export GOOGLE_API_KEY="your-api-key-here"
```

**On Windows (PowerShell):**
```powershell
$env:GOOGLE_API_KEY="your-api-key-here"
```

Or create a `.env` file in the project root:
```
GOOGLE_API_KEY=your-api-key-here
```

### 5. Set up Douyin cookies (for bypassing login)

Follow the instructions in `COOKIE_INSTRUCTIONS.md` to export your Douyin cookies.

---

## ✅ Verify Installation

Test that everything is installed correctly:

```bash
python3 -c "import playwright; import google.generativeai; import PIL; import imagehash; print('✅ All dependencies installed!')"
```

---

## 🎯 Quick Start

### Single Product Search:
```bash
python3 find_product_videos.py
```

### Multi-Product Search:
```bash
python3 Find_Multiple_Products.py
```

### Remove Duplicates:
```bash
python3 remove_duplicates.py Matches/GAMEBOY.csv
```

---

## 📁 Required Folders

The script will create these automatically, but you can create them manually:

```bash
mkdir -p Products Matches Research
```

- `Products/` - Put your reference product images here (for multi-product search)
- `Matches/` - Output CSV files with matching videos
- `Research/` - Output CSV files with non-matching videos

---

## 🆘 Troubleshooting

### "No module named 'playwright'"
```bash
pip3 install playwright
playwright install chromium
```

### "No module named 'google.generativeai'"
```bash
pip3 install google-generativeai
```

### "No module named 'imagehash'"
```bash
pip3 install imagehash
```

### "API key not found"
Make sure you've set the `GOOGLE_API_KEY` environment variable (see step 4 above).

### Playwright browser not found
```bash
playwright install chromium
```

---

## 📚 Documentation

- `README.md` - Project overview and features
- `COOKIE_INSTRUCTIONS.md` - How to export Douyin cookies
- `REMOVE_DUPLICATES_USAGE.md` - How to use the duplicate remover

---

## 🎉 You're Ready!

Everything should be set up now. Run your first search:

```bash
python3 find_product_videos.py
```

Happy scraping! 🚀

