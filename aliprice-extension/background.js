// Gemini API Configuration
const GEMINI_API_KEY = 'AIzaSyBBPy4HW6-TFeC6jm8ZV4W5bvsqMB_AVoU';
const GEMINI_MODEL = 'gemini-2.5-flash-preview-09-2025';

// Create the context menu item when the extension is installed
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "searchAliPrice",
    title: "Search on AliPrice",
    contexts: ["image"]
  });
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "searchAliPrice" && info.srcUrl) {
    // URL-encode the image URL
    const encodedUrl = encodeURIComponent(info.srcUrl);
    // Create the AliPrice search URL
    const searchUrl = `https://www.aliprice.com/Index/searchByImage.html?image=${encodedUrl}`;
    
    // Open in new tab and inject content script when ready
    chrome.tabs.create({ url: searchUrl }, (newTab) => {
      // Wait for page load, then inject content script
      chrome.tabs.onUpdated.addListener(function listener(tabId, info) {
        if (tabId === newTab.id && info.status === 'complete') {
          chrome.tabs.onUpdated.removeListener(listener);
          chrome.scripting.executeScript({
            target: { tabId: newTab.id },
            files: ['content.js']
          });
        }
      });
    });
  }
});

// Convert image URL to base64
async function imageUrlToBase64(url) {
  const response = await fetch(url);
  const blob = await response.blob();
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const base64 = reader.result.split(',')[1];
      resolve(base64);
    };
    reader.readAsDataURL(blob);
  });
}

// Compare images using Gemini API
async function compareWithGemini(referenceBase64, productBase64) {
  const prompt = `Compare these two watches using SEPARATE scores for each attribute.

FIRST image = Reference watch
SECOND image = Product from search results

IGNORE brand names completely - they don't matter at all.

Score each attribute from 0-100:

1. SHAPE (overall watch shape, case shape, proportions, size appearance):
   - 90-100: Nearly identical shape
   - 70-89: Very similar shape with minor differences
   - 50-69: Same general category but noticeable shape differences
   - 30-49: Different shapes but still recognizable as similar type
   - 0-29: Very different shapes

2. STRAP (strap/band type, style, texture, width):
   - 90-100: Nearly identical strap type and style
   - 70-89: Same strap type with minor style differences
   - 50-69: Similar strap type but different styling
   - 30-49: Different strap types (e.g., metal vs leather)
   - 0-29: Completely different strap types

3. DIAL (dial design, markers/numbers type, hands style, layout):
   - 90-100: Nearly identical dial design and markers
   - 70-89: Very similar dial with minor differences in markers
   - 50-69: Similar dial style but different marker types (e.g., arabic vs roman)
   - 30-49: Different dial designs but recognizable similarity
   - 0-29: Completely different dial designs

4. COLOR (overall color scheme - this is LEAST important, shade differences are OK):
   - 90-100: Nearly identical colors
   - 70-89: Same color family (e.g., both gold, both silver)
   - 50-69: Different shades but harmonious (e.g., tan vs brown)
   - 30-49: Different color categories but not clashing
   - 0-29: Completely different color schemes

Answer in this EXACT format (four lines, numbers only):
SHAPE: [0-100]
STRAP: [0-100]
DIAL: [0-100]
COLOR: [0-100]`;

  try {
    const response = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/${GEMINI_MODEL}:generateContent?key=${GEMINI_API_KEY}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents: [{
            parts: [
              { text: prompt },
              { inline_data: { mime_type: 'image/jpeg', data: referenceBase64 } },
              { inline_data: { mime_type: 'image/jpeg', data: productBase64 } }
            ]
          }]
        })
      }
    );
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`Gemini API HTTP Error ${response.status}:`, errorText);
      throw new Error(`HTTP ${response.status}: ${errorText.substring(0, 200)}`);
    }
    
    const data = await response.json();
    
    if (!data.candidates || !data.candidates[0] || !data.candidates[0].content) {
      console.error('Unexpected Gemini API response:', data);
      throw new Error('Invalid API response structure');
    }
    
    const text = data.candidates[0].content.parts[0].text;
    
    // Parse scores (same logic as Python script)
    const scores = {};
    text.split('\n').forEach(line => {
      if (line.includes(':')) {
        const [key, value] = line.split(':');
        const match = value.match(/\d+/);
        if (match) {
          const scoreKey = key.trim().toUpperCase();
          if (['SHAPE', 'STRAP', 'DIAL', 'COLOR'].includes(scoreKey)) {
            scores[scoreKey] = parseInt(match[0]);
          }
        }
      }
    });
    
    // Calculate weighted score (Shape 35%, Strap 25%, Dial 25%, Color 15%)
    const finalScore = (
      scores.SHAPE * 0.35 +
      scores.STRAP * 0.25 +
      scores.DIAL * 0.25 +
      scores.COLOR * 0.15
    ).toFixed(1);
    
    return {
      final_score: parseFloat(finalScore),
      shape: scores.SHAPE,
      strap: scores.STRAP,
      dial: scores.DIAL,
      color: scores.COLOR
    };
  } catch (error) {
    console.error('Gemini API error:', error);
    return {
      final_score: 0,
      shape: 0,
      strap: 0,
      dial: 0,
      color: 0,
      error: error.message
    };
  }
}

// Generate and download CSV
function generateAndDownloadCSV(referenceUrl, results) {
  // CSV header
  let csv = 'reference_image_url,product_number,final_score,shape_score,strap_score,dial_score,color_score,price,1688_url,1688_product_image_url\n';
  
  // Add each result
  results.forEach(result => {
    csv += `${referenceUrl},${result.index},${result.final_score},${result.shape},${result.strap},${result.dial},${result.color},"${result.price}",${result.product_url},${result.image_url}\n`;
  });
  
  // Convert CSV to data URL (works in service workers)
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
  const dataUrl = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv);
  
  chrome.downloads.download({
    url: dataUrl,
    filename: `aliprice_comparison_${timestamp}.csv`,
    saveAs: true
  }, (downloadId) => {
    if (chrome.runtime.lastError) {
      console.error('Download error:', chrome.runtime.lastError);
    } else {
      console.log('✅ CSV download started with ID:', downloadId);
    }
  });
}

// Handle messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('📨 Message received in background script:', request.action);
  if (request.action === 'compareImages') {
    console.log(`📦 Data received: ${request.products.length} products`);
    // Process async without waiting for response
    processComparison(request.referenceImageUrl, request.referenceBase64, request.products);
    // Don't return true - we're not sending a response
  }
});

async function processComparison(referenceImageUrl, referenceBase64, products) {
  console.log(`🚀 Starting AI comparison for ${products.length} products with parallel processing...`);
  
  const results = [];
  const batchSize = 50;
  const maxWorkers = 25;
  const totalBatches = Math.ceil(products.length / batchSize);
  
  for (let batchNum = 0; batchNum < totalBatches; batchNum++) {
    const startIdx = batchNum * batchSize;
    const endIdx = Math.min(startIdx + batchSize, products.length);
    const batch = products.slice(startIdx, endIdx);
    
    console.log(`\n📦 Processing batch ${batchNum + 1}/${totalBatches} (${batch.length} products)`);
    console.log(`   Products ${startIdx + 1}-${endIdx} of ${products.length}`);
    
    // Process batch in parallel with max 25 concurrent requests
    const batchPromises = batch.map(async (product, i) => {
      const productNum = startIdx + i + 1;
      try {
        const scoreData = await compareWithGemini(referenceBase64, product.image_base64);
        console.log(`  ✅ Product ${productNum}: Score ${scoreData.final_score} (Shape: ${scoreData.shape}, Strap: ${scoreData.strap}, Dial: ${scoreData.dial}, Color: ${scoreData.color})`);
        return {
          index: product.index,
          product_url: product.product_url,
          image_url: product.image_url,
          price: product.price,
          ...scoreData
        };
      } catch (error) {
        console.error(`  ❌ Error processing product ${productNum}:`, error);
        return {
          index: product.index,
          product_url: product.product_url,
          image_url: product.image_url,
          price: product.price,
          final_score: 0,
          shape: 0,
          strap: 0,
          dial: 0,
          color: 0,
          error: error.message
        };
      }
    });
    
    // Wait for all products in this batch to complete
    const batchResults = await Promise.all(batchPromises);
    results.push(...batchResults);
    
    console.log(`   ✅ Batch complete: ${batchResults.length} products scored`);
    
    // Small delay between batches
    if (batchNum < totalBatches - 1) {
      await new Promise(resolve => setTimeout(resolve, 500));
    }
  }
  
  // Generate and download CSV
  console.log('\n📊 Generating CSV...');
  generateAndDownloadCSV(referenceImageUrl, results);
  console.log('✅ Done! CSV should be downloading...');
}

