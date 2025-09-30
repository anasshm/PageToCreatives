#!/usr/bin/env python3
"""
Export Chrome cookies for Douyin
This creates a cookie file that Playwright can use to bypass login
"""

import json
import subprocess
import os
import sqlite3
import shutil
from pathlib import Path

def find_chrome_cookies():
    """Find Chrome cookies database location"""
    possible_paths = [
        os.path.expanduser('~/Library/Application Support/Google/Chrome/Default/Cookies'),
        os.path.expanduser('~/Library/Application Support/Google/Chrome/Profile 1/Cookies'),
        os.path.expanduser('~/Library/Application Support/Chromium/Default/Cookies'),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None

def export_cookies():
    """Export Douyin cookies from Chrome"""
    
    print("🍪 Chrome Cookie Exporter for Douyin")
    print("=" * 50)
    
    # Find Chrome cookies
    cookies_db = find_chrome_cookies()
    
    if not cookies_db:
        print("❌ Could not find Chrome cookies database!")
        print("\nPlease use the manual method:")
        print("1. Install 'EditThisCookie' Chrome extension")
        print("2. Go to douyin.com in Chrome")
        print("3. Click the EditThisCookie icon")
        print("4. Click 'Export' button")
        print("5. Save as 'chrome_cookies.json'")
        print("6. Run: python3 convert_cookies.py")
        return False
    
    print(f"✅ Found Chrome cookies: {cookies_db}")
    
    # Copy to temp location (Chrome locks the file)
    temp_db = '/tmp/chrome_cookies_temp.db'
    try:
        shutil.copy2(cookies_db, temp_db)
    except Exception as e:
        print(f"❌ Error copying cookies database: {e}")
        print("Please close Chrome and try again, or use the manual method above.")
        return False
    
    try:
        # Connect to cookies database
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Query for douyin.com cookies
        cursor.execute("""
            SELECT name, value, host_key, path, expires_utc, is_secure, is_httponly, samesite
            FROM cookies 
            WHERE host_key LIKE '%douyin.com%' OR host_key LIKE '%douyincdn.com%'
        """)
        
        cookies = []
        for row in cursor.fetchall():
            name, value, domain, path, expires, secure, httponly, samesite = row
            
            # Convert Chrome's timestamp (microseconds since Jan 1, 1601) to Unix timestamp
            if expires > 0:
                expires = (expires / 1000000) - 11644473600
            else:
                expires = -1
            
            cookie = {
                'name': name,
                'value': value,
                'domain': domain,
                'path': path,
                'expires': expires,
                'httpOnly': bool(httponly),
                'secure': bool(secure),
                'sameSite': ['None', 'Lax', 'Strict'][samesite] if samesite in [0, 1, 2] else 'None'
            }
            cookies.append(cookie)
        
        conn.close()
        os.remove(temp_db)
        
        if not cookies:
            print("❌ No Douyin cookies found!")
            print("\nPlease:")
            print("1. Open douyin.com in Chrome")
            print("2. Browse around (don't need to login)")
            print("3. Run this script again")
            return False
        
        # Create Playwright storage state format
        storage_state = {
            'cookies': cookies,
            'origins': []
        }
        
        # Save to file
        output_file = 'douyin_cookies.json'
        with open(output_file, 'w') as f:
            json.dump(storage_state, f, indent=2)
        
        print(f"✅ Exported {len(cookies)} cookies to {output_file}")
        print(f"\n🎉 You can now run the script without login!")
        return True
        
    except Exception as e:
        print(f"❌ Error reading cookies: {e}")
        if os.path.exists(temp_db):
            os.remove(temp_db)
        return False

def main():
    success = export_cookies()
    
    if not success:
        print("\n" + "=" * 50)
        print("ALTERNATIVE METHOD - Manual Export:")
        print("=" * 50)
        print("\n1. Install Chrome extension: 'Cookie-Editor'")
        print("   https://chrome.google.com/webstore/detail/cookie-editor/")
        print("\n2. Go to https://www.douyin.com in Chrome")
        print("\n3. Click the Cookie-Editor extension icon")
        print("\n4. Click 'Export' → 'Export as JSON'")
        print("\n5. Save the file as 'douyin_cookies_raw.json'")
        print("\n6. Run: python3 convert_cookies.py")

if __name__ == "__main__":
    main()
