#!/usr/bin/env python3
"""
Douyin Multi-Product Finder
Finds all videos containing multiple products in their thumbnails using Gemini AI
Checks multiple reference products simultaneously for efficiency
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
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading

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

def load_reference_images_from_folder(folder_path):
    """Load all reference product images from folder
    
    Returns:
        dict: {product_name: PIL.Image} or None if error
    """
    try:
        if not os.path.exists(folder_path):
            print(f"❌ Folder not found: {folder_path}")
            return None
        
        if not os.path.isdir(folder_path):
            print(f"❌ Path is not a folder: {folder_path}")
            return None
        
        # Supported image formats
        valid_extensions = {'.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG'}
        
        # Load all images
        reference_images = {}
        image_files = []
        
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            
            # Skip if not a file
            if not os.path.isfile(file_path):
                continue
            
            # Check extension
            _, ext = os.path.splitext(filename)
            if ext not in valid_extensions:
                continue
            
            image_files.append((filename, file_path))
        
        if not image_files:
            print(f"❌ No image files found in: {folder_path}")
            print(f"   Supported formats: .png, .jpg, .jpeg")
            return None
        
        # Load each image
        print(f"\n📁 Loading reference images from: {folder_path}")
        print(f"=" * 50)
        
        for idx, (filename, file_path) in enumerate(image_files, 1):
            try:
                image = Image.open(file_path)
                file_size_kb = os.path.getsize(file_path) / 1024
                reference_images[filename] = image
                print(f"   {idx}. ✅ {filename} ({file_size_kb:.0f}KB, {image.size[0]}x{image.size[1]})")
            except Exception as e:
                print(f"   {idx}. ❌ {filename} - Error: {e}")
                return None
        
        print(f"=" * 50)
        print(f"✅ Loaded {len(reference_images)} products successfully\n")
        
        return reference_images
        
    except Exception as e:
        print(f"❌ Error loading images from folder: {e}")
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

def extract_user_id_from_url(url):
    """Extract user ID from Douyin URL"""
    try:
        # Format: https://www.douyin.com/user/MS4wLjABAAAA...
        if '/user/' in url:
            user_id = url.split('/user/')[-1].split('?')[0].split('/')[0]
            return user_id
        return None
    except Exception as e:
        print(f"  ⚠️ Error extracting user ID: {e}")
        return None

def save_non_matches_to_research(douyin_url, non_matching_videos):
    """Save non-matching videos to Research folder (overwrites if exists)"""
    
    # Extract user ID from URL
    user_id = extract_user_id_from_url(douyin_url)
    if not user_id:
        print(f"  ⚠️ Could not extract user ID from URL")
        return False
    
    # Create Research folder if it doesn't exist
    research_folder = 'Research'
    if not os.path.exists(research_folder):
        os.makedirs(research_folder)
    
    # Create filename based on user ID
    research_file = os.path.join(research_folder, f"{user_id}.csv")
    
    try:
        with open(research_file, 'w', newline='', encoding='utf-8') as f:
            # Write header comments
            f.write(f"# Source Page: {douyin_url}\n")
            f.write(f"# Non-Matches: {len(non_matching_videos)}\n")
            f.write(f"# Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            # Write CSV data
            writer = csv.DictWriter(f, fieldnames=['video_url', 'thumbnail_url', 'likes', 'index'])
            writer.writeheader()
            writer.writerows(non_matching_videos)
        
        print(f"✅ Saved non-matches to {research_file}")
        return True
    except Exception as e:
        print(f"  ⚠️ Error writing to {research_file}: {e}")
        return False

def compare_images_with_gemini(model, reference_image, thumbnail_image, video_index=None):
    """Compare thumbnail with reference image using Gemini (LEGACY - single product)
    
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
                return (is_match, None)  # Success - no error
            else:
                return (None, 'empty_response')  # API returned empty response
                
        except Exception as e:
            error_msg = str(e).lower()
            
            # Handle rate limit errors
            if "quota" in error_msg or "rate limit" in error_msg or "429" in error_msg:
                if attempt < max_retries - 1:
                    print(f"  ⚠️ Rate limit hit, retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                else:
                    return (None, 'rate_limit')  # Rate limit error
            else:
                # Other API errors
                return (None, f'api_error: {str(e)[:100]}')
    
    return (None, 'max_retries_exceeded')

def compare_multiple_products_with_gemini(model, reference_images_dict, thumbnail_image, video_index=None):
    """Compare thumbnail with MULTIPLE reference products using Gemini
    
    Args:
        model: Gemini model instance
        reference_images_dict: dict of {product_name: PIL.Image}
        thumbnail_image: PIL.Image of video thumbnail
        video_index: Optional video number for logging
    
    Returns:
        tuple: (matched_products, error_type)
        - matched_products: list of product names that matched (e.g., ["Leafo.png", "GAMEBOY.png"])
        - error_type: None if success, or error description
    """
    max_retries = 2
    retry_delay = 2
    
    product_names = list(reference_images_dict.keys())
    
    for attempt in range(max_retries):
        try:
            # Build prompt with all products
            prompt = f"""I have {len(product_names)} reference product images and 1 video thumbnail.

Reference products (in order):
"""
            for idx, name in enumerate(product_names, 1):
                prompt += f"  {idx}. {name}\n"
            
            prompt += f"""
The LAST image is the video thumbnail to check.

Does the video thumbnail contain ANY of the reference products?

Answer in this EXACT format:
- If matches found: "MATCH: product1.png, product2.png" (list ALL that match)
- If no matches: "NO MATCH"

Be strict - only list products you're confident are in the thumbnail.
Look for exact same product type, design, and appearance."""

            # Build images list: [ref1, ref2, ref3, ..., thumbnail]
            images_list = [prompt]
            for name in product_names:
                images_list.append(reference_images_dict[name])
            images_list.append(thumbnail_image)
            
            response = model.generate_content(images_list)
            
            if response and response.text:
                answer = response.text.strip()
                
                # Parse response
                if "NO MATCH" in answer.upper():
                    return ([], None)  # No products matched
                elif "MATCH:" in answer.upper():
                    # Extract product names from response
                    match_part = answer.upper().split("MATCH:")[1].strip()
                    matched_products = []
                    
                    # Check each product name if it's mentioned
                    for product_name in product_names:
                        if product_name.upper() in match_part:
                            matched_products.append(product_name)
                    
                    return (matched_products, None)  # Success
                else:
                    # Unexpected format, try to be lenient
                    matched_products = []
                    for product_name in product_names:
                        if product_name.upper() in answer.upper():
                            matched_products.append(product_name)
                    return (matched_products, None)
            else:
                return (None, 'empty_response')
                
        except Exception as e:
            error_msg = str(e).lower()
            
            # Handle rate limit errors
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

def process_single_video(model, reference_image, video, video_num, total_videos):
    """Process a single video - download and compare (LEGACY - single product)
    
    Returns:
        tuple: (is_match, error_type)
        - is_match: True/False/None (None means error)
        - error_type: None if success, or error description
    """
    try:
        # Download thumbnail
        thumbnail = download_thumbnail(video['thumbnail_url'])
        if not thumbnail:
            print(f"  [{video_num}/{total_videos}] ⚠️ Failed to download thumbnail")
            return (None, 'download_failed')
        
        # Compare with reference image
        result, error = compare_images_with_gemini(model, reference_image, thumbnail, video_num)
        
        if error:
            # API error occurred
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
        print(f"  [{video_num}/{total_videos}] ⚠️ Processing error: {e}")
        return (None, f'processing_error: {str(e)}')

def process_single_video_multi_product(model, reference_images_dict, video, video_num, total_videos):
    """Process a single video against MULTIPLE products
    
    Args:
        model: Gemini model instance
        reference_images_dict: dict of {product_name: PIL.Image}
        video: video data dict
        video_num: current video number
        total_videos: total number of videos
    
    Returns:
        tuple: (matched_products, error_type)
        - matched_products: list of product names that matched (or None if error)
        - error_type: None if success, or error description
    """
    try:
        # Download thumbnail
        thumbnail = download_thumbnail(video['thumbnail_url'])
        if not thumbnail:
            print(f"  [{video_num}/{total_videos}] ⚠️ Failed to download thumbnail")
            return (None, 'download_failed')
        
        # Compare with all reference products
        matched_products, error = compare_multiple_products_with_gemini(
            model, reference_images_dict, thumbnail, video_num
        )
        
        if error:
            # API error occurred
            if 'rate_limit' in error:
                print(f"  [{video_num}/{total_videos}] 🚫 RATE LIMIT - API quota exceeded")
            elif 'api_error' in error:
                print(f"  [{video_num}/{total_videos}] ❌ API ERROR: {error}")
            else:
                print(f"  [{video_num}/{total_videos}] ⚠️ ERROR: {error}")
            return (None, error)
        elif matched_products:
            # Show which products matched
            products_str = ", ".join(matched_products)
            print(f"  [{video_num}/{total_videos}] ✅ MATCH: {products_str}")
            return (matched_products, None)
        else:
            print(f"  [{video_num}/{total_videos}] ❌ No match")
            return ([], None)
        
    except Exception as e:
        print(f"  [{video_num}/{total_videos}] ⚠️ Processing error: {e}")
        return (None, f'processing_error: {str(e)}')

def scroll_and_load_all_videos(page, max_duration_minutes=30):
    """Scroll page to load all videos with time limit"""
    print(f"⏬ Scrolling to load all videos (max {max_duration_minutes} minutes)...")
    
    start_time = time.time()
    max_duration_seconds = max_duration_minutes * 60
    max_scrolls = 200  # Maximum scroll attempts
    scroll_pause_time = 2  # Wait between scrolls
    
    previous_height = None
    scroll_count = 0
    
    # Find the scroll container (Douyin uses a div with class 'route-scroll-container')
    scroll_container_selector = "document.querySelector('.route-scroll-container')"
    
    while scroll_count < max_scrolls:
        # Check time limit
        elapsed = time.time() - start_time
        if elapsed > max_duration_seconds:
            print(f"  ⏱️ Reached {max_duration_minutes} minute time limit")
            break
        
        # Scroll the container to bottom
        page.evaluate(f"{scroll_container_selector}.scrollTo(0, {scroll_container_selector}.scrollHeight)")
        
        # Wait for new content to load
        time.sleep(scroll_pause_time)
        
        # Get current scroll height of the container
        current_height = page.evaluate(f"{scroll_container_selector}.scrollHeight")
        
        # Count videos for progress
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
    """Extract video URLs, thumbnail URLs, and likes from page - FAST version"""
    print("🔍 Extracting video data from page...")
    
    try:
        # Wait for content to load
        page.wait_for_selector('img', timeout=10000)
        
        # Extract ALL video data in ONE JavaScript call (much faster!)
        videos = page.evaluate("""
            () => {
                const videoLinks = document.querySelectorAll('a[href*="/video/"]');
                const videos = [];
                
                videoLinks.forEach((link, index) => {
                    const videoUrl = link.href;
                    const img = link.querySelector('img');
                    const thumbnailUrl = img ? (img.src || img.getAttribute('data-src')) : null;
                    
                    // Try to find likes count (Douyin shows it in various places)
                    let likes = '';
                    
                    // Look for common like count patterns in the video card
                    const container = link.closest('li') || link.closest('div[class*="video"]');
                    if (container) {
                        // Try different selectors for like count
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
                                // Check if it looks like a number (could be "1.2w", "10k", "1234", etc.)
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

def find_matching_videos(douyin_url, reference_image_path, output_csv='matching_videos.csv', max_duration_minutes=30):
    """Main function to find matching videos"""
    
    print("🎬 Douyin Product Finder")
    print("=" * 50)
    
    # Setup Gemini API
    model = setup_gemini_api()
    if not model:
        return False
    
    # Load reference image
    reference_image = load_reference_image(reference_image_path)
    if not reference_image:
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
            print(f"   Instructions will be shown after the run.")
        
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
        
        # Override navigator.webdriver
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
            total_videos = scroll_and_load_all_videos(page, max_duration_minutes)
            
            # Extract video data
            videos = extract_videos_from_page(page)
            
            if not videos:
                print("❌ No videos found on page!")
                browser.close()
                return False
            
            print(f"\n🔎 Analyzing {len(videos)} videos with parallel processing...")
            print("=" * 50)
            
            matching_videos = []
            non_matching_videos = []
            error_count = 0
            error_types = {}
            
            # Process in batches for parallel requests
            batch_size = 50  # Process 50 videos at a time
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
                            process_single_video,
                            model, reference_image, video, video_num, len(videos)
                        )
                        futures.append((future, video))
                    
                    # Collect results
                    batch_matches = 0
                    batch_errors = 0
                    for future, video in futures:
                        try:
                            is_match, error = future.result(timeout=30)
                            
                            if error:
                                # Track error
                                error_count += 1
                                batch_errors += 1
                                error_types[error] = error_types.get(error, 0) + 1
                            elif is_match:
                                matching_videos.append(video)
                                batch_matches += 1
                            else:
                                non_matching_videos.append(video)
                        except Exception as e:
                            print(f"  ⚠️ Thread error: {e}")
                            error_count += 1
                            batch_errors += 1
                    
                    print(f"   ✅ Batch complete: {batch_matches} matches, {batch_errors} errors")
                    
                    # Small delay between batches to respect rate limits
                    if batch_num < total_batches - 1:
                        time.sleep(0.5)
            
            # Save matches to Matches folder
            matches_folder = 'Matches'
            if not os.path.exists(matches_folder):
                os.makedirs(matches_folder)
            
            matches_file = os.path.join(matches_folder, output_csv)
            
            print(f"\n💾 Saving matches to {matches_file}...")
            with open(matches_file, 'w', newline='', encoding='utf-8') as f:
                # Write source page URL as a comment at the top
                f.write(f"# Source Page: {douyin_url}\n")
                f.write(f"# Total Matches: {len(matching_videos)}\n")
                f.write(f"# Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                
                # Write CSV data
                writer = csv.DictWriter(f, fieldnames=['video_url', 'thumbnail_url', 'likes', 'index'])
                writer.writeheader()
                writer.writerows(matching_videos)
            
            print(f"\n🎉 Search complete!")
            print(f"📊 Total videos: {len(videos)}")
            print(f"✅ Matches: {len(matching_videos)}")
            print(f"❌ Non-matches: {len(non_matching_videos)}")
            
            # Show error summary if any errors occurred
            if error_count > 0:
                print(f"\n⚠️  ERRORS ENCOUNTERED: {error_count} videos failed")
                print(f"=" * 50)
                for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                    if 'rate_limit' in error_type:
                        print(f"  🚫 Rate Limit (429): {count} videos")
                        print(f"     → Your Gemini API quota is exceeded")
                        print(f"     → Wait for quota reset or upgrade API plan")
                    elif 'api_error' in error_type:
                        print(f"  ❌ API Error: {count} videos")
                        print(f"     → {error_type}")
                    elif 'download_failed' in error_type:
                        print(f"  ⚠️  Download Failed: {count} thumbnails")
                    else:
                        print(f"  ⚠️  {error_type}: {count} videos")
                print(f"=" * 50)
                print(f"⚠️  {error_count} videos were skipped due to errors")
                print(f"💡 Consider re-running later or checking your API key\n")
            
            print(f"📄 Matches saved to: {matches_file}")
            
            # Save non-matches to Research folder
            if non_matching_videos:
                print(f"\n💾 Saving non-matches to Research folder...")
                save_non_matches_to_research(douyin_url, non_matching_videos)
            
            # Save cookies for future use if not already saved
            if not os.path.exists('douyin_cookies.json'):
                try:
                    storage = context.storage_state()
                    with open('douyin_cookies.json', 'w') as f:
                        json.dump(storage, f, indent=2)
                    print(f"💾 Cookies saved to douyin_cookies.json for future use!")
                except:
                    pass
            
            browser.close()
            return True
            
        except Exception as e:
            print(f"❌ Error during search: {e}")
            browser.close()
            return False

def find_matching_videos_multi_product(douyin_url, reference_images_dict, max_duration_minutes=30):
    """Main function to find videos matching MULTIPLE products
    
    Args:
        douyin_url: Douyin user page URL
        reference_images_dict: dict of {product_name: PIL.Image}
        max_duration_minutes: Max time to scroll (default 30)
    
    Returns:
        bool: True if successful, False if error
    """
    
    print("🎬 Douyin Multi-Product Finder")
    print("=" * 50)
    
    # Setup Gemini API
    model = setup_gemini_api()
    if not model:
        return False
    
    print(f"\n🌐 Opening Douyin page: {douyin_url}")
    
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
        
        page = context.new_page()
        
        # Override navigator.webdriver
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        try:
            # Navigate to page
            page.goto(douyin_url, wait_until='networkidle', timeout=60000)
            
            # Wait for user to complete CAPTCHA
            print("\n⏸️  CAPTCHA Check")
            print("=" * 50)
            print("If you see a CAPTCHA, please complete it now.")
            print("When ready, press ENTER to start collecting videos...")
            input()
            print("\n✅ Starting video collection...")
            
            # Scroll and load all videos
            total_videos = scroll_and_load_all_videos(page, max_duration_minutes)
            
            # Extract video data
            videos = extract_videos_from_page(page)
            
            if not videos:
                print("❌ No videos found on page!")
                browser.close()
                return False
            
            print(f"\n🔎 Analyzing {len(videos)} videos with parallel processing...")
            print("=" * 50)
            
            # Track matches per product
            product_matches = {name: [] for name in reference_images_dict.keys()}
            videos_with_any_match = set()  # Track which videos matched ANY product
            error_count = 0
            error_types = {}
            
            # Process EACH PRODUCT INDIVIDUALLY for best accuracy
            product_list = list(reference_images_dict.items())
            total_products = len(product_list)
            
            for product_idx, (product_name, product_image) in enumerate(product_list, 1):
                print(f"\n{'=' * 60}")
                print(f"🔍 Product {product_idx}/{total_products}: {product_name}")
                print(f"{'=' * 60}")
                
                # Process in batches for this specific product
                batch_size = 50
                total_batches = (len(videos) + batch_size - 1) // batch_size
                
                with ThreadPoolExecutor(max_workers=50) as executor:
                    for batch_num in range(total_batches):
                        start_idx = batch_num * batch_size
                        end_idx = min(start_idx + batch_size, len(videos))
                        batch = videos[start_idx:end_idx]
                        
                        print(f"\n📦 Batch {batch_num + 1}/{total_batches} ({len(batch)} videos)")
                        print(f"   Videos {start_idx + 1}-{end_idx} of {len(videos)}")
                        
                        # Submit batch to thread pool
                        futures = []
                        for i, video in enumerate(batch):
                            video_num = start_idx + i + 1
                            future = executor.submit(
                                process_single_video,
                                model, product_image, video, video_num, len(videos)
                            )
                            futures.append((future, video))
                        
                        # Collect results for this product
                        batch_matches = 0
                        batch_errors = 0
                        for future, video in futures:
                            try:
                                is_match, error = future.result(timeout=30)
                                
                                if error:
                                    # Track error
                                    error_count += 1
                                    batch_errors += 1
                                    error_types[error] = error_types.get(error, 0) + 1
                                elif is_match:
                                    # This video matches this product
                                    product_matches[product_name].append(video)
                                    videos_with_any_match.add(video['video_url'])
                                    batch_matches += 1
                            except Exception as e:
                                print(f"  ⚠️ Thread error: {e}")
                                error_count += 1
                                batch_errors += 1
                        
                        print(f"   ✅ Batch complete: {batch_matches} matches, {batch_errors} errors")
                        
                        # Small delay between batches
                        if batch_num < total_batches - 1:
                            time.sleep(0.5)
                
                # Show summary for this product
                matches_found = len(product_matches[product_name])
                print(f"\n✅ {product_name}: {matches_found} matches found")
                
                # Save matches for this product immediately (if any matches found)
                if matches_found > 0:
                    # Generate CSV filename from product name
                    product_base_name = os.path.splitext(product_name)[0]  # Remove extension
                    output_csv = f"{product_base_name}.csv"
                    
                    # Auto-increment if file exists in Matches folder
                    matches_folder = 'Matches'
                    if not os.path.exists(matches_folder):
                        os.makedirs(matches_folder)
                    
                    counter = 1
                    while os.path.exists(os.path.join(matches_folder, output_csv)):
                        output_csv = f"{product_base_name}{counter}.csv"
                        counter += 1
                    
                    matches_file = os.path.join(matches_folder, output_csv)
                    
                    # Save to CSV
                    try:
                        with open(matches_file, 'w', newline='', encoding='utf-8') as f:
                            # Write header comments
                            f.write(f"# Source Page: {douyin_url}\n")
                            f.write(f"# Product: {product_name}\n")
                            f.write(f"# Total Matches: {matches_found}\n")
                            f.write(f"# Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                            
                            # Write CSV data
                            writer = csv.DictWriter(f, fieldnames=['video_url', 'thumbnail_url', 'likes', 'index'])
                            writer.writeheader()
                            writer.writerows(product_matches[product_name])
                        
                        print(f"   💾 Saved to: {matches_file}")
                    except Exception as e:
                        print(f"   ⚠️ Error saving CSV: {e}")
                else:
                    print(f"   ⏭️  No matches - skipping CSV creation")
            
            # Calculate non-matches (videos that didn't match ANY product)
            non_matching_videos = [v for v in videos if v['video_url'] not in videos_with_any_match]
            
            # Display results summary
            print(f"\n{'=' * 60}")
            print(f"🎉 SEARCH COMPLETE!")
            print(f"{'=' * 60}")
            print(f"📊 Total videos analyzed: {len(videos)}")
            print(f"\n✅ Product matches found:")
            for product_name, matches in product_matches.items():
                if matches:
                    print(f"   - {product_name}: {len(matches)} matches")
            print(f"\n❌ Non-matches: {len(non_matching_videos)}")
            
            # Show error summary if any
            if error_count > 0:
                print(f"\n⚠️  ERRORS ENCOUNTERED: {error_count} videos failed")
                print(f"=" * 50)
                for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                    if 'rate_limit' in error_type:
                        print(f"  🚫 Rate Limit (429): {count} videos")
                        print(f"     → Your Gemini API quota is exceeded")
                    elif 'api_error' in error_type:
                        print(f"  ❌ API Error: {count} videos")
                    elif 'download_failed' in error_type:
                        print(f"  ⚠️  Download Failed: {count} thumbnails")
                print(f"=" * 50)
            
            # Save non-matches to Research folder
            print(f"\n💾 Saving non-matches to Research folder...")
            if non_matching_videos:
                success = save_non_matches_to_research(douyin_url, non_matching_videos)
                if not success:
                    print(f"   ⚠️  Failed to save non-matches")
            else:
                print(f"   ℹ️  No non-matches to save (all videos matched at least one product!)")
            
            print(f"\n{'=' * 60}")
            print(f"✅ ALL FILES SAVED SUCCESSFULLY!")
            print(f"{'=' * 60}")
            
            # Save cookies
            if not os.path.exists('douyin_cookies.json'):
                try:
                    storage = context.storage_state()
                    with open('douyin_cookies.json', 'w') as f:
                        json.dump(storage, f, indent=2)
                    print(f"💾 Cookies saved to douyin_cookies.json for future use!")
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
    
    print("🎬 Douyin Multi-Product Video Finder")
    print("=" * 50)
    
    # Get reference images folder from user
    products_folder = input("\n📁 Enter path to Products folder (default: 'Products'): ").strip()
    if not products_folder:
        products_folder = 'Products'
    
    # Handle escaped spaces from drag-and-drop
    products_folder = products_folder.replace('\\', '')
    
    # Load all reference images from folder
    reference_images = load_reference_images_from_folder(products_folder)
    if not reference_images:
        print("❌ Failed to load reference images!")
        return
    
    # Get Douyin page URL
    douyin_url = input("🌐 Enter Douyin page URL: ").strip()
    if not douyin_url:
        print("❌ No URL provided!")
        return
    
    print(f"\n🚀 Starting multi-product search...")
    print(f"   Products: {len(reference_images)}")
    print(f"   Source: {douyin_url}\n")
    
    # Run the multi-product search
    success = find_matching_videos_multi_product(douyin_url, reference_images, max_duration_minutes=30)
    
    if not success:
        print("\n💥 Search failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()