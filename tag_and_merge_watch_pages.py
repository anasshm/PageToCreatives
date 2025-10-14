#!/usr/bin/env python3
"""
Tag and Merge Watch Pages
Incrementally adds new videos to existing tagged collection
Only tags videos not already processed
"""

import os
import sys
import csv
import json
import time
import shutil
from pathlib import Path
import google.generativeai as genai
from PIL import Image
import io
import requests
from concurrent.futures import ThreadPoolExecutor

def setup_gemini_api():
    """Setup Gemini API"""
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        # Try loading from .env file
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                for line in f:
                    if line.startswith('GEMINI_API_KEY='):
                        api_key = line.split('=', 1)[1].strip()
                        break
    
    if not api_key:
        print("🔑 Gemini API Key Setup")
        print("=" * 50)
        api_key = input("Enter your Google AI Studio API key: ").strip()
        
        if not api_key:
            print("❌ No API key provided!")
            return None
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash-lite-preview-09-2025')
        print("✅ Gemini API configured successfully")
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
        return None

def generate_tagging_prompt():
    """Generate AI prompt for watch attribute extraction"""
    
    prompt = """Analyze this watch image and extract ALL visible attributes.

**IMPORTANT RULES:**
1. Use ONLY the exact words from the allowed lists below
2. For ALL color fields: ALWAYS choose the closest matching color from the list
3. Return valid JSON only, no explanations

**CASE SHAPE** (choose ONE):
round, square, rectangular, oval, triangular, other

**CASE COLOR** (choose ONE - pick the closest match):
gold, silver, rose-gold, black, white

**DIAL COLOR** (choose ONE - MUST pick closest color match):
white, black, gold, silver, blue, pink, red, green, purple, brown

**DIAL MARKERS** (choose ONE - numbers/markers on the dial):
roman, arabic, minimalist, crystals, mixed, other

**STRAP TYPE** (choose ONE):
metal-bracelet, leather, fabric, rubber, other

**STRAP COLOR** (choose ONE - MUST pick closest color match):
gold, silver, black, brown, tan, white, pink, red, blue, green

Respond in this EXACT JSON format (no markdown, just raw JSON):
{
  "case_shape": "square",
  "case_color": "silver",
  "dial_color": "pink",
  "dial_markers": "minimalist",
  "strap_type": "metal-bracelet",
  "strap_color": "silver"
}

IMPORTANT: For colors, always choose the closest match. No "other" allowed for color fields.
Return ONLY valid JSON, no explanations."""

    return prompt

def tag_single_video(model, video, video_num, total_videos, prompt):
    """Tag a single video using Gemini AI"""
    
    try:
        # Download thumbnail
        thumbnail = download_thumbnail(video['thumbnail_url'])
        if not thumbnail:
            return (video, None, 'download_failed')
        
        # Call Gemini API
        try:
            response = model.generate_content([prompt, thumbnail])
            
            if response and response.text:
                # Parse JSON response
                response_text = response.text.strip()
                
                # Remove markdown code blocks if present
                if response_text.startswith('```'):
                    lines = response_text.split('\n')
                    response_text = '\n'.join(lines[1:-1])
                if response_text.startswith('json'):
                    response_text = response_text[4:].strip()
                
                tags = json.loads(response_text)
                
                # Validate all required fields are present
                required_fields = ['case_shape', 'case_color', 'dial_color', 'dial_markers', 'strap_type', 'strap_color']
                for field in required_fields:
                    if field not in tags:
                        tags[field] = 'other'
                
                # Generate fingerprint for easy display
                fingerprint = f"{tags['case_shape']}-{tags['case_color']}-{tags['dial_color']}-{tags['dial_markers']}-{tags['strap_type']}-{tags['strap_color']}"
                
                print(f"  [{video_num}/{total_videos}] ✅ Tagged: {fingerprint}")
                return (video, tags, None)
            else:
                return (video, None, 'empty_response')
                
        except json.JSONDecodeError as e:
            return (video, None, 'json_error')
        except Exception as e:
            error_msg = str(e).lower()
            if "quota" in error_msg or "rate limit" in error_msg or "429" in error_msg:
                return (video, None, 'rate_limit')
            else:
                return (video, None, f'api_error: {str(e)[:100]}')
        
    except Exception as e:
        return (video, None, f'processing_error: {str(e)}')

def load_existing_tagged_videos(json_path):
    """Load existing tagged videos from JSON file"""
    if not os.path.exists(json_path):
        return []
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            videos = json.load(f)
        return videos
    except Exception as e:
        print(f"⚠️ Error loading existing JSON: {e}")
        return []

def extract_tagged_urls(videos):
    """Extract set of video URLs for fast lookup"""
    return set(video.get('video_url', '') for video in videos)

def read_csv_with_comments(csv_path):
    """Read CSV file, skip comment lines"""
    rows = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Skip comment lines
    csv_start = 0
    for i, line in enumerate(lines):
        if line.strip().startswith('#'):
            csv_start = i + 1
        else:
            break
    
    # Read CSV data
    csv_lines = lines[csv_start:]
    if csv_lines:
        reader = csv.DictReader(csv_lines)
        for row in reader:
            rows.append(row)
    
    return rows

def filter_new_videos(csv_videos, existing_urls):
    """Return only videos not in existing tagged set"""
    new_videos = []
    for video in csv_videos:
        if video.get('video_url', '') not in existing_urls:
            new_videos.append(video)
    return new_videos

def backup_existing_file(filepath):
    """Create backup copy before overwriting"""
    if os.path.exists(filepath):
        backup_path = f"{filepath}.backup"
        shutil.copy2(filepath, backup_path)
        print(f"✅ Backed up existing file to: {backup_path}")

def save_tagged_csv(tagged_videos, output_csv):
    """Save tagged videos to CSV with attribute columns"""
    try:
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            # Write header comment
            f.write(f"# Tagged Watch Pages CSV\n")
            f.write(f"# Total Videos: {len(tagged_videos)}\n")
            f.write(f"# Last Updated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"#\n")
            
            # Define fieldnames
            fieldnames = ['video_url', 'thumbnail_url', 'likes', 'index', 'source_page', 
                         'case_shape', 'case_color', 'dial_color', 'dial_markers', 'strap_type', 'strap_color']
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            # Write data
            for video in tagged_videos:
                row = {
                    'video_url': video.get('video_url', ''),
                    'thumbnail_url': video.get('thumbnail_url', ''),
                    'likes': video.get('likes', ''),
                    'index': video.get('index', ''),
                    'source_page': video.get('source_page', ''),
                    'case_shape': video['tags'].get('case_shape', 'other'),
                    'case_color': video['tags'].get('case_color', 'other'),
                    'dial_color': video['tags'].get('dial_color', 'other'),
                    'dial_markers': video['tags'].get('dial_markers', 'other'),
                    'strap_type': video['tags'].get('strap_type', 'other'),
                    'strap_color': video['tags'].get('strap_color', 'other')
                }
                writer.writerow(row)
        
        return True
    except Exception as e:
        print(f"❌ Error saving CSV: {e}")
        return False

def regenerate_gallery(tagged_json):
    """Auto-regenerate the gallery HTML"""
    print(f"\n🌐 Regenerating gallery...")
    
    try:
        # Import and run gallery generator
        import subprocess
        result = subprocess.run(
            ['python3', 'generate_watch_pages_gallery.py', tagged_json],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Gallery regenerated successfully")
        else:
            print(f"⚠️ Gallery generation had issues: {result.stderr}")
    except Exception as e:
        print(f"⚠️ Could not auto-regenerate gallery: {e}")
        print(f"💡 Run manually: python3 generate_watch_pages_gallery.py {tagged_json}")

def tag_and_merge(new_csv_path, existing_json_path='Watch Pages_tagged.json', max_videos=None, batch_size=50):
    """Main function to tag new videos and merge with existing"""
    
    print("🔄 Watch Pages - Tag & Merge System")
    print("=" * 50)
    
    # Load existing tagged videos
    print(f"\n📂 Loading existing tagged videos...")
    existing_videos = load_existing_tagged_videos(existing_json_path)
    existing_urls = extract_tagged_urls(existing_videos)
    print(f"✅ Found {len(existing_videos)} existing tagged videos")
    
    # Read new CSV
    print(f"\n📖 Reading new CSV: {new_csv_path}")
    try:
        csv_videos = read_csv_with_comments(new_csv_path)
        print(f"✅ Loaded {len(csv_videos)} videos from CSV")
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return False
    
    # Filter to only new videos
    print(f"\n🔍 Filtering new videos...")
    new_videos = filter_new_videos(csv_videos, existing_urls)
    already_tagged = len(csv_videos) - len(new_videos)
    
    print(f"📊 Analysis:")
    print(f"   Videos in CSV: {len(csv_videos)}")
    print(f"   Already tagged (skipping): {already_tagged}")
    print(f"   New videos to tag: {len(new_videos)}")
    
    if len(new_videos) == 0:
        print("\n✅ No new videos to tag! All videos are already processed.")
        return True
    
    # Limit videos if specified
    if max_videos:
        new_videos = new_videos[:max_videos]
        print(f"⚠️ Processing first {max_videos} new videos only (testing mode)")
    
    # Setup Gemini API
    model = setup_gemini_api()
    if not model:
        return False
    
    # Generate prompt
    prompt = generate_tagging_prompt()
    
    # Process new videos in batches
    print(f"\n🔄 Tagging {len(new_videos)} new videos...")
    print("=" * 50)
    
    newly_tagged_videos = []
    error_count = 0
    error_types = {}
    
    total_batches = (len(new_videos) + batch_size - 1) // batch_size
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(new_videos))
            batch = new_videos[start_idx:end_idx]
            
            print(f"\n📦 Processing batch {batch_num + 1}/{total_batches} ({len(batch)} videos)")
            print(f"   Videos {start_idx + 1}-{end_idx} of {len(new_videos)}")
            
            # Submit batch to thread pool
            futures = []
            for i, video in enumerate(batch):
                video_num = start_idx + i + 1
                future = executor.submit(
                    tag_single_video,
                    model, video, video_num, len(new_videos), prompt
                )
                futures.append(future)
            
            # Collect results
            batch_success = 0
            batch_errors = 0
            for future in futures:
                try:
                    video, tags, error = future.result(timeout=30)
                    
                    if error:
                        error_count += 1
                        batch_errors += 1
                        error_types[error] = error_types.get(error, 0) + 1
                    else:
                        # Add tags to video data
                        video_with_tags = video.copy()
                        video_with_tags['tags'] = tags
                        newly_tagged_videos.append(video_with_tags)
                        batch_success += 1
                except Exception as e:
                    print(f"  ⚠️ Thread error: {e}")
                    error_count += 1
                    batch_errors += 1
            
            print(f"   ✅ Batch complete: {batch_success} tagged, {batch_errors} errors")
            
            # Small delay between batches
            if batch_num < total_batches - 1:
                time.sleep(0.5)
    
    # Merge existing + newly tagged
    print(f"\n💾 Merging & Saving...")
    all_videos = existing_videos + newly_tagged_videos
    total_count = len(all_videos)
    
    print(f"📊 Final count: {total_count} videos ({len(existing_videos)} existing + {len(newly_tagged_videos)} new)")
    
    # Backup existing file
    backup_existing_file(existing_json_path)
    
    # Save JSON
    try:
        with open(existing_json_path, 'w', encoding='utf-8') as f:
            json.dump(all_videos, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved JSON: {existing_json_path} ({total_count} videos)")
    except Exception as e:
        print(f"❌ Error saving JSON: {e}")
        return False
    
    # Save CSV
    csv_path = existing_json_path.replace('.json', '.csv')
    if save_tagged_csv(all_videos, csv_path):
        print(f"✅ Saved CSV: {csv_path} ({total_count} videos)")
    
    # Summary
    print(f"\n{'=' * 50}")
    print(f"🎉 Merge Complete!")
    print(f"{'=' * 50}")
    print(f"📊 Previous total: {len(existing_videos)} videos")
    print(f"➕ Newly tagged: {len(newly_tagged_videos)} videos")
    print(f"❌ Errors: {error_count} videos")
    print(f"✅ New total: {total_count} videos")
    
    if error_types:
        print(f"\n⚠️ Error breakdown:")
        for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {error_type}: {count}")
    
    # Auto-regenerate gallery
    regenerate_gallery(existing_json_path)
    
    print(f"\n📄 Outputs:")
    print(f"  - {existing_json_path}")
    print(f"  - {csv_path}")
    print(f"  - watch_pages_gallery.html")
    
    return True

def main():
    """Main entry point"""
    
    # Get new CSV file
    if len(sys.argv) > 1:
        new_csv_path = sys.argv[1]
    else:
        new_csv_path = input("\n📂 Enter new CSV file path: ").strip()
        new_csv_path = new_csv_path.replace('\\', '').strip('"').strip("'")
    
    if not new_csv_path:
        print("❌ No file provided!")
        return
    
    if not os.path.exists(new_csv_path):
        print(f"❌ File not found: {new_csv_path}")
        return
    
    # Ask for test mode
    test_mode = input("\n🧪 Test mode? Tag only first 100 new videos? (y/n, default: n): ").strip().lower()
    max_videos = 100 if test_mode == 'y' else None
    
    # Run merge
    success = tag_and_merge(new_csv_path, max_videos=max_videos)
    
    if not success:
        print("\n💥 Merge failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()


