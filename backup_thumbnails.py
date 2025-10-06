#!/usr/bin/env python3
"""
Backup Thumbnail URLs to Cloudinary
Uploads expiring Douyin thumbnails to Cloudinary for permanent storage
"""

import os
import csv
import sys
from pathlib import Path
import cloudinary
import cloudinary.uploader
from cloudinary.exceptions import Error as CloudinaryError

def load_env():
    """Load environment variables from .env file"""
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

def setup_cloudinary():
    """Setup Cloudinary configuration from environment variables"""
    cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
    api_key = os.getenv('CLOUDINARY_API_KEY')
    api_secret = os.getenv('CLOUDINARY_API_SECRET')
    
    if not all([cloud_name, api_key, api_secret]):
        print("❌ Cloudinary credentials not found in .env file!")
        print("\nPlease add these lines to your .env file:")
        print("CLOUDINARY_CLOUD_NAME=your_cloud_name")
        print("CLOUDINARY_API_KEY=your_api_key")
        print("CLOUDINARY_API_SECRET=your_api_secret")
        print("\nGet your credentials from: https://cloudinary.com/console")
        return False
    
    try:
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True
        )
        print("✅ Cloudinary configured successfully")
        return True
    except Exception as e:
        print(f"❌ Error configuring Cloudinary: {e}")
        return False

def upload_to_cloudinary(image_url, retries=3):
    """Upload image URL to Cloudinary and return permanent URL"""
    for attempt in range(retries):
        try:
            response = cloudinary.uploader.upload(
                image_url,
                folder='douyin_thumbnails',  # Organize in a folder
                resource_type='image'
            )
            return response['secure_url']
        except CloudinaryError as e:
            if attempt < retries - 1:
                print(f"  ⚠️ Upload failed (attempt {attempt + 1}/{retries}), retrying...")
                continue
            else:
                print(f"  ❌ Upload failed after {retries} attempts: {e}")
                return None
        except Exception as e:
            print(f"  ❌ Unexpected error: {e}")
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

def backup_thumbnails(csv_path):
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
    
    # Process thumbnails
    successful = 0
    failed = 0
    consecutive_failures = 0
    max_consecutive_failures = 10
    
    print(f"\n🔄 Uploading thumbnails to Cloudinary...")
    print("=" * 50)
    
    for i, row in enumerate(rows, 1):
        thumbnail_url = row.get('thumbnail_url', '')
        
        # Skip if already backed up
        if row.get(backup_column):
            print(f"  [{i}/{len(rows)}] ⏭️  Already backed up, skipping")
            successful += 1
            consecutive_failures = 0
            continue
        
        if not thumbnail_url:
            print(f"  [{i}/{len(rows)}] ⚠️  No thumbnail URL, skipping")
            failed += 1
            consecutive_failures += 1
            row[backup_column] = 'No URL'
            continue
        
        print(f"  [{i}/{len(rows)}] Uploading thumbnail...")
        backup_url = upload_to_cloudinary(thumbnail_url)
        
        if backup_url:
            row[backup_column] = backup_url
            successful += 1
            consecutive_failures = 0
            print(f"  [{i}/{len(rows)}] ✅ Success")
        else:
            row[backup_column] = 'Failed'
            failed += 1
            consecutive_failures += 1
            print(f"  [{i}/{len(rows)}] ❌ Failed")
        
        # Check for too many consecutive failures
        if consecutive_failures >= max_consecutive_failures:
            print(f"\n⚠️  WARNING: {max_consecutive_failures} consecutive failures detected!")
            print("Stopping script to prevent further issues.")
            print("\nPossible causes:")
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
    print("🔄 Douyin Thumbnail Backup Tool")
    print("=" * 50)
    
    # Load environment variables
    load_env()
    
    # Setup Cloudinary
    if not setup_cloudinary():
        sys.exit(1)
    
    # Get CSV file paths from user
    csv_input = input("\n📂 Drag and drop CSV file(s) here (or enter path): ").strip()
    
    if not csv_input:
        print("❌ No file path provided!")
        sys.exit(1)
    
    # Parse multiple file paths
    csv_paths = []
    
    # Check if input has escaped spaces (single file drag-and-drop)
    if '\\ ' in csv_input:
        # Single file with escaped spaces - just remove the backslashes
        csv_path = csv_input.replace('\\', '').strip('"').strip("'")
        csv_paths = [csv_path]
    else:
        # Multiple files or single file without spaces
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
        
        success = backup_thumbnails(csv_path)
        
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

