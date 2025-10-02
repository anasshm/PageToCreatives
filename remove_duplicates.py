#!/usr/bin/env python3
"""
Remove Duplicate Videos from CSV
Removes duplicate videos based on thumbnail URL
Keeps the first occurrence of each unique thumbnail
"""

import csv
import sys
from pathlib import Path

def remove_duplicates(input_csv, output_csv=None):
    """Remove duplicate videos from CSV based on thumbnail URL
    
    Args:
        input_csv: Path to input CSV file
        output_csv: Path to output CSV file (optional, defaults to input_unique.csv)
    
    Returns:
        tuple: (original_count, unique_count, duplicates_removed)
    """
    
    # Generate output filename if not provided
    if not output_csv:
        input_path = Path(input_csv)
        output_csv = input_path.parent / f"{input_path.stem}_unique{input_path.suffix}"
    
    seen_thumbnails = set()
    unique_videos = []
    duplicate_count = 0
    
    # Read input CSV
    print(f"📖 Reading: {input_csv}")
    
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
            
            for row in reader:
                thumbnail_url = row.get('thumbnail_url', '')
                
                if thumbnail_url not in seen_thumbnails:
                    # First time seeing this thumbnail - keep it
                    seen_thumbnails.add(thumbnail_url)
                    unique_videos.append(row)
                else:
                    # Duplicate thumbnail - skip it
                    duplicate_count += 1
        
        original_count = len(unique_videos) + duplicate_count
        
        # Write output CSV
        print(f"💾 Writing: {output_csv}")
        
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
            f.write(f"# Duplicates Removed: {duplicate_count}\n")
            
            # Write CSV data
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(unique_videos)
        
        return (original_count, len(unique_videos), duplicate_count)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    """Main entry point"""
    print("🧹 CSV Duplicate Remover")
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
    
    print()
    
    # Process file
    result = remove_duplicates(input_csv, output_csv)
    
    if result:
        original_count, unique_count, duplicates_removed = result
        
        print(f"\n✅ Done!")
        print(f"=" * 50)
        print(f"📊 Original videos: {original_count}")
        print(f"✅ Unique videos: {unique_count}")
        print(f"🗑️  Duplicates removed: {duplicates_removed}")
        
        if duplicates_removed > 0:
            percentage = (duplicates_removed / original_count) * 100
            print(f"📉 Reduction: {percentage:.1f}%")
        
        print(f"=" * 50)
        print(f"📄 Output saved to: {output_csv if output_csv else Path(input_csv).parent / f'{Path(input_csv).stem}_unique{Path(input_csv).suffix}'}")

if __name__ == "__main__":
    main()

