# Mangaverse Scraper

A Python-based web scraper for collecting manga/manhwa data from KomikCast, including metadata, chapter information, and image links. The scraper supports automatic uploads to Supabase storage and includes an auto-update mode for tracking new chapters.

## Features

- 📚 **Scrape manga/manhwa listings** with metadata (title, rating, cover image)
- 🔗 **Extract chapter links and image URLs** from individual manga pages
- ☁️ **Automatic Supabase upload** for images and metadata
- 🔄 **Auto-update mode** to check for new chapters
- 💾 **Progress tracking** with resume capability
- 🎯 **Configurable limits** for pages, comics, and chapters
- ⚡ **Adjustable delays** to control scraping speed

## Project Structure

```
Scrape/
├── detail_komik.py              # Scrapes manga list from main pages
├── scrape_links_only.py         # Scrapes chapter images and uploads to Supabase
├── generate-manifest.py         # Generates manifest files
├── config.example.py            # Configuration template
├── requirements.txt             # Python dependencies
├── manhwa_list.json            # Output: List of manga/manhwa
├── manga_local_image_links.json # Output: Chapter image links
├── comics-list.json            # Additional comics data
├── AUTO_UPDATE_MODE.md         # Documentation for auto-update feature
├── PANDUAN_SCRAPE_LINKS.md     # Guide for link scraping
└── manhwa_link/                # Directory for progress tracking
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. **Clone or download this repository**

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment**:
   - Windows:
     ```bash
     .venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source .venv/bin/activate
     ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure Supabase** (optional, for cloud storage):
   - Copy `config.example.py` to `config.py`
   - Fill in your Supabase credentials:
     ```python
     SUPABASE_URL = "https://your-project-id.supabase.co"
     SUPABASE_KEY = "your-anon-key-here"
     BUCKET_NAME = "manga-data"
     ```

## Usage

### 1. Scrape Manga List

Run `detail_komik.py` to scrape manga listings from KomikCast:

```bash
python detail_komik.py
```

**Configuration options** (edit in the file):
- `max_pages`: Number of pages to scrape (default: 5)
- Output: `komikcast_scrape_results.json`

### 2. Scrape Chapter Images

Run `scrape_links_only.py` to extract chapter images and upload to Supabase:

```bash
python scrape_links_only.py
```

**Configuration options** (edit at the top of the file):

```python
# Supabase Configuration
ENABLE_SUPABASE_UPLOAD = True  # Set False for local-only mode

# Scraping Configuration
JSON_FILE = 'manhwa_list.json'
MAX_COMICS_TO_PROCESS = 5  # Number of comics to process

# Auto Update Mode
AUTO_UPDATE_MODE = True  # Check all comics for new chapters
AUTO_UPDATE_MAX_COMICS = 20  # Max comics to check per run

# Speed Configuration
DELAY_BETWEEN_CHAPTERS = 0.5  # Delay between chapters (seconds)
DELAY_BETWEEN_COMICS = 1      # Delay between comics (seconds)
REQUEST_TIMEOUT = 10          # Request timeout (seconds)
```

**Outputs**:
- `manga_local_image_links.json`: Local copy of all image links
- `manhwa_link/scrape_links_progress.json`: Progress tracking file

### 3. Generate Manifest

Run `generate-manifest.py` to create manifest files:

```bash
python generate-manifest.py
```

## Features in Detail

### Auto-Update Mode

The scraper can automatically check existing comics for new chapters:

1. Set `AUTO_UPDATE_MODE = True` in `scrape_links_only.py`
2. The scraper will check all comics in the JSON file
3. Only new chapters will be processed and uploaded
4. Progress is saved to resume interrupted runs

See `AUTO_UPDATE_MODE.md` for detailed documentation.

### Progress Tracking

The scraper saves progress after each comic:
- Resume interrupted scraping sessions
- Skip already processed comics
- Track upload status to Supabase

### Local-Only Mode

To scrape without uploading to Supabase:
```python
ENABLE_SUPABASE_UPLOAD = False
```

All data will be saved to `manga_local_image_links.json`.

## Dependencies

- **requests**: HTTP requests
- **beautifulsoup4**: HTML parsing
- **supabase**: Supabase client
- **lxml**: XML/HTML parser
- **Pillow**: Image processing
- **websockets**: WebSocket support for Supabase realtime

See `requirements.txt` for specific versions.

## Important Notes

### Rate Limiting

- The scraper includes delays between requests to avoid overloading servers
- Adjust `DELAY_BETWEEN_CHAPTERS` and `DELAY_BETWEEN_COMICS` as needed
- Be respectful of the target website's resources

### Legal Considerations

- This scraper is for educational purposes only
- Ensure you have permission to scrape the target website
- Respect the website's `robots.txt` and terms of service
- Do not use scraped data for commercial purposes without permission

### Error Handling

- The scraper includes error handling for network issues
- Failed requests are logged and skipped
- Progress is saved regularly to prevent data loss

## Troubleshooting

### Common Issues

1. **Connection errors**:
   - Check your internet connection
   - Verify the target website is accessible
   - Increase `REQUEST_TIMEOUT` value

2. **Supabase upload fails**:
   - Verify your Supabase credentials in `config.py`
   - Check bucket permissions
   - Ensure bucket name is correct

3. **Missing data in output**:
   - Website structure may have changed
   - Check console output for error messages
   - Verify the CSS selectors in the code

4. **Scraper stops unexpectedly**:
   - Check `scrape_links_progress.json` for last processed item
   - Run again to resume from last position
   - Review error logs in console

## Configuration Files

### config.py (create from config.example.py)

Contains sensitive credentials and configuration:
- Supabase URL and API key
- Bucket name
- Request headers
- Delay settings

**⚠️ Never commit `config.py` to version control!**

## Contributing

Feel free to submit issues or pull requests to improve the scraper.

## License

This project is provided as-is for educational purposes.

## Disclaimer

This tool is intended for personal use and educational purposes only. Users are responsible for ensuring their use complies with applicable laws and the terms of service of the websites they scrape.
