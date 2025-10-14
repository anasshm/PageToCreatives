#!/usr/bin/env python3
"""
Generate Watch Comparison Gallery
Creates an interactive HTML gallery from master_watch_prices.csv
Shows reference watch alongside top 3 matching products with filtering
"""

import csv
import os
import json
import re


def extract_price_value(price_str):
    """Extract numeric value from price string like '¥52.00'"""
    if not price_str:
        return 0
    match = re.search(r'[\d.]+', price_str)
    if match:
        return float(match.group())
    return 0


def read_master_csv(csv_file):
    """Read the master watch prices CSV file"""
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found!")
        return []
    
    watches = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Extract numeric price for filtering/sorting
            price1_num = extract_price_value(row.get('price1', ''))
            
            # Extract numeric score for filtering/sorting
            score1_str = row.get('final_score1', '0')
            try:
                score1_num = float(score1_str) if score1_str else 0
            except ValueError:
                score1_num = 0
            
            watch = {
                'ref_img_url': row.get('ref_img_url', ''),
                'price1': row.get('price1', ''),
                'price2': row.get('price2', ''),
                'price3': row.get('price3', ''),
                'price1_num': price1_num,
                'final_score1': row.get('final_score1', ''),
                'final_score2': row.get('final_score2', ''),
                'final_score3': row.get('final_score3', ''),
                'score1_num': score1_num,
                'img_url1': row.get('img_url1', ''),
                'img_url2': row.get('img_url2', ''),
                'img_url3': row.get('img_url3', ''),
                'aliprice_link1': row.get('aliprice_link1', ''),
                'aliprice_link2': row.get('aliprice_link2', ''),
                'aliprice_link3': row.get('aliprice_link3', '')
            }
            watches.append(watch)
    
    return watches


def generate_html_gallery(watches, output_file):
    """Generate interactive HTML gallery with filtering"""
    
    # Convert watches data to JSON for embedding in HTML
    watches_json = json.dumps(watches, ensure_ascii=False)
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Watch Comparison Gallery</title>
    <style>
        * {{
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: #0a0a0a;
            color: #ffffff;
            margin: 0;
            padding: 20px;
        }}
        
        h1 {{
            text-align: center;
            color: #fe2c55;
            margin-bottom: 10px;
            font-size: 2.5em;
        }}
        
        .subtitle {{
            text-align: center;
            color: #8a8b91;
            margin-bottom: 30px;
            font-size: 1.1em;
        }}
        
        .filter-section {{
            max-width: 1600px;
            margin: 0 auto 20px;
            padding: 25px;
            background-color: #161823;
            border-radius: 12px;
        }}
        
        .filter-row {{
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
            margin-bottom: 15px;
        }}
        
        .filter-group {{
            display: flex;
            gap: 8px;
            align-items: center;
            background-color: #0a0a0a;
            padding: 8px 12px;
            border-radius: 6px;
        }}
        
        .filter-group label {{
            color: #8a8b91;
            font-size: 0.85em;
            font-weight: 600;
            min-width: 80px;
        }}
        
        .filter-group input {{
            padding: 6px 10px;
            background-color: #161823;
            border: 1px solid #333;
            border-radius: 4px;
            color: #ffffff;
            width: 90px;
            font-size: 0.85em;
        }}
        
        .filter-group select {{
            padding: 6px 10px;
            background-color: #161823;
            border: 1px solid #333;
            border-radius: 4px;
            color: #ffffff;
            font-size: 0.85em;
            min-width: 180px;
        }}
        
        .filter-group input:focus,
        .filter-group select:focus {{
            outline: none;
            border-color: #fe2c55;
        }}
        
        .filter-buttons {{
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }}
        
        .filter-buttons button {{
            padding: 10px 20px;
            background-color: #333;
            border: none;
            border-radius: 6px;
            color: white;
            font-weight: 600;
            cursor: pointer;
            font-size: 0.9em;
        }}
        
        .filter-buttons button:hover {{
            background-color: #444;
        }}
        
        .filter-buttons button.primary {{
            background-color: #fe2c55;
        }}
        
        .filter-buttons button.primary:hover {{
            background-color: #d91d45;
        }}
        
        .export-section {{
            max-width: 1600px;
            margin: 20px auto;
            padding: 20px;
            background-color: #161823;
            border-radius: 12px;
            text-align: center;
        }}
        
        .export-section button {{
            padding: 12px 30px;
            background-color: #4ade80;
            border: none;
            border-radius: 8px;
            color: #0a0a0a;
            font-weight: 700;
            cursor: pointer;
            font-size: 1em;
        }}
        
        .export-section button:hover {{
            background-color: #22c55e;
        }}
        
        .export-section button:disabled {{
            background-color: #333;
            color: #666;
            cursor: not-allowed;
        }}
        
        .selection-info {{
            color: #8a8b91;
            margin-top: 10px;
            font-size: 0.9em;
        }}
        
        .selection-info.active {{
            color: #4ade80;
            font-weight: 600;
        }}
        
        .stats {{
            text-align: center;
            color: #8a8b91;
            margin-bottom: 20px;
            font-size: 1.1em;
        }}
        
        .gallery {{
            max-width: 1600px;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}
        
        .watch-row {{
            display: grid;
            grid-template-columns: 50px 1fr 1fr 1fr 1fr;
            gap: 15px;
            background-color: #161823;
            padding: 15px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            transition: background-color 0.2s ease;
        }}
        
        .watch-row.active {{
            background-color: #1f2430;
            border: 2px solid #4ade80;
        }}
        
        .row-checkbox {{
            display: flex;
            align-items: center;
            justify-content: center;
            padding-top: 40px;
        }}
        
        .row-checkbox input[type="checkbox"] {{
            width: 24px;
            height: 24px;
            cursor: pointer;
            accent-color: #4ade80;
        }}
        
        .watch-item {{
            position: relative;
            border-radius: 8px;
            overflow: hidden;
            background-color: #0a0a0a;
        }}
        
        .watch-item.reference {{
            border: 2px solid #fe2c55;
        }}
        
        .watch-item img {{
            width: 100%;
            height: auto;
            display: block;
            aspect-ratio: 1;
            object-fit: cover;
        }}
        
        .watch-item a {{
            display: block;
            text-decoration: none;
        }}
        
        .watch-item:hover {{
            transform: scale(1.02);
            transition: transform 0.2s ease;
        }}
        
        .watch-item.product {{
            position: relative;
        }}
        
        .watch-item.product.selected {{
            border: 3px solid #4ade80;
            box-shadow: 0 0 15px rgba(74, 222, 128, 0.5);
        }}
        
        .product-checkbox {{
            position: absolute;
            top: 8px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 20;
            background-color: rgba(0, 0, 0, 0.8);
            padding: 8px;
            border-radius: 6px;
            cursor: pointer;
        }}
        
        .product-checkbox input[type="checkbox"] {{
            width: 20px;
            height: 20px;
            cursor: pointer;
            accent-color: #4ade80;
        }}
        
        .watch-info {{
            padding: 10px;
            background-color: #0a0a0a;
        }}
        
        .watch-label {{
            color: #fe2c55;
            font-size: 0.75em;
            font-weight: 600;
            text-transform: uppercase;
            margin-bottom: 4px;
        }}
        
        .watch-price {{
            color: #ffffff;
            font-size: 1.1em;
            font-weight: 600;
            margin-bottom: 2px;
        }}
        
        .watch-score {{
            color: #8a8b91;
            font-size: 0.85em;
        }}
        
        .watch-score.high {{
            color: #4ade80;
        }}
        
        .watch-item.empty {{
            opacity: 0.3;
            pointer-events: none;
        }}
        
        .watch-item.empty .watch-info {{
            text-align: center;
            padding: 20px 10px;
        }}
        
        .watch-item.empty .watch-label {{
            color: #8a8b91;
        }}
        
        .no-results {{
            text-align: center;
            color: #8a8b91;
            font-size: 1.2em;
            margin-top: 50px;
            padding: 40px;
        }}
        
        @media (max-width: 1400px) {{
            .watch-row {{
                grid-template-columns: 50px 1fr 1fr;
                gap: 10px;
            }}
        }}
        
        @media (max-width: 900px) {{
            .watch-row {{
                grid-template-columns: 50px 1fr;
                gap: 10px;
            }}
            
            h1 {{
                font-size: 1.8em;
            }}
        }}
    </style>
</head>
<body>
    <h1>⌚ Watch Comparison Gallery</h1>
    <div class="subtitle">Visual comparison of reference watches with matched products</div>
    
    <div class="filter-section">
        <div class="filter-row">
            <div class="filter-group">
                <label>Price Range:</label>
                <input type="number" id="minPrice" placeholder="Min ¥" step="0.01">
                <span style="color: #8a8b91;">—</span>
                <input type="number" id="maxPrice" placeholder="Max ¥" step="0.01">
            </div>
            
            <div class="filter-group">
                <label>Score Range:</label>
                <input type="number" id="minScore" placeholder="Min %" step="0.1" min="0" max="100">
                <span style="color: #8a8b91;">—</span>
                <input type="number" id="maxScore" placeholder="Max %" step="0.1" min="0" max="100">
            </div>
            
            <div class="filter-group">
                <label>Sort By:</label>
                <select id="sortBy">
                    <option value="price-asc">Price (Low to High)</option>
                    <option value="price-desc">Price (High to Low)</option>
                    <option value="score-desc">Score (High to Low)</option>
                    <option value="score-asc">Score (Low to High)</option>
                </select>
            </div>
        </div>
        
        <div class="filter-buttons">
            <button class="primary" onclick="applyFilters()">Apply Filters</button>
            <button onclick="resetFilters()">Reset</button>
        </div>
    </div>
    
    <div class="export-section">
        <button id="exportBtn" onclick="exportSelections()" disabled>📥 Export Selected Matches</button>
        <div class="selection-info" id="selectionInfo">Check a row's checkbox and click a product to select your preferred match</div>
    </div>
    
    <div class="stats" id="stats">Loading...</div>
    
    <div class="gallery" id="gallery"></div>
    
    <script>
        // Embedded watch data
        const allWatches = {watches_json};
        let filteredWatches = [...allWatches];
        
        // Track which rows are active (checkbox checked)
        let activeRows = new Set();
        
        // Track selections: {{ rowIndex: productNum (1, 2, or 3) }}
        let selections = {{}};
        
        function toggleRowActive(rowIndex) {{
            const checkbox = document.getElementById('checkbox-' + rowIndex);
            const isActive = checkbox.checked;
            
            if (isActive) {{
                activeRows.add(rowIndex);
            }} else {{
                activeRows.delete(rowIndex);
                // Clear selection for this row
                delete selections[rowIndex];
            }}
            
            updateSelectionInfo();
            renderGallery();
        }}
        
        function selectProduct(rowIndex, productNum) {{
            // Only allow selection if row is active
            if (!activeRows.has(rowIndex)) {{
                return;
            }}
            
            const checkbox = document.getElementById('product-' + rowIndex + '-' + productNum);
            const isChecked = checkbox.checked;
            
            if (isChecked) {{
                // Uncheck other products in this row
                for (let i = 1; i <= 3; i++) {{
                    if (i !== productNum) {{
                        const otherCheckbox = document.getElementById('product-' + rowIndex + '-' + i);
                        if (otherCheckbox) {{
                            otherCheckbox.checked = false;
                        }}
                    }}
                }}
                selections[rowIndex] = productNum;
            }} else {{
                delete selections[rowIndex];
            }}
            
            updateSelectionInfo();
            renderGallery();
        }}
        
        function updateSelectionInfo() {{
            const info = document.getElementById('selectionInfo');
            const btn = document.getElementById('exportBtn');
            const count = Object.keys(selections).length;
            
            if (count > 0) {{
                info.textContent = count + ' watch(es) selected for export';
                info.classList.add('active');
                btn.disabled = false;
            }} else {{
                info.textContent = 'Check a row\\'s checkbox and click a product to select your preferred match';
                info.classList.remove('active');
                btn.disabled = true;
            }}
        }}
        
        function exportSelections() {{
            if (Object.keys(selections).length === 0) {{
                alert('Please select at least one product match first!');
                return;
            }}
            
            // Build CSV content
            let csvContent = 'ref_img_url,selected_aliprice_link\\n';
            
            Object.keys(selections).forEach(rowIndex => {{
                const watch = filteredWatches[rowIndex];
                const productNum = selections[rowIndex];
                const linkKey = 'aliprice_link' + productNum;
                const selectedLink = watch[linkKey];
                
                if (selectedLink) {{
                    csvContent += '"' + watch.ref_img_url + '","' + selectedLink + '"\\n';
                }}
            }});
            
            // Create and download file
            const blob = new Blob([csvContent], {{ type: 'text/csv;charset=utf-8;' }});
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);
            
            link.setAttribute('href', url);
            link.setAttribute('download', 'selected_watch_matches.csv');
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            alert('✅ Exported ' + Object.keys(selections).length + ' selected matches!');
        }}
        
        function renderGallery() {{
            const gallery = document.getElementById('gallery');
            const stats = document.getElementById('stats');
            
            if (filteredWatches.length === 0) {{
                gallery.innerHTML = '<div class="no-results">No watches match your filters</div>';
                stats.textContent = 'Showing 0 of ' + allWatches.length + ' watches';
                return;
            }}
            
            stats.textContent = 'Showing ' + filteredWatches.length + ' of ' + allWatches.length + ' watches';
            
            let html = '';
            
            filteredWatches.forEach((watch, index) => {{
                const isActive = activeRows.has(index);
                const selectedProduct = selections[index];
                const rowClass = isActive ? 'active' : '';
                
                html += '<div class="watch-row ' + rowClass + '">';
                
                // Checkbox
                html += '<div class="row-checkbox">';
                html += '<input type="checkbox" id="checkbox-' + index + '" ';
                html += 'onchange="toggleRowActive(' + index + ')" ';
                if (isActive) html += 'checked';
                html += '>';
                html += '</div>';
                
                // Reference image
                html += '<div class="watch-item reference">';
                html += '<img src="' + watch.ref_img_url + '" alt="Reference Watch" loading="lazy">';
                html += '<div class="watch-info">';
                html += '<div class="watch-label">Reference</div>';
                html += '</div>';
                html += '</div>';
                
                // Product 1 (Cheapest)
                if (watch.img_url1 && watch.aliprice_link1) {{
                    const isSelected1 = selectedProduct === 1;
                    const productClass = 'watch-item product' + (isSelected1 ? ' selected' : '');
                    html += '<div class="' + productClass + '">';
                    html += '<div class="product-checkbox">';
                    html += '<input type="checkbox" id="product-' + index + '-1" ';
                    html += 'onchange="selectProduct(' + index + ', 1)" ';
                    if (isSelected1) html += 'checked';
                    if (!isActive) html += ' disabled';
                    html += '>';
                    html += '</div>';
                    html += '<a href="' + watch.aliprice_link1 + '" target="_blank" rel="noopener noreferrer">';
                    html += '<img src="' + watch.img_url1 + '" alt="Product 1" loading="lazy">';
                    html += '<div class="watch-info">';
                    html += '<div class="watch-label">Cheapest</div>';
                    html += '<div class="watch-price">' + (watch.price1 || 'N/A') + '</div>';
                    html += '<div class="watch-score ' + (watch.score1_num >= 95 ? 'high' : '') + '">Score: ' + (watch.final_score1 || 'N/A') + '%</div>';
                    html += '</div>';
                    html += '</a>';
                    html += '</div>';
                }} else {{
                    html += '<div class="watch-item empty">';
                    html += '<div class="watch-info">';
                    html += '<div class="watch-label">No Match</div>';
                    html += '</div>';
                    html += '</div>';
                }}
                
                // Product 2 (2nd Cheapest)
                if (watch.img_url2 && watch.aliprice_link2) {{
                    const isSelected2 = selectedProduct === 2;
                    const productClass = 'watch-item product' + (isSelected2 ? ' selected' : '');
                    html += '<div class="' + productClass + '">';
                    html += '<div class="product-checkbox">';
                    html += '<input type="checkbox" id="product-' + index + '-2" ';
                    html += 'onchange="selectProduct(' + index + ', 2)" ';
                    if (isSelected2) html += 'checked';
                    if (!isActive) html += ' disabled';
                    html += '>';
                    html += '</div>';
                    html += '<a href="' + watch.aliprice_link2 + '" target="_blank" rel="noopener noreferrer">';
                    html += '<img src="' + watch.img_url2 + '" alt="Product 2" loading="lazy">';
                    html += '<div class="watch-info">';
                    html += '<div class="watch-label">2nd Cheapest</div>';
                    html += '<div class="watch-price">' + (watch.price2 || 'N/A') + '</div>';
                    html += '<div class="watch-score ' + (parseFloat(watch.final_score2) >= 95 ? 'high' : '') + '">Score: ' + (watch.final_score2 || 'N/A') + '%</div>';
                    html += '</div>';
                    html += '</a>';
                    html += '</div>';
                }} else {{
                    html += '<div class="watch-item empty">';
                    html += '<div class="watch-info">';
                    html += '<div class="watch-label">No Match</div>';
                    html += '</div>';
                    html += '</div>';
                }}
                
                // Product 3 (3rd Cheapest)
                if (watch.img_url3 && watch.aliprice_link3) {{
                    const isSelected3 = selectedProduct === 3;
                    const productClass = 'watch-item product' + (isSelected3 ? ' selected' : '');
                    html += '<div class="' + productClass + '">';
                    html += '<div class="product-checkbox">';
                    html += '<input type="checkbox" id="product-' + index + '-3" ';
                    html += 'onchange="selectProduct(' + index + ', 3)" ';
                    if (isSelected3) html += 'checked';
                    if (!isActive) html += ' disabled';
                    html += '>';
                    html += '</div>';
                    html += '<a href="' + watch.aliprice_link3 + '" target="_blank" rel="noopener noreferrer">';
                    html += '<img src="' + watch.img_url3 + '" alt="Product 3" loading="lazy">';
                    html += '<div class="watch-info">';
                    html += '<div class="watch-label">3rd Cheapest</div>';
                    html += '<div class="watch-price">' + (watch.price3 || 'N/A') + '</div>';
                    html += '<div class="watch-score ' + (parseFloat(watch.final_score3) >= 95 ? 'high' : '') + '">Score: ' + (watch.final_score3 || 'N/A') + '%</div>';
                    html += '</div>';
                    html += '</a>';
                    html += '</div>';
                }} else {{
                    html += '<div class="watch-item empty">';
                    html += '<div class="watch-info">';
                    html += '<div class="watch-label">No Match</div>';
                    html += '</div>';
                    html += '</div>';
                }}
                
                html += '</div>';
            }});
            
            gallery.innerHTML = html;
        }}
        
        function applyFilters() {{
            const minPrice = parseFloat(document.getElementById('minPrice').value) || 0;
            const maxPrice = parseFloat(document.getElementById('maxPrice').value) || Infinity;
            const minScore = parseFloat(document.getElementById('minScore').value) || 0;
            const maxScore = parseFloat(document.getElementById('maxScore').value) || 100;
            const sortBy = document.getElementById('sortBy').value;
            
            // Filter
            filteredWatches = allWatches.filter(watch => {{
                const price = watch.price1_num;
                const score = watch.score1_num;
                
                return price >= minPrice && price <= maxPrice && 
                       score >= minScore && score <= maxScore;
            }});
            
            // Sort
            if (sortBy === 'price-asc') {{
                filteredWatches.sort((a, b) => a.price1_num - b.price1_num);
            }} else if (sortBy === 'price-desc') {{
                filteredWatches.sort((a, b) => b.price1_num - a.price1_num);
            }} else if (sortBy === 'score-desc') {{
                filteredWatches.sort((a, b) => b.score1_num - a.score1_num);
            }} else if (sortBy === 'score-asc') {{
                filteredWatches.sort((a, b) => a.score1_num - b.score1_num);
            }}
            
            renderGallery();
        }}
        
        function resetFilters() {{
            document.getElementById('minPrice').value = '';
            document.getElementById('maxPrice').value = '';
            document.getElementById('minScore').value = '';
            document.getElementById('maxScore').value = '';
            document.getElementById('sortBy').value = 'price-asc';
            
            // Clear selections and active rows
            activeRows.clear();
            selections = {{}};
            
            filteredWatches = [...allWatches];
            updateSelectionInfo();
            renderGallery();
        }}
        
        // Initial render
        updateSelectionInfo();
        renderGallery();
    </script>
</body>
</html>"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Watch gallery created: {output_file}")
    print(f"📊 Total watches: {len(watches)}")


def main():
    """Main function"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file = os.path.join(base_dir, 'Watches Detailed prices', 'master_watch_prices.csv')
    output_file = os.path.join(base_dir, 'master_watch_gallery.html')
    
    print("=" * 60)
    print("Watch Comparison Gallery Generator")
    print("=" * 60)
    print(f"Reading: {csv_file}")
    
    # Read CSV data
    watches = read_master_csv(csv_file)
    
    if not watches:
        print("❌ No watch data found!")
        return
    
    print(f"Found {len(watches)} watches")
    
    # Generate HTML gallery
    generate_html_gallery(watches, output_file)
    
    print("\n" + "=" * 60)
    print("✅ Done! Open master_watch_gallery.html in your browser")
    print("=" * 60)


if __name__ == "__main__":
    main()

