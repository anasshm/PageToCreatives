#!/usr/bin/env python3
"""
Consolidate watch price CSVs into a master file.
Filters for products with final_score > 90% and selects the cheapest 3 per reference watch.
"""

import csv
import os
import glob
import re


def extract_price_value(price_str):
    """Extract numeric value from price string like '¥52.00'"""
    if not price_str:
        return float('inf')
    # Remove ¥ symbol and convert to float
    match = re.search(r'[\d.]+', price_str)
    if match:
        return float(match.group())
    return float('inf')


def process_watch_csvs(input_folder, output_file):
    """
    Process all watch price CSV files and create master consolidated file.
    
    Args:
        input_folder: Path to folder containing Watched_prices_detailed*.csv files
        output_file: Path to output master CSV file
    """
    # Get all CSV files matching the pattern
    csv_pattern = os.path.join(input_folder, 'Watched_prices_detailed*.csv')
    csv_files = sorted(glob.glob(csv_pattern))
    
    print(f"Found {len(csv_files)} CSV files to process")
    
    # Store results for each reference image
    master_data = []
    
    # Process each CSV file (one per reference watch)
    for csv_file in csv_files:
        filename = os.path.basename(csv_file)
        print(f"\nProcessing {filename}...")
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            if not rows:
                print(f"  No data found in {filename}")
                continue
            
            # Get reference image URL (should be same for all rows in this file)
            ref_img_url = rows[0].get('reference_image_url', '')
            
            # Filter for final_score > 90%
            filtered_rows = []
            for row in rows:
                try:
                    final_score = float(row.get('final_score', 0))
                    if final_score > 90.0:
                        filtered_rows.append(row)
                except ValueError:
                    continue
            
            print(f"  Found {len(filtered_rows)} products with score > 90%")
            
            if not filtered_rows:
                print(f"  No products met the > 90% threshold")
                continue
            
            # Sort by price (cheapest first)
            filtered_rows.sort(key=lambda x: extract_price_value(x.get('price', '')))
            
            # Take top 3 cheapest
            top_3 = filtered_rows[:3]
            
            # Build master row
            master_row = {'ref_img_url': ref_img_url}
            
            # Add data for each of the top 3 (or fewer)
            for i in range(3):
                num = i + 1
                if i < len(top_3):
                    master_row[f'price{num}'] = top_3[i].get('price', '')
                    master_row[f'final_score{num}'] = top_3[i].get('final_score', '')
                    master_row[f'img_url{num}'] = top_3[i].get('1688_product_image_url', '')
                    master_row[f'aliprice_link{num}'] = top_3[i].get('1688_url', '')
                else:
                    # Fill with empty strings if fewer than 3 products
                    master_row[f'price{num}'] = ''
                    master_row[f'final_score{num}'] = ''
                    master_row[f'img_url{num}'] = ''
                    master_row[f'aliprice_link{num}'] = ''
            
            master_data.append(master_row)
            print(f"  Added to master with {len(top_3)} product(s)")
            
        except Exception as e:
            print(f"  Error processing {filename}: {e}")
            continue
    
    # Write master CSV
    if not master_data:
        print("\nNo data to write to master file!")
        return
    
    fieldnames = [
        'ref_img_url',
        'price1', 'price2', 'price3',
        'final_score1', 'final_score2', 'final_score3',
        'img_url1', 'img_url2', 'img_url3',
        'aliprice_link1', 'aliprice_link2', 'aliprice_link3'
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(master_data)
    
    print(f"\n✓ Master CSV created: {output_file}")
    print(f"✓ Total reference watches: {len(master_data)}")


def main():
    # Set up paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_folder = os.path.join(base_dir, 'Watches Detailed prices')
    output_file = os.path.join(input_folder, 'master_watch_prices.csv')
    
    print("=" * 60)
    print("Watch Prices Consolidator")
    print("=" * 60)
    print(f"Input folder: {input_folder}")
    print(f"Output file: {output_file}")
    
    # Verify input folder exists
    if not os.path.exists(input_folder):
        print(f"\nError: Input folder not found: {input_folder}")
        return
    
    # Process the files
    process_watch_csvs(input_folder, output_file)
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()

