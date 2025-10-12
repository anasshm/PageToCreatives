#!/usr/bin/env python3
"""
Douyin Page Extractor - Simple Data Collection
Scrolls Douyin pages and collects all video data without any comparison or filtering
"""

import os
import sys
import csv
import time
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

def extract_user_id_from_url(url):
    """Extract user ID from Douyin URL"""
    try:
        # Format: https://www.douyin.com/user/MS4wLjABAAAA...
        if '/user/' in url:
            user_id = url.split('/user/')[-1].split('?')[0].split('/')[0]
            return user_id
        # Fallback: use hash of URL
        return f"page_{hash(url) % 100000}"
    except Exception as e:
        return f"page_{hash(url) % 100000}"

def scroll_and_load_all_videos(page, max_duration_minutes=30):
    """Scroll page to load all videos with time limit"""
    print(f"⏬ Scrolling to load all videos (max {max_duration_minutes} minutes)...")
    
    start_time = time.time()
    max_duration_seconds = max_duration_minutes * 60
    max_scrolls = 200
    scroll_pause_time = 2
    
    previous_height = None
    scroll_count = 0
    
    # Wait for page to fully load and find scroll container
    print("  ⏳ Waiting for page to load...")
    time.sleep(3)  # Give page time to fully render
    
    # Try to find the scroll container - use fallback if not found
    scroll_container_selector = """
        document.querySelector('.route-scroll-container') || 
        document.querySelector('#douyin-right-container') || 
        document.body
    """
    
    while scroll_count < max_scrolls:
        elapsed = time.time() - start_time
        if elapsed > max_duration_seconds:
            print(f"  ⏱️ Reached {max_duration_minutes} minute time limit")
            break
        
        # Scroll to bottom
        page.evaluate(f"({scroll_container_selector}).scrollTo(0, ({scroll_container_selector}).scrollHeight)")
        time.sleep(scroll_pause_time)
        
        # Get current scroll height
        current_height = page.evaluate(f"({scroll_container_selector}).scrollHeight")
        video_count = page.locator('a[href*="/video/"]').count()
        
        # Check if height changed (new content loaded)
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

def save_to_csv(videos, douyin_url, output_folder):
    """Save videos to CSV file in specified folder"""
    
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"✅ Created output folder: {output_folder}")
    
    # Generate filename based on user ID
    user_id = extract_user_id_from_url(douyin_url)
    csv_file = os.path.join(output_folder, f"{user_id}.csv")
    
    # Auto-increment if file exists
    counter = 1
    base_file = csv_file
    while os.path.exists(csv_file):
        csv_file = os.path.join(output_folder, f"{user_id}_{counter}.csv")
        counter += 1
    
    try:
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            # Write header comments
            f.write(f"# Source Page: {douyin_url}\n")
            f.write(f"# Total Videos: {len(videos)}\n")
            f.write(f"# Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            # Write CSV data
            fieldnames = ['video_url', 'thumbnail_url', 'likes', 'index']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(videos)
        
        print(f"💾 Saved {len(videos)} videos to {csv_file}")
        return csv_file
    except Exception as e:
        print(f"❌ Error saving CSV: {e}")
        return None

def main():
    """Main entry point"""
    
    print("📝 Douyin Page Extractor - Simple Data Collection")
    print("=" * 50)
    
    # Get output folder
    print("\n📁 Where should the CSV files be saved?")
    output_folder = input("Enter folder path (or press ENTER for current directory): ").strip()
    
    if not output_folder:
        output_folder = "."
    
    # Handle escaped spaces
    output_folder = output_folder.replace('\\', '')
    
    # Check if user entered a file instead of folder
    if output_folder.endswith('.py') or (os.path.exists(output_folder) and os.path.isfile(output_folder)):
        print(f"⚠️  That's a file, not a folder! Using current directory instead.")
        output_folder = "."
    
    print(f"✅ Output folder: {os.path.abspath(output_folder)}")
    
    # Get Douyin URLs
    print("\n🌐 Enter Douyin page URLs (one per line)")
    print("Press ENTER on an empty line when done:")
    
    page_urls = []
    while True:
        url = input().strip()
        if not url:
            break
        page_urls.append(url)
        print(f"  ✅ Added page {len(page_urls)}: {url[:80]}...")
    
    if not page_urls:
        print("❌ No URLs provided!")
        return False
    
    print(f"\n✅ Ready to process {len(page_urls)} pages")
    
    with sync_playwright() as p:
        # Launch browser
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
            print(f"\n✅ Loading cookies from {cookies_file}")
            with open(cookies_file, 'r') as f:
                storage_state = json.load(f)
        
        # Create context
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
        
        try:
            # Phase 1: Open ALL pages at once
            print(f"\n🌐 Phase 1: Opening {len(page_urls)} pages in separate tabs...")
            pages = []
            failed_urls = []
            
            for i, url in enumerate(page_urls, 1):
                try:
                    page = context.new_page()
                    
                    # Hide automation indicators
                    page.add_init_script("""
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        });
                    """)
                    
                    print(f"  Tab {i}: Loading {url[:60]}...")
                    page.goto(url, wait_until='domcontentloaded', timeout=120000)
                    pages.append(page)
                    print(f"    ✅ Tab {i} loaded successfully")
                    
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"    ⚠️ Tab {i} failed to load: {str(e)[:80]}")
                    print(f"    Skipping this page and continuing...")
                    failed_urls.append(url)
                    continue
            
            if not pages:
                print("❌ No pages loaded successfully!")
                browser.close()
                return False
            
            print(f"\n✅ Successfully loaded {len(pages)} out of {len(page_urls)} pages")
            if failed_urls:
                print(f"⚠️  Failed to load {len(failed_urls)} pages:")
                for url in failed_urls:
                    print(f"   - {url}")
            
            # Wait for user to complete ALL CAPTCHAs
            print("\n⏸️  CAPTCHA Check - MULTI-PAGE MODE")
            print("=" * 50)
            print(f"Please complete CAPTCHAs in ALL {len(pages)} tabs if needed.")
            print("When ALL CAPTCHAs are done, press ENTER to start scrolling...")
            input()
            
            # Phase 2: Process each page one by one
            print("\n🔄 Phase 2: Processing pages one by one...")
            print("=" * 50)
            
            all_csv_files = []
            successfully_loaded_urls = [url for url in page_urls if url not in failed_urls]
            
            for i, page in enumerate(pages, 1):
                print(f"\n{'=' * 50}")
                print(f"📄 Processing Page {i}/{len(pages)}")
                print(f"🌐 URL: {successfully_loaded_urls[i-1][:60]}...")
                print(f"{'=' * 50}")
                
                page.bring_to_front()
                
                try:
                    print(f"\n✅ Starting video collection for page {i}...")
                    
                    # Scroll and load all videos
                    total_videos = scroll_and_load_all_videos(page, max_duration_minutes=30)
                    
                    # Extract video data
                    videos = extract_videos_from_page(page)
                    
                    if not videos:
                        print(f"⚠️ No videos found on page {i}!")
                        page.close()
                        continue
                    
                    # Save to CSV
                    csv_file = save_to_csv(videos, successfully_loaded_urls[i-1], output_folder)
                    if csv_file:
                        all_csv_files.append(csv_file)
                    
                    print(f"\n✅ Page {i}/{len(pages)} complete: {len(videos)} videos saved")
                    
                    # Close page
                    print(f"🗑️  Closing Tab {i}...")
                    page.close()
                    
                except Exception as e:
                    print(f"❌ Error processing page {i}: {e}")
                    page.close()
                    continue
            
            # Save cookies for future use
            if not os.path.exists('douyin_cookies.json'):
                try:
                    storage = context.storage_state()
                    with open('douyin_cookies.json', 'w') as f:
                        json.dump(storage, f, indent=2)
                    print(f"\n💾 Cookies saved to douyin_cookies.json for future use!")
                except:
                    pass
            
            # Print final summary
            print(f"\n{'=' * 50}")
            print(f"🎉 All Done!")
            print(f"{'=' * 50}")
            print(f"📊 Total pages processed: {len(all_csv_files)}/{len(page_urls)}")
            print(f"📁 Output folder: {os.path.abspath(output_folder)}")
            print(f"\n📄 CSV Files Created:")
            for csv_file in all_csv_files:
                print(f"  - {csv_file}")
            print(f"{'=' * 50}")
            
            browser.close()
            return True
            
        except Exception as e:
            print(f"❌ Error during collection: {e}")
            browser.close()
            return False

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

