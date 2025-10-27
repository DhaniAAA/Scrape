# Setup Environment Variables

Script ini sekarang menggunakan file `.env` untuk menyimpan konfigurasi sensitif dan pengaturan aplikasi.

## Setup

1. **Copy file `.env.example` menjadi `.env`:**
   ```bash
   cp .env.example .env
   ```

2. **Edit file `.env` dan isi dengan nilai yang sesuai:**
   - `SUPABASE_URL`: URL project Supabase Anda
   - `SUPABASE_KEY`: Service role key dari Supabase
   - Sesuaikan konfigurasi lainnya sesuai kebutuhan

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Jalankan script:**
   ```bash
   python scrape_links_only.py
   ```

## Konfigurasi Available

### Supabase Configuration
- `SUPABASE_URL`: URL project Supabase
- `SUPABASE_KEY`: Service role key dari Supabase
- `BUCKET_NAME`: Nama bucket di Supabase Storage (default: `manga-data`)
- `ENABLE_SUPABASE_UPLOAD`: Enable/disable upload ke Supabase (`True`/`False`)

### Scraping Configuration
- `JSON_FILE`: File JSON input berisi daftar komik (default: `manhwa_list.json`)
- `OUTPUT_FILE`: File output untuk hasil scraping (default: `manga_local_image_links.json`)
- `MAX_COMICS_TO_PROCESS`: Jumlah maksimal komik yang diproses per run (default: `50`)
- `PROGRESS_FILE`: File untuk menyimpan progress (default: `scrape_links_progress.json`)

### Auto Update Mode
- `AUTO_UPDATE_MODE`: Enable auto update mode untuk cek chapter baru (`True`/`False`)
- `AUTO_UPDATE_MAX_COMICS`: Maksimal komik yang dicek per run di auto update mode (default: `100`)

### Speed Configuration
- `DELAY_BETWEEN_CHAPTERS`: Delay antar chapter dalam detik (default: `0.5`)
- `DELAY_BETWEEN_COMICS`: Delay antar komik dalam detik (default: `1`)
- `REQUEST_TIMEOUT`: Timeout untuk HTTP request dalam detik (default: `10`)

### Parallel Processing Configuration
- `MAX_CHAPTER_WORKERS`: Jumlah thread untuk parallel chapter scraping (default: `5`)
- `MAX_COMIC_WORKERS`: Jumlah thread untuk parallel comic processing (default: `2`)
- `ENABLE_PARALLEL`: Enable/disable parallel processing (`True`/`False`)

### Headers Configuration
- `USER_AGENT`: User agent untuk HTTP requests
- `REFERER`: Referer header untuk HTTP requests

## Keamanan

⚠️ **PENTING**: File `.env` berisi informasi sensitif (API keys, credentials, dll). 
- File `.env` sudah ada di `.gitignore` dan tidak akan ter-commit ke git
- Jangan pernah share atau commit file `.env` ke repository
- Gunakan `.env.example` sebagai template untuk dokumentasi

## Troubleshooting

Jika script tidak membaca file `.env`:
1. Pastikan file `.env` ada di direktori yang sama dengan script
2. Pastikan package `python-dotenv` sudah terinstall
3. Periksa format file `.env` (tidak ada tanda kutip di sekitar nilai)
