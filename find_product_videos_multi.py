#!/usr/bin/env python3
"""
Douyin Product Finder - Multi-Page Version
Finds all videos containing a specific product across MULTIPLE Douyin pages
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
        # Use latest Gemini 2.5 Flash model (September 2025)
        model = genai.GenerativeModel('gemini-2.5-flash-lite-preview-09-2025')
        print("✅ Gemini API configured successfully (using gemini-2.5-flash-lite-preview-09-2025)")
        return model
    except Exception as e:
        print(f"❌ Error configuring Gemini API: {e}")
        return None

def load_reference_image(image_path):
    """Load reference product image"""
    try:
        if not os.path.exists(image_path):
            print(f"❌ Reference image not found: {image_path}")
            return None
        
        image = Image.open(image_path)
        print(f"✅ Reference image loaded: {image_path}")
        print(f"   Size: {image.size}, Format: {image.format}")
        return image
    except Exception as e:
        print(f"❌ Error loading reference image: {e}")
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
        return None

def extract_user_id_from_url(url):
    """Extract user ID from Douyin URL"""
    try:
        # Format: https://www.douyin.com/user/MS4wLjABAAAA...
        if '/user/' in url:
            user_id = url.split('/user/')[-1].split('?')[0].split('/')[0]
            return user_id
        return None
    except Exception as e:
        return None

def compare_images_with_gemini(model, reference_image, thumbnail_image):
    """Compare thumbnail with reference image using Gemini
    
    Returns:
        tuple: (result, error_type)
        - result: True if match, False if no match, None if error
        - error_type: None if success, 'rate_limit', 'api_error', etc.
    """
    max_retries = 2
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            prompt = """Compare these two images. 
            
The FIRST image is the reference product I'm looking for.
The SECOND image is a video thumbnail.

Does the video thumbnail contain the EXACT SAME product as shown in the reference image? 

Look for:
- Same product type
- Same design/shape
- Same or very similar appearance

Answer with ONLY ONE WORD:
- "MATCH" if the thumbnail clearly contains this exact product
- "NO" if the product is not present or is different

Be strict - only say MATCH if you're confident it's the same product."""

            response = model.generate_content([prompt, reference_image, thumbnail_image])
            
            if response and response.text:
                answer = response.text.strip().upper()
                is_match = "MATCH" in answer
                return (is_match, None)
            else:
                return (None, 'empty_response')
                
        except Exception as e:
            error_msg = str(e).lower()
            
            # Handle rate limit errors
            if "quota" in error_msg or "rate limit" in error_msg or "429" in error_msg:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                else:
                    return (None, 'rate_limit')
            else:
                return (None, f'api_error: {str(e)[:100]}')
    
    return (None, 'max_retries_exceeded')

def process_single_video(model, reference_image, video, video_num, total_videos):
    """Process a single video - download and compare"""
    try:
        # Download thumbnail
        thumbnail = download_thumbnail(video['thumbnail_url'])
        if not thumbnail:
            return (None, 'download_failed')
        
        # Compare with reference image
        result, error = compare_images_with_gemini(model, reference_image, thumbnail)
        
        if error:
            if 'rate_limit' in error:
                print(f"  [{video_num}/{total_videos}] 🚫 RATE LIMIT - API quota exceeded")
            elif 'api_error' in error:
                print(f"  [{video_num}/{total_videos}] ❌ API ERROR: {error}")
            else:
                print(f"  [{video_num}/{total_videos}] ⚠️ ERROR: {error}")
            return (None, error)
        elif result:
            print(f"  [{video_num}/{total_videos}] ✅ MATCH FOUND!")
            return (True, None)
        else:
            print(f"  [{video_num}/{total_videos}] ❌ No match")
            return (False, None)
        
    except Exception as e:
        return (None, f'processing_error: {str(e)}')

def scroll_and_load_all_videos(page, page_num, total_pages, max_duration_minutes=30):
    """Scroll page to load all videos with time limit"""
    print(f"\n⏬ Scrolling Page {page_num}/{total_pages} to load all videos (max {max_duration_minutes} minutes)...")
    
    start_time = time.time()
    max_duration_seconds = max_duration_minutes * 60
    max_scrolls = 200
    scroll_pause_time = 1  # Reduced from 2s to 1s for faster scrolling
    
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
    print(f"✅ Page {page_num}/{total_pages} finished scrolling. Total videos: {final_count}")
    return final_count

def extract_videos_from_page(page, page_url):
    """Extract video URLs, thumbnail URLs, and likes from page"""
    print(f"🔍 Extracting video data from page...")
    
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
        
        # Add page_url to each video for tracking
        for video in videos:
            video['source_page'] = page_url
        
        print(f"✅ Extracted {len(videos)} videos")
        return videos
        
    except Exception as e:
        print(f"❌ Error extracting videos: {e}")
        return []

def save_results(all_matching_videos, all_non_matching_videos, output_csv, all_page_urls):
    """Save matching and non-matching videos to files"""
    
    # Save matches to Matches folder
    matches_folder = 'Matches'
    if not os.path.exists(matches_folder):
        os.makedirs(matches_folder)
    
    matches_file = os.path.join(matches_folder, output_csv)
    
    print(f"\n💾 Saving matches to {matches_file}...")
    with open(matches_file, 'w', newline='', encoding='utf-8') as f:
        # Write source pages as comments
        f.write(f"# Source Pages ({len(all_page_urls)}):\n")
        for i, url in enumerate(all_page_urls, 1):
            f.write(f"#   {i}. {url}\n")
        f.write(f"# Total Matches: {len(all_matching_videos)}\n")
        f.write(f"# Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Write CSV data
        writer = csv.DictWriter(f, fieldnames=['video_url', 'thumbnail_url', 'likes', 'index', 'source_page'])
        writer.writeheader()
        writer.writerows(all_matching_videos)
    
    print(f"✅ Saved {len(all_matching_videos)} matches to {matches_file}")
    
    # Save non-matches to Research folder (grouped by source page)
    if all_non_matching_videos:
        print(f"\n💾 Saving non-matches to Research folder...")
        research_folder = 'Research'
        if not os.path.exists(research_folder):
            os.makedirs(research_folder)
        
        # Group non-matches by source page
        non_matches_by_page = {}
        for video in all_non_matching_videos:
            page_url = video.get('source_page', 'unknown')
            if page_url not in non_matches_by_page:
                non_matches_by_page[page_url] = []
            non_matches_by_page[page_url].append(video)
        
        # Save each page's non-matches
        for page_url, videos in non_matches_by_page.items():
            user_id = extract_user_id_from_url(page_url)
            if not user_id:
                user_id = f"unknown_{hash(page_url) % 10000}"
            
            research_file = os.path.join(research_folder, f"{user_id}.csv")
            
            with open(research_file, 'w', newline='', encoding='utf-8') as f:
                f.write(f"# Source Page: {page_url}\n")
                f.write(f"# Non-Matches: {len(videos)}\n")
                f.write(f"# Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                
                writer = csv.DictWriter(f, fieldnames=['video_url', 'thumbnail_url', 'likes', 'index', 'source_page'])
                writer.writeheader()
                writer.writerows(videos)
            
            print(f"  ✅ Saved {len(videos)} non-matches from {user_id}")

def find_matching_videos_multi(page_urls, reference_image_path, output_csv='matching_videos.csv', max_duration_minutes=30):
    """Main function to find matching videos across multiple pages"""
    
    print("🎬 Douyin Product Finder - Multi-Page Mode")
    print("=" * 50)
    print(f"📄 Processing {len(page_urls)} pages")
    
    # Setup Gemini API
    model = setup_gemini_api()
    if not model:
        return False
    
    # Load reference image
    reference_image = load_reference_image(reference_image_path)
    if not reference_image:
        return False
    
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
            print(f"✅ Loading cookies from {cookies_file}")
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
        
        pages = []
        failed_urls = []
        
        try:
            # Phase 1: Open all URLs in separate tabs (LIGHT - just initial load with CAPTCHA)
            print(f"\n🌐 Phase 1: Opening {len(page_urls)} pages (light initial load)...")
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
                    # Increase timeout to 2 minutes and use 'domcontentloaded' for faster loading
                    page.goto(url, wait_until='domcontentloaded', timeout=120000)
                    pages.append(page)
                    print(f"    ✅ Tab {i} loaded successfully")
                    
                    # Small delay between opening tabs to avoid overwhelming the browser
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
            
            # Phase 2: Process each page one by one (HEAVY scroll → extract → close)
            print("\n🔄 Phase 2: Processing pages one by one...")
            print("=" * 50)
            
            all_videos = []
            successfully_loaded_urls = [url for url in page_urls if url not in failed_urls]
            
            for i, page in enumerate(pages, 1):
                print(f"\n📄 Processing Page {i}/{len(pages)}...")
                
                # Bring this tab to front
                page.bring_to_front()
                
                # Scroll this page fully (HEAVY - loads 10,000+ videos)
                scroll_and_load_all_videos(page, i, len(pages), max_duration_minutes)
                
                # Extract videos from this page
                videos = extract_videos_from_page(page, successfully_loaded_urls[i-1])
                all_videos.extend(videos)
                
                print(f"✅ Page {i}/{len(pages)} extracted: {len(videos)} videos")
                
                # CLOSE THIS TAB immediately to free RAM
                print(f"🗑️  Closing Tab {i} to free RAM...")
                page.close()
                print(f"✅ Tab {i} closed. Moving to next page...")
            
            print(f"\n✅ All pages processed! Total videos collected: {len(all_videos)}")
            print(f"💾 All tabs are now closed. RAM freed.")
            
            if not all_videos:
                print("❌ No videos found across all pages!")
                browser.close()
                return False
            
            # Now analyze ALL videos from ALL pages
            print(f"\n🔎 Analyzing {len(all_videos)} videos from {len(pages)} pages...")
            print("=" * 50)
            
            all_matching_videos = []
            all_non_matching_videos = []
            error_count = 0
            error_types = {}
            
            # Process in batches
            batch_size = 50
            total_batches = (len(all_videos) + batch_size - 1) // batch_size
            
            with ThreadPoolExecutor(max_workers=50) as executor:
                for batch_num in range(total_batches):
                    start_idx = batch_num * batch_size
                    end_idx = min(start_idx + batch_size, len(all_videos))
                    batch = all_videos[start_idx:end_idx]
                    
                    print(f"\n📦 Processing batch {batch_num + 1}/{total_batches} ({len(batch)} videos)")
                    print(f"   Videos {start_idx + 1}-{end_idx} of {len(all_videos)}")
                    
                    # Submit all videos in batch
                    futures = []
                    for i, video in enumerate(batch):
                        video_num = start_idx + i + 1
                        future = executor.submit(
                            process_single_video,
                            model, reference_image, video, video_num, len(all_videos)
                        )
                        futures.append((future, video))
                    
                    # Collect results
                    batch_matches = 0
                    batch_errors = 0
                    for future, video in futures:
                        try:
                            is_match, error = future.result(timeout=30)
                            
                            if error:
                                error_count += 1
                                batch_errors += 1
                                error_types[error] = error_types.get(error, 0) + 1
                            elif is_match:
                                all_matching_videos.append(video)
                                batch_matches += 1
                            else:
                                all_non_matching_videos.append(video)
                        except Exception as e:
                            error_count += 1
                            batch_errors += 1
                    
                    print(f"   ✅ Batch complete: {batch_matches} matches, {batch_errors} errors")
                    
                    if batch_num < total_batches - 1:
                        time.sleep(0.5)
            
            # Save all results
            save_results(all_matching_videos, all_non_matching_videos, output_csv, successfully_loaded_urls)
            
            # Print summary
            print(f"\n🎉 Multi-page search complete!")
            print(f"📊 Total pages processed: {len(pages)}")
            print(f"📊 Total videos analyzed: {len(all_videos)}")
            print(f"✅ Total matches: {len(all_matching_videos)}")
            print(f"❌ Total non-matches: {len(all_non_matching_videos)}")
            
            if error_count > 0:
                print(f"\n⚠️  ERRORS ENCOUNTERED: {error_count} videos failed")
                for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                    if 'rate_limit' in error_type:
                        print(f"  🚫 Rate Limit: {count} videos")
                    elif 'download_failed' in error_type:
                        print(f"  ⚠️  Download Failed: {count} thumbnails")
                    else:
                        print(f"  ⚠️  {error_type}: {count} videos")
            
            # Save cookies for future use
            if not os.path.exists('douyin_cookies.json'):
                try:
                    storage = context.storage_state()
                    with open('douyin_cookies.json', 'w') as f:
                        json.dump(storage, f, indent=2)
                    print(f"\n💾 Cookies saved to douyin_cookies.json for future use!")
                except:
                    pass
            
            browser.close()
            return True
            
        except Exception as e:
            print(f"❌ Error during search: {e}")
            browser.close()
            return False

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
    
    print("🎬 Douyin Product Video Finder - Multi-Page Mode")
    print("=" * 50)
    
    # Get reference image path
    reference_image = input("\n📸 Enter path to reference product image: ").strip()
    if not reference_image:
        print("❌ No image path provided!")
        return
    
    reference_image = reference_image.replace('\\', '')
    
    if not os.path.exists(reference_image):
        print(f"❌ Reference image not found: {reference_image}")
        return
    
    print(f"✅ Found reference image: {reference_image}")
    
    # Auto-generate CSV filename
    image_name = os.path.splitext(os.path.basename(reference_image))[0]
    output_csv = f"{image_name}.csv"
    
    matches_folder = 'Matches'
    counter = 1
    while os.path.exists(os.path.join(matches_folder, output_csv)):
        output_csv = f"{image_name}{counter}.csv"
        counter += 1
    
    print(f"💾 Output will be saved to: Matches/{output_csv}")
    
    # Get multiple Douyin page URLs
    print("\n🌐 Enter Douyin page URLs (one per line)")
    print("Press ENTER on an empty line when done:")
    
    page_urls = []
    while True:
        url = input().strip()
        if not url:
            break
        page_urls.append(url)
        print(f"  ✅ Added page {len(page_urls)}: {url}")
    
    if not page_urls:
        print("❌ No URLs provided!")
        return
    
    print(f"\n✅ Ready to process {len(page_urls)} pages")
    
    # Run the multi-page search
    success = find_matching_videos_multi(page_urls, reference_image, output_csv)
    
    if not success:
        print("\n💥 Search failed!")
        sys.exit(1)
    else:
        print("\n✅ All done! You can now review the results.")

if __name__ == "__main__":
    main()
