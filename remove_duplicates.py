#!/usr/bin/env python3
"""
Remove Duplicate Videos from CSV
Removes duplicate videos based on visual similarity of thumbnails
Uses perceptual hashing to detect visually identical images
Keeps the first occurrence of each unique thumbnail
"""

import csv
import sys
from pathlib import Path
import requests
from PIL import Image
from io import BytesIO
import imagehash

def download_thumbnail(url):
    """Download thumbnail image from URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        return image
    except Exception as e:
        return None

def get_image_hash(image):
    """Get perceptual hash of image for similarity detection"""
    try:
        # Use average hash (fast and good for exact duplicates)
        return str(imagehash.average_hash(image, hash_size=8))
    except:
        return None

def remove_duplicates(input_csv, output_csv=None, similarity_threshold=0):
    """Remove duplicate videos from CSV based on visual similarity of thumbnails
    
    Args:
        input_csv: Path to input CSV file
        output_csv: Path to output CSV file (optional, defaults to input_unique.csv)
        similarity_threshold: How many bits can differ (0=exact, 5=very similar, 10=similar)
    
    Returns:
        tuple: (original_count, unique_count, duplicates_removed)
    """
    
    # Generate output filename if not provided
    if not output_csv:
        input_path = Path(input_csv)
        output_csv = input_path.parent / f"{input_path.stem}_unique{input_path.suffix}"
    
    seen_hashes = {}  # hash -> first video with this hash
    unique_videos = []
    duplicate_count = 0
    download_errors = 0
    
    # Read input CSV
    print(f"📖 Reading: {input_csv}")
    print(f"🖼️  Analyzing thumbnails for visual duplicates...")
    
    try:
        with open(input_csv, 'r', encoding='utf-8') as f:
            # Read header comments
            header_comments = []
            line = f.readline()
            while line.startswith('#'):
                header_comments.append(line)
                line = f.readline()
            
            # The last line we read should be the CSV header
            # Go back one line
            f.seek(0)
            
            # Skip comments again
            for _ in header_comments:
                f.readline()
            
            # Now read CSV
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            
            total_rows = 0
            for row in reader:
                total_rows += 1
                thumbnail_url = row.get('thumbnail_url', '')
                
                if not thumbnail_url:
                    unique_videos.append(row)
                    continue
                
                # Download and hash the thumbnail
                print(f"  [{total_rows}] Checking thumbnail...", end='\r')
                image = download_thumbnail(thumbnail_url)
                
                if not image:
                    # Can't download - keep it to be safe
                    download_errors += 1
                    unique_videos.append(row)
                    continue
                
                image_hash = get_image_hash(image)
                
                if not image_hash:
                    # Can't hash - keep it to be safe
                    unique_videos.append(row)
                    continue
                
                # Check if we've seen a similar hash
                is_duplicate = False
                for seen_hash in seen_hashes.keys():
                    # Calculate Hamming distance (number of differing bits)
                    hash_diff = imagehash.hex_to_hash(image_hash) - imagehash.hex_to_hash(seen_hash)
                    
                    if hash_diff <= similarity_threshold:
                        # Duplicate found!
                        is_duplicate = True
                        duplicate_count += 1
                        print(f"  [{total_rows}] 🔍 Duplicate found (diff={hash_diff})    ")
                        break
                
                if not is_duplicate:
                    # First time seeing this image - keep it
                    seen_hashes[image_hash] = row
                    unique_videos.append(row)
        
        original_count = len(unique_videos) + duplicate_count
        
        print(f"\n💾 Writing: {output_csv}")
        
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            # Write header comments
            for comment in header_comments:
                # Update the count if it exists
                if '# Total Matches:' in comment or '# Non-Matches:' in comment:
                    # Replace the number with new count
                    parts = comment.split(':')
                    if len(parts) == 2:
                        f.write(f"{parts[0]}: {len(unique_videos)}\n")
                    else:
                        f.write(comment)
                else:
                    f.write(comment)
            
            # Add deduplication info
            f.write(f"# Duplicates Removed (Visual): {duplicate_count}\n")
            if download_errors > 0:
                f.write(f"# Download Errors: {download_errors}\n")
            
            # Write CSV data
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(unique_videos)
        
        return (original_count, len(unique_videos), duplicate_count, download_errors)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    """Main entry point"""
    print("🧹 CSV Duplicate Remover (Visual Similarity)")
    print("=" * 50)
    
    # Get input file
    if len(sys.argv) > 1:
        input_csv = sys.argv[1]
    else:
        input_csv = input("\n📄 Enter CSV file path: ").strip()
        # Handle drag-and-drop escaped spaces
        input_csv = input_csv.replace('\\', '')
    
    if not input_csv:
        print("❌ No file provided!")
        return
    
    # Check if file exists
    if not Path(input_csv).exists():
        print(f"❌ File not found: {input_csv}")
        return
    
    # Get output file (optional)
    output_csv = None
    if len(sys.argv) > 2:
        output_csv = sys.argv[2]
    else:
        custom_output = input("💾 Output file (press Enter for auto-name): ").strip()
        if custom_output:
            output_csv = custom_output.replace('\\', '')
    
    # Get similarity threshold
    similarity_threshold = 0  # Default: exact match only
    if len(sys.argv) > 3:
        try:
            similarity_threshold = int(sys.argv[3])
        except:
            similarity_threshold = 0
    else:
        threshold_input = input("🎯 Similarity threshold (0=exact, 5=very similar, press Enter=0): ").strip()
        if threshold_input:
            try:
                similarity_threshold = int(threshold_input)
            except:
                similarity_threshold = 0
    
    print(f"\n🔍 Detecting duplicates (threshold: {similarity_threshold})")
    print()
    
    # Process file
    result = remove_duplicates(input_csv, output_csv, similarity_threshold)
    
    if result:
        original_count, unique_count, duplicates_removed, download_errors = result
        
        print(f"\n✅ Done!")
        print(f"=" * 50)
        print(f"📊 Original videos: {original_count}")
        print(f"✅ Unique videos: {unique_count}")
        print(f"🗑️  Visual duplicates removed: {duplicates_removed}")
        
        if download_errors > 0:
            print(f"⚠️  Download errors: {download_errors} (kept in output)")
        
        if duplicates_removed > 0:
            percentage = (duplicates_removed / original_count) * 100
            print(f"📉 Reduction: {percentage:.1f}%")
        
        print(f"=" * 50)
        output_path = output_csv if output_csv else Path(input_csv).parent / f'{Path(input_csv).stem}_unique{Path(input_csv).suffix}'
        print(f"📄 Output saved to: {output_path}")

if __name__ == "__main__":
    main()

