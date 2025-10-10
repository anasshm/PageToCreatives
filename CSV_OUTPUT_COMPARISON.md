# CSV Output Comparison

## Before (Old watch_prices.py)
```csv
reference_image_url,1688_url,1688_product_image_url,price,similarity_score
https://example.com/watch1.jpg,https://1688.com/product-x,https://1688.com/img-x.jpg,¥89,95
```

**Only 1 result:** The most similar product

---

## After (New watch_prices.py)
```csv
reference_image_url,best_match_url,best_match_image_url,best_match_price,best_match_similarity,cheapest_90plus_url,cheapest_90plus_image_url,cheapest_90plus_price,cheapest_90plus_similarity
https://example.com/watch1.jpg,https://1688.com/product-x,https://1688.com/img-x.jpg,¥89,95,https://1688.com/product-y,https://1688.com/img-y.jpg,¥44,92
```

**2 results in one row:**
- **Best Match:** Most similar (Score: 95, Price: ¥89)
- **Cheapest 90%+:** Best value (Score: 92, Price: ¥44)

---

## Benefits
✅ **Compare options**: See the highest quality match vs best value match
✅ **Save money**: Identify cheaper alternatives that still meet quality threshold
✅ **Better decisions**: Choose based on your priority (similarity or price)
✅ **Improved accuracy**: New AI prompt ignores irrelevant differences (color shades, brand names)

---

## Example Decision Making

### Scenario 1: Reference watch = ¥200 luxury brand
**Results:**
- Best Match: ¥180, Similarity: 98% (almost identical, still expensive)
- Cheapest 90%+: ¥45, Similarity: 91% (same shape/material, different brand)

**Decision:** Choose cheapest if you care about style, not brand

### Scenario 2: Reference watch = ¥50 fashion watch  
**Results:**
- Best Match: ¥52, Similarity: 96% (nearly same watch)
- Cheapest 90%+: ¥52, Similarity: 96% (same product!)

**Decision:** They're the same! Go with it

### Scenario 3: Unique design watch
**Results:**
- Best Match: ¥120, Similarity: 85% (close but not quite)
- Cheapest 90%+: (none found)

**Decision:** No good cheaper alternatives exist, need to pay for quality

