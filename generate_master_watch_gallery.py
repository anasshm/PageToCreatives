#!/usr/bin/env python3
"""
Generate Master Watch Gallery
Creates a comprehensive HTML gallery from all tagged watch videos
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

def load_tagged_watches(json_file):
    """Load tagged watch data from JSON file"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"✓ Loaded {len(data)} watch videos")
    return data

def get_unique_values(watches):
    """Extract all unique values for each tag type"""
    unique_values = defaultdict(set)
    
    for watch in watches:
        if watch.get('tags'):
            tags = watch['tags']
            for key, value in tags.items():
                if isinstance(value, list):
                    unique_values[key].update(value)
                else:
                    unique_values[key].add(value)
    
    # Sort each set and convert to list
    return {key: sorted(list(values)) for key, values in unique_values.items()}

def generate_html(watches, output_file):
    """Generate the master HTML gallery"""
    
    # Get unique values for filters
    unique_vals = get_unique_values(watches)
    
    # Count tagged vs untagged
    tagged_count = sum(1 for w in watches if w.get('tags'))
    
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Master Watch Gallery - {len(watches)} Watches</title>
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
        
        .info-banner {{
            max-width: 1400px;
            margin: 0 auto 20px;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 12px;
            text-align: center;
        }}
        
        .info-banner strong {{
            font-size: 1.2em;
        }}
        
        .selection-bar {{
            max-width: 1400px;
            margin: 0 auto 20px;
            padding: 20px;
            background-color: #161823;
            border-radius: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }}
        
        .selection-info {{
            color: #8a8b91;
            font-size: 1.1em;
            font-weight: 600;
        }}
        
        .selection-info.active {{
            color: #4ade80;
        }}
        
        .selection-buttons {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        
        .selection-buttons button {{
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            font-size: 0.9em;
        }}
        
        .btn-select-all {{
            background-color: #667eea;
            color: white;
        }}
        
        .btn-clear {{
            background-color: #666;
            color: white;
        }}
        
        .btn-export {{
            background-color: #10b981;
            color: white;
        }}
        
        .btn-export:hover {{
            background-color: #059669;
        }}
        
        .filter-section {{
            max-width: 1400px;
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
            flex: 1;
            min-width: 200px;
        }}
        
        .filter-group label {{
            color: #8a8b91;
            font-size: 0.85em;
            font-weight: 600;
            min-width: 100px;
        }}
        
        .filter-group select {{
            flex: 1;
            padding: 6px 10px;
            background-color: #161823;
            border: 1px solid #333;
            border-radius: 4px;
            color: #ffffff;
            font-size: 0.85em;
        }}
        
        .filter-buttons {{
            display: flex;
            gap: 10px;
            justify-content: center;
            margin-top: 15px;
            flex-wrap: wrap;
        }}
        
        .filter-buttons button {{
            padding: 10px 24px;
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
        
        .filter-buttons button.nav {{
            background-color: #667eea;
        }}
        
        .filter-buttons button.nav:hover {{
            background-color: #5568d3;
        }}
        
        .filter-buttons button:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
        }}
        
        .stats {{
            text-align: center;
            color: #8a8b91;
            margin-bottom: 20px;
            font-size: 1.1em;
        }}
        
        .gallery {{
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .video-card {{
            position: relative;
            border-radius: 12px;
            overflow: hidden;
            background-color: #161823;
            transition: transform 0.2s ease, outline 0.2s ease;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            cursor: pointer;
        }}
        
        .video-card:hover {{
            transform: scale(1.03);
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
        }}
        
        .video-card.selected {{
            border: 3px solid #4ade80;
            box-shadow: 0 0 15px rgba(74, 222, 128, 0.5);
        }}
        
        .product-checkbox {{
            position: absolute;
            top: 8px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 20;
            background-color: rgba(0, 0, 0, 0.7);
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
        
        .video-stats {{
            color: #ffffff;
            font-size: 0.9em;
            margin-bottom: 8px;
        }}
        
        .video-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
            margin-bottom: 8px;
        }}
        
        .tag {{
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.65em;
            font-weight: 600;
            cursor: pointer;
            transition: opacity 0.2s ease, transform 0.1s ease;
        }}
        
        .tag:hover {{
            opacity: 0.8;
            transform: scale(1.05);
        }}
        
        .tag.case {{
            background-color: #2d5a87;
            color: #ffffff;
        }}
        
        .tag.dial {{
            background-color: #744c9e;
            color: #ffffff;
        }}
        
        .tag.strap {{
            background-color: #2a5a3e;
            color: #ffffff;
        }}
        
        .tag.no-tags {{
            background-color: #666;
            color: #fff;
            cursor: default;
        }}
        
        .tag.no-tags:hover {{
            opacity: 1;
            transform: none;
        }}
        
        .apply-all-btn {{
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.7em;
            font-weight: 600;
            cursor: pointer;
            background-color: #fe2c55;
            color: white;
            border: none;
            transition: opacity 0.2s ease, transform 0.1s ease;
            margin-left: 4px;
        }}
        
        .apply-all-btn:hover {{
            opacity: 0.8;
            transform: scale(1.05);
        }}
        
        .pagination {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
            margin-top: 40px;
            flex-wrap: wrap;
        }}
        
        .pagination button {{
            padding: 8px 16px;
            background-color: #161823;
            color: #ffffff;
            border: 1px solid #333;
            border-radius: 6px;
            cursor: pointer;
        }}
        
        .pagination button:hover:not(:disabled) {{
            background-color: #fe2c55;
            border-color: #fe2c55;
        }}
        
        .pagination button.active {{
            background-color: #fe2c55;
            border-color: #fe2c55;
        }}
        
        .pagination button:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
        }}
        
        .pagination span {{
            color: #8a8b91;
            padding: 0 10px;
        }}
        
        .no-results {{
            text-align: center;
            color: #8a8b91;
            font-size: 1.2em;
            margin-top: 50px;
        }}
        
        @media (max-width: 1400px) {{
            .gallery {{
                grid-template-columns: repeat(4, 1fr);
            }}
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
            
            .filter-row {{
                flex-direction: column;
            }}
            
            .filter-group {{
                width: 100%;
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
        }}
    </style>
</head>
<body>
    <h1>⌚ Master Watch Gallery</h1>
    <div class="subtitle">Complete collection of {len(watches):,} watch videos</div>
    
    <div class="info-banner">
        <strong>📊 {tagged_count:,} tagged watches</strong> | {len(watches) - tagged_count} untagged
    </div>
    
    <div class="selection-bar">
        <div class="selection-info">
            <span id="selectionCount">Select watches using checkboxes to export</span>
        </div>
        <div class="selection-buttons">
            <button class="btn-select-all" onclick="selectAllFiltered()">Select All on Page</button>
            <button class="btn-clear" onclick="clearSelection()">Clear Selection</button>
            <button class="btn-export" onclick="exportSelection()">📥 Export Selected</button>
        </div>
    </div>
    
    <div class="filter-section">
        <div class="filter-row">
            <div class="filter-group">
                <label>Case Shape:</label>
                <select id="caseShapeFilter">
                    <option value="">All</option>
'''
    
    # Add case shape options
    for value in unique_vals.get('case_shape', []):
        html_content += f'                    <option value="{value}">{value.title()}</option>\n'
    
    html_content += '''                </select>
            </div>
            
            <div class="filter-group">
                <label>Case Color:</label>
                <select id="caseColorFilter">
                    <option value="">All</option>
'''
    
    # Add case color options
    for value in unique_vals.get('case_color', []):
        html_content += f'                    <option value="{value}">{value.title()}</option>\n'
    
    html_content += '''                </select>
            </div>
            
            <div class="filter-group">
                <label>Dial Color:</label>
                <select id="dialColorFilter">
                    <option value="">All</option>
'''
    
    # Add dial color options
    for value in unique_vals.get('dial_color', []):
        html_content += f'                    <option value="{value}">{value.title()}</option>\n'
    
    html_content += '''                </select>
            </div>
        </div>
        
        <div class="filter-row">
            <div class="filter-group">
                <label>Dial Markers:</label>
                <select id="dialMarkersFilter">
                    <option value="">All</option>
'''
    
    # Add dial markers options
    for value in unique_vals.get('dial_markers', []):
        html_content += f'                    <option value="{value}">{value.title()}</option>\n'
    
    html_content += '''                </select>
            </div>
            
            <div class="filter-group">
                <label>Strap Type:</label>
                <select id="strapTypeFilter">
                    <option value="">All</option>
'''
    
    # Add strap type options
    for value in unique_vals.get('strap_type', []):
        html_content += f'                    <option value="{value}">{value.title()}</option>\n'
    
    html_content += '''                </select>
            </div>
            
            <div class="filter-group">
                <label>Strap Color:</label>
                <select id="strapColorFilter">
                    <option value="">All</option>
'''
    
    # Add strap color options
    for value in unique_vals.get('strap_color', []):
        html_content += f'                    <option value="{value}">{value.title()}</option>\n'
    
    html_content += '''                </select>
            </div>
        </div>
        
        <div class="filter-row">
            <div class="filter-group">
                <label>Show:</label>
                <select id="taggedFilter">
                    <option value="">All Watches</option>
                    <option value="tagged">Tagged Only</option>
                    <option value="untagged">Untagged Only</option>
                </select>
            </div>
            
            <div class="filter-group">
                <label>Min Likes:</label>
                <input type="number" id="minLikesFilter" placeholder="0" min="0" style="flex: 1; padding: 6px 10px; background-color: #161823; border: 1px solid #333; border-radius: 4px; color: #ffffff; font-size: 0.85em;">
            </div>
            
            <div class="filter-group">
                <label>Max Likes:</label>
                <input type="number" id="maxLikesFilter" placeholder="∞" min="0" style="flex: 1; padding: 6px 10px; background-color: #161823; border: 1px solid #333; border-radius: 4px; color: #ffffff; font-size: 0.85em;">
            </div>
            
            <div class="filter-group">
                <label>Sort By:</label>
                <select id="sortFilter">
                    <option value="">Default Order</option>
                    <option value="likes-desc">Most Liked</option>
                    <option value="likes-asc">Least Liked</option>
                </select>
            </div>
        </div>
        
        <div class="filter-buttons">
            <button class="nav" id="backBtn" onclick="navigateFilterHistory('back')" disabled>← Back</button>
            <button class="nav" id="forwardBtn" onclick="navigateFilterHistory('forward')" disabled>Forward →</button>
            <button class="primary" onclick="applyFilters()">Apply Filters</button>
            <button onclick="resetFilters()">Reset All</button>
        </div>
    </div>
    
    <div class="stats" id="stats">Loading...</div>
    
    <div class="gallery" id="gallery"></div>
    
    <div class="pagination" id="pagination"></div>
    
    <script>
        // Video data embedded in JavaScript
        const allVideos = '''
    
    # Add video data as JSON
    html_content += json.dumps(watches, ensure_ascii=False)
    
    html_content += ''';
        
        let currentPage = 1;
        const itemsPerPage = 100;
        let filteredVideos = [...allVideos];
        let selectedVideos = new Set();
        
        // Filter history for back/forward navigation
        let filterHistory = [];
        let historyIndex = -1;
        let isNavigating = false;
        
        // Save current filter state to history
        function saveFilterState() {
            if (isNavigating) return; // Don't save when navigating through history
            
            const state = {
                caseShape: document.getElementById('caseShapeFilter').value,
                caseColor: document.getElementById('caseColorFilter').value,
                dialColor: document.getElementById('dialColorFilter').value,
                dialMarkers: document.getElementById('dialMarkersFilter').value,
                strapType: document.getElementById('strapTypeFilter').value,
                strapColor: document.getElementById('strapColorFilter').value,
                taggedFilter: document.getElementById('taggedFilter').value,
                minLikes: document.getElementById('minLikesFilter').value,
                maxLikes: document.getElementById('maxLikesFilter').value,
                sortBy: document.getElementById('sortFilter').value
            };
            
            // If we're not at the end of history, remove future states
            if (historyIndex < filterHistory.length - 1) {
                filterHistory = filterHistory.slice(0, historyIndex + 1);
            }
            
            // Add new state
            filterHistory.push(state);
            historyIndex = filterHistory.length - 1;
            
            updateHistoryButtons();
        }
        
        // Restore filter state from history
        function restoreFilterState(state) {
            isNavigating = true;
            
            document.getElementById('caseShapeFilter').value = state.caseShape;
            document.getElementById('caseColorFilter').value = state.caseColor;
            document.getElementById('dialColorFilter').value = state.dialColor;
            document.getElementById('dialMarkersFilter').value = state.dialMarkers;
            document.getElementById('strapTypeFilter').value = state.strapType;
            document.getElementById('strapColorFilter').value = state.strapColor;
            document.getElementById('taggedFilter').value = state.taggedFilter;
            document.getElementById('minLikesFilter').value = state.minLikes;
            document.getElementById('maxLikesFilter').value = state.maxLikes;
            document.getElementById('sortFilter').value = state.sortBy;
            
            applyFilters();
            
            isNavigating = false;
        }
        
        // Navigate through filter history
        function navigateFilterHistory(direction) {
            if (direction === 'back' && historyIndex > 0) {
                historyIndex--;
                restoreFilterState(filterHistory[historyIndex]);
            } else if (direction === 'forward' && historyIndex < filterHistory.length - 1) {
                historyIndex++;
                restoreFilterState(filterHistory[historyIndex]);
            }
            updateHistoryButtons();
        }
        
        // Update back/forward button states
        function updateHistoryButtons() {
            document.getElementById('backBtn').disabled = historyIndex <= 0;
            document.getElementById('forwardBtn').disabled = historyIndex >= filterHistory.length - 1;
        }
        
        // Apply all filters
        function applyFilters() {
            const caseShape = document.getElementById('caseShapeFilter').value;
            const caseColor = document.getElementById('caseColorFilter').value;
            const dialColor = document.getElementById('dialColorFilter').value;
            const dialMarkers = document.getElementById('dialMarkersFilter').value;
            const strapType = document.getElementById('strapTypeFilter').value;
            const strapColor = document.getElementById('strapColorFilter').value;
            const taggedFilter = document.getElementById('taggedFilter').value;
            const minLikes = parseInt(document.getElementById('minLikesFilter').value) || 0;
            const maxLikes = parseInt(document.getElementById('maxLikesFilter').value) || Infinity;
            const sortBy = document.getElementById('sortFilter').value;
            
            filteredVideos = allVideos.filter(video => {
                // Filter by tagged/untagged status
                if (taggedFilter === 'tagged' && !video.tags) return false;
                if (taggedFilter === 'untagged' && video.tags) return false;
                
                // Filter by likes
                const likes = parseInt(video.likes) || 0;
                if (likes < minLikes || likes > maxLikes) return false;
                
                // If no tags and we're filtering by attributes, exclude
                if (!video.tags && (caseShape || caseColor || dialColor || dialMarkers || strapType || strapColor)) {
                    return false;
                }
                
                if (!video.tags) return true; // Pass through untagged if no attribute filters
                
                // Helper function to check if array contains value
                const hasValue = (tagArray, filterValue) => {
                    if (!filterValue) return true; // No filter applied
                    if (Array.isArray(tagArray)) {
                        return tagArray.includes(filterValue);
                    }
                    return tagArray === filterValue; // Fallback for non-array tags
                };
                
                // Apply each filter (AND logic - all must match)
                if (!hasValue(video.tags.case_shape, caseShape)) return false;
                if (!hasValue(video.tags.case_color, caseColor)) return false;
                if (!hasValue(video.tags.dial_color, dialColor)) return false;
                if (!hasValue(video.tags.dial_markers, dialMarkers)) return false;
                if (!hasValue(video.tags.strap_type, strapType)) return false;
                if (!hasValue(video.tags.strap_color, strapColor)) return false;
                
                return true;
            });
            
            // Apply sorting
            if (sortBy === 'likes-desc') {
                filteredVideos.sort((a, b) => (parseInt(b.likes) || 0) - (parseInt(a.likes) || 0));
            } else if (sortBy === 'likes-asc') {
                filteredVideos.sort((a, b) => (parseInt(a.likes) || 0) - (parseInt(b.likes) || 0));
            }
            
            // Save to history (only if not navigating)
            if (!isNavigating) {
                saveFilterState();
            }
            
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
            document.getElementById('taggedFilter').value = '';
            document.getElementById('minLikesFilter').value = '';
            document.getElementById('maxLikesFilter').value = '';
            document.getElementById('sortFilter').value = '';
            
            filteredVideos = [...allVideos];
            currentPage = 1;
            
            // Save reset state to history
            saveFilterState();
            
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
                `Showing ${startIdx + 1}-${Math.min(endIdx, filteredVideos.length)} of ${filteredVideos.length.toLocaleString()} watches (Page ${currentPage}/${totalPages || 1})`;
            
            // Render gallery
            const gallery = document.getElementById('gallery');
            
            if (pageVideos.length === 0) {
                gallery.innerHTML = '<div class="no-results">No watches match your filters. Try adjusting the selections.</div>';
            } else {
                gallery.innerHTML = pageVideos.map(video => {
                    const tags = video.tags || {};
                    let tagsHTML = '';
                    
                    // Helper to format tag arrays with click handlers
                    const formatTags = (tagArray, className, filterType) => {
                        if (!tagArray) return '';
                        const arr = Array.isArray(tagArray) ? tagArray : [tagArray];
                        return arr.map(t => 
                            `<span class="tag ${className}" 
                                   onclick="event.preventDefault(); event.stopPropagation(); applyTagFilter('${filterType}', '${t}')" 
                                   title="Click to filter by ${t}">${t}</span>`
                        ).join('');
                    };
                    
                    if (video.tags) {
                        tagsHTML += formatTags(tags.case_shape, 'case', 'case_shape');
                        tagsHTML += formatTags(tags.case_color, 'case', 'case_color');
                        tagsHTML += formatTags(tags.dial_color, 'dial', 'dial_color');
                        tagsHTML += formatTags(tags.dial_markers, 'dial', 'dial_markers');
                        tagsHTML += formatTags(tags.strap_type, 'strap', 'strap_type');
                        tagsHTML += formatTags(tags.strap_color, 'strap', 'strap_color');
                        
                        // Add "Apply All" button
                        const tagsJSON = JSON.stringify(tags).replace(/"/g, '&quot;');
                        tagsHTML += `<button class="apply-all-btn" 
                                            onclick="event.preventDefault(); event.stopPropagation(); applyAllTags(${tagsJSON})" 
                                            title="Apply all filters from this watch">Apply All</button>`;
                    } else {
                        tagsHTML = '<span class="tag no-tags">No tags</span>';
                    }
                    
                    const isSelected = selectedVideos.has(video.video_url);
                    const videoIndex = allVideos.findIndex(v => v.video_url === video.video_url);
                    
                    return `
                        <div class="video-card ${isSelected ? 'selected' : ''}" 
                             data-video-url="${video.video_url}">
                            <div class="product-checkbox">
                                <input type="checkbox" 
                                       id="checkbox-${videoIndex}" 
                                       onchange="toggleSelection(${videoIndex})"
                                       ${isSelected ? 'checked' : ''}>
                            </div>
                            <a href="${video.video_url}" target="_blank" rel="noopener noreferrer">
                                <img src="${video.thumbnail_url}" alt="Watch" loading="lazy">
                                <div class="video-info">
                                    <div class="video-stats">❤️ ${video.likes || '0'} | #${video.index || ''}</div>
                                    <div class="video-tags">${tagsHTML}</div>
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
        
        // Apply filter from tag click
        function applyTagFilter(filterType, value) {
            // Map tag types to filter IDs
            const filterMap = {
                'case_shape': 'caseShapeFilter',
                'case_color': 'caseColorFilter',
                'dial_color': 'dialColorFilter',
                'dial_markers': 'dialMarkersFilter',
                'strap_type': 'strapTypeFilter',
                'strap_color': 'strapColorFilter'
            };
            
            const filterId = filterMap[filterType];
            if (filterId) {
                document.getElementById(filterId).value = value;
                applyFilters();
                
                // Scroll to top to see filtered results
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        }
        
        // Apply all tags from a video
        function applyAllTags(tags) {
            // Map tag types to filter IDs
            const filterMap = {
                'case_shape': 'caseShapeFilter',
                'case_color': 'caseColorFilter',
                'dial_color': 'dialColorFilter',
                'dial_markers': 'dialMarkersFilter',
                'strap_type': 'strapTypeFilter',
                'strap_color': 'strapColorFilter'
            };
            
            // Apply first value for each tag type (if array, take first item)
            Object.keys(filterMap).forEach(tagType => {
                const tagValue = tags[tagType];
                const filterId = filterMap[tagType];
                
                if (tagValue && filterId) {
                    const value = Array.isArray(tagValue) ? tagValue[0] : tagValue;
                    document.getElementById(filterId).value = value;
                }
            });
            
            applyFilters();
            
            // Scroll to top to see filtered results
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
        
        // Toggle video selection
        function toggleSelection(videoIndex) {
            const video = allVideos[videoIndex];
            const checkbox = document.getElementById('checkbox-' + videoIndex);
            const isChecked = checkbox.checked;
            
            if (isChecked) {
                selectedVideos.add(video.video_url);
            } else {
                selectedVideos.delete(video.video_url);
            }
            updateSelectionUI();
        }
        
        // Select all filtered videos on current page
        function selectAllFiltered() {
            const startIdx = (currentPage - 1) * itemsPerPage;
            const endIdx = startIdx + itemsPerPage;
            const pageVideos = filteredVideos.slice(startIdx, endIdx);
            
            pageVideos.forEach(video => {
                selectedVideos.add(video.video_url);
                // Find and check the checkbox
                const videoIndex = allVideos.findIndex(v => v.video_url === video.video_url);
                const checkbox = document.getElementById('checkbox-' + videoIndex);
                if (checkbox) {
                    checkbox.checked = true;
                }
            });
            updateSelectionUI();
        }
        
        // Clear selection
        function clearSelection() {
            selectedVideos.clear();
            // Uncheck all checkboxes
            document.querySelectorAll('input[type="checkbox"]').forEach(cb => {
                cb.checked = false;
            });
            updateSelectionUI();
        }
        
        // Update selection UI
        function updateSelectionUI() {
            const count = selectedVideos.size;
            const info = document.getElementById('selectionCount');
            
            // Update count and styling
            if (count > 0) {
                info.textContent = `${count} watch${count !== 1 ? 'es' : ''} selected`;
                info.classList.add('active');
            } else {
                info.textContent = 'Select watches using checkboxes to export';
                info.classList.remove('active');
            }
            
            // Update cards
            document.querySelectorAll('.video-card').forEach(card => {
                const videoUrl = card.dataset.videoUrl;
                if (selectedVideos.has(videoUrl)) {
                    card.classList.add('selected');
                } else {
                    card.classList.remove('selected');
                }
            });
        }
        
        // Export selected videos
        function exportSelection() {
            if (selectedVideos.size === 0) {
                alert('No watches selected! Please select at least one watch to export.');
                return;
            }
            
            // Get selected video data
            const selectedData = allVideos.filter(v => selectedVideos.has(v.video_url));
            
            // Create CSV content
            let csvContent = "Image URL,Video URL,Likes\\n";
            selectedData.forEach(video => {
                const imageUrl = video.thumbnail_url || '';
                const videoUrl = video.video_url || '';
                const likes = video.likes || '0';
                
                // Escape commas and quotes in URLs
                const escapeCSV = (str) => {
                    if (str.includes(',') || str.includes('"') || str.includes('\\n')) {
                        return '"' + str.replace(/"/g, '""') + '"';
                    }
                    return str;
                };
                
                csvContent += `${escapeCSV(imageUrl)},${escapeCSV(videoUrl)},${likes}\\n`;
            });
            
            // Create download link
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);
            
            const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '');
            link.setAttribute('href', url);
            link.setAttribute('download', `selected_watches_${timestamp}.csv`);
            link.style.visibility = 'hidden';
            
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            console.log(`Exported ${selectedVideos.size} watches`);
        }
        
        // Initial render
        renderGallery();
    </script>
</body>
</html>'''
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✓ Gallery saved to: {output_file}")
    print(f"✓ Total videos: {len(watches):,}")
    print(f"✓ Tagged: {tagged_count:,}")
    print(f"✓ Untagged: {len(watches) - tagged_count:,}")

def main():
    # File paths
    json_file = Path("Watch Pages_tagged.json")
    output_file = Path("master_watch_gallery_18k.html")
    
    if not json_file.exists():
        print(f"❌ Error: {json_file} not found!")
        sys.exit(1)
    
    print(f"🔨 Generating Master Watch Gallery...")
    print(f"📂 Input: {json_file}")
    print(f"📄 Output: {output_file}")
    print()
    
    # Load data
    watches = load_tagged_watches(json_file)
    
    # Generate HTML
    generate_html(watches, output_file)
    
    print()
    print(f"✅ Done! Open {output_file} in your browser to view the gallery.")
    print(f"📊 The gallery includes:")
    print(f"   • All {len(watches):,} watch videos")
    print(f"   • Advanced filtering by attributes")
    print(f"   • Filter by tagged/untagged status")
    print(f"   • Pagination (100 items per page)")

if __name__ == "__main__":
    main()

