#!/usr/bin/env python3
"""
Generate Tagged Research Gallery
Creates an HTML gallery from tagged research videos with smart search
"""

import json
import sys
import os

def load_taxonomy():
    """Load taxonomy for synonym mapping"""
    try:
        with open('product_taxonomy.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def generate_tagged_gallery(tagged_json):
    """Generate HTML gallery with tagged videos and smart search"""
    
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
    
    # Load taxonomy for synonyms
    taxonomy = load_taxonomy()
    
    # Generate HTML with embedded JavaScript
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tagged Research Gallery</title>
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
        
        .search-section {
            max-width: 1400px;
            margin: 0 auto 20px;
            padding: 25px;
            background-color: #161823;
            border-radius: 12px;
        }
        
        .search-box {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .search-box input {
            flex: 1;
            padding: 12px 16px;
            background-color: #0a0a0a;
            border: 2px solid #333;
            border-radius: 8px;
            color: #ffffff;
            font-size: 1em;
        }
        
        .search-box input:focus {
            outline: none;
            border-color: #fe2c55;
        }
        
        .search-box button {
            padding: 12px 24px;
            background-color: #fe2c55;
            border: none;
            border-radius: 8px;
            color: white;
            font-weight: 600;
            cursor: pointer;
            font-size: 1em;
        }
        
        .search-box button:hover {
            background-color: #d91d45;
        }
        
        .search-hint {
            color: #8a8b91;
            font-size: 0.9em;
            margin-bottom: 15px;
        }
        
        .search-expansion {
            background-color: #1a1d29;
            padding: 10px 15px;
            border-radius: 6px;
            margin-bottom: 15px;
            font-size: 0.9em;
            color: #8a8b91;
            display: none;
        }
        
        .search-expansion.active {
            display: block;
        }
        
        .search-expansion strong {
            color: #fe2c55;
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
        }
        
        .filter-group label {
            color: #8a8b91;
            font-size: 0.85em;
            font-weight: 600;
            min-width: 60px;
        }
        
        .filter-group input {
            padding: 6px 10px;
            background-color: #161823;
            border: 1px solid #333;
            border-radius: 4px;
            color: #ffffff;
            width: 80px;
            font-size: 0.85em;
        }
        
        .filter-group select {
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
        }
        
        .filter-buttons button {
            padding: 8px 16px;
            background-color: #333;
            border: none;
            border-radius: 6px;
            color: white;
            font-weight: 600;
            cursor: pointer;
            font-size: 0.85em;
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
            font-size: 0.75em;
            font-weight: 600;
        }
        
        .tag.shape {
            background-color: #2d5a87;
            color: #ffffff;
        }
        
        .tag.type {
            background-color: #744c9e;
            color: #ffffff;
        }
        
        .tag.color {
            background-color: #4a5568;
            color: #ffffff;
        }
        
        .tag.material {
            background-color: #2a5a3e;
            color: #ffffff;
        }
        
        .tag.pairing {
            background-color: #fe2c55;
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
                align-items: stretch;
            }
            
            .filter-group {
                flex-direction: column;
                align-items: stretch;
            }
            
            .filter-group input,
            .filter-group select {
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
    <h1>🏷️ Tagged Research Gallery</h1>
    <div class="subtitle">Smart product search with AI tags</div>
    
    <div class="search-section">
        <div class="search-box">
            <input type="text" id="tagSearch" placeholder="Search by tag (e.g., clover, butterfly, fourleaf...)" />
            <button onclick="searchByTag()">🔍 Search</button>
        </div>
        
        <div class="search-hint">
            💡 Try: clover, butterfly, fourleaf, star, leaf, pearl, black, gold, necklace, earring
        </div>
        
        <div class="search-expansion" id="searchExpansion"></div>
        
        <div class="filter-row">
            <div class="filter-group">
                <label>Product:</label>
                <select id="productType">
                    <option value="">All</option>
                    <option value="necklace">Necklace</option>
                    <option value="earring">Earring</option>
                    <option value="ring">Ring</option>
                    <option value="bracelet">Bracelet</option>
                    <option value="watch">Watch</option>
                </select>
            </div>
            
            <div class="filter-group">
                <label>Color:</label>
                <select id="colorFilter">
                    <option value="">All</option>
                    <option value="black">Black</option>
                    <option value="white">White</option>
                    <option value="red">Red</option>
                    <option value="blue">Blue</option>
                    <option value="green">Green</option>
                    <option value="pink">Pink</option>
                    <option value="purple">Purple</option>
                    <option value="yellow">Yellow</option>
                    <option value="brown">Brown</option>
                    <option value="multicolor">Multicolor</option>
                </select>
            </div>
            
            <div class="filter-group">
                <label>Metal:</label>
                <select id="metalFilter">
                    <option value="">All</option>
                    <option value="gold">Gold</option>
                    <option value="silver">Silver</option>
                    <option value="white-gold">White Gold</option>
                    <option value="rose-gold">Rose Gold</option>
                    <option value="two-tone">Two-Tone</option>
                </select>
            </div>
            
            <div class="filter-group">
                <label>Material:</label>
                <select id="materialFilter">
                    <option value="">All</option>
                    <option value="pearl">Pearl</option>
                    <option value="mother-of-pearl">Mother of Pearl</option>
                    <option value="crystal">Crystal</option>
                    <option value="diamond">Diamond</option>
                    <option value="enamel">Enamel</option>
                    <option value="resin">Resin</option>
                </select>
            </div>
        </div>
        
        <div class="filter-row">
            <div class="filter-group">
                <label>Likes Min:</label>
                <input type="number" id="likesMin" placeholder="0">
            </div>
            <div class="filter-group">
                <label>Likes Max:</label>
                <input type="number" id="likesMax" placeholder="∞">
            </div>
            
            <div class="filter-group">
                <label>Index Min:</label>
                <input type="number" id="indexMin" placeholder="1">
            </div>
            <div class="filter-group">
                <label>Index Max:</label>
                <input type="number" id="indexMax" placeholder="∞">
            </div>
        </div>
        
        <div class="filter-buttons">
            <button class="primary" onclick="applyFilters()">Apply Filters</button>
            <button onclick="resetFilters()">Reset All</button>
            <button onclick="findPairs()">🔗 Find Pairs</button>
        </div>
    </div>
    
    <div class="stats" id="stats">Loading...</div>
    
    <div class="gallery" id="gallery"></div>
    
    <div class="pagination" id="pagination"></div>
    
    <script>
        // Video data and taxonomy embedded in JavaScript
        const allVideos = """
    
    # Add video data as JSON
    html_content += json.dumps(videos, ensure_ascii=False)
    
    html_content += """;
        
        const taxonomy = """
    
    # Add taxonomy as JSON
    if taxonomy:
        html_content += json.dumps(taxonomy, ensure_ascii=False)
    else:
        html_content += "{}"
    
    html_content += """;
        
        let currentPage = 1;
        const itemsPerPage = 100;
        let filteredVideos = [...allVideos];
        let currentSearchTerm = '';
        
        // Parse likes to number
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
        
        // Get all synonyms for a search term
        function getSynonyms(searchTerm) {
            searchTerm = searchTerm.toLowerCase().trim();
            const allSynonyms = new Set([searchTerm]);
            
            // Check all taxonomy categories
            for (const category of Object.values(taxonomy)) {
                for (const [primary, data] of Object.entries(category)) {
                    if (primary.toLowerCase() === searchTerm || 
                        (data.synonyms && data.synonyms.some(syn => syn.toLowerCase() === searchTerm))) {
                        allSynonyms.add(primary.toLowerCase());
                        if (data.synonyms) {
                            data.synonyms.forEach(syn => allSynonyms.add(syn.toLowerCase()));
                        }
                    }
                }
            }
            
            return Array.from(allSynonyms);
        }
        
        // Search by tag with synonym support
        function searchByTag() {
            const searchInput = document.getElementById('tagSearch').value.trim();
            
            if (!searchInput) {
                currentSearchTerm = '';
                document.getElementById('searchExpansion').classList.remove('active');
                applyFilters();
                return;
            }
            
            currentSearchTerm = searchInput;
            const synonyms = getSynonyms(searchInput);
            
            // Show expansion
            const expansionDiv = document.getElementById('searchExpansion');
            if (synonyms.length > 1) {
                expansionDiv.innerHTML = `<strong>💡 Also searching:</strong> ${synonyms.filter(s => s !== searchInput.toLowerCase()).join(', ')}`;
                expansionDiv.classList.add('active');
            } else {
                expansionDiv.classList.remove('active');
            }
            
            // Apply filters with search
            applyFilters();
        }
        
        // Find matching pairs
        function findPairs() {
            const pairingKeys = {};
            
            allVideos.forEach(video => {
                if (video.tags && video.tags.pairing_key) {
                    const key = video.tags.pairing_key;
                    if (!pairingKeys[key]) {
                        pairingKeys[key] = [];
                    }
                    pairingKeys[key].push(video);
                }
            });
            
            // Filter to only keys with multiple items
            const pairs = Object.entries(pairingKeys)
                .filter(([key, videos]) => videos.length > 1)
                .sort((a, b) => b[1].length - a[1].length);
            
            if (pairs.length === 0) {
                alert('No matching pairs found. Try tagging more videos or adjusting your search.');
                return;
            }
            
            // Show first pair
            const [firstKey, firstPair] = pairs[0];
            alert(`Found ${pairs.length} pairing groups!\\nShowing largest group: ${firstKey} (${firstPair.length} items)`);
            
            // Filter to show this pair
            filteredVideos = firstPair;
            currentPage = 1;
            renderGallery();
        }
        
        // Apply all filters
        function applyFilters() {
            const likesMin = parseInt(document.getElementById('likesMin').value) || 0;
            const likesMax = parseInt(document.getElementById('likesMax').value) || Infinity;
            const indexMin = parseInt(document.getElementById('indexMin').value) || 0;
            const indexMax = parseInt(document.getElementById('indexMax').value) || Infinity;
            const productType = document.getElementById('productType').value;
            const colorFilter = document.getElementById('colorFilter').value;
            const metalFilter = document.getElementById('metalFilter').value;
            const materialFilter = document.getElementById('materialFilter').value;
            
            filteredVideos = allVideos.filter(video => {
                const likes = parseLikes(video.likes);
                const index = parseInt(video.index) || 0;
                
                // Likes and index filters
                if (likes < likesMin || likes > likesMax) return false;
                if (index < indexMin || index > indexMax) return false;
                
                // Product type filter
                if (productType && video.tags && video.tags.product_type !== productType) return false;
                
                // Color filter (EXACT match - no synonyms)
                if (colorFilter && video.tags) {
                    const videoColors = [
                        video.tags.primary_color,
                        ...(video.tags.secondary_colors || [])
                    ].filter(Boolean).map(c => c.toLowerCase());
                    
                    if (!videoColors.includes(colorFilter.toLowerCase())) return false;
                }
                
                // Metal filter (EXACT match - no synonyms)
                if (metalFilter && video.tags) {
                    if (video.tags.metal_color?.toLowerCase() !== metalFilter.toLowerCase()) return false;
                }
                
                // Material filter (EXACT match - no synonyms)
                if (materialFilter && video.tags) {
                    const videoMaterials = (video.tags.materials || []).map(m => m.toLowerCase());
                    if (!videoMaterials.includes(materialFilter.toLowerCase())) return false;
                }
                
                // Tag search filter (for shapes - with synonyms)
                // Multiple search terms are AND logic (all must match)
                if (currentSearchTerm && video.tags) {
                    const searchTerms = currentSearchTerm.toLowerCase().split(/\s+/).filter(t => t.length > 0);
                    
                    // Get all video tags (shapes only for synonym expansion)
                    const videoShapes = [
                        video.tags.primary_shape,
                        ...(video.tags.secondary_shapes || [])
                    ].filter(Boolean).map(t => t.toLowerCase());
                    
                    const videoOtherTags = [
                        video.tags.product_type,
                        video.tags.style
                    ].filter(Boolean).map(t => t.toLowerCase());
                    
                    // For each search term, check if it matches
                    for (const term of searchTerms) {
                        // Get synonyms for shapes only
                        const synonyms = getSynonyms(term);
                        
                        // Check if this term matches any video tag
                        const matchesShape = synonyms.some(syn => 
                            videoShapes.some(shape => shape.includes(syn) || syn.includes(shape))
                        );
                        
                        const matchesOther = videoOtherTags.some(tag => 
                            tag.includes(term) || term.includes(tag)
                        );
                        
                        // If this term doesn't match, exclude this video (AND logic)
                        if (!matchesShape && !matchesOther) {
                            return false;
                        }
                    }
                }
                
                return true;
            });
            
            currentPage = 1;
            renderGallery();
        }
        
        // Reset all filters
        function resetFilters() {
            document.getElementById('tagSearch').value = '';
            document.getElementById('likesMin').value = '';
            document.getElementById('likesMax').value = '';
            document.getElementById('indexMin').value = '';
            document.getElementById('indexMax').value = '';
            document.getElementById('productType').value = '';
            document.getElementById('colorFilter').value = '';
            document.getElementById('metalFilter').value = '';
            document.getElementById('materialFilter').value = '';
            document.getElementById('searchExpansion').classList.remove('active');
            
            currentSearchTerm = '';
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
                `Showing ${startIdx + 1}-${Math.min(endIdx, filteredVideos.length)} of ${filteredVideos.length} videos (Page ${currentPage}/${totalPages || 1})`;
            
            // Render gallery
            const gallery = document.getElementById('gallery');
            
            if (pageVideos.length === 0) {
                gallery.innerHTML = '<div class="no-results">No videos match your filters. Try adjusting the search or filters.</div>';
            } else {
                gallery.innerHTML = pageVideos.map(video => {
                    const tags = video.tags || {};
                    let tagsHTML = '';
                    
                    if (tags.product_type) {
                        tagsHTML += `<span class="tag type">${tags.product_type}</span>`;
                    }
                    if (tags.primary_shape) {
                        tagsHTML += `<span class="tag shape">${tags.primary_shape}</span>`;
                    }
                    if (tags.primary_color) {
                        tagsHTML += `<span class="tag color">${tags.primary_color}</span>`;
                    }
                    if (tags.metal_color) {
                        tagsHTML += `<span class="tag color">${tags.metal_color}</span>`;
                    }
                    if (tags.pairing_key) {
                        tagsHTML += `<span class="tag pairing">${tags.pairing_key}</span>`;
                    }
                    
                    return `
                        <div class="video-card">
                            <a href="${video.video_url}" target="_blank" rel="noopener noreferrer">
                                <img src="${video.thumbnail_url}" alt="Product" loading="lazy">
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
        
        // Allow Enter key to search
        document.getElementById('tagSearch').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchByTag();
            }
        });
        
        // Initial render
        renderGallery();
    </script>
</body>
</html>"""
    
    # Save HTML file
    output_file = 'tagged_research_gallery.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Gallery created successfully!")
    print(f"📄 Output: {output_file}")
    print(f"🌐 Open '{output_file}' in your browser to view")
    print(f"\nFeatures:")
    print(f"  ✅ Smart search with synonym support (fourleaf → clover)")
    print(f"  ✅ Filter by product type, likes, index")
    print(f"  ✅ Find matching pairs automatically")
    print(f"  ✅ 100 videos per page with pagination")
    print(f"  ✅ Visual tags on each product")
    
    return True

def main():
    """Main entry point"""
    print("🎨 Tagged Research Gallery Generator")
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
    success = generate_tagged_gallery(tagged_json)
    
    if not success:
        print("\n❌ Failed to generate gallery")
        sys.exit(1)

if __name__ == "__main__":
    main()

