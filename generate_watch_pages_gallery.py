#!/usr/bin/env python3
"""
Generate Watch Pages Gallery
Creates an HTML gallery from tagged watch videos with filterable attributes
"""

import json
import sys
import os

def generate_watch_gallery(tagged_json):
    """Generate HTML gallery with tagged watches and attribute filters"""
    
    print(f"📖 Reading tagged data: {tagged_json}")
    
    # Load tagged videos
    try:
        with open(tagged_json, 'r', encoding='utf-8') as f:
            videos = json.load(f)
        print(f"✅ Loaded {len(videos)} tagged videos")
    except Exception as e:
        print(f"❌ Error reading JSON: {e}")
        return False
    
    if not videos:
        print("❌ No videos found in JSON!")
        return False
    
    # Extract unique values for each attribute
    case_shapes = sorted(set(v['tags'].get('case_shape', 'other') for v in videos if v.get('tags')))
    case_colors = sorted(set(v['tags'].get('case_color', 'other') for v in videos if v.get('tags')))
    dial_colors = sorted(set(v['tags'].get('dial_color', 'other') for v in videos if v.get('tags')))
    dial_markers = sorted(set(v['tags'].get('dial_markers', 'other') for v in videos if v.get('tags')))
    strap_types = sorted(set(v['tags'].get('strap_type', 'other') for v in videos if v.get('tags')))
    strap_colors = sorted(set(v['tags'].get('strap_color', 'other') for v in videos if v.get('tags')))
    
    print(f"📊 Found {len(case_shapes)} case shapes, {len(case_colors)} case colors, {len(dial_colors)} dial colors")
    print(f"   {len(dial_markers)} dial markers, {len(strap_types)} strap types, {len(strap_colors)} strap colors")
    
    # Generate HTML with embedded JavaScript
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Watch Pages Gallery</title>
    <style>
        * {
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: #0a0a0a;
            color: #ffffff;
            margin: 0;
            padding: 20px;
        }
        
        h1 {
            text-align: center;
            color: #fe2c55;
            margin-bottom: 10px;
            font-size: 2.5em;
        }
        
        .subtitle {
            text-align: center;
            color: #8a8b91;
            margin-bottom: 30px;
            font-size: 1.1em;
        }
        
        .filter-section {
            max-width: 1400px;
            margin: 0 auto 20px;
            padding: 25px;
            background-color: #161823;
            border-radius: 12px;
        }
        
        .filter-row {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .filter-group {
            display: flex;
            gap: 8px;
            align-items: center;
            background-color: #0a0a0a;
            padding: 8px 12px;
            border-radius: 6px;
            flex: 1;
            min-width: 200px;
        }
        
        .filter-group label {
            color: #8a8b91;
            font-size: 0.85em;
            font-weight: 600;
            min-width: 80px;
        }
        
        .filter-group select {
            flex: 1;
            padding: 6px 10px;
            background-color: #161823;
            border: 1px solid #333;
            border-radius: 4px;
            color: #ffffff;
            font-size: 0.85em;
        }
        
        .filter-buttons {
            display: flex;
            gap: 10px;
            justify-content: center;
            margin-top: 15px;
        }
        
        .filter-buttons button {
            padding: 10px 24px;
            background-color: #333;
            border: none;
            border-radius: 6px;
            color: white;
            font-weight: 600;
            cursor: pointer;
            font-size: 0.9em;
        }
        
        .filter-buttons button:hover {
            background-color: #444;
        }
        
        .filter-buttons button.primary {
            background-color: #fe2c55;
        }
        
        .filter-buttons button.primary:hover {
            background-color: #d91d45;
        }
        
        .stats {
            text-align: center;
            color: #8a8b91;
            margin-bottom: 20px;
            font-size: 1.1em;
        }
        
        .gallery {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .video-card {
            position: relative;
            border-radius: 12px;
            overflow: hidden;
            background-color: #161823;
            transition: transform 0.2s ease;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        
        .video-card:hover {
            transform: scale(1.03);
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
        }
        
        .video-card a {
            display: block;
            text-decoration: none;
        }
        
        .video-card img {
            width: 100%;
            height: auto;
            display: block;
            aspect-ratio: 9/16;
            object-fit: cover;
        }
        
        .video-info {
            padding: 12px;
            background-color: #161823;
        }
        
        .video-stats {
            color: #ffffff;
            font-size: 0.9em;
            margin-bottom: 8px;
        }
        
        .video-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
            margin-bottom: 8px;
        }
        
        .tag {
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.7em;
            font-weight: 600;
        }
        
        .tag.case {
            background-color: #2d5a87;
            color: #ffffff;
        }
        
        .tag.dial {
            background-color: #744c9e;
            color: #ffffff;
        }
        
        .tag.strap {
            background-color: #2a5a3e;
            color: #ffffff;
        }
        
        .pagination {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
            margin-top: 40px;
            flex-wrap: wrap;
        }
        
        .pagination button {
            padding: 8px 16px;
            background-color: #161823;
            color: #ffffff;
            border: 1px solid #333;
            border-radius: 6px;
            cursor: pointer;
        }
        
        .pagination button:hover:not(:disabled) {
            background-color: #fe2c55;
            border-color: #fe2c55;
        }
        
        .pagination button.active {
            background-color: #fe2c55;
            border-color: #fe2c55;
        }
        
        .pagination button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .pagination span {
            color: #8a8b91;
            padding: 0 10px;
        }
        
        .no-results {
            text-align: center;
            color: #8a8b91;
            font-size: 1.2em;
            margin-top: 50px;
        }
        
        @media (max-width: 1200px) {
            .gallery {
                grid-template-columns: repeat(3, 1fr);
            }
        }
        
        @media (max-width: 900px) {
            .gallery {
                grid-template-columns: repeat(2, 1fr);
                gap: 15px;
            }
            
            .filter-row {
                flex-direction: column;
            }
            
            .filter-group {
                width: 100%;
            }
        }
        
        @media (max-width: 600px) {
            .gallery {
                grid-template-columns: repeat(2, 1fr);
                gap: 10px;
            }
            
            h1 {
                font-size: 1.8em;
            }
        }
    </style>
</head>
<body>
    <h1>⌚ Watch Pages Gallery</h1>
    <div class="subtitle">Filter watches by attributes</div>
    
    <div class="filter-section">
        <div class="filter-row">
            <div class="filter-group">
                <label>Case Shape:</label>
                <select id="caseShapeFilter">
                    <option value="">All</option>
"""
    
    # Add case shape options
    for shape in case_shapes:
        html_content += f'                    <option value="{shape}">{shape.title()}</option>\n'
    
    html_content += """                </select>
            </div>
            
            <div class="filter-group">
                <label>Case Color:</label>
                <select id="caseColorFilter">
                    <option value="">All</option>
"""
    
    # Add case color options
    for color in case_colors:
        html_content += f'                    <option value="{color}">{color.title()}</option>\n'
    
    html_content += """                </select>
            </div>
            
            <div class="filter-group">
                <label>Dial Color:</label>
                <select id="dialColorFilter">
                    <option value="">All</option>
"""
    
    # Add dial color options
    for color in dial_colors:
        html_content += f'                    <option value="{color}">{color.title()}</option>\n'
    
    html_content += """                </select>
            </div>
        </div>
        
        <div class="filter-row">
            <div class="filter-group">
                <label>Dial Markers:</label>
                <select id="dialMarkersFilter">
                    <option value="">All</option>
"""
    
    # Add dial markers options
    for marker in dial_markers:
        html_content += f'                    <option value="{marker}">{marker.title()}</option>\n'
    
    html_content += """                </select>
            </div>
            
            <div class="filter-group">
                <label>Strap Type:</label>
                <select id="strapTypeFilter">
                    <option value="">All</option>
"""
    
    # Add strap type options
    for strap in strap_types:
        html_content += f'                    <option value="{strap}">{strap.title()}</option>\n'
    
    html_content += """                </select>
            </div>
            
            <div class="filter-group">
                <label>Strap Color:</label>
                <select id="strapColorFilter">
                    <option value="">All</option>
"""
    
    # Add strap color options
    for color in strap_colors:
        html_content += f'                    <option value="{color}">{color.title()}</option>\n'
    
    html_content += """                </select>
            </div>
        </div>
        
        <div class="filter-buttons">
            <button class="primary" onclick="applyFilters()">Apply Filters</button>
            <button onclick="resetFilters()">Reset All</button>
        </div>
    </div>
    
    <div class="stats" id="stats">Loading...</div>
    
    <div class="gallery" id="gallery"></div>
    
    <div class="pagination" id="pagination"></div>
    
    <script>
        // Video data embedded in JavaScript
        const allVideos = """
    
    # Add video data as JSON
    html_content += json.dumps(videos, ensure_ascii=False)
    
    html_content += """;
        
        let currentPage = 1;
        const itemsPerPage = 100;
        let filteredVideos = [...allVideos];
        
        // Apply all filters
        function applyFilters() {
            const caseShape = document.getElementById('caseShapeFilter').value;
            const caseColor = document.getElementById('caseColorFilter').value;
            const dialColor = document.getElementById('dialColorFilter').value;
            const dialMarkers = document.getElementById('dialMarkersFilter').value;
            const strapType = document.getElementById('strapTypeFilter').value;
            const strapColor = document.getElementById('strapColorFilter').value;
            
            filteredVideos = allVideos.filter(video => {
                if (!video.tags) return false;
                
                // Apply each filter (AND logic - all must match)
                if (caseShape && video.tags.case_shape !== caseShape) return false;
                if (caseColor && video.tags.case_color !== caseColor) return false;
                if (dialColor && video.tags.dial_color !== dialColor) return false;
                if (dialMarkers && video.tags.dial_markers !== dialMarkers) return false;
                if (strapType && video.tags.strap_type !== strapType) return false;
                if (strapColor && video.tags.strap_color !== strapColor) return false;
                
                return true;
            });
            
            currentPage = 1;
            renderGallery();
        }
        
        // Reset all filters
        function resetFilters() {
            document.getElementById('caseShapeFilter').value = '';
            document.getElementById('caseColorFilter').value = '';
            document.getElementById('dialColorFilter').value = '';
            document.getElementById('dialMarkersFilter').value = '';
            document.getElementById('strapTypeFilter').value = '';
            document.getElementById('strapColorFilter').value = '';
            
            filteredVideos = [...allVideos];
            currentPage = 1;
            renderGallery();
        }
        
        // Render gallery
        function renderGallery() {
            const totalPages = Math.ceil(filteredVideos.length / itemsPerPage);
            const startIdx = (currentPage - 1) * itemsPerPage;
            const endIdx = startIdx + itemsPerPage;
            const pageVideos = filteredVideos.slice(startIdx, endIdx);
            
            // Update stats
            document.getElementById('stats').textContent = 
                `Showing ${startIdx + 1}-${Math.min(endIdx, filteredVideos.length)} of ${filteredVideos.length} watches (Page ${currentPage}/${totalPages || 1})`;
            
            // Render gallery
            const gallery = document.getElementById('gallery');
            
            if (pageVideos.length === 0) {
                gallery.innerHTML = '<div class="no-results">No watches match your filters. Try adjusting the selections.</div>';
            } else {
                gallery.innerHTML = pageVideos.map(video => {
                    const tags = video.tags || {};
                    let tagsHTML = '';
                    
                    if (tags.case_shape) {
                        tagsHTML += `<span class="tag case">${tags.case_shape}</span>`;
                    }
                    if (tags.case_color) {
                        tagsHTML += `<span class="tag case">${tags.case_color}</span>`;
                    }
                    if (tags.dial_color) {
                        tagsHTML += `<span class="tag dial">${tags.dial_color}</span>`;
                    }
                    if (tags.dial_markers) {
                        tagsHTML += `<span class="tag dial">${tags.dial_markers}</span>`;
                    }
                    if (tags.strap_type) {
                        tagsHTML += `<span class="tag strap">${tags.strap_type}</span>`;
                    }
                    if (tags.strap_color) {
                        tagsHTML += `<span class="tag strap">${tags.strap_color}</span>`;
                    }
                    
                    return `
                        <div class="video-card">
                            <a href="${video.video_url}" target="_blank" rel="noopener noreferrer">
                                <img src="${video.thumbnail_url}" alt="Watch" loading="lazy">
                                <div class="video-info">
                                    <div class="video-stats">❤️ ${video.likes} | #${video.index}</div>
                                    <div class="video-tags">${tagsHTML || '<span class="tag">No tags</span>'}</div>
                                </div>
                            </a>
                        </div>
                    `;
                }).join('');
            }
            
            // Render pagination
            renderPagination(totalPages);
        }
        
        // Render pagination
        function renderPagination(totalPages) {
            const pagination = document.getElementById('pagination');
            
            if (totalPages <= 1) {
                pagination.innerHTML = '';
                return;
            }
            
            let paginationHTML = '';
            
            // Previous button
            paginationHTML += `<button onclick="changePage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>← Previous</button>`;
            
            // Page numbers (show max 10 pages)
            const maxVisible = 10;
            let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
            let endPage = Math.min(totalPages, startPage + maxVisible - 1);
            
            if (endPage - startPage < maxVisible - 1) {
                startPage = Math.max(1, endPage - maxVisible + 1);
            }
            
            if (startPage > 1) {
                paginationHTML += `<button onclick="changePage(1)">1</button>`;
                if (startPage > 2) {
                    paginationHTML += `<span>...</span>`;
                }
            }
            
            for (let i = startPage; i <= endPage; i++) {
                paginationHTML += `<button onclick="changePage(${i})" class="${i === currentPage ? 'active' : ''}">${i}</button>`;
            }
            
            if (endPage < totalPages) {
                if (endPage < totalPages - 1) {
                    paginationHTML += `<span>...</span>`;
                }
                paginationHTML += `<button onclick="changePage(${totalPages})">${totalPages}</button>`;
            }
            
            // Next button
            paginationHTML += `<button onclick="changePage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>Next →</button>`;
            
            pagination.innerHTML = paginationHTML;
        }
        
        // Change page
        function changePage(page) {
            const totalPages = Math.ceil(filteredVideos.length / itemsPerPage);
            if (page < 1 || page > totalPages) return;
            
            currentPage = page;
            renderGallery();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
        
        // Initial render
        renderGallery();
    </script>
</body>
</html>"""
    
    # Save HTML file
    output_file = 'watch_pages_gallery.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n✅ Gallery created successfully!")
    print(f"📄 Output: {output_file}")
    print(f"🌐 Open '{output_file}' in your browser to view")
    print(f"\nFeatures:")
    print(f"  ✅ 6 attribute filters (case shape, case color, dial color, dial markers, strap type, strap color)")
    print(f"  ✅ Combination filtering (AND logic)")
    print(f"  ✅ 100 watches per page with pagination")
    print(f"  ✅ Visual tags on each watch card")
    
    return True

def main():
    """Main entry point"""
    print("🎨 Watch Pages Gallery Generator")
    print("=" * 50)
    
    # Get JSON file
    if len(sys.argv) > 1:
        tagged_json = sys.argv[1]
    else:
        tagged_json = input("\n📂 Enter tagged JSON file path: ").strip()
        tagged_json = tagged_json.replace('\\', '').strip('"').strip("'")
    
    if not tagged_json:
        print("❌ No file provided!")
        return
    
    if not os.path.exists(tagged_json):
        print(f"❌ File not found: {tagged_json}")
        return
    
    # Generate gallery
    success = generate_watch_gallery(tagged_json)
    
    if not success:
        print("\n❌ Failed to generate gallery")
        sys.exit(1)

if __name__ == "__main__":
    main()

