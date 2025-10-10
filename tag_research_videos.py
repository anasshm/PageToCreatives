#!/usr/bin/env python3
"""
AI Tagging for Research Videos
Tags product images using Gemini AI with structured taxonomy
"""

import os
import sys
import csv
import json
import time
from pathlib import Path
import google.generativeai as genai
from PIL import Image
import io
import requests
from concurrent.futures import ThreadPoolExecutor
import threading

def load_taxonomy():
    """Load product taxonomy with synonyms"""
    try:
        with open('product_taxonomy.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading taxonomy: {e}")
        return None

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
        # Use latest Gemini 2.5 Flash model (September 2025)
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
        return None

def generate_tagging_prompt(taxonomy):
    """Generate AI prompt with controlled vocabulary from taxonomy"""
    
    # Extract all valid options
    product_types = list(taxonomy['product_types'].keys())
    shapes = list(taxonomy['shapes'].keys())
    materials = list(taxonomy['materials'].keys())
    metal_colors = list(taxonomy['metal_colors'].keys())
    colors = list(taxonomy['colors'].keys())
    styles = list(taxonomy['styles'].keys())
    
    prompt = f"""Analyze this jewelry/accessory product image and extract ALL visible attributes.

**IMPORTANT RULES:**
1. Use ONLY the exact words from the allowed lists below
2. Return multiple tags if you see multiple features
3. Be inclusive - if you see any part of a shape, include it
4. Use PRIMARY TERMS only (e.g., "clover" not "fourleaf")
5. Return as many applicable tags as you find

**PRODUCT TYPE** (choose ONE):
{', '.join(product_types)}

**PRIMARY SHAPE** (choose ONE main design element):
{', '.join(shapes)}

**SECONDARY SHAPES** (list any additional shapes):
{', '.join(shapes)}

**PRIMARY COLOR** (main visible color):
{', '.join(colors)}

**METAL COLOR**:
{', '.join(metal_colors)}

**MATERIALS** (list all visible):
{', '.join(materials)}

**STYLE**:
{', '.join(styles)}

**SIZE** (relative size):
small, medium, large

Respond in this EXACT JSON format (no markdown, just raw JSON):
{{
  "product_type": "necklace",
  "primary_shape": "clover",
  "secondary_shapes": ["circle"],
  "primary_color": "black",
  "secondary_colors": [],
  "metal_color": "gold",
  "materials": ["enamel", "crystal"],
  "style": "luxury",
  "size": "small"
}}

If unsure about any field, use empty string "" or empty array [].
Return ONLY valid JSON, no explanations."""

    return prompt

def tag_single_video(model, taxonomy, video, video_num, total_videos, prompt):
    """Tag a single video using Gemini AI"""
    
    try:
        # Download thumbnail
        thumbnail = download_thumbnail(video['thumbnail_url'])
        if not thumbnail:
            print(f"  [{video_num}/{total_videos}] ⚠️ Failed to download thumbnail")
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
                
                # Generate pairing key
                pairing_key = f"{tags.get('primary_shape', '')}-{tags.get('primary_color', '')}-{tags.get('metal_color', '')}"
                tags['pairing_key'] = pairing_key.lower().replace(' ', '-')
                
                print(f"  [{video_num}/{total_videos}] ✅ Tagged: {tags.get('product_type', 'unknown')} - {tags.get('primary_shape', 'unknown')}")
                return (video, tags, None)
            else:
                print(f"  [{video_num}/{total_videos}] ⚠️ Empty response")
                return (video, None, 'empty_response')
                
        except json.JSONDecodeError as e:
            print(f"  [{video_num}/{total_videos}] ⚠️ JSON parse error: {e}")
            return (video, None, 'json_error')
        except Exception as e:
            error_msg = str(e).lower()
            if "quota" in error_msg or "rate limit" in error_msg or "429" in error_msg:
                print(f"  [{video_num}/{total_videos}] 🚫 Rate limit hit")
                return (video, None, 'rate_limit')
            else:
                print(f"  [{video_num}/{total_videos}] ❌ API error: {str(e)[:100]}")
                return (video, None, f'api_error: {str(e)[:100]}')
        
    except Exception as e:
        print(f"  [{video_num}/{total_videos}] ⚠️ Processing error: {e}")
        return (video, None, f'processing_error: {str(e)}')

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

def tag_research_videos(csv_path, output_json, max_videos=None, batch_size=50):
    """Main function to tag research videos"""
    
    print("🏷️ AI Product Tagging System")
    print("=" * 50)
    
    # Load taxonomy
    taxonomy = load_taxonomy()
    if not taxonomy:
        return False
    
    print(f"✅ Loaded taxonomy with {len(taxonomy['shapes'])} shapes")
    
    # Setup Gemini API
    model = setup_gemini_api()
    if not model:
        return False
    
    # Read CSV
    print(f"\n📖 Reading CSV: {csv_path}")
    try:
        videos = read_csv_with_comments(csv_path)
        print(f"✅ Loaded {len(videos)} videos")
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return False
    
    if not videos:
        print("❌ No videos found in CSV!")
        return False
    
    # Limit videos if specified
    if max_videos:
        videos = videos[:max_videos]
        print(f"⚠️ Processing first {max_videos} videos only (testing mode)")
    
    # Generate prompt
    prompt = generate_tagging_prompt(taxonomy)
    
    # Process videos in batches
    print(f"\n🔄 Tagging {len(videos)} videos...")
    print("=" * 50)
    
    tagged_videos = []
    error_count = 0
    error_types = {}
    
    total_batches = (len(videos) + batch_size - 1) // batch_size
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(videos))
            batch = videos[start_idx:end_idx]
            
            print(f"\n📦 Processing batch {batch_num + 1}/{total_batches} ({len(batch)} videos)")
            print(f"   Videos {start_idx + 1}-{end_idx} of {len(videos)}")
            
            # Submit batch to thread pool
            futures = []
            for i, video in enumerate(batch):
                video_num = start_idx + i + 1
                future = executor.submit(
                    tag_single_video,
                    model, taxonomy, video, video_num, len(videos), prompt
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
                        tagged_videos.append(video_with_tags)
                        batch_success += 1
                except Exception as e:
                    print(f"  ⚠️ Thread error: {e}")
                    error_count += 1
                    batch_errors += 1
            
            print(f"   ✅ Batch complete: {batch_success} tagged, {batch_errors} errors")
            
            # Small delay between batches
            if batch_num < total_batches - 1:
                time.sleep(0.5)
    
    # Save results
    print(f"\n💾 Saving tagged data to {output_json}...")
    try:
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(tagged_videos, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved {len(tagged_videos)} tagged videos")
    except Exception as e:
        print(f"❌ Error saving JSON: {e}")
        return False
    
    # Summary
    print(f"\n{'=' * 50}")
    print(f"🎉 Tagging Complete!")
    print(f"{'=' * 50}")
    print(f"✅ Successfully tagged: {len(tagged_videos)} videos")
    print(f"❌ Errors: {error_count} videos")
    
    if error_types:
        print(f"\n⚠️ Error breakdown:")
        for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {error_type}: {count}")
    
    print(f"\n📄 Output saved to: {output_json}")
    print(f"🌐 Next step: Generate gallery with tagged data")
    
    return True

def main():
    """Main entry point"""
    
    # Get CSV file
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    else:
        csv_path = input("\n📂 Enter CSV file path: ").strip()
        csv_path = csv_path.replace('\\', '').strip('"').strip("'")
    
    if not csv_path:
        print("❌ No file provided!")
        return
    
    if not os.path.exists(csv_path):
        print(f"❌ File not found: {csv_path}")
        return
    
    # Get output filename
    csv_name = Path(csv_path).stem
    output_json = f"{csv_name}_tagged.json"
    
    # Ask for test mode
    test_mode = input("\n🧪 Test mode? Tag only 100 videos? (y/n, default: n): ").strip().lower()
    max_videos = 100 if test_mode == 'y' else None
    
    # Run tagging
    success = tag_research_videos(csv_path, output_json, max_videos=max_videos)
    
    if not success:
        print("\n💥 Tagging failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()

