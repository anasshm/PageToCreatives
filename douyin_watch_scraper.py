#!/usr/bin/env python3
"""
Douyin Watch Scraper with Deduplication
Scrapes watch images from Douyin pages and eliminates duplicates using perceptual hashing + AI attribute extraction
"""

import os
import sys
import csv
import time
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import google.generativeai as genai
from PIL import Image
import io
import requests
from concurrent.futures import ThreadPoolExecutor
import imagehash

def setup_gemini_api():
    """Setup Gemini API with user's API key"""
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("🔑 Gemini API Key Setup")
        print("=" * 30)
        api_key = input("Enter your Google AI Studio API key: ").strip()
        
        if not api_key:
            print("❌ No API key provided!")
            return None
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash-lite-preview-09-2025')
        print("✅ Gemini API configured successfully (using gemini-2.5-flash-lite-preview-09-2025)")
        return model
    except Exception as e:
        print(f"❌ Error configuring Gemini API: {e}")
        return None

def download_thumbnail(url):
    """Download thumbnail from URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        image = Image.open(io.BytesIO(response.content))
        return image
    except Exception as e:
        print(f"  ⚠️ Error downloading thumbnail: {e}")
        return None

def calculate_perceptual_hash(image):
    """Calculate perceptual hash using pHash algorithm"""
    try:
        phash = imagehash.phash(image, hash_size=8)
        return str(phash)
    except Exception as e:
        print(f"  ⚠️ Error calculating phash: {e}")
        return None

def check_multiple_products(model, image):
    """Filter 1: Check if image contains multiple products
    Returns: (is_single_product: bool or None, error: str or None)
    """
    max_retries = 2
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            prompt = '''Look at this image carefully.

How many DISTINCT watch/jewelry products are visible?

Count separate products, not:
- Same product shown from different angles
- Reflections or shadows of one product
- Product + packaging/box

Answer with ONLY ONE WORD:
- "SINGLE" if exactly one product
- "MULTIPLE" if two or more different products
- "NONE" if no products visible'''

            response = model.generate_content([prompt, image])
            
            if response and response.text:
                answer = response.text.strip().upper()
                
                if "SINGLE" in answer:
                    return (True, None)
                elif "MULTIPLE" in answer or "NONE" in answer:
                    return (False, None)
                else:
                    return (None, 'invalid_response')
            else:
                return (None, 'empty_response')
                
        except Exception as e:
            error_msg = str(e).lower()
            
            if "quota" in error_msg or "rate limit" in error_msg or "429" in error_msg:
                if attempt < max_retries - 1:
                    print(f"  ⚠️ Rate limit hit, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                else:
                    return (None, 'rate_limit')
            else:
                return (None, f'api_error: {str(e)[:100]}')
    
    return (None, 'max_retries_exceeded')

def extract_watch_attributes(model, image):
    """Filter 2: Extract watch attributes for fingerprinting
    Returns: (attributes_dict, error)
    """
    max_retries = 2
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            prompt = '''Analyze this watch and extract these attributes:

1. CASE_SHAPE: round, square, rectangular, oval, triangular, other
2. CASE_COLOR: gold, silver, rose-gold, black, other
3. DIAL_COLOR: white, black, gold, blue, pink, other
4. DIAL_MARKERS: roman, arabic, minimalist, crystals, mixed, other
5. STRAP_TYPE: metal-bracelet, leather, fabric, other
6. STRAP_COLOR: gold, silver, black, brown, tan, pink, other

Answer in this EXACT format (one per line):
CASE_SHAPE: [value]
CASE_COLOR: [value]
DIAL_COLOR: [value]
DIAL_MARKERS: [value]
STRAP_TYPE: [value]
STRAP_COLOR: [value]'''

            response = model.generate_content([prompt, image])
            
            if response and response.text:
                answer = response.text.strip()
                
                # Parse response into dict
                attributes = {}
                for line in answer.split('\n'):
                    line = line.strip()
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip().lower()
                        
                        if key in ['CASE_SHAPE', 'CASE_COLOR', 'DIAL_COLOR', 'DIAL_MARKERS', 'STRAP_TYPE', 'STRAP_COLOR']:
                            attributes[key] = value
                
                # Verify all required attributes are present
                required = ['CASE_SHAPE', 'CASE_COLOR', 'DIAL_COLOR', 'DIAL_MARKERS', 'STRAP_TYPE', 'STRAP_COLOR']
                if all(key in attributes for key in required):
                    return (attributes, None)
                else:
                    return (None, 'incomplete_attributes')
            else:
                return (None, 'empty_response')
                
        except Exception as e:
            error_msg = str(e).lower()
            
            if "quota" in error_msg or "rate limit" in error_msg or "429" in error_msg:
                if attempt < max_retries - 1:
                    print(f"  ⚠️ Rate limit hit, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                else:
                    return (None, 'rate_limit')
            else:
                return (None, f'api_error: {str(e)[:100]}')
    
    return (None, 'max_retries_exceeded')

def generate_watch_fingerprint(attributes):
    """Generate unique fingerprint from attributes"""
    fingerprint_str = f"{attributes['CASE_SHAPE']}|{attributes['CASE_COLOR']}|{attributes['DIAL_COLOR']}|{attributes['DIAL_MARKERS']}|{attributes['STRAP_TYPE']}|{attributes['STRAP_COLOR']}"
    return fingerprint_str

def load_database():
    """Load processed_watches_db.json or create if missing"""
    db_file = 'processed_watches_db.json'
    
    if os.path.exists(db_file):
        try:
            with open(db_file, 'r', encoding='utf-8') as f:
                db = json.load(f)
                
                # Migrate old format: list to dict
                if isinstance(db.get('phashes'), list):
                    print(f"⚠️ Migrating old database format (list → dict)...")
                    old_phashes = db['phashes']
                    db['phashes'] = {}
                    # Old phashes won't have URLs, so they'll just be lost in migration
                    # This is okay since it's just a one-time migration
                    print(f"   Cleared {len(old_phashes)} old phashes (no URL data available)")
                
                print(f"✅ Loaded database: {len(db.get('phashes', {}))} phashes, {len(db.get('fingerprints', {}))} fingerprints")
                return db
        except Exception as e:
            print(f"⚠️ Error loading database: {e}")
            print("Creating new database...")
    
    # Create new database
    db = {
        'phashes': {},  # Dict to store phash -> URL mapping
        'fingerprints': {}
    }
    return db

def save_database(db):
    """Save database to JSON file"""
    db_file = 'processed_watches_db.json'
    
    try:
        with open(db_file, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=2, ensure_ascii=False)
        print(f"💾 Database saved: {len(db['phashes'])} phashes, {len(db['fingerprints'])} fingerprints")
        return True
    except Exception as e:
        print(f"❌ Error saving database: {e}")
        return False

def is_duplicate_phash(phash, db):
    """Check if perceptual hash exists in database
    Returns: (is_duplicate: bool, duplicate_url: str or None)
    """
    if phash in db.get('phashes', {}):
        return (True, db['phashes'][phash])
    return (False, None)

def is_duplicate_fingerprint(fingerprint, db):
    """Check if fingerprint exists in database
    Returns: (is_duplicate: bool, duplicate_url: str or None)
    """
    if fingerprint in db.get('fingerprints', {}):
        return (True, db['fingerprints'][fingerprint]['thumbnail_url'])
    return (False, None)

def add_to_database(db, phash, fingerprint, thumbnail_url):
    """Add new watch to database"""
    # Add phash with URL
    if phash and phash not in db['phashes']:
        db['phashes'][phash] = thumbnail_url
    
    # Add fingerprint
    if fingerprint and fingerprint not in db['fingerprints']:
        db['fingerprints'][fingerprint] = {
            'first_seen': time.strftime('%Y-%m-%d'),
            'thumbnail_url': thumbnail_url,
            'count': 1
        }
    elif fingerprint:
        db['fingerprints'][fingerprint]['count'] += 1

def process_watch_thumbnail(model, video, db, video_num, total):
    """
    Process single watch through deduplication pipeline
    
    Returns: (result, error)
      result: dict if unique, None if duplicate/filtered
    """
    try:
        # Step 1: Download thumbnail
        image = download_thumbnail(video['thumbnail_url'])
        if not image:
            print(f"  [{video_num}/{total}] ⚠️ Failed to download thumbnail")
            return (None, 'download_failed')
        
        # Step 2: Perceptual hash check
        phash = calculate_perceptual_hash(image)
        if not phash:
            print(f"  [{video_num}/{total}] ⚠️ Failed to calculate phash")
            return (None, 'phash_failed')
        
        is_dup_phash, dup_url = is_duplicate_phash(phash, db)
        if is_dup_phash:
            print(f"  [{video_num}/{total}] ⏭️  SKIP - Duplicate image (phash)")
            print(f"      Dup: {dup_url[:80]}...")
            return (None, 'duplicate_phash')
        
        # Step 3: AI Filter 1 - Multiple products check
        is_single, error = check_multiple_products(model, image)
        if error:
            if 'rate_limit' in str(error):
                print(f"  [{video_num}/{total}] 🚫 RATE LIMIT")
            else:
                print(f"  [{video_num}/{total}] ⚠️ ERROR: {error}")
            return (None, error)
        
        if not is_single:
            print(f"  [{video_num}/{total}] ⏭️  SKIP - Multiple products")
            return (None, 'multiple_products')
        
        # Step 4: AI Filter 2 - Extract attributes
        attributes, error = extract_watch_attributes(model, image)
        if error:
            if 'rate_limit' in str(error):
                print(f"  [{video_num}/{total}] 🚫 RATE LIMIT")
            else:
                print(f"  [{video_num}/{total}] ⚠️ ERROR: {error}")
            return (None, error)
        
        # Step 5: Fingerprint check
        fingerprint = generate_watch_fingerprint(attributes)
        is_dup_fingerprint, dup_url = is_duplicate_fingerprint(fingerprint, db)
        if is_dup_fingerprint:
            print(f"  [{video_num}/{total}] ⏭️  SKIP - Duplicate watch (attributes)")
            print(f"      Fingerprint: {fingerprint}")
            print(f"      Dup: {dup_url[:80]}...")
            return (None, 'duplicate_fingerprint')
        
        # Step 6: Unique watch found!
        print(f"  [{video_num}/{total}] ✅ UNIQUE WATCH - {fingerprint}")
        return ({
            'video_url': video['video_url'],
            'thumbnail_url': video['thumbnail_url'],
            'likes': video['likes'],
            'phash': phash,
            'fingerprint': fingerprint,
            'attributes': attributes
        }, None)
        
    except Exception as e:
        print(f"  [{video_num}/{total}] ⚠️ Processing error: {e}")
        return (None, f'processing_error: {str(e)}')

def scroll_and_load_all_videos(page, max_duration_minutes=30):
    """Scroll page to load all videos with time limit"""
    print(f"⏬ Scrolling to load all videos (max {max_duration_minutes} minutes)...")
    
    start_time = time.time()
    max_duration_seconds = max_duration_minutes * 60
    max_scrolls = 200
    scroll_pause_time = 2
    
    previous_height = None
    scroll_count = 0
    
    scroll_container_selector = "document.querySelector('.route-scroll-container')"
    
    while scroll_count < max_scrolls:
        elapsed = time.time() - start_time
        if elapsed > max_duration_seconds:
            print(f"  ⏱️ Reached {max_duration_minutes} minute time limit")
            break
        
        page.evaluate(f"{scroll_container_selector}.scrollTo(0, {scroll_container_selector}.scrollHeight)")
        time.sleep(scroll_pause_time)
        
        current_height = page.evaluate(f"{scroll_container_selector}.scrollHeight")
        video_count = page.locator('a[href*="/video/"]').count()
        
        if current_height == previous_height:
            print(f"  ✅ No more content to load. Found {video_count} videos.")
            break
        
        print(f"  📊 Loaded {video_count} videos... (elapsed: {int(elapsed)}s)")
        previous_height = current_height
        scroll_count += 1
    
    final_count = page.locator('a[href*="/video/"]').count()
    print(f"✅ Finished scrolling. Total videos: {final_count}")
    return final_count

def extract_videos_from_page(page):
    """Extract video URLs, thumbnail URLs, and likes from page"""
    print("🔍 Extracting video data from page...")
    
    try:
        page.wait_for_selector('img', timeout=10000)
        
        videos = page.evaluate("""
            () => {
                const videoLinks = document.querySelectorAll('a[href*="/video/"]');
                const videos = [];
                
                videoLinks.forEach((link, index) => {
                    const videoUrl = link.href;
                    const img = link.querySelector('img');
                    const thumbnailUrl = img ? (img.src || img.getAttribute('data-src')) : null;
                    
                    let likes = '';
                    
                    const container = link.closest('li') || link.closest('div[class*="video"]');
                    if (container) {
                        const likeSelectors = [
                            'span[class*="count"]',
                            'span[class*="like"]',
                            'div[class*="count"]',
                            'div[class*="digg"]',
                            'span[class*="digg"]'
                        ];
                        
                        for (const selector of likeSelectors) {
                            const elements = container.querySelectorAll(selector);
                            for (const el of elements) {
                                const text = el.textContent.trim();
                                if (text && /[\d.]+[wkm万千]?/i.test(text)) {
                                    likes = text;
                                    break;
                                }
                            }
                            if (likes) break;
                        }
                    }
                    
                    if (videoUrl && thumbnailUrl) {
                        videos.push({
                            video_url: videoUrl,
                            thumbnail_url: thumbnailUrl,
                            likes: likes || 'N/A',
                            index: index + 1
                        });
                    }
                });
                
                return videos;
            }
        """)
        
        print(f"✅ Extracted {len(videos)} videos with thumbnails and likes")
        return videos
        
    except Exception as e:
        print(f"❌ Error extracting videos: {e}")
        return []

def save_to_csv(unique_watches, douyin_url):
    """Save unique watches to CSV file"""
    # Auto-increment filename if exists
    base_filename = 'watch_sources'
    csv_file = f'{base_filename}.csv'
    counter = 1
    
    while os.path.exists(csv_file):
        csv_file = f'{base_filename}{counter}.csv'
        counter += 1
    
    try:
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            # Write header comments
            f.write(f"# Source Page: {douyin_url}\n")
            f.write(f"# Unique Watches: {len(unique_watches)}\n")
            f.write(f"# Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            # Write CSV data
            fieldnames = ['video_url', 'thumbnail_url', 'likes', 'case_shape', 'case_color', 
                         'dial_color', 'dial_markers', 'strap_type', 'strap_color', 
                         'fingerprint', 'phash']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for watch in unique_watches:
                row = {
                    'video_url': watch['video_url'],
                    'thumbnail_url': watch['thumbnail_url'],
                    'likes': watch['likes'],
                    'case_shape': watch['attributes']['CASE_SHAPE'],
                    'case_color': watch['attributes']['CASE_COLOR'],
                    'dial_color': watch['attributes']['DIAL_COLOR'],
                    'dial_markers': watch['attributes']['DIAL_MARKERS'],
                    'strap_type': watch['attributes']['STRAP_TYPE'],
                    'strap_color': watch['attributes']['STRAP_COLOR'],
                    'fingerprint': watch['fingerprint'],
                    'phash': watch['phash']
                }
                writer.writerow(row)
        
        print(f"💾 Saved {len(unique_watches)} unique watches to {csv_file}")
        return csv_file
    except Exception as e:
        print(f"❌ Error saving CSV: {e}")
        return None

def main():
    """Main entry point"""
    # Try to load API key from .env file
    if os.path.exists('.env'):
        try:
            with open('.env', 'r') as f:
                for line in f:
                    if line.startswith('GEMINI_API_KEY='):
                        api_key = line.split('=', 1)[1].strip()
                        os.environ['GEMINI_API_KEY'] = api_key
                        break
        except:
            pass
    
    print("🔍 Douyin Watch Scraper with Deduplication")
    print("=" * 50)
    
    # Setup Gemini API
    model = setup_gemini_api()
    if not model:
        return False
    
    # Get Douyin page URL
    douyin_url = input("\n🌐 Enter Douyin page URL: ").strip()
    if not douyin_url:
        print("❌ No URL provided!")
        return False
    
    print(f"\n🌐 Opening Douyin page: {douyin_url}")
    
    with sync_playwright() as p:
        # Launch browser with anti-detection settings
        browser = p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process'
            ]
        )
        
        # Load cookies if available
        cookies_file = 'douyin_cookies.json'
        storage_state = None
        
        if os.path.exists(cookies_file):
            print(f"✅ Loading cookies from {cookies_file}")
            with open(cookies_file, 'r') as f:
                storage_state = json.load(f)
        else:
            print(f"ℹ️ No cookies file found. Create '{cookies_file}' to avoid login.")
        
        # Create context with realistic browser fingerprint
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York',
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Referer': 'https://www.douyin.com/',
            },
            storage_state=storage_state
        )
        
        # Hide automation indicators
        page = context.new_page()
        
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        try:
            # Navigate to page
            page.goto(douyin_url, wait_until='networkidle', timeout=60000)
            
            # Wait for user to complete CAPTCHA manually
            print("\n⏸️  CAPTCHA Check")
            print("=" * 50)
            print("If you see a CAPTCHA, please complete it now.")
            print("When ready, press ENTER to start collecting videos...")
            input()
            print("\n✅ Starting video collection...")
            
            # Scroll and load all videos
            total_videos = scroll_and_load_all_videos(page, max_duration_minutes=30)
            
            # Extract video data
            videos = extract_videos_from_page(page)
            
            if not videos:
                print("❌ No videos found on page!")
                browser.close()
                return False
            
            # Load database
            print(f"\n📂 Loading watch database...")
            db = load_database()
            
            # Process all thumbnails with parallel processing
            print(f"\n🔎 Analyzing {len(videos)} videos with deduplication...")
            print("=" * 50)
            
            unique_watches = []
            stats = {
                'total': len(videos),
                'duplicate_phash': 0,
                'multiple_products': 0,
                'duplicate_fingerprint': 0,
                'unique': 0,
                'errors': 0
            }
            
            # Process in batches
            batch_size = 50
            total_batches = (len(videos) + batch_size - 1) // batch_size
            
            with ThreadPoolExecutor(max_workers=50) as executor:
                for batch_num in range(total_batches):
                    start_idx = batch_num * batch_size
                    end_idx = min(start_idx + batch_size, len(videos))
                    batch = videos[start_idx:end_idx]
                    
                    print(f"\n📦 Processing batch {batch_num + 1}/{total_batches} ({len(batch)} videos)")
                    print(f"   Videos {start_idx + 1}-{end_idx} of {len(videos)}")
                    
                    # Submit all videos in batch to thread pool
                    futures = []
                    for i, video in enumerate(batch):
                        video_num = start_idx + i + 1
                        future = executor.submit(
                            process_watch_thumbnail,
                            model, video, db, video_num, len(videos)
                        )
                        futures.append((future, video))
                    
                    # Collect results
                    batch_unique = 0
                    for future, video in futures:
                        try:
                            result, error = future.result(timeout=30)
                            
                            if error:
                                # Track error
                                if error == 'duplicate_phash':
                                    stats['duplicate_phash'] += 1
                                elif error == 'multiple_products':
                                    stats['multiple_products'] += 1
                                elif error == 'duplicate_fingerprint':
                                    stats['duplicate_fingerprint'] += 1
                                else:
                                    stats['errors'] += 1
                            elif result:
                                unique_watches.append(result)
                                batch_unique += 1
                                stats['unique'] += 1
                                
                                # Add to database
                                add_to_database(db, result['phash'], result['fingerprint'], result['thumbnail_url'])
                        except Exception as e:
                            print(f"  ⚠️ Thread error: {e}")
                            stats['errors'] += 1
                    
                    print(f"   ✅ Batch complete: {batch_unique} unique watches found")
                    
                    # Small delay between batches
                    if batch_num < total_batches - 1:
                        time.sleep(0.5)
            
            # Save database
            print(f"\n💾 Saving database...")
            save_database(db)
            
            # Save results to CSV
            if unique_watches:
                print(f"\n💾 Saving results...")
                csv_file = save_to_csv(unique_watches, douyin_url)
            else:
                print(f"\n⚠️ No unique watches found - no CSV created")
                csv_file = None
            
            # Print summary statistics
            print(f"\n{'=' * 50}")
            print(f"🎉 Processing Complete!")
            print(f"{'=' * 50}")
            print(f"📊 STATISTICS:")
            print(f"   Total videos processed: {stats['total']}")
            print(f"   ✅ Unique watches found: {stats['unique']}")
            print(f"   ⏭️  Duplicate images (phash): {stats['duplicate_phash']}")
            print(f"   ⏭️  Multiple products filtered: {stats['multiple_products']}")
            print(f"   ⏭️  Duplicate watches (attributes): {stats['duplicate_fingerprint']}")
            print(f"   ⚠️  Errors: {stats['errors']}")
            print(f"{'=' * 50}")
            
            if csv_file:
                print(f"📄 Results saved to: {csv_file}")
                print(f"💾 Database updated: processed_watches_db.json")
            
            # Save cookies for future use if not already saved
            if not os.path.exists('douyin_cookies.json'):
                try:
                    storage = context.storage_state()
                    with open('douyin_cookies.json', 'w') as f:
                        json.dump(storage, f, indent=2)
                    print(f"💾 Cookies saved to douyin_cookies.json for future use!")
                except:
                    pass
            
            # Close browser after all processing is complete
            browser.close()
            print(f"✅ Browser closed")
            
            return True
            
        except Exception as e:
            print(f"❌ Error during scraping: {e}")
            import traceback
            traceback.print_exc()
            browser.close()
            return False

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

