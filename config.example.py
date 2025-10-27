# ==================== SUPABASE CONFIGURATION ====================
# Copy file ini menjadi config.py dan isi dengan kredensial Anda

SUPABASE_URL = "https://your-project-id.supabase.co"
SUPABASE_KEY = "your-anon-key-here"
BUCKET_NAME = "manga"

# ==================== SCRAPING CONFIGURATION ====================
JSON_FILE = 'komikcast_scrape_results.json'
MAX_COMICS_TO_PROCESS = 5
PROGRESS_FILE = 'supabase_upload_progress.json'

# ==================== REQUEST HEADERS ====================
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': 'https://komikcast03.com/'
}

# ==================== DELAY SETTINGS (in seconds) ====================
DELAY_BETWEEN_IMAGES = 0.5
DELAY_BETWEEN_CHAPTERS = 1
DELAY_BETWEEN_COMICS = 2
