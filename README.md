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
├── scrape_links_only.py         # Main scraper for chapter images
├── generate-manifest.py         # Generates manifest files from Supabase
├── merger_link.json            # Input: List of manga/manhwa to scrape
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
├── .env                         # Local environment configuration (not committed)
├── manga_local_image_links.json # Output: Chapter image links (local copy)
├── scrape_links_progress.json   # Progress tracking file
├── README_ENV.md               # Environment setup documentation
├── GITHUB_SECRETS_SETUP.md     # GitHub Actions secrets guide
├── .github/
│   └── workflows/
│       ├── Update-Chapter.yml   # GitHub Actions: Update chapters
│       └── manifest-komik.yaml  # GitHub Actions: Generate manifest
└── .gitignore                   # Git ignore patterns
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

5. **Configure environment variables**:

   **For Local Development:**
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` and fill in your configuration:
     ```bash
     SUPABASE_URL=https://your-project.supabase.co
     SUPABASE_KEY=your-service-role-key-here
     BUCKET_NAME=manga-data
     # ... other settings
     ```

   **For GitHub Actions:**
   - Go to Repository Settings > Secrets and variables > Actions
   - Add the required secrets (see `GITHUB_SECRETS_SETUP.md` for details)

   📖 **Complete setup guide:** [`README_ENV.md`](./README_ENV.md)

## Usage

### 1. Local Development

**Scrape Chapter Images:**
```bash
python scrape_links_only.py
```

**Generate Manifest (from Supabase):**
```bash
python generate-manifest.py
```

### 2. GitHub Actions (Automated)

The project includes two automated workflows:

**Update Chapter Manhwa/Manhua:**
- **Trigger:** Manual or scheduled (daily at 14:00 UTC)
- **Action:** Scrapes new chapters and uploads to Supabase
- **File:** `.github/workflows/Update-Chapter.yml`

**Generate Manifest:**
- **Trigger:** Manual or scheduled (daily at 14:00 UTC)
- **Action:** Generates manifest files from Supabase bucket
- **File:** `.github/workflows/manifest-komik.yaml`

### 3. Manual Trigger

You can manually trigger workflows from the GitHub Actions tab:

1. Go to **Actions** tab in your repository
2. Select the desired workflow
3. Click **Run workflow**
4. Choose parameters if available

## Configuration

The scraper supports two configuration methods:

### Environment Variables (.env file)
For local development, edit the `.env` file:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
BUCKET_NAME=manga-data
ENABLE_SUPABASE_UPLOAD=True

# Scraping Configuration
JSON_FILE=merger_link.json
MAX_COMICS_TO_PROCESS=50
AUTO_UPDATE_MODE=True
AUTO_UPDATE_MAX_COMICS=255

# Speed Configuration
DELAY_BETWEEN_CHAPTERS=0.5
DELAY_BETWEEN_COMICS=1
REQUEST_TIMEOUT=10

# Parallel Processing
MAX_CHAPTER_WORKERS=5
MAX_COMIC_WORKERS=2
ENABLE_PARALLEL=True
```

### GitHub Secrets (for Actions)
For GitHub Actions, add secrets in Repository Settings:
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `BUCKET_NAME`
- And other configuration variables

📖 **See [`README_ENV.md`](./README_ENV.md) for complete configuration guide**

### Auto-Update Mode

The scraper can automatically check existing comics for new chapters:

1. Set `AUTO_UPDATE_MODE = True` in environment variables
2. The scraper will check all comics in `merger_link.json`
3. Only new chapters will be processed and uploaded
4. Progress is saved to resume interrupted runs

### Progress Tracking

The scraper saves progress after each comic:
- Resume interrupted scraping sessions
- Skip already processed comics
- Track upload status to Supabase
- Progress saved in `scrape_links_progress.json`

### Parallel Processing

The scraper supports multi-threaded processing:
- **Chapter-level parallelism**: Process multiple chapters simultaneously
- **Comic-level parallelism**: Process multiple comics simultaneously (normal mode only)
- Configurable thread counts via environment variables
- Thread-safe operations to prevent race conditions

### Local-Only Mode

To scrape without uploading to Supabase:
```bash
ENABLE_SUPABASE_UPLOAD=False
```

All data will be saved to `manga_local_image_links.json`.

## GitHub Actions Integration

This project includes automated workflows for continuous scraping:

### Automated Workflows

1. **Update-Chapter.yml**: Scrapes new chapters and uploads to Supabase
   - Scheduled: Daily at 14:00 UTC
   - Manual trigger available
   - Uses GitHub repository secrets for configuration

2. **manifest-komik.yaml**: Generates manifest files from Supabase
   - Scheduled: Daily at 14:00 UTC
   - Manual trigger available
   - Updates comics listing for frontend

### Manual Triggers

Both workflows can be triggered manually:
1. Go to **Actions** tab in GitHub repository
2. Select the desired workflow
3. Click **Run workflow**
4. Monitor execution in real-time

📖 **Complete GitHub Actions guide:** [`GITHUB_SECRETS_SETUP.md`](./GITHUB_SECRETS_SETUP.md)

## Dependencies

- **requests**: HTTP requests
- **beautifulsoup4**: HTML parsing
- **supabase**: Supabase client
- **lxml**: XML/HTML parser
- **Pillow**: Image processing
- **websockets**: WebSocket support for Supabase realtime
- **python-dotenv**: Environment variables management
- **storage3**: Supabase storage client
- **realtime**: Supabase realtime client

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

### Local Development Issues

1. **Environment variables not loading**:
   - Ensure `.env` file exists in project root
   - Check that `python-dotenv` is installed: `pip install python-dotenv`
   - Verify `.env` file format (no quotes around values)

2. **Supabase connection fails**:
   - Verify `SUPABASE_URL` and `SUPABASE_KEY` in `.env`
   - Ensure Supabase project is active and accessible
   - Check that service role key is used (not anon key)

3. **Missing dependencies**:
   - Run `pip install -r requirements.txt`
   - Check for any installation errors

### GitHub Actions Issues

1. **Workflow fails to start**:
   - Verify all required secrets are added to repository settings
   - Check that workflow files are properly formatted
   - Ensure repository has proper permissions

2. **Script can't read environment variables**:
   - Confirm secrets are correctly named in workflow files
   - Check workflow logs for detailed error messages
   - Verify secret values are properly set

3. **Supabase upload fails in Actions**:
   - Verify `SUPABASE_KEY` has proper permissions
   - Check bucket name and existence
   - Ensure service role key is used (not anon key)

### Common Issues

1. **Connection errors**:
   - Check your internet connection
   - Verify the target website is accessible
   - Increase `REQUEST_TIMEOUT` value in environment variables

2. **Missing data in output**:
   - Website structure may have changed
   - Check console output for error messages
   - Verify the CSS selectors in the code

3. **Scraper stops unexpectedly**:
   - Check `scrape_links_progress.json` for last processed item
   - Run again to resume from last position
   - Review error logs in console or GitHub Actions

## Configuration

### Environment Variables (.env)
For local development, create a `.env` file from `.env.example`:

```bash
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
BUCKET_NAME=manga-data

# Optional (with defaults)
ENABLE_SUPABASE_UPLOAD=True
JSON_FILE=merger_link.json
MAX_COMICS_TO_PROCESS=50
AUTO_UPDATE_MODE=True
# ... see .env.example for all options
```

### GitHub Repository Secrets
For GitHub Actions, add these secrets in repository settings:

**Required:**
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `BUCKET_NAME`

**Optional:**
- `ENABLE_SUPABASE_UPLOAD`
- `JSON_FILE`
- `MAX_COMICS_TO_PROCESS`
- `AUTO_UPDATE_MODE`
- And other configuration variables

📖 **Complete configuration guide:** [`README_ENV.md`](./README_ENV.md)

⚠️ **Security Note:** Never commit `.env` files or expose secrets in code!

## Project Status

This project has been updated to support modern development practices:

### ✅ Current Features
- **Environment-based configuration** (.env files and GitHub secrets)
- **Automated workflows** via GitHub Actions
- **Parallel processing** for improved performance
- **Progress tracking** with resume capability
- **Auto-update mode** for new chapters detection
- **Supabase integration** for cloud storage

### 📁 Key Files
- `scrape_links_only.py` - Main scraper script
- `generate-manifest.py` - Manifest generation script
- `merger_link.json` - Input data (manga list)
- `.env.example` - Environment variables template
- `requirements.txt` - Python dependencies

### 🔄 Workflows
- **Update-Chapter.yml** - Automated chapter scraping
- **manifest-komik.yaml** - Automated manifest generation

### 📖 Documentation
- [`README_ENV.md`](./README_ENV.md) - Environment setup guide
- [`GITHUB_SECRETS_SETUP.md`](./GITHUB_SECRETS_SETUP.md) - GitHub Actions secrets guide

## Quick Start

### For Local Development
```bash
# 1. Setup environment
cp .env.example .env
# Edit .env with your credentials

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run scraper
python scrape_links_only.py
```

### For GitHub Actions
```bash
# 1. Add repository secrets (see GITHUB_SECRETS_SETUP.md)
# 2. Push code to repository
# 3. Workflows will run automatically or can be triggered manually
```

## Contributing

Feel free to submit issues or pull requests to improve the scraper.

## License

This project is provided as-is for educational purposes.

## Disclaimer

This tool is intended for personal use and educational purposes only. Users are responsible for ensuring their use complies with applicable laws and the terms of service of the websites they scrape.

**⚠️ Important Security Notes:**
- Never commit `.env` files or secrets to version control
- Use service role keys for Supabase (not anon keys)
- Respect website rate limits and terms of service
- Only scrape content you have permission to access
