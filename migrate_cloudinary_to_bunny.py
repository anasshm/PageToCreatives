#!/usr/bin/env python3
"""
Migrate Cloudinary URLs to Bunny.net
Downloads images from Cloudinary and re-uploads to Bunny.net CDN
Updates JSON files with new Bunny.net URLs
"""

import os
import sys
import json
from pathlib import Path
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import hashlib

def load_env():
    """Load environment variables from .env file"""
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

def setup_bunny():
    """Setup Bunny.net configuration from environment variables"""
    api_key = os.getenv('BUNNY_API_KEY')
    storage_zone = os.getenv('BUNNY_STORAGE_ZONE')
    
    if not all([api_key, storage_zone]):
        print("❌ Bunny.net credentials not found in .env file!")
        return None
    
    config = {
        'api_key': api_key,
        'storage_zone': storage_zone,
        'storage_endpoint': f'https://storage.bunnycdn.com/{storage_zone}',
        'cdn_url': f'https://{storage_zone}.b-cdn.net'
    }
    
    print("✅ Bunny.net configured successfully")
    print(f"   Storage Zone: {storage_zone}")
    print(f"   CDN URL: {config['cdn_url']}")
    return config

def migrate_image(cloudinary_url, bunny_config, retries=3):
    """Download from Cloudinary and upload to Bunny.net"""
    
    # Generate unique filename from original URL
    url_hash = hashlib.md5(cloudinary_url.encode()).hexdigest()
    filename = f"douyin_thumbnails/{url_hash}.jpg"
    
    for attempt in range(retries):
        try:
            # Download from Cloudinary
            img_response = requests.get(cloudinary_url, timeout=30)
            if img_response.status_code != 200:
                return None, f"Failed to download: HTTP {img_response.status_code}"
            
            # Upload to Bunny Storage
            upload_url = f"{bunny_config['storage_endpoint']}/{filename}"
            headers = {
                'AccessKey': bunny_config['api_key'],
                'Content-Type': 'application/octet-stream'
            }
            
            upload_response = requests.put(
                upload_url,
                headers=headers,
                data=img_response.content,
                timeout=30
            )
            
            if upload_response.status_code == 201:
                # Return Bunny CDN URL
                cdn_url = f"{bunny_config['cdn_url']}/{filename}"
                return cdn_url, None
            else:
                if attempt < retries - 1:
                    continue
                else:
                    return None, f"Upload failed: HTTP {upload_response.status_code}"
                    
        except Exception as e:
            if attempt < retries - 1:
                continue
            else:
                return None, str(e)
    
    return None, "Max retries exceeded"

def migrate_json(json_path, bunny_config):
    """Migrate all Cloudinary URLs in a JSON file to Bunny.net"""
    
    print(f"\n📂 Processing: {json_path}")
    
    # Read JSON
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            videos = json.load(f)
        print(f"✅ Loaded {len(videos)} videos")
    except Exception as e:
        print(f"❌ Error reading JSON: {e}")
        return False
    
    # Find videos with Cloudinary URLs
    cloudinary_videos = [v for v in videos if v.get('backup_thumbnail_url', '').startswith('https://res.cloudinary.com')]
    
    if not cloudinary_videos:
        print("ℹ️  No Cloudinary URLs found - already migrated or no backups")
        return True
    
    print(f"🔄 Found {len(cloudinary_videos)} Cloudinary URLs to migrate")
    print(f"⏭️  Skipping {len(videos) - len(cloudinary_videos)} videos (already on Bunny.net or no backup)")
    
    # Migrate with parallel processing
    successful = 0
    failed = 0
    lock = threading.Lock()
    
    print(f"\n🚀 Migrating to Bunny.net (20 concurrent uploads)...")
    print("=" * 60)
    
    def process_migration(index, video):
        """Process a single image migration"""
        cloudinary_url = video.get('backup_thumbnail_url', '')
        
        with lock:
            print(f"  [{index + 1}/{len(cloudinary_videos)}] Migrating...")
        
        bunny_url, error = migrate_image(cloudinary_url, bunny_config)
        
        if bunny_url:
            video['backup_thumbnail_url'] = bunny_url
            with lock:
                print(f"  [{index + 1}/{len(cloudinary_videos)}] ✅ Success")
            return 'success', video
        else:
            with lock:
                print(f"  [{index + 1}/{len(cloudinary_videos)}] ❌ Failed: {error}")
            return 'failed', video
    
    # Use ThreadPoolExecutor for parallel migrations (20 concurrent, CPU-friendly)
    max_workers = 20
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_migration, i, v): i for i, v in enumerate(cloudinary_videos)}
        
        for future in as_completed(futures):
            try:
                status, _ = future.result()
                if status == 'success':
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"  ❌ Thread error: {e}")
                failed += 1
    
    # Check failure rate
    failure_rate = failed / len(cloudinary_videos) if cloudinary_videos else 0
    if failure_rate > 0.5 and failed > 10:
        print(f"\n⚠️  WARNING: High failure rate ({failed}/{len(cloudinary_videos)} failed)!")
        return False
    
    # Create output filename
    json_name = Path(json_path).stem
    json_dir = Path(json_path).parent
    output_path = json_dir / f"Bunny_{json_name}.json"
    
    # Write migrated JSON
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(videos, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Migration complete!")
        print(f"📄 Saved to: {output_path}")
    except Exception as e:
        print(f"\n❌ Error writing output: {e}")
        return False
    
    # Print summary
    print(f"\n📊 SUMMARY")
    print("=" * 60)
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📁 Total migrated: {len(cloudinary_videos)}")
    print(f"⏭️  Skipped: {len(videos) - len(cloudinary_videos)}")
    print("=" * 60)
    
    return True

def main():
    """Main entry point"""
    print("🔄 Cloudinary to Bunny.net Migration Tool")
    print("=" * 60)
    
    # Load environment variables
    load_env()
    
    # Setup Bunny.net
    bunny_config = setup_bunny()
    if not bunny_config:
        sys.exit(1)
    
    # Get JSON file path
    if len(sys.argv) > 1:
        json_path = sys.argv[1].replace('\\', '').strip('"').strip("'")
    else:
        json_input = input("\n📂 Drag and drop JSON file here (or enter path): ").strip()
        if not json_input:
            print("❌ No file path provided!")
            sys.exit(1)
        json_path = json_input.replace('\\', '').strip('"').strip("'")
    
    # Validate path
    if not os.path.exists(json_path):
        print(f"❌ File not found: {json_path}")
        sys.exit(1)
    
    # Migrate
    success = migrate_json(json_path, bunny_config)
    
    if not success:
        print("\n❌ Migration failed")
        sys.exit(1)
    
    print("\n🎉 Migration complete! Your images are now on Bunny.net CDN.")

if __name__ == "__main__":
    main()

