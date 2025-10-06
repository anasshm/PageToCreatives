#!/usr/bin/env python3
"""
Master Gallery Creator
Combines multiple HTML galleries into one master gallery with sections
"""

import os
import sys
import json
from bs4 import BeautifulSoup

def extract_gallery_data(html_file_path):
    """Extract video data from an existing HTML gallery"""
    if not os.path.exists(html_file_path):
        print(f"❌ Error: File '{html_file_path}' not found!")
        return None
    
    try:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return None
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        videos = []
        video_cards = soup.find_all('div', class_='video-card')
        
        for card in video_cards:
            # Extract video URL
            link = card.find('a')
            if not link:
                continue
            video_url = link.get('href', '')
            
            # Extract thumbnail URL
            img = card.find('img')
            if not img:
                continue
            thumbnail_url = img.get('src', '')
            
            # Extract title
            title_elem = card.find('div', class_='video-title')
            if title_elem:
                title = title_elem.get_text(strip=True)
            else:
                title = f"Video #{len(videos) + 1}"
            
            if video_url and thumbnail_url:
                videos.append({
                    'title': title,
                    'video_url': video_url,
                    'thumbnail_url': thumbnail_url
                })
        
        return videos
    
    except Exception as e:
        print(f"❌ Error parsing HTML: {e}")
        return None

def get_section_name(html_file_path):
    """Get section name from filename"""
    filename = os.path.basename(html_file_path)
    # Remove .html extension
    section_name = filename.replace('.html', '')
    return section_name

def load_master_data():
    """Load existing master gallery data"""
    master_data_file = 'master_gallery_data.json'
    if os.path.exists(master_data_file):
        try:
            with open(master_data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return []

def save_master_data(sections):
    """Save master gallery data"""
    master_data_file = 'master_gallery_data.json'
    try:
        with open(master_data_file, 'w', encoding='utf-8') as f:
            json.dump(sections, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Warning: Could not save master data: {e}")

def generate_master_gallery(sections):
    """Generate master HTML gallery"""
    
    # Count total videos
    total_videos = sum(len(section['videos']) for section in sections)
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Master Douyin Video Gallery</title>
    <style>
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
            margin-bottom: 30px;
            font-size: 2.5em;
        }}
        
        .section {{
            margin-bottom: 50px;
        }}
        
        .section-title {{
            color: #fe2c55;
            font-size: 1.8em;
            font-weight: 600;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #fe2c55;
        }}
        
        .gallery {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .video-card {{
            position: relative;
            border-radius: 12px;
            overflow: hidden;
            background-color: #161823;
            transition: transform 0.2s ease;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }}
        
        .video-card:hover {{
            transform: scale(1.05);
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
        }}
        
        .video-card a {{
            display: block;
            text-decoration: none;
        }}
        
        .video-card img {{
            width: 100%;
            height: auto;
            display: block;
            aspect-ratio: 9/16;
            object-fit: cover;
        }}
        
        .video-info {{
            padding: 12px;
            background-color: #161823;
        }}
        
        .video-title {{
            color: #ffffff;
            font-size: 1.1em;
            font-weight: 600;
            margin-bottom: 6px;
            line-height: 1.3;
            min-height: 1.3em;
        }}
        
        .video-title.empty {{
            color: #8a8b91;
            font-style: italic;
            font-weight: normal;
        }}
        
        .video-link {{
            color: #fe2c55;
            font-size: 0.85em;
            word-break: break-all;
            opacity: 0.8;
        }}
        
        .stats {{
            text-align: center;
            color: #8a8b91;
            margin-bottom: 30px;
            font-size: 1.1em;
        }}
        
        @media (max-width: 1200px) {{
            .gallery {{
                grid-template-columns: repeat(3, 1fr);
            }}
        }}
        
        @media (max-width: 900px) {{
            .gallery {{
                grid-template-columns: repeat(2, 1fr);
                gap: 15px;
            }}
        }}
        
        @media (max-width: 600px) {{
            .gallery {{
                grid-template-columns: repeat(2, 1fr);
                gap: 10px;
            }}
            
            h1 {{
                font-size: 1.8em;
            }}
            
            .section-title {{
                font-size: 1.4em;
            }}
        }}
    </style>
</head>
<body>
    <h1>🎥 Master Douyin Video Gallery</h1>
    <div class="stats">Showing {total_videos} videos across {len(sections)} sections</div>
"""
    
    # Add each section
    for section in sections:
        section_name = section['name']
        videos = section['videos']
        
        if not videos:
            continue
            
        html_content += f"""
    <div class="section">
        <h2 class="section-title">{section_name}</h2>
        <div class="gallery">
"""
        
        for video in videos:
            title = video['title']
            video_url = video['video_url']
            thumbnail_url = video['thumbnail_url']
            
            # Handle empty titles
            if title.strip():
                title_display = title
                title_class = ""
            else:
                title_display = "Untitled Video"
                title_class = ' class="empty"'
            
            html_content += f"""            <div class="video-card">
                <a href="{video_url}" target="_blank" rel="noopener noreferrer">
                    <img src="{thumbnail_url}" alt="{title_display}" loading="lazy">
                    <div class="video-info">
                        <div class="video-title"{title_class}>{title_display}</div>
                        <div class="video-link">{video_url}</div>
                    </div>
                </a>
            </div>
"""
        
        html_content += """        </div>
    </div>
"""
    
    html_content += """</body>
</html>"""
    
    # Save master gallery
    master_file = 'master_gallery.html'
    try:
        with open(master_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✅ Master gallery created: {master_file}")
        print(f"📊 Total: {total_videos} videos across {len(sections)} sections")
        return True
    except Exception as e:
        print(f"❌ Error saving master gallery: {e}")
        return False

def add_gallery_to_master():
    """Add a new gallery to the master gallery"""
    
    # Get file path from user
    if len(sys.argv) > 1:
        html_file_path = sys.argv[1]
    else:
        html_file_path = input("📁 Enter the path to the HTML gallery file to add: ").strip()
        
        # Remove quotes if user wrapped the path in quotes
        if html_file_path.startswith('"') and html_file_path.endswith('"'):
            html_file_path = html_file_path[1:-1]
        elif html_file_path.startswith("'") and html_file_path.endswith("'"):
            html_file_path = html_file_path[1:-1]
    
    if not html_file_path:
        print("❌ No file path provided!")
        return False
    
    print(f"📖 Reading gallery: {html_file_path}")
    
    # Extract data from the HTML file
    videos = extract_gallery_data(html_file_path)
    if not videos:
        print("❌ Could not extract video data from the gallery!")
        return False
    
    print(f"📊 Found {len(videos)} videos in the gallery")
    
    # Get section name
    section_name = get_section_name(html_file_path)
    print(f"📝 Section name: {section_name}")
    
    # Load existing master data
    sections = load_master_data()
    
    # Check if section already exists
    existing_section = None
    for i, section in enumerate(sections):
        if section['name'] == section_name:
            existing_section = i
            break
    
    if existing_section is not None:
        # Update existing section
        sections[existing_section]['videos'] = videos
        print(f"🔄 Updated existing section: {section_name}")
    else:
        # Add new section at the top (newest first)
        new_section = {
            'name': section_name,
            'videos': videos
        }
        sections.insert(0, new_section)
        print(f"➕ Added new section: {section_name}")
    
    # Save master data
    save_master_data(sections)
    
    # Generate master gallery
    success = generate_master_gallery(sections)
    
    if success:
        print(f"\n🎉 Master gallery updated successfully!")
        print(f"🌐 Open 'master_gallery.html' in your browser to view")
    
    return success

def main():
    """Main function"""
    print("🎨 Master Gallery Creator")
    print("=" * 50)
    
    success = add_gallery_to_master()
    
    if not success:
        print("\n💥 Failed to update master gallery!")

if __name__ == "__main__":
    main()
