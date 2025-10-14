// Content script for AliPrice image search results page
// This script runs on the AliPrice results page to extract and compare products

(async function() {
  console.log('🚀 AliPrice Image Comparison Extension - Content Script Started');
  
  // Wait 10 seconds for page to fully load
  console.log('⏳ Waiting 10 seconds for page to load...');
  await new Promise(resolve => setTimeout(resolve, 10000));
  
  // Scroll to load more products
  console.log('📜 Scrolling to load products...');
  for (let i = 0; i < 10; i++) {
    window.scrollTo(0, document.body.scrollHeight);
    console.log(`Scroll ${i + 1}/10`);
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
  
  // Extract reference image
  console.log('🖼️  Extracting reference image...');
  const refImg = document.querySelector('.imgsearch-banner-box .imgsearch-left img');
  
  if (!refImg || !refImg.src) {
    console.error('❌ Could not find reference image!');
    alert('Error: Could not find reference image on the page.');
    return;
  }
  
  const referenceImageUrl = refImg.src;
  console.log(`✅ Reference image found: ${referenceImageUrl.substring(0, 60)}...`);
  
  // Extract product images (same selectors as watch_prices.py)
  console.log('🔍 Extracting product images...');
  const products = [];
  const productItems = document.querySelectorAll('li.image_li');
  
  console.log(`Found ${productItems.length} product items`);
  
  productItems.forEach((item, index) => {
    try {
      const link = item.querySelector('a.img-link');
      if (!link) return;
      
      const href = link.href;
      if (!href || href === '#') return;
      
      const img = link.querySelector('img');
      if (!img) return;
      
      const imgUrl = img.src || img.getAttribute('data-src');
      if (!imgUrl || imgUrl.includes('qq-kf')) return;
      
      const priceElement = item.querySelector('.item-price');
      let price = 'N/A';
      if (priceElement) {
        price = priceElement.textContent.trim();
      }
      
      products.push({
        product_url: href,
        image_url: imgUrl,
        price: price,
        index: products.length + 1
      });
    } catch (err) {
      console.error(`Error processing item ${index}:`, err);
    }
  });
  
  console.log(`✅ Extracted ${products.length} products`);
  
  if (products.length === 0) {
    console.error('❌ No products found!');
    alert('Error: No products found on the page. Please try again.');
    return;
  }
  
  // Show sample products in console
  console.log('📋 Sample products:');
  products.slice(0, 3).forEach((prod, i) => {
    console.log(`  ${i + 1}. URL: ${prod.product_url.substring(0, 60)}...`);
    console.log(`     Image: ${prod.image_url.substring(0, 60)}...`);
    console.log(`     Price: ${prod.price}`);
  });
  
  // Convert images to base64 (to avoid CORS issues)
  console.log('🔄 Converting images to base64...');
  
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
  
  // Convert reference image
  const referenceBase64 = await imageUrlToBase64(referenceImageUrl);
  console.log('✅ Reference image converted to base64');
  
  // Convert all product images
  const productsWithBase64 = [];
  for (let i = 0; i < products.length; i++) {
    try {
      const productBase64 = await imageUrlToBase64(products[i].image_url);
      productsWithBase64.push({
        ...products[i],
        image_base64: productBase64
      });
      if ((i + 1) % 10 === 0) {
        console.log(`Converted ${i + 1}/${products.length} product images...`);
      }
    } catch (error) {
      console.error(`Error converting product ${i + 1}:`, error);
    }
  }
  
  console.log(`✅ Converted ${productsWithBase64.length} product images to base64`);
  
  // Send data to background script for AI comparison
  console.log('📤 Sending data to background script for AI comparison...');
  chrome.runtime.sendMessage({
    action: 'compareImages',
    referenceImageUrl: referenceImageUrl,
    referenceBase64: referenceBase64,
    products: productsWithBase64
  });
  
  console.log('✅ Content script completed! Check background script for AI comparison progress.');
  alert(`Found ${products.length} products! Starting AI comparison... This may take a few minutes. Check the Downloads folder for the CSV when complete.`);
})();

