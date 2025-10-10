#!/usr/bin/env python3
"""
Watch Prices - 1688 Product Finder
Finds similar products on 1688 using image search and AI comparison
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
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
        model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')
        print("✅ Gemini API configured successfully (using gemini-2.5-flash-preview-09-2025)")
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

def download_product_image(url):
    """Download product image from URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        image = Image.open(io.BytesIO(response.content))
        return image
    except Exception as e:
        print(f"  ⚠️ Error downloading product image: {e}")
        return None

def upload_image_to_aliprice(context, page, image_url, is_first_url=False):
    """Upload image URL to aliprice.com and wait for results"""
    try:
        print(f"📤 Navigating to aliprice.com...")
        page.goto('https://www.aliprice.com/independent/1688.html', wait_until='domcontentloaded', timeout=30000)
        
        print("⏳ Waiting for page to fully load...")
        time.sleep(5)
        
        print("🔍 Looking for input field...")
        try:
            input_field = page.locator('input[placeholder*="image url"], input[placeholder*="product url"]').first
            input_field.wait_for(state='visible', timeout=10000)
            print("✅ Found input field")
            
            print("🖱️  Clicking on input field...")
            input_field.click()
            time.sleep(0.5)
            
            input_field.fill('')
            time.sleep(0.3)
            
            print(f"📋 Pasting URL: {image_url[:60]}...")
            input_field.fill(image_url)
            time.sleep(1)
            
            print("⏳ Pressing Enter to submit and waiting for new tab...")
            
            # Use context.expect_page() to properly capture the new tab
            with context.expect_page() as new_page_info:
                input_field.press('Enter')
            
            # Get the new page that was opened
            new_page = new_page_info.value
            print(f"✅ New tab captured! URL: {new_page.url[:80]}")
            
            # Store it for later use
            results_page = new_page
            
        except Exception as e:
            print(f"⚠️ Could not interact with input field: {e}")
            results_page = None
        
        # Check if we successfully captured the results page
        if not results_page:
            print("❌ Failed to capture new tab!")
            return None
        
        # Now check if login is needed (only on first URL)    
        if is_first_url:
            print("\n" + "=" * 60, flush=True)
            print("🔐 LOGIN CHECK", flush=True)
            print("=" * 60, flush=True)
            print("The new tab has opened with search results.", flush=True)
            print("If a LOGIN POPUP appeared, please log in now.", flush=True)
            print("After login, the popup will close and products will appear.", flush=True)
            print("", flush=True)
            print(">>> Press ENTER when login is done (or if no login needed) <<<", flush=True)
            print("=" * 60, flush=True)
            
            try:
                import select
                while True:
                    try:
                        if select.select([sys.stdin], [], [], 0)[0]:
                            sys.stdin.readline()
                        else:
                            break
                    except:
                        break
            except:
                pass
            
            try:
                input("Press ENTER when ready: ")
                print("✅ Continuing...", flush=True)
                time.sleep(2)
                
            except KeyboardInterrupt:
                print("\n⚠️ Interrupted by user", flush=True)
                return None
        
        # Use the captured results page
        page = results_page
        print(f"\n📍 Using captured search results page: {page.url[:80]}...")
        
        # Scroll to load products
        print("📜 Scrolling to load products...")
        for i in range(3):
            try:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)
            except:
                pass
        
        # Check for products
        product_count = page.locator('li.image_li').count()
        print(f"📊 Detected {product_count} product containers")
        
        if product_count > 0:
            print("✅ Products found!")
            return page
        else:
            print("⚠️ No products detected, waiting 10 seconds...")
            time.sleep(10)
            
            for i in range(3):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(3)
            
            product_count = page.locator('li.image_li').count()
            if product_count > 0:
                print(f"✅ Found {product_count} products after extended wait!")
                return page
            else:
                print("❌ Still no products found")
                page.screenshot(path='debug_no_products.png')
                return None
            
    except Exception as e:
        print(f"❌ Error submitting image URL: {e}")
        import traceback
        traceback.print_exc()
        return None

def extract_products_from_results(page):
    """Extract all visible products from the results page"""
    print("🔍 Extracting products from results page...")
    
    try:
        print("📜 Final scroll to bottom...")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(3)
        
        page.screenshot(path='temp_screenshot.png')
        print("📸 Screenshot saved to temp_screenshot.png")
        
        products = page.evaluate("""
            () => {
                const products = [];
                const productItems = document.querySelectorAll('li.image_li');
                
                console.log('Found', productItems.length, 'li.image_li items');
                
                productItems.forEach((item, index) => {
                    try {
                        const link = item.querySelector('a.img-link');
                        if (!link) return;
                        
                        const href = link.href;
                        if (!href || href === '#') return;
                        
                        const img = link.querySelector('img');
                        if (!img) return;
                        
                        const imgUrl = img.src || img.getAttribute('data-src');
                        if (!imgUrl || imgUrl.includes('qq-kf')) return;
                        
                        const priceElement = item.querySelector('.item-price');
                        let price = 'N/A';
                        if (priceElement) {
                            price = priceElement.textContent.trim();
                        }
                        
                        console.log('Product', products.length + 1, ':', price);
                        
                        products.push({
                            product_url: href,
                            image_url: imgUrl,
                            price: price,
                            index: products.length + 1
                        });
                        
                    } catch (err) {
                        console.error('Error processing item', index, ':', err);
                    }
                });
                
                console.log('Total products extracted:', products.length);
                return products;
            }
        """)
        
        print(f"✅ Extracted {len(products)} products from page")
        
        if products and len(products) > 0:
            print(f"📋 Sample products:")
            for i, prod in enumerate(products[:3], 1):
                print(f"   {i}. URL: {prod['product_url'][:60]}...")
                print(f"      Image: {prod['image_url'][:60]}...")
                print(f"      Price: {prod['price']}")
        else:
            print("⚠️ No products extracted - check temp_screenshot.png")
        
        return products
        
    except Exception as e:
        print(f"❌ Error extracting products: {e}")
        import traceback
        traceback.print_exc()
        return []

def compare_image_with_gemini_score(model, reference_image, product_image, product_num=None):
    """Compare product image with reference image using structured attribute scoring"""
    max_retries = 2
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            prompt = """Compare these two watches using SEPARATE scores for each attribute.

FIRST image = Reference watch
SECOND image = Product from search results

IGNORE brand names completely - they don't matter at all.

Score each attribute from 0-100:

1. SHAPE (overall watch shape, case shape, proportions, size appearance):
   - 90-100: Nearly identical shape
   - 70-89: Very similar shape with minor differences
   - 50-69: Same general category but noticeable shape differences
   - 30-49: Different shapes but still recognizable as similar type
   - 0-29: Very different shapes

2. STRAP (strap/band type, style, texture, width):
   - 90-100: Nearly identical strap type and style
   - 70-89: Same strap type with minor style differences
   - 50-69: Similar strap type but different styling
   - 30-49: Different strap types (e.g., metal vs leather)
   - 0-29: Completely different strap types

3. DIAL (dial design, markers/numbers type, hands style, layout):
   - 90-100: Nearly identical dial design and markers
   - 70-89: Very similar dial with minor differences in markers
   - 50-69: Similar dial style but different marker types (e.g., arabic vs roman)
   - 30-49: Different dial designs but recognizable similarity
   - 0-29: Completely different dial designs

4. COLOR (overall color scheme - this is LEAST important, shade differences are OK):
   - 90-100: Nearly identical colors
   - 70-89: Same color family (e.g., both gold, both silver)
   - 50-69: Different shades but harmonious (e.g., tan vs brown)
   - 30-49: Different color categories but not clashing
   - 0-29: Completely different color schemes

Answer in this EXACT format (four lines, numbers only):
SHAPE: [0-100]
STRAP: [0-100]
DIAL: [0-100]
COLOR: [0-100]"""

            response = model.generate_content([prompt, reference_image, product_image])
            
            if response and response.text:
                answer = response.text.strip()
                
                # Parse the structured response
                scores = {}
                for line in answer.split('\n'):
                    line = line.strip()
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip().upper()
                        value = value.strip()
                        
                        # Extract number from value
                        match = re.search(r'\d+', value)
                        if match and key in ['SHAPE', 'STRAP', 'DIAL', 'COLOR']:
                            score = int(match.group())
                            score = max(0, min(100, score))
                            scores[key] = score
                
                # Check if we got all required scores
                required = ['SHAPE', 'STRAP', 'DIAL', 'COLOR']
                if all(key in scores for key in required):
                    # Calculate weighted final score
                    # Shape: 35%, Strap: 25%, Dial: 25%, Color: 15%
                    final_score = (
                        scores['SHAPE'] * 0.35 +
                        scores['STRAP'] * 0.25 +
                        scores['DIAL'] * 0.25 +
                        scores['COLOR'] * 0.15
                    )
                    final_score = round(final_score, 1)
                    
                    # Return structured data
                    result = {
                        'final_score': final_score,
                        'shape': scores['SHAPE'],
                        'strap': scores['STRAP'],
                        'dial': scores['DIAL'],
                        'color': scores['COLOR']
                    }
                    return (result, None)
                else:
                    missing = [k for k in required if k not in scores]
                    return (None, f'incomplete_scores: missing {missing}')
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

def process_single_product(model, reference_image, product, product_num, total_products):
    """Process a single product - download and compare"""
    try:
        product_image = download_product_image(product['image_url'])
        if not product_image:
            print(f"  [{product_num}/{total_products}] ⚠️ Failed to download image")
            return (None, 'download_failed')
        
        score_data, error = compare_image_with_gemini_score(model, reference_image, product_image, product_num)
        
        if error:
            if 'rate_limit' in str(error):
                print(f"  [{product_num}/{total_products}] 🚫 RATE LIMIT")
            elif 'api_error' in str(error):
                print(f"  [{product_num}/{total_products}] ❌ API ERROR")
            else:
                print(f"  [{product_num}/{total_products}] ⚠️ ERROR: {error}")
            return (None, error)
        else:
            # Print detailed breakdown
            print(f"  [{product_num}/{total_products}] 📊 Final: {score_data['final_score']:.1f} | "
                  f"Shape: {score_data['shape']} | Strap: {score_data['strap']} | "
                  f"Dial: {score_data['dial']} | Color: {score_data['color']}")
            return (score_data, None)
        
    except Exception as e:
        print(f"  [{product_num}/{total_products}] ⚠️ Processing error: {e}")
        return (None, f'processing_error: {str(e)}')

def process_products_parallel(model, reference_image, products):
    """Process all products in parallel and return the one with highest score"""
    print(f"\n🔎 Analyzing {len(products)} products with parallel processing...")
    print("=" * 50)
    
    results = []
    error_count = 0
    
    batch_size = 50
    total_batches = (len(products) + batch_size - 1) // batch_size
    
    with ThreadPoolExecutor(max_workers=25) as executor:
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(products))
            batch = products[start_idx:end_idx]
            
            print(f"\n📦 Processing batch {batch_num + 1}/{total_batches} ({len(batch)} products)")
            print(f"   Products {start_idx + 1}-{end_idx} of {len(products)}")
            
            futures = []
            for i, product in enumerate(batch):
                product_num = start_idx + i + 1
                future = executor.submit(
                    process_single_product,
                    model, reference_image, product, product_num, len(products)
                )
                futures.append((future, product))
            
            batch_processed = 0
            for future, product in futures:
                try:
                    score_data, error = future.result(timeout=30)
                    
                    if error:
                        error_count += 1
                    elif score_data is not None:
                        results.append((product, score_data))
                        batch_processed += 1
                except Exception as e:
                    print(f"  ⚠️ Thread error: {e}")
                    error_count += 1
            
            print(f"   ✅ Batch complete: {batch_processed} products scored")
            
            if batch_num < total_batches - 1:
                time.sleep(0.5)
    
    # Sort results by final_score (highest first) for display
    results_sorted = sorted(results, key=lambda x: x[1]['final_score'], reverse=True)
    
    # Display all scores
    print(f"\n📊 All Product Scores (sorted by Final Score):")
    print("=" * 50)
    for product, score_data in results_sorted:
        print(f"  #{product['index']}: Final={score_data['final_score']:.1f} | "
              f"Shape={score_data['shape']} Strap={score_data['strap']} "
              f"Dial={score_data['dial']} Color={score_data['color']} | "
              f"Price: {product['price']}")
    
    if results:
        best_product, best_score_data = max(results, key=lambda x: x[1]['final_score'])
        print(f"\n🏆 Best match found!")
        print(f"   Product #: {best_product['index']}")
        print(f"   Final Score: {best_score_data['final_score']:.1f}/100")
        print(f"   └─ Shape: {best_score_data['shape']}/100 (35% weight)")
        print(f"   └─ Strap: {best_score_data['strap']}/100 (25% weight)")
        print(f"   └─ Dial: {best_score_data['dial']}/100 (25% weight)")
        print(f"   └─ Color: {best_score_data['color']}/100 (15% weight)")
        print(f"   URL: {best_product['product_url'][:80]}...")
        print(f"   Price: {best_product['price']}")
        return (best_product, best_score_data, error_count, results_sorted)
    else:
        print(f"\n❌ No valid matches found (all products failed)")
        return (None, None, error_count, [])

def save_to_csv(reference_image_url, product_url, product_image_url, price, score_data):
    """Save result to Watched_prices.csv in accumulative mode"""
    csv_file = 'Watched_prices.csv'
    file_exists = os.path.isfile(csv_file)
    
    try:
        with open(csv_file, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            if not file_exists:
                writer.writerow(['reference_image_url', '1688_url', '1688_product_image_url', 'price', 
                               'final_score', 'shape_score', 'strap_score', 'dial_score', 'color_score'])
            
            writer.writerow([
                reference_image_url, 
                product_url, 
                product_image_url, 
                price, 
                score_data['final_score'],
                score_data['shape'],
                score_data['strap'],
                score_data['dial'],
                score_data['color']
            ])
        
        print(f"💾 Saved to {csv_file}")
        return True
    except Exception as e:
        print(f"❌ Error saving to CSV: {e}")
        return False

def save_cheapest_high_quality_match(reference_image_url, all_products_with_scores):
    """Save the cheapest product with ≥95% score to Watches.csv"""
    csv_file = 'Watches.csv'
    file_exists = os.path.isfile(csv_file)
    
    # Filter products with final_score >= 95
    high_quality_products = [
        (product, score_data) for product, score_data in all_products_with_scores
        if score_data['final_score'] >= 95.0
    ]
    
    if not high_quality_products:
        print(f"⚠️ No products with ≥95% score found for Watches.csv")
        return False
    
    # Parse prices and find the cheapest
    def parse_price(price_str):
        """Extract numeric value from price string (e.g., '¥27.03' -> 27.03)"""
        try:
            # Remove currency symbols and other non-numeric chars except . and digits
            import re
            numbers = re.findall(r'\d+\.?\d*', price_str)
            if numbers:
                return float(numbers[0])
            return float('inf')  # If can't parse, treat as expensive
        except:
            return float('inf')
    
    # Find cheapest among high quality products
    cheapest_product, cheapest_score_data = min(
        high_quality_products,
        key=lambda x: parse_price(x[0]['price'])
    )
    
    try:
        with open(csv_file, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            if not file_exists:
                writer.writerow(['reference_image_url', 'final_score', 'price', '1688_url', '1688_thumbnail'])
            
            writer.writerow([
                reference_image_url,
                cheapest_score_data['final_score'],
                cheapest_product['price'],
                cheapest_product['product_url'],
                cheapest_product['image_url']
            ])
        
        print(f"💎 Saved to {csv_file} (cheapest ≥95% match: {cheapest_product['price']})")
        return True
    except Exception as e:
        print(f"❌ Error saving to Watches.csv: {e}")
        return False

def save_all_products_to_csv(reference_image_url, all_products_with_scores):
    """Save all products with their scores to a detailed CSV file"""
    # Auto-increment filename if exists
    base_filename = 'Watched_prices_detailed'
    csv_file = f'{base_filename}.csv'
    counter = 1
    
    while os.path.exists(csv_file):
        csv_file = f'{base_filename}{counter}.csv'
        counter += 1
    
    try:
        with open(csv_file, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Always write header for new file
            writer.writerow(['reference_image_url', 'product_number', 'final_score', 
                           'shape_score', 'strap_score', 'dial_score', 'color_score',
                           'price', '1688_url', '1688_product_image_url'])
            
            for product, score_data in all_products_with_scores:
                writer.writerow([
                    reference_image_url,
                    product['index'],
                    score_data['final_score'],
                    score_data['shape'],
                    score_data['strap'],
                    score_data['dial'],
                    score_data['color'],
                    product['price'],
                    product['product_url'],
                    product['image_url']
                ])
        
        print(f"💾 Saved all {len(all_products_with_scores)} products to {csv_file}")
        return csv_file
    except Exception as e:
        print(f"❌ Error saving detailed CSV: {e}")
        return None

def load_chrome_cookies(cookies_file='new_chrome_cookies.json'):
    """Load Chrome cookies and convert to Playwright format"""
    try:
        if not os.path.exists(cookies_file):
            print(f"ℹ️  No cookies file found: {cookies_file}")
            return None
        
        with open(cookies_file, 'r') as f:
            chrome_cookies = json.load(f)
        
        playwright_cookies = []
        for cookie in chrome_cookies:
            pw_cookie = {
                'name': cookie['name'],
                'value': cookie['value'],
                'domain': cookie['domain'],
                'path': cookie['path'],
                'secure': cookie.get('secure', False),
                'httpOnly': cookie.get('httpOnly', False),
            }
            
            if 'expirationDate' in cookie:
                pw_cookie['expires'] = int(cookie['expirationDate'])
            
            if 'sameSite' in cookie:
                sameSite = cookie['sameSite']
                if sameSite == 'no_restriction':
                    pw_cookie['sameSite'] = 'None'
                elif sameSite in ['lax', 'strict']:
                    pw_cookie['sameSite'] = sameSite.capitalize()
            
            playwright_cookies.append(pw_cookie)
        
        print(f"✅ Loaded {len(playwright_cookies)} cookies from {cookies_file}")
        return playwright_cookies
        
    except Exception as e:
        print(f"⚠️ Error loading cookies: {e}")
        return None

def download_image_from_url(url, temp_filename):
    """Download image from URL to temporary file"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        with open(temp_filename, 'wb') as f:
            f.write(response.content)
        
        return True
    except Exception as e:
        print(f"❌ Error downloading image from URL: {e}")
        return False

def get_imgbb_api_key():
    """Get ImgBB API key from environment or user input"""
    api_key = os.getenv('IMGBB_API_KEY')
    
    if not api_key:
        print("\n🔑 ImgBB API Key Setup (FREE - takes 30 seconds!)")
        print("=" * 60)
        print("1. Go to: https://api.imgbb.com/")
        print("2. Click 'Get API Key' (no credit card needed)")
        print("3. Sign up with email (free forever)")
        print("4. Copy your API key")
        print("=" * 60)
        api_key = input("Paste your ImgBB API key here: ").strip()
        
        if not api_key:
            print("❌ No API key provided!")
            print("💡 Tip: Set IMGBB_API_KEY environment variable to skip this step")
            return None
        
        # Offer to save it
        save = input("\n💾 Save this key to .env file? (y/n): ").strip().lower()
        if save == 'y':
            try:
                with open('.env', 'a') as f:
                    f.write(f"\nIMGBB_API_KEY={api_key}\n")
                print("✅ Key saved to .env file!")
            except Exception as e:
                print(f"⚠️ Could not save to .env: {e}")
    
    return api_key

def upload_local_image_to_imgbb(image_path, api_key):
    """Upload local image to ImgBB and return the URL with proper extension"""
    try:
        # ImgBB free upload - using multipart form
        url = 'https://api.imgbb.com/1/upload'
        
        # Get file extension
        file_ext = os.path.splitext(image_path)[1].lower()
        if not file_ext or file_ext not in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            file_ext = '.jpg'  # Default to .jpg
        
        # Read the image file
        with open(image_path, 'rb') as f:
            files = {
                'image': (os.path.basename(image_path), f, 'image/' + file_ext[1:])
            }
            
            params = {
                'key': api_key
            }
            
            print(f"📤 Uploading local image to ImgBB...")
            response = requests.post(url, params=params, files=files, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                # Get the direct URL to the image - ImgBB gives us the URL with extension
                image_url = result['data']['url']
                
                print(f"✅ Image uploaded successfully!")
                print(f"   URL: {image_url[:80]}...")
                return image_url
            else:
                error_msg = result.get('error', {}).get('message', 'Unknown error')
                print(f"❌ ImgBB upload failed: {error_msg}")
                return None
        else:
            print(f"❌ ImgBB API error: {response.status_code}")
            if response.text:
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data.get('error', {}).get('message', response.text[:200])}")
                except:
                    print(f"   Response: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"❌ Error uploading to ImgBB: {e}")
        import traceback
        traceback.print_exc()
        return None

def is_url(path):
    """Check if the input is a URL or local file path"""
    return path.startswith('http://') or path.startswith('https://')

def normalize_file_path(path):
    """Normalize file path - handle escaped spaces and expand user paths"""
    # Remove quotes if present
    path = path.strip('"').strip("'")
    
    # Handle escaped spaces (from drag-and-drop in terminal)
    # Replace "\ " with actual space
    path = path.replace('\\ ', ' ')
    
    # Expand user home directory (~)
    path = os.path.expanduser(path)
    
    # Convert to absolute path if relative
    if not os.path.isabs(path):
        path = os.path.abspath(path)
    
    return path

def main():
    """Main function"""
    print("🔍 Watch Prices - 1688 Product Finder")
    print("=" * 50)
    
    model = setup_gemini_api()
    if not model:
        return False
    
    print("\n🔗 Enter image URL(s) or local file path(s):")
    print("   - For single input: paste one URL or file path")
    print("   - For multiple inputs: separate with |||")
    print("   Example (URLs): |||https://example.com/img1.jpg|||https://example.com/img2.jpg")
    print("   Example (Files): |||/path/to/image1.jpg|||/path/to/image2.png")
    print("   Example (Mixed): |||https://example.com/img1.jpg|||/path/to/image2.jpg")
    print()
    sys.stdout.flush()
    user_input = input("Image URL(s) or path(s): ").strip()
    
    try:
        import select
        while select.select([sys.stdin], [], [], 0)[0]:
            sys.stdin.readline()
    except:
        pass
    
    if not user_input:
        print("❌ No URLs provided!")
        return False
    
    if '|||' in user_input:
        image_inputs = [inp.strip() for inp in user_input.split('|||') if inp.strip()]
    else:
        image_inputs = [user_input]
    
    if not image_inputs:
        print("❌ No valid inputs found!")
        return False
    
    print(f"\n✅ Found {len(image_inputs)} input(s) to process")
    if len(image_inputs) <= 5:
        for i, inp in enumerate(image_inputs, 1):
            input_type = "URL" if is_url(inp) else "File"
            print(f"   {i}. [{input_type}] {inp[:70]}{'...' if len(inp) > 70 else ''}")
    else:
        for i, inp in enumerate(image_inputs[:3], 1):
            input_type = "URL" if is_url(inp) else "File"
            print(f"   {i}. [{input_type}] {inp[:70]}{'...' if len(inp) > 70 else ''}")
        print(f"   ... and {len(image_inputs) - 3} more")
    
    temp_dir = 'temp_images'
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    # Convert all inputs to URLs (upload local files if needed)
    image_urls = []
    imgbb_api_key = None  # Will be requested only if needed
    
    for idx, image_input in enumerate(image_inputs, 1):
        print(f"\n{'=' * 50}")
        print(f"📝 Preparing input {idx}/{len(image_inputs)}")
        print(f"{'=' * 50}")
        
        if is_url(image_input):
            # It's already a URL
            print(f"✅ Using URL directly: {image_input[:60]}...")
            image_urls.append(image_input)
        else:
            # It's a local file path - need to upload it
            print(f"📁 Local file detected: {image_input}")
            
            # Get ImgBB API key if we haven't already
            if imgbb_api_key is None:
                imgbb_api_key = get_imgbb_api_key()
                if not imgbb_api_key:
                    print(f"⚠️ Cannot upload without ImgBB API key")
                    print(f"⚠️ Skipping all remaining local files")
                    # Skip all remaining local files
                    for remaining_idx in range(idx, len(image_inputs) + 1):
                        if not is_url(image_inputs[remaining_idx - 1] if remaining_idx <= len(image_inputs) else ""):
                            image_urls.append(None)
                    break
            
            # Normalize the path (handle escaped spaces, quotes, etc.)
            normalized_path = normalize_file_path(image_input)
            print(f"📝 Normalized path: {normalized_path}")
            
            # Check if file exists
            if not os.path.exists(normalized_path):
                print(f"❌ File not found: {normalized_path}")
                print(f"⚠️ Skipping this input")
                image_urls.append(None)
                continue
            
            # Check if it's a valid image
            try:
                test_img = Image.open(normalized_path)
                print(f"✅ Valid image: {test_img.size}, {test_img.format}")
                test_img.close()
            except Exception as e:
                print(f"❌ Invalid image file: {e}")
                print(f"⚠️ Skipping this input")
                image_urls.append(None)
                continue
            
            # Upload to ImgBB to get a URL
            uploaded_url = upload_local_image_to_imgbb(normalized_path, imgbb_api_key)
            if uploaded_url:
                image_urls.append(uploaded_url)
            else:
                print(f"⚠️ Skipping this input - could not upload image")
                image_urls.append(None)
    
    # Launch browser once and reuse it for all URLs
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
            ]
        )
        
        cookies = load_chrome_cookies('new_chrome_cookies.json')
        
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        )
        
        if cookies:
            context.add_cookies(cookies)
            print(f"🍪 Cookies loaded into browser context")
        
        # Now process all URLs using the same browser
        for idx, image_url in enumerate(image_urls, 1):
            if image_url is None:
                print(f"\n⏭️  Skipping input {idx} (failed to prepare)")
                continue
                
            is_first_url = (idx == 1)
            print(f"\n{'=' * 50}")
            print(f"📸 Processing input {idx}/{len(image_urls)}")
            print(f"   URL: {image_url[:80]}{'...' if len(image_url) > 80 else ''}")
            print(f"{'=' * 50}")
            
            temp_filename = os.path.join(temp_dir, f'temp_image_{idx}.jpg')
            print(f"⬇️  Downloading reference image...")
            
            if not download_image_from_url(image_url, temp_filename):
                print(f"⚠️ Skipping this input - could not download reference image")
                continue
            
            reference_image = load_reference_image(temp_filename)
            if not reference_image:
                print(f"⚠️ Skipping this URL - could not load reference image")
                if os.path.exists(temp_filename):
                    os.remove(temp_filename)
                continue
            
            # Create a new page (tab) for this search
            page = context.new_page()
            
            try:
                result_page = upload_image_to_aliprice(context, page, image_url, is_first_url=is_first_url)
                
                if not result_page:
                    print(f"⚠️ Failed to submit image URL - skipping")
                    page.close()  # Close only the current tab
                    if os.path.exists(temp_filename):
                        os.remove(temp_filename)
                    continue
                
                page = result_page
                
                products = extract_products_from_results(page)
                
                if not products:
                    print(f"⚠️ No products found in results - skipping")
                    page.close()  # Close only the current tab
                    if os.path.exists(temp_filename):
                        os.remove(temp_filename)
                    continue
                
                # Keep browser open, just close the search results tab after processing
                best_product, best_score, error_count, all_results = process_products_parallel(
                    model, reference_image, products
                )
                
                # Close the search results tab now that we've extracted the data
                page.close()
                
                # Save all products with scores to detailed CSV
                detailed_csv = None
                if all_results:
                    detailed_csv = save_all_products_to_csv(image_url, all_results)
                    # Also save the cheapest high-quality match to Watches.csv
                    save_cheapest_high_quality_match(image_url, all_results)
                
                # Save the best product to main CSV
                if best_product and best_score is not None:
                    save_to_csv(
                        image_url,
                        best_product['product_url'],
                        best_product['image_url'],
                        best_product['price'],
                        best_score
                    )
                    print(f"✅ Successfully processed URL")
                    if detailed_csv:
                        print(f"   Detailed results: {detailed_csv}")
                else:
                    print(f"❌ Could not find a match for this URL")
                
                if error_count > 0:
                    print(f"⚠️ {error_count} products had errors during processing")
                
                if os.path.exists(temp_filename):
                    os.remove(temp_filename)
                
            except Exception as e:
                print(f"❌ Error processing URL: {e}")
                import traceback
                traceback.print_exc()
                try:
                    page.close()  # Close only the current tab
                except:
                    pass
                if os.path.exists(temp_filename):
                    os.remove(temp_filename)
                continue
        
        # Browser will close automatically when exiting the 'with' block
        print(f"\n🌐 Browser will remain open. Close it manually when done.")
    
    try:
        if os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir)
    except:
        pass
    
    print(f"\n{'=' * 50}")
    print(f"🎉 All inputs processed!")
    print(f"📊 Results saved to:")
    print(f"   - Watches.csv (cheapest products with ≥95% score)")
    print(f"   - Watched_prices.csv (best overall matches)")
    print(f"   - Watched_prices_detailed*.csv (all products with detailed scores)")
    print(f"     Note: A new detailed file is created for each run")
    print(f"{'=' * 50}")
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
