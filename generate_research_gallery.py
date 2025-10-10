#!/usr/bin/env python3
"""
Generate Paginated HTML Gallery from Research CSV
Creates an interactive gallery with filtering by likes and index
"""

import csv
import sys
import re

def parse_likes_to_number(likes_str):
    """Convert likes string (e.g., '14.2K', '2', 'N/A') to a number for comparison"""
    if not likes_str or likes_str == 'N/A':
        return 0
    
    likes_str = str(likes_str).upper().strip()
    
    # Handle K (thousands)
    if 'K' in likes_str:
        try:
            num = float(likes_str.replace('K', ''))
            return int(num * 1000)
        except:
            return 0
    
    # Handle W (万 = 10,000 in Chinese)
    if 'W' in likes_str:
        try:
            num = float(likes_str.replace('W', ''))
            return int(num * 10000)
        except:
            return 0
    
    # Handle regular numbers
    try:
        return int(likes_str)
    except:
        return 0

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

def generate_html_gallery(csv_path):
    """Generate HTML gallery with filtering and pagination"""
    
    print(f"📖 Reading CSV: {csv_path}")
    
    # Read CSV
    try:
        videos = read_csv_with_comments(csv_path)
        print(f"✅ Loaded {len(videos)} videos")
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return False
    
    if not videos:
        print("❌ No videos found in CSV!")
        return False
    
    # Generate HTML with embedded JavaScript for client-side filtering and pagination
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Research Video Gallery</title>
    <style>
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
            margin-bottom: 20px;
            font-size: 2.5em;
        }
        
        .filters {
            max-width: 1400px;
            margin: 0 auto 30px;
            padding: 20px;
            background-color: #161823;
            border-radius: 12px;
            display: flex;
            gap: 20px;
            align-items: center;
            flex-wrap: wrap;
        }
        
        .filter-group {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        .filter-group label {
            color: #8a8b91;
            font-size: 0.9em;
            min-width: 80px;
        }
        
        .filter-group input {
            padding: 8px 12px;
            background-color: #0a0a0a;
            border: 1px solid #333;
            border-radius: 6px;
            color: #ffffff;
            width: 100px;
            font-size: 0.9em;
        }
        
        .filter-group input:focus {
            outline: none;
            border-color: #fe2c55;
        }
        
        button {
            padding: 8px 20px;
            background-color: #fe2c55;
            border: none;
            border-radius: 6px;
            color: white;
            font-weight: 600;
            cursor: pointer;
            font-size: 0.9em;
        }
        
        button:hover {
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
            transform: scale(1.05);
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
            font-size: 1em;
            font-weight: 600;
            margin-bottom: 4px;
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
        }
        
        .pagination button:hover {
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
            
            .filters {
                flex-direction: column;
                align-items: stretch;
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
    <h1>🎥 Research Video Gallery</h1>
    
    <div class="filters">
        <div class="filter-group">
            <label>Likes Min:</label>
            <input type="number" id="likesMin" placeholder="e.g., 1000">
        </div>
        <div class="filter-group">
            <label>Likes Max:</label>
            <input type="number" id="likesMax" placeholder="e.g., 5000">
        </div>
        <div class="filter-group">
            <label>Index Min:</label>
            <input type="number" id="indexMin" placeholder="e.g., 1">
        </div>
        <div class="filter-group">
            <label>Index Max:</label>
            <input type="number" id="indexMax" placeholder="e.g., 100">
        </div>
        <button onclick="applyFilters()">Apply Filters</button>
        <button onclick="resetFilters()">Reset</button>
    </div>
    
    <div class="stats" id="stats">Loading...</div>
    
    <div class="gallery" id="gallery"></div>
    
    <div class="pagination" id="pagination"></div>
    
    <script>
        // Video data embedded in JavaScript
        const allVideos = """
    
    # Add video data as JSON
    import json
    
    # Convert videos to JSON-friendly format
    videos_data = []
    for video in videos:
        videos_data.append({
            'video_url': video.get('video_url', ''),
            'thumbnail_url': video.get('thumbnail_url', ''),
            'likes': video.get('likes', 'N/A'),
            'index': video.get('index', '0')
        })
    
    html_content += json.dumps(videos_data, ensure_ascii=False)
    
    html_content += """;
        
        let currentPage = 1;
        const itemsPerPage = 100;
        let filteredVideos = [...allVideos];
        
        // Parse likes to number for filtering
        function parseLikes(likesStr) {
            if (!likesStr || likesStr === 'N/A') return 0;
            
            likesStr = String(likesStr).toUpperCase().trim();
            
            if (likesStr.includes('K')) {
                return parseFloat(likesStr.replace('K', '')) * 1000;
            }
            if (likesStr.includes('W')) {
                return parseFloat(likesStr.replace('W', '')) * 10000;
            }
            
            return parseInt(likesStr) || 0;
        }
        
        function applyFilters() {
            const likesMin = parseInt(document.getElementById('likesMin').value) || 0;
            const likesMax = parseInt(document.getElementById('likesMax').value) || Infinity;
            const indexMin = parseInt(document.getElementById('indexMin').value) || 0;
            const indexMax = parseInt(document.getElementById('indexMax').value) || Infinity;
            
            filteredVideos = allVideos.filter(video => {
                const likes = parseLikes(video.likes);
                const index = parseInt(video.index) || 0;
                
                return likes >= likesMin && likes <= likesMax &&
                       index >= indexMin && index <= indexMax;
            });
            
            currentPage = 1;
            renderGallery();
        }
        
        function resetFilters() {
            document.getElementById('likesMin').value = '';
            document.getElementById('likesMax').value = '';
            document.getElementById('indexMin').value = '';
            document.getElementById('indexMax').value = '';
            
            filteredVideos = [...allVideos];
            currentPage = 1;
            renderGallery();
        }
        
        function renderGallery() {
            const totalPages = Math.ceil(filteredVideos.length / itemsPerPage);
            const startIdx = (currentPage - 1) * itemsPerPage;
            const endIdx = startIdx + itemsPerPage;
            const pageVideos = filteredVideos.slice(startIdx, endIdx);
            
            // Update stats
            document.getElementById('stats').textContent = 
                `Showing ${startIdx + 1}-${Math.min(endIdx, filteredVideos.length)} of ${filteredVideos.length} videos (Page ${currentPage}/${totalPages})`;
            
            // Render gallery
            const gallery = document.getElementById('gallery');
            
            if (pageVideos.length === 0) {
                gallery.innerHTML = '<div class="no-results">No videos match your filters. Try adjusting the ranges.</div>';
            } else {
                gallery.innerHTML = pageVideos.map(video => `
                    <div class="video-card">
                        <a href="${video.video_url}" target="_blank" rel="noopener noreferrer">
                            <img src="${video.thumbnail_url}" alt="Video thumbnail" loading="lazy">
                            <div class="video-info">
                                <div class="video-stats">❤️ ${video.likes} | #${video.index}</div>
                            </div>
                        </a>
                    </div>
                `).join('');
            }
            
            // Render pagination
            renderPagination(totalPages);
        }
        
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
                    paginationHTML += `<span style="color: #8a8b91; padding: 0 10px;">...</span>`;
                }
            }
            
            for (let i = startPage; i <= endPage; i++) {
                paginationHTML += `<button onclick="changePage(${i})" class="${i === currentPage ? 'active' : ''}">${i}</button>`;
            }
            
            if (endPage < totalPages) {
                if (endPage < totalPages - 1) {
                    paginationHTML += `<span style="color: #8a8b91; padding: 0 10px;">...</span>`;
                }
                paginationHTML += `<button onclick="changePage(${totalPages})">${totalPages}</button>`;
            }
            
            // Next button
            paginationHTML += `<button onclick="changePage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>Next →</button>`;
            
            pagination.innerHTML = paginationHTML;
        }
        
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
    output_file = 'research_gallery.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Gallery created successfully!")
    print(f"📄 Output: {output_file}")
    print(f"🌐 Open '{output_file}' in your browser to view")
    print(f"\nFeatures:")
    print(f"  - 100 videos per page")
    print(f"  - Filter by likes range")
    print(f"  - Filter by index range")
    print(f"  - Click thumbnails to open videos on Douyin")
    
    return True

def main():
    """Main entry point"""
    print("🎨 Research Gallery Generator")
    print("=" * 50)
    
    # Get CSV file
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    else:
        csv_path = input("\n📂 Enter CSV file path (or drag-and-drop): ").strip()
        csv_path = csv_path.replace('\\', '').strip('"').strip("'")
    
    if not csv_path:
        print("❌ No file provided!")
        return
    
    # Generate gallery
    success = generate_html_gallery(csv_path)
    
    if not success:
        print("\n❌ Failed to generate gallery")
        sys.exit(1)

if __name__ == "__main__":
    main()

