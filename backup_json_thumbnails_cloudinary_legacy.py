#!/usr/bin/env python3
"""
Backup JSON Thumbnail URLs to Cloudinary
Uploads expiring Douyin thumbnails to Cloudinary and generates HTML gallery
"""

import os
import sys
import json
from pathlib import Path
import cloudinary
import cloudinary.uploader
from cloudinary.exceptions import Error as CloudinaryError
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

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

def load_taxonomy():
    """Load taxonomy for synonym mapping"""
    try:
        with open('product_taxonomy.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def backup_json_thumbnails(json_path, limit=None):
    """Main function to backup thumbnails from JSON and generate HTML"""
    
    print(f"📂 Processing JSON: {json_path}")
    
    # Read JSON
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            videos = json.load(f)
        print(f"✅ Loaded {len(videos)} videos from JSON")
    except Exception as e:
        print(f"❌ Error reading JSON: {e}")
        return False
    
    if not videos:
        print("❌ No videos found in JSON!")
        return False
    
    # Apply limit if specified
    if limit and limit > 0:
        videos = videos[:limit]
        print(f"⚠️  Processing only first {limit} videos (test mode)")
    
    # Process thumbnails with parallel uploads
    successful = 0
    failed = 0
    lock = threading.Lock()
    
    print(f"\n🔄 Uploading thumbnails to Cloudinary (parallel processing)...")
    print("=" * 50)
    
    def process_thumbnail(index, video):
        """Process a single thumbnail upload"""
        thumbnail_url = video.get('thumbnail_url', '')
        
        # Skip if already backed up
        if video.get('backup_thumbnail_url'):
            with lock:
                print(f"  [{index + 1}/{len(videos)}] ⏭️  Already backed up, skipping")
            return 'skipped', video
        
        if not thumbnail_url:
            with lock:
                print(f"  [{index + 1}/{len(videos)}] ⚠️  No thumbnail URL, skipping")
            video['backup_thumbnail_url'] = 'No URL'
            return 'failed', video
        
        with lock:
            print(f"  [{index + 1}/{len(videos)}] Uploading thumbnail...")
        
        backup_url = upload_to_cloudinary(thumbnail_url)
        
        if backup_url:
            video['backup_thumbnail_url'] = backup_url
            with lock:
                print(f"  [{index + 1}/{len(videos)}] ✅ Success")
            return 'success', video
        else:
            video['backup_thumbnail_url'] = 'Failed'
            with lock:
                print(f"  [{index + 1}/{len(videos)}] ❌ Failed")
            return 'failed', video
    
    # Use ThreadPoolExecutor for parallel uploads
    max_workers = 10
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all upload tasks
        futures = {executor.submit(process_thumbnail, i, video): i for i, video in enumerate(videos)}
        
        # Process results as they complete
        for future in as_completed(futures):
            try:
                status, updated_video = future.result()
                if status == 'success' or status == 'skipped':
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"  ❌ Thread error: {e}")
                failed += 1
    
    # Check failure rate
    failure_rate = failed / len(videos) if len(videos) > 0 else 0
    if failure_rate > 0.5 and failed > 10:
        print(f"\n⚠️  WARNING: High failure rate detected ({failed}/{len(videos)} failed)!")
        print("Possible causes:")
        print("  - Cloudinary API quota exceeded")
        print("  - Network connection issues")
        print("  - Invalid Cloudinary credentials")
        return False
    
    # Create output filenames
    json_name = Path(json_path).stem
    json_dir = Path(json_path).parent
    output_json_path = json_dir / f"Backed_{json_name}.json"
    output_html_path = json_dir / "backed_research_gallery.html"
    
    # Write updated JSON
    try:
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(videos, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Backup JSON complete!")
        print(f"📄 Saved to: {output_json_path}")
    except Exception as e:
        print(f"\n❌ Error writing output JSON: {e}")
        return False
    
    # Generate HTML gallery
    print(f"\n🎨 Generating HTML gallery...")
    try:
        generate_html_gallery(videos, output_html_path)
        print(f"✅ HTML gallery created!")
        print(f"📄 Saved to: {output_html_path}")
    except Exception as e:
        print(f"❌ Error generating HTML: {e}")
        return False
    
    # Print summary
    print(f"\n📊 SUMMARY")
    print("=" * 50)
    print(f"✅ Successful uploads: {successful}")
    print(f"❌ Failed uploads: {failed}")
    print(f"📁 Total videos: {len(videos)}")
    print(f"📄 Output JSON: {output_json_path.name}")
    print(f"🌐 Output HTML: {output_html_path.name}")
    print("=" * 50)
    
    return True

def generate_html_gallery(videos, output_path):
    """Generate HTML gallery using backup thumbnail URLs"""
    
    # Load taxonomy for synonyms
    taxonomy = load_taxonomy()
    
    # Generate HTML with embedded JavaScript
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Backed Research Gallery</title>
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
    <h1>☁️ Backed Research Gallery</h1>
    <div class="subtitle">Using Cloudinary backup URLs - thumbnails won't expire!</div>
    
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
                    
                    // Use backup_thumbnail_url instead of thumbnail_url
                    const thumbnailUrl = video.backup_thumbnail_url || video.thumbnail_url || '';
                    
                    return `
                        <div class="video-card">
                            <a href="${video.video_url}" target="_blank" rel="noopener noreferrer">
                                <img src="${thumbnailUrl}" alt="Product" loading="lazy">
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
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

def main():
    """Main entry point"""
    print("🔄 Douyin JSON Thumbnail Backup Tool")
    print("=" * 50)
    
    # Load environment variables
    load_env()
    
    # Setup Cloudinary
    if not setup_cloudinary():
        sys.exit(1)
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        # Command line mode
        json_path = sys.argv[1].replace('\\', '').strip('"').strip("'")
        limit = None
        if len(sys.argv) > 2:
            try:
                limit = int(sys.argv[2])
                if limit <= 0:
                    limit = None
            except ValueError:
                print(f"⚠️  Invalid limit '{sys.argv[2]}', processing all videos")
                limit = None
    else:
        # Interactive mode
        json_input = input("\n📂 Drag and drop JSON file here (or enter path): ").strip()
        
        if not json_input:
            print("❌ No file path provided!")
            sys.exit(1)
        
        # Clean up input path
        json_path = json_input.replace('\\', '').strip('"').strip("'")
        
        # Ask for limit
        limit_input = input("\n🔢 Limit to first N videos? (press Enter for all, or enter number like 100): ").strip()
        limit = None
        if limit_input:
            try:
                limit = int(limit_input)
                if limit <= 0:
                    print("⚠️  Invalid limit, processing all videos")
                    limit = None
            except ValueError:
                print("⚠️  Invalid number, processing all videos")
                limit = None
    
    # Validate path exists
    if not os.path.exists(json_path):
        print(f"❌ File not found: {json_path}")
        sys.exit(1)
    
    # Process JSON
    success = backup_json_thumbnails(json_path, limit=limit)
    
    if not success:
        print("\n❌ Failed to backup thumbnails")
        sys.exit(1)
    
    print("\n🎉 All done! Open 'backed_research_gallery.html' in your browser.")

if __name__ == "__main__":
    main()

