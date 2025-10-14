# Bunny.net Setup Guide

This project has been migrated from Cloudinary to Bunny.net for cost-effective image storage.

## Cost Comparison

- **Cloudinary**: $90/month (cheapest paid tier)
- **Bunny.net**: ~$1-10/month (pay for what you use)
  - Storage: $0.01/GB/month
  - Bandwidth: $0.01/GB
  - For 100GB storage: ~$1/month
  - For 500GB storage: ~$5/month

## Setup Instructions

### 1. Create Bunny.net Account

1. Go to https://bunny.net
2. Sign up for a free account
3. Verify your email

### 2. Create Storage Zone

1. In Bunny.net dashboard, go to **Storage** → **Add Storage Zone**
2. Enter a name (e.g., `douyin-thumbnails`)
3. Choose a region:
   - `de` - Germany (Europe)
   - `ny` - New York (US East)
   - `la` - Los Angeles (US West)
   - `sg` - Singapore (Asia)
4. Click **Add Storage Zone**
5. The system will automatically create a CDN Pull Zone for you

### 3. Get Your Credentials

After creating the storage zone:

1. Click **Manage** on your storage zone
2. Copy the following information:
   - **Storage Zone Name**: The name you chose (e.g., `douyin-thumbnails`)
   - **API Key/Password**: Found in the FTP & API Access section
   - **Region Code**: The region you selected (e.g., `de`, `ny`, `la`, `sg`)

### 4. Configure Environment Variables

Create a `.env` file in the project root with:

```env
# Bunny.net Storage Configuration
BUNNY_API_KEY=your_api_key_here
BUNNY_STORAGE_ZONE=your_storage_zone_name
BUNNY_REGION=de  # or ny, la, sg, etc.
```

**Example**:
```env
BUNNY_API_KEY=abc123-def456-ghi789-jkl012
BUNNY_STORAGE_ZONE=douyin-thumbnails
BUNNY_REGION=de
```

### 5. Install Dependencies

```bash
pip3 install -r requirements.txt
```

### 6. Run the Backup Script

```bash
python3 backup_thumbnails.py
```

The script will:
- Load your Bunny.net credentials from `.env`
- Upload thumbnails to Bunny.net storage
- Return permanent CDN URLs
- Save updated CSV with `backup_thumbnail_url` column

## How It Works

1. **Download**: Script downloads the Douyin thumbnail from the expiring URL
2. **Upload**: Uploads to Bunny.net storage with a unique filename (MD5 hash)
3. **CDN URL**: Returns a permanent CDN URL in format:
   ```
   https://your-storage-zone.b-cdn.net/douyin_thumbnails/abc123def456.jpg
   ```

## Features

- ✅ Parallel uploads (10 concurrent)
- ✅ Automatic retry on failures (3 attempts)
- ✅ Organized in `douyin_thumbnails/` folder
- ✅ Unique filenames prevent duplicates
- ✅ Fast global CDN delivery
- ✅ Pay only for storage used

## Troubleshooting

### "❌ Bunny.net credentials not found"
- Make sure `.env` file exists in project root
- Verify all three variables are set: `BUNNY_API_KEY`, `BUNNY_STORAGE_ZONE`, `BUNNY_REGION`

### "❌ Upload failed: HTTP 401"
- Check your API key is correct
- API key is case-sensitive

### "❌ Upload failed: HTTP 404"
- Verify storage zone name is correct
- Make sure storage zone exists in your Bunny.net account

### "❌ Failed to download image: HTTP 403"
- Original Douyin URL may have expired
- This is expected for old URLs (that's why we backup!)

## Pricing Details

Based on actual usage (100GB storage, minimal bandwidth):

| Month | Storage | Bandwidth | Total |
|-------|---------|-----------|-------|
| 100GB | $1.00 | ~$0.10 | ~$1.10 |
| 200GB | $2.00 | ~$0.20 | ~$2.20 |
| 500GB | $5.00 | ~$0.50 | ~$5.50 |
| 1TB | $10.00 | ~$1.00 | ~$11.00 |

**Note**: Bandwidth is minimal if you're the only user accessing the images.

## Support

For Bunny.net support:
- Documentation: https://docs.bunny.net/
- Support: https://support.bunny.net/
- Dashboard: https://panel.bunny.net/

