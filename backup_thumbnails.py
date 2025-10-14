#!/usr/bin/env python3
"""
Backup Thumbnail URLs to Bunny.net
Uploads expiring Douyin thumbnails to Bunny.net for permanent storage
"""

import os
import csv
import sys
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
    region = os.getenv('BUNNY_REGION', 'de')  # Default to Germany
    
    if not all([api_key, storage_zone]):
        print("❌ Bunny.net credentials not found in .env file!")
        print("\nPlease add these lines to your .env file:")
        print("BUNNY_API_KEY=your_api_key")
        print("BUNNY_STORAGE_ZONE=your_storage_zone_name")
        print("BUNNY_REGION=de  # or ny, la, sg, etc.")
        print("\nGet your credentials from: https://panel.bunny.net/storage")
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

def upload_to_bunny(image_url, bunny_config, retries=3):
    """Upload image URL to Bunny.net and return permanent CDN URL"""
    
    # Generate unique filename from URL
    url_hash = hashlib.md5(image_url.encode()).hexdigest()
    filename = f"douyin_thumbnails/{url_hash}.jpg"
    
    for attempt in range(retries):
        try:
            # Download the image
            img_response = requests.get(image_url, timeout=30)
            if img_response.status_code != 200:
                print(f"  ❌ Failed to download image: HTTP {img_response.status_code}")
                return None
            
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
                # Return CDN URL
                cdn_url = f"{bunny_config['cdn_url']}/{filename}"
                return cdn_url
            else:
                if attempt < retries - 1:
                    print(f"  ⚠️ Upload failed (attempt {attempt + 1}/{retries}), retrying...")
                    continue
                else:
                    print(f"  ❌ Upload failed after {retries} attempts: HTTP {upload_response.status_code}")
                    return None
                    
        except Exception as e:
            if attempt < retries - 1:
                print(f"  ⚠️ Error (attempt {attempt + 1}/{retries}): {e}, retrying...")
                continue
            else:
                print(f"  ❌ Unexpected error after {retries} attempts: {e}")
                return None
    return None

def read_csv_with_comments(csv_path):
    """Read CSV file preserving header comments (lines starting with #)"""
    comments = []
    rows = []
    delimiter = ','  # Default delimiter
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        # Collect comment lines
        lines = f.readlines()
        
    # Separate comments from CSV data
    csv_start = 0
    for i, line in enumerate(lines):
        if line.strip().startswith('#'):
            comments.append(line.rstrip('\n'))
            csv_start = i + 1
        else:
            break
    
    # Read CSV data (skip comment lines)
    csv_lines = lines[csv_start:]
    if csv_lines:
        # Auto-detect delimiter from first non-comment line
        sample = csv_lines[0] if csv_lines else ""
        sniffer = csv.Sniffer()
        try:
            delimiter = sniffer.sniff(sample).delimiter
        except:
            delimiter = ','  # Default to comma if detection fails
        
        reader = csv.DictReader(csv_lines, delimiter=delimiter)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)
    else:
        fieldnames = []
    
    return comments, fieldnames, rows, delimiter

def write_csv_with_comments(csv_path, comments, fieldnames, rows, delimiter=','):
    """Write CSV file with header comments preserved"""
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        # Write comments
        for comment in comments:
            f.write(comment + '\n')
        
        # Write CSV data
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
        writer.writeheader()
        writer.writerows(rows)

def backup_thumbnails(csv_path, bunny_config):
    """Main function to backup thumbnails from CSV"""
    
    print(f"📂 Processing CSV: {csv_path}")
    
    # Read CSV with comments
    try:
        comments, fieldnames, rows, delimiter = read_csv_with_comments(csv_path)
        delimiter_name = 'comma' if delimiter == ',' else 'semicolon' if delimiter == ';' else f"'{delimiter}'"
        print(f"✅ Loaded {len(rows)} rows from CSV (delimiter: {delimiter_name})")
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return False
    
    # Check if thumbnail_url column exists
    if 'thumbnail_url' not in fieldnames:
        print("❌ CSV must contain 'thumbnail_url' column!")
        return False
    
    # Add backup column if not exists
    backup_column = 'backup_thumbnail_url'
    if backup_column not in fieldnames:
        fieldnames = list(fieldnames) + [backup_column]
        print(f"➕ Adding '{backup_column}' column")
    
    # Process thumbnails with parallel uploads
    successful = 0
    failed = 0
    lock = threading.Lock()
    
    print(f"\n🔄 Uploading thumbnails to Cloudinary (parallel processing)...")
    print("=" * 50)
    
    def process_thumbnail(index, row):
        """Process a single thumbnail upload"""
        thumbnail_url = row.get('thumbnail_url', '')
        
        # Skip if already backed up
        if row.get(backup_column):
            with lock:
                print(f"  [{index + 1}/{len(rows)}] ⏭️  Already backed up, skipping")
            return 'skipped', row
        
        if not thumbnail_url:
            with lock:
                print(f"  [{index + 1}/{len(rows)}] ⚠️  No thumbnail URL, skipping")
            row[backup_column] = 'No URL'
            return 'failed', row
        
        with lock:
            print(f"  [{index + 1}/{len(rows)}] Uploading thumbnail...")
        
        backup_url = upload_to_bunny(thumbnail_url, bunny_config)
        
        if backup_url:
            row[backup_column] = backup_url
            with lock:
                print(f"  [{index + 1}/{len(rows)}] ✅ Success")
            return 'success', row
        else:
            row[backup_column] = 'Failed'
            with lock:
                print(f"  [{index + 1}/{len(rows)}] ❌ Failed")
            return 'failed', row
    
    # Use ThreadPoolExecutor for parallel uploads (30 concurrent, well under Bunny.net's 50 limit)
    max_workers = 30
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all upload tasks
        futures = {executor.submit(process_thumbnail, i, row): i for i, row in enumerate(rows)}
        
        # Process results as they complete
        for future in as_completed(futures):
            try:
                status, updated_row = future.result()
                if status == 'success' or status == 'skipped':
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"  ❌ Thread error: {e}")
                failed += 1
    
    # Check if too many failures overall (not consecutive since we're parallel)
    failure_rate = failed / len(rows) if len(rows) > 0 else 0
    if failure_rate > 0.5 and failed > 10:
        print(f"\n⚠️  WARNING: High failure rate detected ({failed}/{len(rows)} failed)!")
        print("Possible causes:")
        print("  - Cloudinary API quota exceeded")
        print("  - Network connection issues")
        print("  - Invalid Cloudinary credentials")
        return False
    
    # Create output filename
    csv_name = Path(csv_path).stem
    csv_dir = Path(csv_path).parent
    output_path = csv_dir / f"Backed_{csv_name}.csv"
    
    # Write updated CSV
    try:
        write_csv_with_comments(output_path, comments, fieldnames, rows, delimiter)
        print(f"\n✅ Backup complete!")
        print(f"📄 Saved to: {output_path}")
    except Exception as e:
        print(f"\n❌ Error writing output CSV: {e}")
        return False
    
    # Delete original file after successful backup
    try:
        os.remove(csv_path)
        print(f"🗑️  Deleted original file: {Path(csv_path).name}")
    except Exception as e:
        print(f"⚠️  Warning: Could not delete original file: {e}")
        # Don't fail the whole operation if delete fails
    
    # Print summary
    print(f"\n📊 SUMMARY")
    print("=" * 50)
    print(f"✅ Successful uploads: {successful}")
    print(f"❌ Failed uploads: {failed}")
    print(f"📁 Total rows: {len(rows)}")
    print("=" * 50)
    
    return True

def main():
    """Main entry point"""
    print("🔄 Douyin Thumbnail Backup Tool (Bunny.net)")
    print("=" * 50)
    
    # Load environment variables
    load_env()
    
    # Setup Bunny.net
    bunny_config = setup_bunny()
    if not bunny_config:
        sys.exit(1)
    
    # Get CSV file paths from user
    csv_input = input("\n📂 Drag and drop CSV file(s) or folder here (or enter path): ").strip()
    
    if not csv_input:
        print("❌ No file path provided!")
        sys.exit(1)
    
    # Parse multiple file paths
    csv_paths = []
    
    # Check if input has escaped spaces (single file/folder drag-and-drop)
    if '\\ ' in csv_input:
        # Single file/folder with escaped spaces - just remove the backslashes
        csv_path = csv_input.replace('\\', '').strip('"').strip("'")
        
        # Check if it's a directory
        if os.path.isdir(csv_path):
            print(f"📁 Detected folder: {csv_path}")
            print(f"🔍 Finding all CSV files in folder...")
            # Get all CSV files in the folder, excluding files that start with "Backed_"
            all_csv_files = sorted(Path(csv_path).glob('*.csv'))
            csv_files = [f for f in all_csv_files if not f.name.startswith('Backed_')]
            csv_paths = [str(f) for f in csv_files]
            
            skipped_count = len(all_csv_files) - len(csv_files)
            if skipped_count > 0:
                print(f"⏭️  Skipped {skipped_count} already backed-up file(s)")
            
            if not csv_paths:
                print(f"❌ No CSV files to backup found in folder!")
                sys.exit(1)
            print(f"✅ Found {len(csv_paths)} CSV file(s) to backup")
        else:
            csv_paths = [csv_path]
    else:
        # Multiple files or single file without spaces
        # First check if it's a simple folder path
        clean_input = csv_input.strip('"').strip("'")
        if os.path.isdir(clean_input):
            print(f"📁 Detected folder: {clean_input}")
            print(f"🔍 Finding all CSV files in folder...")
            # Get all CSV files in the folder, excluding files that start with "Backed_"
            all_csv_files = sorted(Path(clean_input).glob('*.csv'))
            csv_files = [f for f in all_csv_files if not f.name.startswith('Backed_')]
            csv_paths = [str(f) for f in csv_files]
            
            skipped_count = len(all_csv_files) - len(csv_files)
            if skipped_count > 0:
                print(f"⏭️  Skipped {skipped_count} already backed-up file(s)")
            
            if not csv_paths:
                print(f"❌ No CSV files to backup found in folder!")
                sys.exit(1)
            print(f"✅ Found {len(csv_paths)} CSV file(s) to backup")
        else:
            # Split by spaces but respect quotes
            current_path = ""
            in_quotes = False
            
            for char in csv_input:
                if char in ('"', "'"):
                    in_quotes = not in_quotes
                elif char == ' ' and not in_quotes:
                    if current_path:
                        csv_paths.append(current_path.strip())
                        current_path = ""
                else:
                    current_path += char
            
            if current_path:
                csv_paths.append(current_path.strip())
            
            # Remove any remaining quotes
            csv_paths = [p.strip('"').strip("'") for p in csv_paths]
    
    # Validate all paths exist
    invalid_paths = [p for p in csv_paths if not os.path.exists(p)]
    if invalid_paths:
        print(f"❌ File(s) not found:")
        for p in invalid_paths:
            print(f"   - {p}")
        sys.exit(1)
    
    print(f"\n📁 Processing {len(csv_paths)} file(s)...\n")
    
    # Process each CSV
    total_success = 0
    total_failed = 0
    
    for i, csv_path in enumerate(csv_paths, 1):
        print(f"\n{'='*50}")
        print(f"📄 File {i}/{len(csv_paths)}: {Path(csv_path).name}")
        print(f"{'='*50}")
        
        success = backup_thumbnails(csv_path, bunny_config)
        
        if success:
            total_success += 1
        else:
            total_failed += 1
    
    # Final summary
    print(f"\n{'='*50}")
    print(f"🎉 ALL FILES PROCESSED!")
    print(f"{'='*50}")
    print(f"✅ Successful: {total_success} file(s)")
    print(f"❌ Failed: {total_failed} file(s)")
    print(f"📁 Total: {len(csv_paths)} file(s)")
    print(f"{'='*50}")
    
    if total_failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()

