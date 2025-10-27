"""
MANGA IMAGE LINKS SCRAPER + SUPABASE UPLOADER
==============================================
Script untuk scraping link gambar manga dari website dan upload ke Supabase Storage.

FITUR PARALLEL PROCESSING:
- Parallel chapter scraping: Scrape multiple chapters secara bersamaan (MAX_CHAPTER_WORKERS)
- Parallel comic processing: Scrape multiple komik secara bersamaan (MAX_COMIC_WORKERS)
- Thread-safe operations untuk menghindari race conditions
- Dapat di-disable dengan set ENABLE_PARALLEL = False

KONFIGURASI PARALLEL:
- MAX_CHAPTER_WORKERS: Jumlah thread untuk scraping chapter (default: 5)
- MAX_COMIC_WORKERS: Jumlah thread untuk scraping komik (default: 2)
- ENABLE_PARALLEL: Enable/disable parallel processing (default: True)

CATATAN:
- Parallel comic processing hanya aktif di mode normal (bukan auto update mode)
- Parallel chapter scraping aktif di semua mode
- Gunakan thread count yang wajar untuk menghindari rate limiting
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import re
import time
from supabase import create_client, Client
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ==================== KONFIGURASI ====================
# Load configuration from .env file

# Supabase Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://nnaizqqgdtqmfpwzcspe.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')
BUCKET_NAME = os.getenv('BUCKET_NAME', 'manga-data')
ENABLE_SUPABASE_UPLOAD = os.getenv('ENABLE_SUPABASE_UPLOAD', 'True').lower() == 'true'

# Scraping Configuration
JSON_FILE = os.getenv('JSON_FILE', 'merger-link.json')
OUTPUT_FILE = os.getenv('OUTPUT_FILE', 'manga_local_image_links.json')
MAX_COMICS_TO_PROCESS = int(os.getenv('MAX_COMICS_TO_PROCESS', '50'))
PROGRESS_FILE = os.getenv('PROGRESS_FILE', 'scrape_links_progress.json')

# Auto Update Mode (cek semua komik yang ada chapter baru)
AUTO_UPDATE_MODE = os.getenv('AUTO_UPDATE_MODE', 'True').lower() == 'true'
AUTO_UPDATE_MAX_COMICS = int(os.getenv('AUTO_UPDATE_MAX_COMICS', '100'))

# Speed Configuration
DELAY_BETWEEN_CHAPTERS = float(os.getenv('DELAY_BETWEEN_CHAPTERS', '0.5'))
DELAY_BETWEEN_COMICS = float(os.getenv('DELAY_BETWEEN_COMICS', '1'))
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '10'))

# Parallel Processing Configuration
MAX_CHAPTER_WORKERS = int(os.getenv('MAX_CHAPTER_WORKERS', '5'))
MAX_COMIC_WORKERS = int(os.getenv('MAX_COMIC_WORKERS', '2'))
ENABLE_PARALLEL = os.getenv('ENABLE_PARALLEL', 'True').lower() == 'true'

# Headers untuk request
HEADERS = {
    'User-Agent': os.getenv('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'),
    'Referer': os.getenv('REFERER', 'https://komikcast03.com/')
}

# ==================== FUNGSI UTILITAS ====================

# Thread lock untuk print yang aman
print_lock = threading.Lock()

def thread_safe_print(*args, **kwargs):
    """Print yang thread-safe untuk parallel processing"""
    with print_lock:
        print(*args, **kwargs)

def sanitize_filename(name):
    """Membersihkan nama file dari karakter tidak valid untuk Supabase Storage"""
    # Hapus karakter tidak valid untuk filesystem dan Supabase
    # Termasuk: \ / * ? : " < > | ' ` ! @ # $ % ^ & ( ) [ ] { } = + ~ , 
    cleaned = re.sub(r'[\\/*?:"<>|\'`!@#$%^&()\[\]{}=+~,]', "", name)
    # Hapus whitespace berlebih (spasi, tab, newline, dll)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    # Ganti spasi dengan dash dan lowercase
    cleaned = cleaned.strip().replace(' ', '-').lower()
    # Hapus dash berlebih (jika ada)
    cleaned = re.sub(r'-+', '-', cleaned)
    # Hapus dash di awal dan akhir
    cleaned = cleaned.strip('-')
    return cleaned

def load_progress():
    """Memuat progress scraping dari file"""
    if not os.path.exists(PROGRESS_FILE):
        return {'last_processed_index': -1, 'scraped_comics': []}
    try:
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {'last_processed_index': -1, 'scraped_comics': []}
            if 'last_processed_index' not in data:
                data['last_processed_index'] = -1
            if 'scraped_comics' not in data:
                data['scraped_comics'] = []
            return data
    except (json.JSONDecodeError, FileNotFoundError, KeyError):
        return {'last_processed_index': -1, 'scraped_comics': []}

def save_progress(index, scraped_comics):
    """Menyimpan progress scraping ke file"""
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            'last_processed_index': index,
            'scraped_comics': scraped_comics
        }, f, indent=2, ensure_ascii=False)

def save_output(data):
    """Menyimpan hasil scraping ke file output"""
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_output():
    """Load existing output file"""
    if not os.path.exists(OUTPUT_FILE):
        return []
    try:
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

# ==================== SUPABASE FUNCTIONS ====================

def init_supabase():
    """Inisialisasi koneksi Supabase"""
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        return supabase
    except Exception as e:
        print(f"✗ Gagal koneksi ke Supabase: {e}")
        return None

def upload_json_to_supabase(supabase, json_data, file_path):
    """Upload JSON file ke Supabase Storage"""
    try:
        json_bytes = json.dumps(json_data, ensure_ascii=False, indent=2).encode('utf-8')
        
        # Try upload
        try:
            supabase.storage.from_(BUCKET_NAME).upload(
                path=file_path,
                file=json_bytes,
                file_options={"content-type": "application/json"}
            )
            return True
        except Exception as e:
            # If exists, update
            if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                supabase.storage.from_(BUCKET_NAME).update(
                    path=file_path,
                    file=json_bytes,
                    file_options={"content-type": "application/json"}
                )
                return True
            else:
                print(f"    ✗ Upload error: {e}")
                return False
    except Exception as e:
        print(f"    ✗ Gagal upload {file_path}: {e}")
        return False

def get_existing_chapters(supabase, comic_slug):
    """Dapatkan daftar chapter yang sudah ada di Supabase dari chapters.json"""
    try:
        chapters_file_path = f"{comic_slug}/chapters.json"
        
        # Download chapters.json dari Supabase
        response = supabase.storage.from_(BUCKET_NAME).download(chapters_file_path)
        
        if response:
            # Parse JSON
            chapters_data = json.loads(response)
            
            # Extract chapter slugs
            chapter_slugs = set()
            if 'chapters' in chapters_data:
                for chapter in chapters_data['chapters']:
                    if 'slug' in chapter:
                        chapter_slugs.add(chapter['slug'])
            
            return chapter_slugs
        else:
            # File tidak ada, return empty set
            return set()
            
    except Exception as e:
        # Jika file tidak ada atau error, return empty set
        return set()

def get_existing_chapters_full(supabase, comic_slug):
    """Dapatkan data lengkap chapters yang sudah ada di Supabase dari chapters.json"""
    try:
        chapters_file_path = f"{comic_slug}/chapters.json"
        
        # Download chapters.json dari Supabase
        response = supabase.storage.from_(BUCKET_NAME).download(chapters_file_path)
        
        if response:
            # Parse JSON
            chapters_data = json.loads(response)
            return chapters_data
        else:
            # File tidak ada, return None
            return None
            
    except Exception as e:
        # Jika file tidak ada atau error, return None
        return None

def is_comic_completed(supabase, comic_slug, total_chapters, status):
    """Cek apakah komik sudah complete (tamat dan semua chapter sudah ada)"""
    # Jika status bukan 'Completed', return False
    if status and 'complete' not in status.lower():
        return False
    
    # Cek apakah semua chapter sudah ada
    try:
        existing = get_existing_chapters(supabase, comic_slug)
        # Jika jumlah chapter existing >= total chapters, dianggap complete
        return len(existing) >= total_chapters
    except:
        return False

def has_new_chapters(supabase, comic_url, comic_slug):
    """Cek apakah komik memiliki chapter baru (untuk auto update mode)"""
    try:
        # Scrape detail untuk dapat total chapters dari website
        details = scrape_comic_details(comic_url)
        if not details:
            return False, 0, 0
        
        total_chapters_website = len(details['chapters'])
        
        # Get existing chapters dari Supabase
        existing_chapters = get_existing_chapters(supabase, comic_slug)
        total_chapters_supabase = len(existing_chapters)
        
        # Ada chapter baru jika total di website > total di Supabase
        has_new = total_chapters_website > total_chapters_supabase
        
        return has_new, total_chapters_website, total_chapters_supabase
    except Exception as e:
        return False, 0, 0

# ==================== SCRAPING FUNCTIONS ====================

def scrape_comic_details(comic_url):
    """Scrape detail komik dari halaman detail"""
    try:
        print(f"  → Mengambil detail dari: {comic_url}")
        response = requests.get(comic_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Ambil informasi dasar
        title_element = soup.select_one('.komik_info-content-body-title')
        title = title_element.get_text(strip=True) if title_element else 'Unknown'

        # Ambil genre
        genres = []
        genre_elements = soup.select('.komik_info-content-genre a')
        for genre in genre_elements:
            genres.append(genre.get_text(strip=True))

        # Ambil synopsis
        synopsis_element = soup.select_one('.komik_info-description-sinopsis')
        synopsis = synopsis_element.get_text(strip=True) if synopsis_element else ''

        # Ambil metadata (Type, Status, Author, dll)
        metadata = {}
        meta_elements = soup.select('.komik_info-content-meta span')
        for meta in meta_elements:
            text = meta.get_text(strip=True)
            if ':' in text:
                key, value = text.split(':', 1)
                metadata[key.strip()] = value.strip()

        # Ambil cover URL
        cover_element = soup.select_one('.komik_info-content-thumbnail img')
        cover_url = cover_element['src'] if cover_element and 'src' in cover_element.attrs else None

        # Ambil daftar chapter
        chapter_list = []
        chapter_elements = soup.select('.komik_info-chapters-item')
        
        for chapter_elem in chapter_elements:
            link_element = chapter_elem.select_one('.chapter-link-item')
            time_element = chapter_elem.select_one('.chapter-link-time')
            
            if link_element:
                # Normalize whitespace di chapter title
                chapter_text = link_element.get_text(strip=True).replace('\n', ' ')
                chapter_text = re.sub(r'\s+', ' ', chapter_text).strip()
                
                chapter_list.append({
                    'chapter': chapter_text,
                    'link': link_element['href'],
                    'waktu_rilis': time_element.get_text(strip=True) if time_element else 'N/A'
                })
        
        return {
            'title': title,
            'genres': genres,
            'synopsis': synopsis,
            'metadata': metadata,
            'cover_url': cover_url,
            'chapters': chapter_list
        }
    
    except Exception as e:
        print(f"  ✗ Error scraping detail: {e}")
        return None

def scrape_chapter_images(chapter_url):
    """Scrape link gambar dari chapter menggunakan selector .main-reading-area"""
    try:
        response = requests.get(chapter_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Cari div dengan class "main-reading-area"
        reading_area = soup.select_one('.main-reading-area')
        
        if not reading_area:
            print(f"    ⚠️  Tidak menemukan .main-reading-area")
            return []
        
        # Ambil semua img tag di dalam reading area
        image_urls = []
        images = reading_area.find_all('img')
        
        for img in images:
            image_url = img.get('src')
            if image_url and image_url.strip().startswith('http'):
                image_urls.append(image_url)
        
        return image_urls
    
    except Exception as e:
        print(f"    ✗ Error scraping chapter: {e}")
        return []

def scrape_single_chapter(chapter_data, idx, total, existing_chapters):
    """
    Scrape satu chapter (untuk parallel processing)
    Returns: tuple (success, chapter_result_dict or None)
    """
    chapter_title = chapter_data['chapter']
    chapter_url = chapter_data['link']
    chapter_slug = sanitize_filename(chapter_title)
    
    thread_safe_print(f"\n  Chapter [{idx + 1}/{total}]: {chapter_title}")
    
    # Cek apakah chapter sudah ada
    if chapter_slug in existing_chapters:
        thread_safe_print(f"✅ Chapter sudah ada, skip...")
        return (False, None)
    
    # Scrape images dari chapter
    image_urls = scrape_chapter_images(chapter_url)
    
    if not image_urls:
        thread_safe_print(f"✗ Tidak ada gambar ditemukan")
        return (False, None)
    
    thread_safe_print(f"✅ Ditemukan {len(image_urls)} gambar")
    
    # Delay antar chapter
    time.sleep(DELAY_BETWEEN_CHAPTERS)
    
    # Return data chapter
    return (True, {
        'slug': chapter_slug,
        'title': chapter_title,
        'url': chapter_url,
        'waktu_rilis': chapter_data['waktu_rilis'],
        'total_images': len(image_urls),
        'images': image_urls
    })

# ==================== MAIN PROCESSING ====================

def process_comic(supabase, comic_data, comic_index):
    """Proses satu komik: scrape detail dan link gambar"""
    
    comic_url = comic_data.get('Link')
    comic_title_raw = comic_data.get('Title', f'Komik-{comic_index}')
    
    if not comic_url:
        print(f"✗ Komik '{comic_title_raw}' tidak memiliki link")
        return None
    
    print(f"\n{'='*60}")
    print(f"[{comic_index + 1}] Memproses: {comic_title_raw}")
    print(f"{'='*60}")
    
    # Scrape detail komik
    details = scrape_comic_details(comic_url)
    if not details:
        print(f"✗ Gagal mendapatkan detail komik")
        return None
    
    # Sanitize nama folder
    comic_slug = sanitize_filename(comic_title_raw)
    
    # Cek status komik
    status = details['metadata'].get('Status', 'Unknown')
    total_chapters = len(details['chapters'])
    
    print(f"  📊 Status: {status} | Total Chapters: {total_chapters}")
    
    # Cek apakah komik sudah complete (tamat dan semua chapter sudah ada)
    if ENABLE_SUPABASE_UPLOAD and supabase:
        if is_comic_completed(supabase, comic_slug, total_chapters, status):
            print(f"\n✅ Komik sudah COMPLETE dan semua chapter sudah ada!")
            print(f"⏭️  Skip komik ini...")
            return None
    
    # Dapatkan daftar chapter yang sudah ada (untuk skip)
    existing_chapters = set()
    if ENABLE_SUPABASE_UPLOAD and supabase:
        existing_chapters = get_existing_chapters(supabase, comic_slug)
        if existing_chapters:
            print(f"  📁 Chapter yang sudah ada: {len(existing_chapters)}")
            # Uncomment untuk melihat daftar chapter yang sudah ada:
            # print(f"  📋 List: {sorted(existing_chapters)[:10]}...")  # Show first 10
    
    # Struktur data untuk komik ini
    comic_result = {
        'slug': comic_slug,
        'title': details['title'],
        'url': comic_url,
        'cover_url': details['cover_url'],
        'genres': details['genres'],
        'synopsis': details['synopsis'],
        'metadata': details['metadata'],
        'total_chapters': total_chapters,
        'chapters': []
    }
    
    # Reverse agar chapter 1 diproses duluan
    chapters = details['chapters'][::-1]
    
    print(f"\n📸 Scraping image links dari {len(chapters)} chapters...")
    
    chapters_scraped = 0
    chapters_skipped = 0
    
    # Parallel processing untuk chapters
    if ENABLE_PARALLEL and MAX_CHAPTER_WORKERS > 1:
        print(f"⚡ Menggunakan {MAX_CHAPTER_WORKERS} workers untuk parallel scraping")
        
        with ThreadPoolExecutor(max_workers=MAX_CHAPTER_WORKERS) as executor:
            # Submit semua chapter untuk diproses parallel
            future_to_chapter = {
                executor.submit(scrape_single_chapter, chapter, idx, len(chapters), existing_chapters): idx
                for idx, chapter in enumerate(chapters)
            }
            
            # Collect hasil
            for future in as_completed(future_to_chapter):
                try:
                    success, chapter_result = future.result()
                    if success and chapter_result:
                        comic_result['chapters'].append(chapter_result)
                        chapters_scraped += 1
                    elif not success and chapter_result is None:
                        # Chapter di-skip atau error
                        chapters_skipped += 1
                except Exception as e:
                    thread_safe_print(f"✗ Error processing chapter: {e}")
    else:
        # Sequential processing (original method)
        print(f"→ Sequential processing (parallel disabled)")
        for idx, chapter in enumerate(chapters):
            chapter_title = chapter['chapter']
            chapter_url = chapter['link']
            chapter_slug = sanitize_filename(chapter_title)
            
            print(f"\n  Chapter [{idx + 1}/{len(chapters)}]: {chapter_title}")
            
            # Cek apakah chapter sudah ada
            if chapter_slug in existing_chapters:
                print(f"✅ Chapter sudah ada, skip...")
                chapters_skipped += 1
                continue
            
            # Scrape images dari chapter
            image_urls = scrape_chapter_images(chapter_url)
            
            if not image_urls:
                print(f"✗ Tidak ada gambar ditemukan")
                continue
            
            print(f"✅ Ditemukan {len(image_urls)} gambar")
            
            # Simpan data chapter
            comic_result['chapters'].append({
                'slug': chapter_slug,
                'title': chapter_title,
                'url': chapter_url,
                'waktu_rilis': chapter['waktu_rilis'],
                'total_images': len(image_urls),
                'images': image_urls
            })
            
            chapters_scraped += 1
            
            # Delay antar chapter
            time.sleep(DELAY_BETWEEN_CHAPTERS)
    
    print(f"\n{'='*60}")
    print(f"✓ Komik '{comic_title_raw}' selesai di-scrape!")
    print(f"  📊 Statistik:")
    print(f"     - Chapter baru di-scrape: {chapters_scraped}")
    print(f"     - Chapter di-skip: {chapters_skipped}")
    print(f"     - Total chapters: {len(chapters)}")
    total_images = sum(ch['total_images'] for ch in comic_result['chapters'])
    print(f"  📸 Total image links (baru): {total_images}")
    print(f"{'='*60}")
    
    # Upload ke Supabase jika enabled
    if ENABLE_SUPABASE_UPLOAD and supabase:
        print(f"\n📤 Uploading ke Supabase...")
        
        # 1. Upload metadata komik (info dasar tanpa chapters)
        metadata_only = {
            'slug': comic_result['slug'],
            'title': comic_result['title'],
            'url': comic_result['url'],
            'cover_url': comic_result['cover_url'],
            'genres': comic_result['genres'],
            'synopsis': comic_result['synopsis'],
            'metadata': comic_result['metadata'],
            'total_chapters': comic_result['total_chapters']
        }
        
        metadata_path = f"{comic_slug}/metadata.json"
        if upload_json_to_supabase(supabase, metadata_only, metadata_path):
            print(f"  ✓ Metadata uploaded: {metadata_path}")
        
        # 2. Gabungkan chapter baru dengan chapter yang sudah ada
        existing_chapters_data = get_existing_chapters_full(supabase, comic_slug)
        
        if existing_chapters_data and 'chapters' in existing_chapters_data:
            # Ada data lama, gabungkan dengan yang baru
            existing_chapters_list = existing_chapters_data['chapters']
            new_chapters_list = comic_result['chapters']
            
            # Buat dictionary untuk merge berdasarkan slug
            chapters_dict = {}
            
            # Masukkan chapter lama
            for ch in existing_chapters_list:
                chapters_dict[ch['slug']] = ch
            
            # Update/tambah dengan chapter baru
            for ch in new_chapters_list:
                chapters_dict[ch['slug']] = ch
            
            # Convert kembali ke list
            merged_chapters = list(chapters_dict.values())
            
            print(f"  📊 Merge: {len(existing_chapters_list)} existing + {len(new_chapters_list)} new = {len(merged_chapters)} total")
        else:
            # Tidak ada data lama, gunakan yang baru saja
            merged_chapters = comic_result['chapters']
            print(f"  📊 New comic: {len(merged_chapters)} chapters")
        
        # 3. Upload semua chapters (gabungan) dalam 1 file JSON
        chapters_data = {
            'slug': comic_result['slug'],
            'title': comic_result['title'],
            'total_chapters': len(merged_chapters),
            'chapters': merged_chapters
        }
        
        chapters_path = f"{comic_slug}/chapters.json"
        if upload_json_to_supabase(supabase, chapters_data, chapters_path):
            print(f"  ✓ All chapters uploaded: {chapters_path} ({len(merged_chapters)} chapters)")
        
        print(f"✅ Upload ke Supabase selesai!")
    
    return comic_result

def process_comic_wrapper(args):
    """
    Wrapper untuk process_comic agar bisa digunakan di parallel processing
    Returns: tuple (current_index, result)
    """
    supabase, comic, current_index = args
    result = process_comic(supabase, comic, current_index)
    return (current_index, result)

# ==================== MAIN FUNCTION ====================

def main():
    """Fungsi utama"""
    print("="*60)
    print("MANGA IMAGE LINKS SCRAPER + SUPABASE UPLOADER")
    print("="*60)
    
    # Init Supabase
    supabase = None
    if ENABLE_SUPABASE_UPLOAD:
        supabase = init_supabase()
        if supabase:
            print("✓ Koneksi Supabase berhasil")
        else:
            print("⚠️  Supabase tidak tersedia, hanya save lokal")
    
    # Load JSON file
    if not os.path.exists(JSON_FILE):
        print(f"✗ File {JSON_FILE} tidak ditemukan!")
        return
    
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        comics_data = json.load(f)
    
    # Load progress
    progress = load_progress()
    last_index = progress['last_processed_index']
    scraped_comics = progress['scraped_comics']
    
    # Load existing output
    output_data = load_output()
    
    # Tentukan range komik yang akan diproses
    if AUTO_UPDATE_MODE:
        # Mode auto update: cek semua komik yang ada chapter baru
        print(f"\n🔄 AUTO UPDATE MODE AKTIF")
        print(f"→ Mengecek komik yang ada chapter baru...")
        print(f"→ Max komik per run: {AUTO_UPDATE_MAX_COMICS}")
        print(f"→ Total komik di database: {len(comics_data)}")
        
        indices_to_process = []
        checked_count = 0
        
        # Cek setiap komik (max AUTO_UPDATE_MAX_COMICS)
        for idx, comic in enumerate(comics_data):
            if checked_count >= AUTO_UPDATE_MAX_COMICS:
                break
            
            comic_title = comic.get('Title', 'Unknown')
            comic_url = comic.get('Link', '')
            comic_slug = sanitize_filename(comic_title)
            
            print(f"\n  [{checked_count + 1}/{AUTO_UPDATE_MAX_COMICS}] Checking: {comic_title}", end=" ")
            
            # Cek apakah ada chapter baru
            has_new, total_web, total_db = has_new_chapters(supabase, comic_url, comic_slug)
            
            if has_new:
                new_chapters = total_web - total_db
                print(f"✅ {new_chapters} chapter baru! ({total_db} → {total_web})")
                indices_to_process.append(idx)
            else:
                print(f"⏭️  No update ({total_db} chapters)")
            
            checked_count += 1
            time.sleep(0.5)  # Delay antar check
        
        print(f"\n📊 Hasil scan:")
        print(f"   - Komik di-cek: {checked_count}")
        print(f"   - Komik dengan update: {len(indices_to_process)}")
        
        if not indices_to_process:
            print(f"\n✅ Tidak ada komik dengan chapter baru!")
            return
        
        print(f"\n→ Akan scrape {len(indices_to_process)} komik dengan chapter baru")
        print(f"→ Index: {indices_to_process}")
        
    else:
        # Mode normal: lanjut dari progress
        start_index = last_index + 1
        end_index = min(start_index + MAX_COMICS_TO_PROCESS, len(comics_data))
        
        print(f"\n→ Akan memproses {end_index - start_index} komik")
        print(f"→ Index: {start_index} hingga {end_index - 1}")
        print(f"→ Total komik di database: {len(comics_data)}")
        
        indices_to_process = range(start_index, end_index)
    
    # Proses setiap komik
    if ENABLE_PARALLEL and MAX_COMIC_WORKERS > 1 and not AUTO_UPDATE_MODE:
        # Parallel processing untuk komik (hanya untuk mode normal, bukan auto update)
        print(f"\n⚡ Menggunakan {MAX_COMIC_WORKERS} workers untuk parallel comic processing")
        
        with ThreadPoolExecutor(max_workers=MAX_COMIC_WORKERS) as executor:
            # Prepare arguments untuk setiap komik
            comic_args = [
                (supabase, comics_data[idx], idx) 
                for idx in indices_to_process
            ]
            
            # Submit semua komik untuk diproses parallel
            future_to_index = {
                executor.submit(process_comic_wrapper, args): args[2]
                for args in comic_args
            }
            
            # Collect hasil
            for future in as_completed(future_to_index):
                try:
                    current_index, result = future.result()
                    
                    if result:
                        # Tambahkan ke output
                        output_data.append(result)
                        scraped_comics.append(result['title'])
                        
                        # Save output setiap kali berhasil
                        save_output(output_data)
                        
                        # Save progress
                        save_progress(current_index, scraped_comics)
                        
                        thread_safe_print(f"\n💾 Progress saved: {current_index + 1}/{len(comics_data)}")
                        
                        # Delay antar komik
                        time.sleep(DELAY_BETWEEN_COMICS)
                except Exception as e:
                    thread_safe_print(f"✗ Error processing comic: {e}")
    else:
        # Sequential processing (original method atau auto update mode)
        if AUTO_UPDATE_MODE:
            print(f"\n→ Sequential processing (auto update mode)")
        else:
            print(f"\n→ Sequential processing (parallel disabled)")
        
        for current_index in indices_to_process:
            comic = comics_data[current_index]
            
            # Proses komik
            result = process_comic(supabase, comic, current_index)
            
            if result:
                # Tambahkan ke output
                output_data.append(result)
                scraped_comics.append(result['title'])
                
                # Save output setiap kali berhasil
                save_output(output_data)
                
                # Save progress
                save_progress(current_index, scraped_comics)
                
                print(f"\n💾 Progress saved: {current_index + 1}/{len(comics_data)}")
                
                # Delay antar komik
                time.sleep(DELAY_BETWEEN_COMICS)
    
    print(f"\n{'='*60}")
    print(f"✅ SCRAPING SELESAI!")
    print(f"{'='*60}")
    print(f"📁 Output file: {OUTPUT_FILE}")
    print(f"📊 Total komik di-scrape: {len(output_data)}")
    total_chapters = sum(len(comic['chapters']) for comic in output_data)
    print(f"📚 Total chapters: {total_chapters}")
    total_images = sum(
        sum(ch['total_images'] for ch in comic['chapters']) 
        for comic in output_data
    )
    print(f"📸 Total image links: {total_images}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
