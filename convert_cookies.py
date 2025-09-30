#!/usr/bin/env python3
"""
Convert Chrome cookie export to Playwright format
"""

import json
import os

def convert_cookies():
    """Convert chrome_cookies_raw.json to Playwright storage format"""
    
    print("🔄 Cookie Format Converter")
    print("=" * 50)
    
    input_file = 'chrome_cookies_raw.json'
    output_file = 'douyin_cookies.json'
    
    if not os.path.exists(input_file):
        print(f"❌ File not found: {input_file}")
        print("\nPlease:")
        print("1. Export cookies from Chrome using Cookie-Editor extension")
        print("2. Save as 'chrome_cookies_raw.json'")
        print("3. Run this script again")
        return False
    
    try:
        with open(input_file, 'r') as f:
            raw_cookies = json.load(f)
        
        # Convert to Playwright format
        playwright_cookies = []
        
        for cookie in raw_cookies:
            # Handle different export formats
            same_site = cookie.get('sameSite', 'None')
            
            # Convert sameSite values
            if same_site == 'no_restriction' or same_site is None:
                same_site = 'None'
            elif same_site not in ['Strict', 'Lax', 'None']:
                same_site = 'None'
            
            playwright_cookie = {
                'name': cookie.get('name', ''),
                'value': cookie.get('value', ''),
                'domain': cookie.get('domain', '.douyin.com'),
                'path': cookie.get('path', '/'),
                'expires': cookie.get('expirationDate', -1),
                'httpOnly': cookie.get('httpOnly', False),
                'secure': cookie.get('secure', False),
                'sameSite': same_site
            }
            playwright_cookies.append(playwright_cookie)
        
        # Create storage state
        storage_state = {
            'cookies': playwright_cookies,
            'origins': []
        }
        
        # Save
        with open(output_file, 'w') as f:
            json.dump(storage_state, f, indent=2)
        
        print(f"✅ Converted {len(playwright_cookies)} cookies")
        print(f"📄 Saved to: {output_file}")
        print(f"\n🎉 You can now run: python3 find_product_videos.py")
        
        # Clean up
        os.remove(input_file)
        print(f"🗑️ Removed temporary file: {input_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error converting cookies: {e}")
        return False

if __name__ == "__main__":
    convert_cookies()
