#!/usr/bin/env python3
"""
Debug Watch Database Viewer
Generates an interactive HTML viewer to inspect watch deduplication results
"""

import json
import os
from collections import defaultdict
from datetime import datetime

def load_database():
    """Load the watch database"""
    db_file = 'processed_watches_db.json'
    
    if not os.path.exists(db_file):
        print(f"❌ Database file not found: {db_file}")
        print("   Run douyin_watch_scraper.py first to create the database.")
        return None
    
    try:
        with open(db_file, 'r', encoding='utf-8') as f:
            db = json.load(f)
        
        print(f"✅ Loaded database:")
        print(f"   Phashes: {len(db.get('phashes', {}))}")
        print(f"   Fingerprints: {len(db.get('fingerprints', {}))}")
        print(f"   AI Verifications: {len(db.get('ai_verifications', {}))}")
        return db
    except Exception as e:
        print(f"❌ Error loading database: {e}")
        return None

def analyze_database(db):
    """Analyze database and prepare data for HTML viewer"""
    
    # Prepare fingerprint groups (with multiple watches)
    fingerprint_groups = []
    for fingerprint, data in db.get('fingerprints', {}).items():
        if data.get('count', 1) > 1:
            # Find all watches with this fingerprint
            watches = []
            
            # Primary watch (first seen)
            watches.append({
                'thumbnail_url': data['thumbnail_url'],
                'first_seen': data['first_seen'],
                'is_primary': True
            })
            
            # Find watches that were verified against this fingerprint
            for video_url, verification in db.get('ai_verifications', {}).items():
                if verification.get('fingerprint') == fingerprint:
                    watches.append({
                        'video_url': video_url,
                        'thumbnail_url': verification.get('original_url'),  # This is the thumbnail being compared
                        'ai_decision': verification.get('ai_decision'),
                        'timestamp': verification.get('timestamp'),
                        'is_primary': False
                    })
            
            fingerprint_groups.append({
                'fingerprint': fingerprint,
                'attributes': parse_fingerprint(fingerprint),
                'count': len(watches),
                'watches': watches
            })
    
    # Sort by count (most watches first)
    fingerprint_groups.sort(key=lambda x: x['count'], reverse=True)
    
    # Prepare phash groups (with multiple URLs)
    phash_groups = []
    for phash, urls in db.get('phashes', {}).items():
        if isinstance(urls, list) and len(urls) > 1:
            phash_groups.append({
                'phash': phash,
                'count': len(urls),
                'urls': urls
            })
    
    # Sort by count (most duplicates first)
    phash_groups.sort(key=lambda x: x['count'], reverse=True)
    
    # AI verification summary
    ai_summary = {
        'total': len(db.get('ai_verifications', {})),
        'match': 0,
        'no_match': 0,
        'errors': 0
    }
    
    for verification in db.get('ai_verifications', {}).values():
        decision = verification.get('ai_decision', '').upper()
        if decision == 'MATCH':
            ai_summary['match'] += 1
        elif decision == 'NO':
            ai_summary['no_match'] += 1
        else:
            ai_summary['errors'] += 1
    
    return {
        'fingerprint_groups': fingerprint_groups,
        'phash_groups': phash_groups,
        'ai_summary': ai_summary,
        'stats': {
            'total_fingerprints': len(db.get('fingerprints', {})),
            'multi_watch_fingerprints': len(fingerprint_groups),
            'total_phashes': len(db.get('phashes', {})),
            'multi_url_phashes': len(phash_groups)
        }
    }

def parse_fingerprint(fingerprint_str):
    """Parse fingerprint string into attribute dict"""
    try:
        parts = fingerprint_str.split('|')
        
        # New format (7 parts - no brand)
        if len(parts) == 7:
            return {
                'case_shape': parts[0],
                'case_color': parts[1],
                'dial_color': parts[2],
                'dial_markers': parts[3],
                'dial_markers_color': parts[4],
                'strap_type': parts[5],
                'strap_color': parts[6]
            }
        # Old format (8 parts - with brand)
        elif len(parts) == 8:
            return {
                'brand': parts[0],
                'case_shape': parts[1],
                'case_color': parts[2],
                'dial_color': parts[3],
                'dial_markers': parts[4],
                'dial_markers_color': parts[5],
                'strap_type': parts[6],
                'strap_color': parts[7]
            }
    except:
        pass
    return {'raw': fingerprint_str}

def generate_html(analysis):
    """Generate HTML debug viewer"""
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Watch Deduplication Debug Viewer</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            padding: 20px;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
        }}
        
        .header h1 {{
            font-size: 28px;
            margin-bottom: 10px;
        }}
        
        .header p {{
            opacity: 0.9;
            font-size: 14px;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f9f9f9;
            border-bottom: 1px solid #e0e0e0;
        }}
        
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        
        .stat-card .label {{
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}
        
        .stat-card .value {{
            font-size: 32px;
            font-weight: bold;
            color: #333;
        }}
        
        .stat-card.highlight {{
            background: #667eea;
            color: white;
        }}
        
        .stat-card.highlight .label {{
            color: rgba(255,255,255,0.8);
        }}
        
        .stat-card.highlight .value {{
            color: white;
        }}
        
        .content {{
            padding: 30px;
        }}
        
        .section {{
            margin-bottom: 40px;
        }}
        
        .section-header {{
            display: flex;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }}
        
        .section-header h2 {{
            font-size: 24px;
            color: #333;
        }}
        
        .section-header .count {{
            margin-left: auto;
            background: #667eea;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 14px;
        }}
        
        .fingerprint-group {{
            background: #f9f9f9;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        
        .fingerprint-header {{
            display: flex;
            align-items: start;
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 1px solid #e0e0e0;
        }}
        
        .fingerprint-info {{
            flex: 1;
        }}
        
        .fingerprint-id {{
            font-family: 'Courier New', monospace;
            font-size: 13px;
            color: #666;
            background: white;
            padding: 8px 12px;
            border-radius: 4px;
            margin-bottom: 10px;
            display: inline-block;
        }}
        
        .attributes {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 8px;
            margin-top: 10px;
        }}
        
        .attribute {{
            font-size: 12px;
            background: white;
            padding: 6px 10px;
            border-radius: 4px;
        }}
        
        .attribute .key {{
            color: #666;
            font-weight: 500;
        }}
        
        .attribute .val {{
            color: #333;
        }}
        
        .watch-count-badge {{
            background: #ffc107;
            color: #000;
            padding: 6px 14px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 14px;
        }}
        
        .watches-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 15px;
        }}
        
        .watch-card {{
            background: white;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            overflow: hidden;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .watch-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        
        .watch-card.primary {{
            border-color: #667eea;
            background: #f0f4ff;
        }}
        
        .watch-card.ai-no {{
            border-color: #4caf50;
            background: #f1f8f4;
        }}
        
        .watch-card.ai-match {{
            border-color: #f44336;
            background: #fff5f5;
        }}
        
        .watch-card.ai-error {{
            border-color: #ff9800;
            background: #fff8f0;
        }}
        
        .watch-image {{
            width: 100%;
            height: 200px;
            object-fit: cover;
            background: #f0f0f0;
        }}
        
        .watch-info {{
            padding: 12px;
        }}
        
        .watch-label {{
            font-size: 11px;
            color: #666;
            margin-bottom: 4px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .watch-url {{
            font-size: 12px;
            color: #667eea;
            word-break: break-all;
            margin-bottom: 8px;
        }}
        
        .watch-url a {{
            color: #667eea;
            text-decoration: none;
        }}
        
        .watch-url a:hover {{
            text-decoration: underline;
        }}
        
        .ai-badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .ai-badge.match {{
            background: #f44336;
            color: white;
        }}
        
        .ai-badge.no {{
            background: #4caf50;
            color: white;
        }}
        
        .ai-badge.error {{
            background: #ff9800;
            color: white;
        }}
        
        .ai-badge.primary {{
            background: #667eea;
            color: white;
        }}
        
        .phash-group {{
            background: #fff8f0;
            border: 1px solid #ff9800;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
        }}
        
        .phash-header {{
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }}
        
        .phash-id {{
            font-family: 'Courier New', monospace;
            font-size: 12px;
            color: #666;
            flex: 1;
        }}
        
        .phash-count {{
            background: #ff9800;
            color: white;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
        }}
        
        .phash-urls {{
            display: flex;
            flex-direction: column;
            gap: 6px;
        }}
        
        .phash-url {{
            font-size: 12px;
            color: #667eea;
            word-break: break-all;
            padding: 6px;
            background: white;
            border-radius: 4px;
        }}
        
        .phash-url a {{
            color: #667eea;
            text-decoration: none;
        }}
        
        .phash-url a:hover {{
            text-decoration: underline;
        }}
        
        .empty-state {{
            text-align: center;
            padding: 60px 20px;
            color: #999;
        }}
        
        .empty-state-icon {{
            font-size: 48px;
            margin-bottom: 16px;
        }}
        
        .filter-controls {{
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        
        .filter-btn {{
            padding: 8px 16px;
            border: 2px solid #667eea;
            background: white;
            color: #667eea;
            border-radius: 20px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s;
        }}
        
        .filter-btn:hover {{
            background: #667eea;
            color: white;
        }}
        
        .filter-btn.active {{
            background: #667eea;
            color: white;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Watch Deduplication Debug Viewer</h1>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="label">Total Fingerprints</div>
                <div class="value">{analysis['stats']['total_fingerprints']}</div>
            </div>
            <div class="stat-card highlight">
                <div class="label">Multi-Watch Fingerprints</div>
                <div class="value">{analysis['stats']['multi_watch_fingerprints']}</div>
            </div>
            <div class="stat-card">
                <div class="label">Total Phashes</div>
                <div class="value">{analysis['stats']['total_phashes']}</div>
            </div>
            <div class="stat-card">
                <div class="label">Multi-URL Phashes</div>
                <div class="value">{analysis['stats']['multi_url_phashes']}</div>
            </div>
            <div class="stat-card">
                <div class="label">AI Verifications</div>
                <div class="value">{analysis['ai_summary']['total']}</div>
            </div>
            <div class="stat-card">
                <div class="label">AI: Match</div>
                <div class="value">{analysis['ai_summary']['match']}</div>
            </div>
            <div class="stat-card">
                <div class="label">AI: Different</div>
                <div class="value">{analysis['ai_summary']['no_match']}</div>
            </div>
            <div class="stat-card">
                <div class="label">AI: Errors</div>
                <div class="value">{analysis['ai_summary']['errors']}</div>
            </div>
        </div>
        
        <div class="content">
"""
    
    # Fingerprint groups section
    html += f"""
            <div class="section">
                <div class="section-header">
                    <h2>📍 Fingerprint Groups (Same Attributes)</h2>
                    <span class="count">{len(analysis['fingerprint_groups'])} groups</span>
                </div>
"""
    
    if analysis['fingerprint_groups']:
        for group in analysis['fingerprint_groups']:
            attrs = group['attributes']
            html += f"""
                <div class="fingerprint-group">
                    <div class="fingerprint-header">
                        <div class="fingerprint-info">
                            <div class="fingerprint-id">{group['fingerprint']}</div>
                            <div class="attributes">
"""
            
            for key, val in attrs.items():
                html += f"""
                                <div class="attribute">
                                    <span class="key">{key}:</span>
                                    <span class="val">{val}</span>
                                </div>
"""
            
            html += f"""
                            </div>
                        </div>
                        <span class="watch-count-badge">{group['count']} watches</span>
                    </div>
                    
                    <div class="watches-grid">
"""
            
            for watch in group['watches']:
                card_class = 'watch-card'
                badge_html = ''
                
                if watch.get('is_primary'):
                    card_class += ' primary'
                    badge_html = '<span class="ai-badge primary">Original</span>'
                else:
                    decision = watch.get('ai_decision', '').upper()
                    if decision == 'MATCH':
                        card_class += ' ai-match'
                        badge_html = '<span class="ai-badge match">AI: Duplicate</span>'
                    elif decision == 'NO':
                        card_class += ' ai-no'
                        badge_html = '<span class="ai-badge no">AI: Different</span>'
                    else:
                        card_class += ' ai-error'
                        badge_html = f'<span class="ai-badge error">{decision[:20]}</span>'
                
                video_url = watch.get('video_url', '')
                thumbnail_url = watch.get('thumbnail_url', '')
                
                html += f"""
                        <div class="{card_class}">
                            <img src="{thumbnail_url}" alt="Watch" class="watch-image" onerror="this.style.display='none'">
                            <div class="watch-info">
                                {badge_html}
"""
                
                if video_url:
                    html += f"""
                                <div class="watch-label">Video URL:</div>
                                <div class="watch-url"><a href="{video_url}" target="_blank">{video_url[:60]}...</a></div>
"""
                
                if watch.get('timestamp'):
                    html += f"""
                                <div class="watch-label">Verified: {watch['timestamp']}</div>
"""
                
                html += """
                            </div>
                        </div>
"""
            
            html += """
                    </div>
                </div>
"""
    else:
        html += """
                <div class="empty-state">
                    <div class="empty-state-icon">✅</div>
                    <div>No fingerprint collisions found</div>
                </div>
"""
    
    html += """
            </div>
"""
    
    # Phash groups section
    html += f"""
            <div class="section">
                <div class="section-header">
                    <h2>🔍 Phash Groups (Visual Duplicates)</h2>
                    <span class="count">{len(analysis['phash_groups'])} groups</span>
                </div>
"""
    
    if analysis['phash_groups']:
        for group in analysis['phash_groups']:
            html += f"""
                <div class="phash-group">
                    <div class="phash-header">
                        <div class="phash-id">Phash: {group['phash']}</div>
                        <span class="phash-count">{group['count']} duplicates</span>
                    </div>
                    <div class="phash-urls">
"""
            
            for url in group['urls']:
                html += f"""
                        <div class="phash-url">
                            <a href="{url}" target="_blank">{url}</a>
                        </div>
"""
            
            html += """
                    </div>
                </div>
"""
    else:
        html += """
                <div class="empty-state">
                    <div class="empty-state-icon">✅</div>
                    <div>No phash duplicates found</div>
                </div>
"""
    
    html += """
            </div>
        </div>
    </div>
</body>
</html>
"""
    
    return html

def main():
    """Main entry point"""
    print("🔍 Watch Database Debug Viewer")
    print("=" * 50)
    
    # Load database
    db = load_database()
    if not db:
        return False
    
    print("\n📊 Analyzing database...")
    analysis = analyze_database(db)
    
    print(f"\n📈 Analysis Results:")
    print(f"   Multi-watch fingerprints: {analysis['stats']['multi_watch_fingerprints']}")
    print(f"   Multi-URL phashes: {analysis['stats']['multi_url_phashes']}")
    print(f"   AI verifications: {analysis['ai_summary']['total']}")
    print(f"     - Confirmed duplicates: {analysis['ai_summary']['match']}")
    print(f"     - Different watches: {analysis['ai_summary']['no_match']}")
    print(f"     - Errors: {analysis['ai_summary']['errors']}")
    
    # Generate HTML
    print("\n🎨 Generating HTML viewer...")
    html = generate_html(analysis)
    
    # Save HTML file
    output_file = 'watch_debug_viewer.html'
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"\n✅ Debug viewer created: {output_file}")
        print(f"   Open this file in your browser to view results")
        
        # Try to open in browser
        try:
            import webbrowser
            abs_path = os.path.abspath(output_file)
            webbrowser.open(f'file://{abs_path}')
            print(f"   🌐 Opening in browser...")
        except:
            pass
        
        return True
    except Exception as e:
        print(f"\n❌ Error saving HTML: {e}")
        return False

if __name__ == "__main__":
    main()

