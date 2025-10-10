# Watches.csv - Best Quality Matches

## Overview

`Watches.csv` automatically captures the **cheapest product with ≥95% score** from each search.

## How It Works

After each search completes:
1. Filters all products with `final_score >= 95%`
2. Among those high-quality matches, finds the one with the **lowest price**
3. Adds that product to `Watches.csv`

## CSV Columns

| Column | Description |
|--------|-------------|
| `reference_image_url` | Your original watch image URL |
| `final_score` | Weighted similarity score (95-100) |
| `price` | Product price |
| `1688_url` | Link to the 1688 product page |
| `1688_thumbnail` | Product thumbnail image URL |

## Example

If your search finds these products:
- Product A: 97.5% score, ¥45
- Product B: 96.2% score, ¥28 ← **This one gets saved to Watches.csv**
- Product C: 95.8% score, ¥52
- Product D: 92.1% score, ¥15 (excluded, below 95%)

Only Product B (cheapest among ≥95%) is added to `Watches.csv`.

## Use Case

Perfect for when you want:
- ✅ **High quality matches only** (95%+ similarity)
- ✅ **Best price** among those quality matches
- ✅ **Clean list** (one entry per search)
- ✅ **Easy sourcing** - Just open Watches.csv and order the cheapest quality alternatives

## File Behavior

- **Accumulative** - Each search adds ONE row (if ≥95% matches exist)
- **Creates on first run** - File auto-created when first high-quality match is found
- **Persists** - Keeps all your best finds in one place

## What If No 95%+ Matches?

You'll see:
```
⚠️ No products with ≥95% score found for Watches.csv
```

The search still completes, and other CSV files are still created. Only `Watches.csv` won't get a new row for that particular search.

## All Output Files

1. **Watches.csv** - Cheapest ≥95% matches (one per search)
2. **Watched_prices.csv** - Best overall match regardless of score
3. **Watched_prices_detailed*.csv** - All products with full score breakdown

