#!/usr/bin/env python3
"""
Generate Complex HTML Gallery from Douyin Thumbnails with Titles
Reads complex_input.txt for video URLs/titles and complex_output.txt for thumbnail URLs
Creates complex_gallery.html with clickable thumbnail images and custom titles
"""

def parse_complex_input(input_file):
    """Parse complex input to get URL list in order"""
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = [line.rstrip() for line in f]
    except FileNotFoundError:
        print(f"Error: {input_file} not found!")
        return []
    
    urls = []
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines
        if not line or line.startswith('#'):
            i += 1
            continue
        
        # Check if current line is a URL
        if 'douyin.com' in line:
            urls.append(line)
            i += 1
        else:
            # This should be a title, check if next line is a URL
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if 'douyin.com' in next_line:
                    urls.append(next_line)
                    i += 2  # Skip both title and URL
                else:
                    i += 1
            else:
                i += 1
    
    return urls

def parse_complex_output(output_file):
    """Parse complex output to get title and thumbnail pairs"""
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: {output_file} not found!")
        print("Please run complex_extractor.py first.")
        return []
    
    entries = []
    for line in lines:
        if '|||' in line:
            parts = line.split('|||', 1)  # Split only on first occurrence
            title = parts[0]
            thumbnail_url = parts[1]
            entries.append({
                'title': title,
                'thumbnail_url': thumbnail_url
            })
        else:
            # Fallback for malformed lines
            entries.append({
                'title': '',
                'thumbnail_url': line
            })
    
    return entries

def generate_gallery():
    """Generate HTML gallery from complex input and output files"""
    
    input_file = 'input.txt'
    output_file = 'output.txt'
    
    # Read video URLs from complex input
    video_urls = parse_complex_input(input_file)
    if not video_urls:
        print("No video URLs found in complex input!")
        return False
    
    # Read title and thumbnail data from complex output
    entries = parse_complex_output(output_file)
    if not entries:
        print("No entries found in complex output!")
        return False
    
    # Create HTML gallery
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Douyin Video Gallery - Custom Titles</title>
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
            margin-bottom: 30px;
            font-size: 2.5em;
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
        
        .video-title {
            color: #ffffff;
            font-size: 1.1em;
            font-weight: 600;
            margin-bottom: 6px;
            line-height: 1.3;
            min-height: 1.3em;
        }
        
        .video-title.empty {
            color: #8a8b91;
            font-style: italic;
            font-weight: normal;
        }
        
        .video-link {
            color: #fe2c55;
            font-size: 0.85em;
            word-break: break-all;
            opacity: 0.8;
        }
        
        .no-videos {
            text-align: center;
            color: #8a8b91;
            font-size: 1.2em;
            margin-top: 50px;
        }
        
        .stats {
            text-align: center;
            color: #8a8b91;
            margin-bottom: 30px;
            font-size: 1.1em;
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
    <h1>🎥 Douyin Video Gallery</h1>
"""
    
    # Process pairs and skip failed thumbnails
    valid_pairs = []
    num_pairs = min(len(video_urls), len(entries))
    
    for i in range(num_pairs):
        video_url = video_urls[i]
        entry = entries[i]
        thumbnail_url = entry['thumbnail_url']
        title = entry['title']
        
        # Skip entries with placeholder URLs (containing "no-thumbnail.com")
        if "no-thumbnail.com" not in thumbnail_url:
            valid_pairs.append((video_url, thumbnail_url, title))
    
    if valid_pairs:
        html_content += f'    <div class="stats">Showing {len(valid_pairs)} videos with thumbnails</div>\n'
        html_content += '    <div class="gallery">\n'
        
        for i, (video_url, thumbnail_url, title) in enumerate(valid_pairs, 1):
            # Handle empty titles
            if title.strip():
                title_display = title
                title_class = ""
            else:
                title_display = f"Video #{i}"
                title_class = ' class="empty"'
            
            html_content += f'''        <div class="video-card">
            <a href="{video_url}" target="_blank" rel="noopener noreferrer">
                <img src="{thumbnail_url}" alt="{title_display}" loading="lazy">
                <div class="video-info">
                    <div class="video-title"{title_class}>{title_display}</div>
                    <div class="video-link">{video_url}</div>
                </div>
            </a>
        </div>
'''
        
        html_content += '    </div>\n'
    else:
        html_content += '    <div class="no-videos">No videos to display. Please run the complex extractor first.</div>\n'
    
    html_content += """</body>
</html>"""
    
    # Save HTML file
    gallery_file = 'gallery.html'
    with open(gallery_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Complex gallery created successfully!")
    print(f"📊 Generated gallery with {len(valid_pairs)} videos with thumbnails")
    print(f"🌐 Open '{gallery_file}' in your browser to view")
    
    # Show statistics about failed extractions
    failed_count = num_pairs - len(valid_pairs)
    if failed_count > 0:
        print(f"\n📝 Note: Skipped {failed_count} videos without thumbnails")
        print("   Videos with failed thumbnail extraction are not shown in the gallery.")
    
    # Note about mismatched total counts
    if len(video_urls) != len(entries):
        print(f"\n⚠️  Warning: Found {len(video_urls)} video URLs but {len(entries)} thumbnail entries")
        print("   This might indicate an issue with the extraction process.")
    
    return True

if __name__ == "__main__":
    generate_gallery()
