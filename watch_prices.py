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
    """Compare product image with reference image using Gemini"""
    max_retries = 2
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            prompt = """Compare these two images and rate their similarity from 0 to 100.

The FIRST image is the reference product.
The SECOND image is a product from search results.

Rate how similar they are:
- 100 = Identical product (same design, shape, style)
- 80-99 = Very similar (same type, minor differences)
- 60-79 = Similar (same category, notable differences)
- 40-59 = Somewhat similar (same general category)
- 20-39 = Different but related
- 0-19 = Completely different

Focus on:
- Product type and category
- Overall shape and design
- Key visual features
- Style and appearance

Answer with ONLY a number from 0 to 100. No other text."""

            response = model.generate_content([prompt, reference_image, product_image])
            
            if response and response.text:
                answer = response.text.strip()
                match = re.search(r'\d+', answer)
                if match:
                    score = int(match.group())
                    score = max(0, min(100, score))
                    return (score, None)
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

def process_single_product(model, reference_image, product, product_num, total_products):
    """Process a single product - download and compare"""
    try:
        product_image = download_product_image(product['image_url'])
        if not product_image:
            print(f"  [{product_num}/{total_products}] ⚠️ Failed to download image")
            return (None, 'download_failed')
        
        score, error = compare_image_with_gemini_score(model, reference_image, product_image, product_num)
        
        if error:
            if 'rate_limit' in str(error):
                print(f"  [{product_num}/{total_products}] 🚫 RATE LIMIT")
            elif 'api_error' in str(error):
                print(f"  [{product_num}/{total_products}] ❌ API ERROR")
            else:
                print(f"  [{product_num}/{total_products}] ⚠️ ERROR: {error}")
            return (None, error)
        else:
            print(f"  [{product_num}/{total_products}] 📊 Score: {score}")
            return (score, None)
        
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
    
    with ThreadPoolExecutor(max_workers=50) as executor:
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
                    score, error = future.result(timeout=30)
                    
                    if error:
                        error_count += 1
                    elif score is not None:
                        results.append((product, score))
                        batch_processed += 1
                except Exception as e:
                    print(f"  ⚠️ Thread error: {e}")
                    error_count += 1
            
            print(f"   ✅ Batch complete: {batch_processed} products scored")
            
            if batch_num < total_batches - 1:
                time.sleep(0.5)
    
    if results:
        best_product, best_score = max(results, key=lambda x: x[1])
        print(f"\n🏆 Best match found!")
        print(f"   Score: {best_score}/100")
        print(f"   URL: {best_product['product_url'][:80]}...")
        print(f"   Price: {best_product['price']}")
        return (best_product, best_score, error_count)
    else:
        print(f"\n❌ No valid matches found (all products failed)")
        return (None, None, error_count)

def save_to_csv(reference_image_url, product_url, product_image_url, price, similarity_score):
    """Save result to Watched_prices.csv in accumulative mode"""
    csv_file = 'Watched_prices.csv'
    file_exists = os.path.isfile(csv_file)
    
    try:
        with open(csv_file, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            if not file_exists:
                writer.writerow(['reference_image_url', '1688_url', '1688_product_image_url', 'price', 'similarity_score'])
            
            writer.writerow([reference_image_url, product_url, product_image_url, price, similarity_score])
        
        print(f"💾 Saved to {csv_file}")
        return True
    except Exception as e:
        print(f"❌ Error saving to CSV: {e}")
        return False

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

def main():
    """Main function"""
    print("🔍 Watch Prices - 1688 Product Finder")
    print("=" * 50)
    
    model = setup_gemini_api()
    if not model:
        return False
    
    print("\n🔗 Enter image URL(s):")
    print("   - For single URL: paste one URL")
    print("   - For multiple URLs: paste URLs separated by |||")
    print("   Example: |||https://example.com/img1.jpg|||https://example.com/img2.jpg")
    print()
    sys.stdout.flush()
    user_input = input("Image URL(s): ").strip()
    
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
        image_urls = [url.strip() for url in user_input.split('|||') if url.strip()]
    else:
        image_urls = [user_input]
    
    if not image_urls:
        print("❌ No valid URLs found!")
        return False
    
    print(f"\n✅ Found {len(image_urls)} URL(s) to process")
    if len(image_urls) <= 5:
        for i, url in enumerate(image_urls, 1):
            print(f"   {i}. {url[:80]}{'...' if len(url) > 80 else ''}")
    else:
        for i, url in enumerate(image_urls[:3], 1):
            print(f"   {i}. {url[:80]}{'...' if len(url) > 80 else ''}")
        print(f"   ... and {len(image_urls) - 3} more")
    
    temp_dir = 'temp_images'
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    for idx, image_url in enumerate(image_urls, 1):
        is_first_url = (idx == 1)
        print(f"\n{'=' * 50}")
        print(f"📸 Processing URL {idx}/{len(image_urls)}")
        print(f"   URL: {image_url[:80]}{'...' if len(image_url) > 80 else ''}")
        print(f"{'=' * 50}")
        
        temp_filename = os.path.join(temp_dir, f'temp_image_{idx}.jpg')
        print(f"⬇️  Downloading reference image...")
        
        if not download_image_from_url(image_url, temp_filename):
            print(f"⚠️ Skipping this URL - could not download reference image")
            continue
        
        reference_image = load_reference_image(temp_filename)
        if not reference_image:
            print(f"⚠️ Skipping this URL - could not load reference image")
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
            continue
        
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
            
            page = context.new_page()
            
            try:
                result_page = upload_image_to_aliprice(context, page, image_url, is_first_url=is_first_url)
                
                if not result_page:
                    print(f"⚠️ Failed to submit image URL - skipping")
                    browser.close()
                    if os.path.exists(temp_filename):
                        os.remove(temp_filename)
                    continue
                
                page = result_page
                
                products = extract_products_from_results(page)
                
                if not products:
                    print(f"⚠️ No products found in results - skipping")
                    browser.close()
                    if os.path.exists(temp_filename):
                        os.remove(temp_filename)
                    continue
                
                browser.close()
                
                best_product, best_score, error_count = process_products_parallel(
                    model, reference_image, products
                )
                
                if best_product and best_score is not None:
                    save_to_csv(
                        image_url,
                        best_product['product_url'],
                        best_product['image_url'],
                        best_product['price'],
                        best_score
                    )
                    print(f"✅ Successfully processed URL")
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
                browser.close()
                if os.path.exists(temp_filename):
                    os.remove(temp_filename)
                continue
    
    try:
        if os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir)
    except:
        pass
    
    print(f"\n{'=' * 50}")
    print(f"🎉 All URLs processed!")
    print(f"📊 Results saved to: Watched_prices.csv")
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
