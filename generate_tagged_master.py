#!/usr/bin/env python3
"""
Generate Tagged Master Gallery
Creates a master gallery HTML that displays tags for each video when available
"""

import os
import json

def load_master_data():
    """Load master gallery data with tags"""
    master_data_file = 'master_gallery_data.json'
    if os.path.exists(master_data_file):
        try:
            with open(master_data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading master data: {e}")
            return []
    else:
        print("❌ No master_gallery_data.json found. Please create a master gallery first.")
        return []

def generate_tagged_master_gallery():
    """Generate master HTML gallery with tags displayed"""
    
    # Load master gallery data with tags
    sections = load_master_data()
    if not sections:
        return False
    
    # Count total videos and tagged videos
    total_videos = 0
    tagged_videos = 0
    
    for section in sections:
        for video in section.get('videos', []):
            total_videos += 1
            if 'tags' in video and video['tags'] and 'error' not in video['tags']:
                tagged_videos += 1
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tagged Master Douyin Video Gallery</title>
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
        
        .video-tags {{
            margin: 8px 0;
            font-size: 0.85em;
        }}
        
        .tag-row {{
            margin-bottom: 4px;
            display: flex;
            align-items: center;
        }}
        
        .tag-label {{
            color: #8a8b91;
            font-weight: 500;
            min-width: 60px;
            margin-right: 8px;
        }}
        
        .tag-value {{
            color: #ffffff;
            background-color: #2a2d3a;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.9em;
        }}
        
        .tag-value.color {{
            background-color: #4a5568;
        }}
        
        .tag-value.shape {{
            background-color: #2d5a87;
        }}
        
        .tag-value.type {{
            background-color: #744c9e;
        }}
        
        .no-tags {{
            color: #8a8b91;
            font-style: italic;
            font-size: 0.8em;
            margin: 8px 0;
        }}
        
        .video-link {{
            color: #fe2c55;
            font-size: 0.75em;
            word-break: break-all;
            opacity: 0.8;
            margin-top: 8px;
        }}
        
        .stats {{
            text-align: center;
            color: #8a8b91;
            margin-bottom: 30px;
            font-size: 1.1em;
        }}
        
        .tag-stats {{
            background-color: #1a1d29;
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
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
                grid-template-columns: repeat(1, 1fr);
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
    <h1>🏷️ Tagged Master Douyin Gallery</h1>
    <div class="tag-stats">
        <strong>{tagged_videos}</strong> of <strong>{total_videos}</strong> videos have been tagged with AI
    </div>
"""
    
    # Add each section
    for section in sections:
        section_name = section['name']
        videos = section['videos']
        
        if not videos:
            continue
        
        # Count tagged videos in this section
        section_tagged = sum(1 for v in videos if 'tags' in v and v['tags'] and 'error' not in v['tags'])
        
        html_content += f"""
    <div class="section">
        <h2 class="section-title">{section_name} ({section_tagged}/{len(videos)} tagged)</h2>
        <div class="gallery">
"""
        
        for i, video in enumerate(videos, 1):
            title = video.get('title', f'Video #{i}')
            video_url = video.get('video_url', '')
            thumbnail_url = video.get('thumbnail_url', '')
            tags = video.get('tags', {})
            
            # Handle empty titles
            if title.strip():
                title_display = title
                title_class = ""
            else:
                title_display = f"Video #{i}"
                title_class = ' class="empty"'
            
            # Generate tags HTML
            tags_html = ""
            if tags and 'error' not in tags:
                if tags.get('color'):
                    tags_html += f'''
                    <div class="tag-row">
                        <span class="tag-label">Color:</span>
                        <span class="tag-value color">{tags['color']}</span>
                    </div>'''
                
                if tags.get('shape'):
                    tags_html += f'''
                    <div class="tag-row">
                        <span class="tag-label">Shape:</span>
                        <span class="tag-value shape">{tags['shape']}</span>
                    </div>'''
                
                if tags.get('jewelry_type'):
                    tags_html += f'''
                    <div class="tag-row">
                        <span class="tag-label">Type:</span>
                        <span class="tag-value type">{tags['jewelry_type']}</span>
                    </div>'''
            else:
                tags_html = '<div class="no-tags">No tags available</div>'
            
            html_content += f'''            <div class="video-card">
                <a href="{video_url}" target="_blank" rel="noopener noreferrer">
                    <img src="{thumbnail_url}" alt="{title_display}" loading="lazy">
                    <div class="video-info">
                        <div class="video-title"{title_class}>{title_display}</div>
                        <div class="video-tags">{tags_html}</div>
                        <div class="video-link">{video_url}</div>
                    </div>
                </a>
            </div>
'''
        
        html_content += """        </div>
    </div>
"""
    
    html_content += """</body>
</html>"""
    
    # Save tagged master gallery
    gallery_file = 'tagged_master_gallery.html'
    try:
        with open(gallery_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"✅ Tagged master gallery created: {gallery_file}")
        print(f"📊 Total: {total_videos} videos across {len(sections)} sections")
        print(f"🏷️ Tagged: {tagged_videos} videos have AI tags")
        print(f"🌐 Open '{gallery_file}' in your browser to view")
        return True
    except Exception as e:
        print(f"❌ Error saving tagged master gallery: {e}")
        return False

def main():
    """Main function"""
    print("🏷️ Tagged Master Gallery Generator")
    print("=" * 50)
    
    success = generate_tagged_master_gallery()
    
    if not success:
        print("\n💥 Failed to generate tagged master gallery!")

if __name__ == "__main__":
    main()

