import os
import json
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
from supabase import create_client, Client
from dotenv import load_dotenv

# Muat environment variables dari file .env
load_dotenv()

# ============================================
# KONFIGURASI
# ============================================
BASE_URL = "https://komikindo.ch"
LIST_URL = "https://komikindo.ch/daftar-manga/page/{}/?status=&type=Manhwa&format=&order=&title="

MAX_COMICS = None  # Limit untuk testing, ubah ke None untuk semua
OUTPUT_FILE = "all-manhwa-metadata.json"

# Supabase config
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
BUCKET_NAME = os.environ.get("BUCKET_NAME", "manga-data")

# Initialize Supabase client
supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    print(" SUPABASE_URL atau SUPABASE_KEY tidak ditemukan. Upload ke Supabase dinonaktifkan.")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def parse_relative_time_indonesian(relative_str: str) -> str:
    """
    Konversi waktu relatif Indonesia ke format ISO 8601.
    Contoh: "3 tahun yang lalu" -> "2023-02-08T12:00:00+07:00"
    """
    if not relative_str:
        return datetime.now().isoformat()

    relative_str = relative_str.lower().strip()
    now = datetime.now()

    # Pattern untuk mengekstrak angka dan unit waktu
    patterns = {
        r'(\d+)\s*detik': lambda x: timedelta(seconds=int(x)),
        r'(\d+)\s*menit': lambda x: timedelta(minutes=int(x)),
        r'(\d+)\s*jam': lambda x: timedelta(hours=int(x)),
        r'(\d+)\s*hari': lambda x: timedelta(days=int(x)),
        r'(\d+)\s*minggu': lambda x: timedelta(weeks=int(x)),
        r'(\d+)\s*bulan': lambda x: timedelta(days=int(x) * 30),  # Approx
        r'(\d+)\s*tahun': lambda x: timedelta(days=int(x) * 365),  # Approx
    }

    for pattern, delta_func in patterns.items():
        match = re.search(pattern, relative_str)
        if match:
            num = match.group(1)
            delta = delta_func(num)
            result_time = now - delta
            return result_time.strftime('%Y-%m-%dT%H:%M:%S+07:00')

    # Jika tidak match, kembalikan waktu sekarang
    return now.strftime('%Y-%m-%dT%H:%M:%S+07:00')

def upload_json(path: str, data: dict | list):
    """Helper untuk meng-upload file JSON ke Supabase (menimpa jika sudah ada)."""
    if not supabase:
        print(f" Supabase tidak tersedia, skip upload {path}")
        return False

    try:
        # Ubah data ke string JSON
        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        # Ubah string ke bytes
        json_bytes = json_data.encode('utf-8')

        # Upload dengan upsert
        supabase.storage.from_(BUCKET_NAME).upload(
            path,
            json_bytes,
            {"content-type": "application/json", "upsert": "true"}
        )
        print(f" Berhasil meng-upload {path}")
        return True
    except Exception as e:
        print(f" Gagal meng-upload {path}: {e}")
        return False

def get_soup(url: str, max_retries: int = 3) -> BeautifulSoup | None:
    """Helper untuk mengambil dan parse HTML dari URL."""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            print(f"      Gagal mengambil {url}: {e}")
            return None
    return None

def get_comics_list(max_comics: int = None) -> list[dict]:
    """Scrape daftar komik dari halaman daftar-manga."""
    all_comics = []
    page = 1


    print(" Mengambil daftar komik dari komikindo.ch...")

    seen_slugs = set()  # Track slugs to avoid duplicates

    while True:
        if max_comics and len(all_comics) >= max_comics:
            break

        url = LIST_URL.format(page)
        print(f"  -> Halaman {page}: {url}")

        soup = get_soup(url)
        if not soup:
            break

        # Cari listupd > film-list (daftar komik utama A-Z)
        listupd = soup.find('div', class_='listupd')
        if not listupd:
            print(f"     Tidak ada listupd di halaman {page}")
            break

        film_list = listupd.find('div', class_='film-list')
        if not film_list:
            print(f"     Tidak ada film-list di halaman {page}")
            break

        # Ambil semua animepost (setiap komik)
        animeposts = film_list.find_all('div', class_='animepost')
        if not animeposts:
            print(f"     Tidak ada animepost di halaman {page}")
            break

        comics_added_this_page = 0  # Track new comics added

        for post in animeposts:
            if max_comics and len(all_comics) >= max_comics:
                break

            try:
                # Cari anchor di dalam animepost
                animposx = post.find('div', class_='animposx')
                if not animposx:
                    continue

                a = animposx.find('a', href=True)
                if not a:
                    continue

                link = a.get('href', '')

                # Skip if not a komik link
                if '/komik/' not in link:
                    continue

                # Get title from anchor's title attribute or from h3
                title = a.get('title', '')
                if not title:
                    h3 = animposx.find('h3')
                    if h3:
                        title = h3.get_text(strip=True)

                # Remove "Komik " prefix
                if title.startswith('Komik '):
                    title = title[6:]

                # Extract slug dari URL
                # URL format: https://komikindo.ch/komik/slug-name/
                slug_match = re.search(r'/komik/([^/]+)/?$', link)
                slug = slug_match.group(1) if slug_match else ''

                # Remove leading numbers from slug (e.g., 179384-solo-leveling -> solo-leveling)
                slug = re.sub(r'^\d+-', '', slug)

                if link and slug and slug not in seen_slugs:
                    seen_slugs.add(slug)
                    all_comics.append({
                        'title': title,
                        'link': link,
                        'slug': slug
                    })
                    comics_added_this_page += 1
            except Exception as e:
                print(f"      Error parsing item: {e}")

        # Jika tidak ada komik baru di halaman ini, berarti sudah loop kembali
        if comics_added_this_page == 0:
            print(f"     Halaman {page} tidak ada komik baru (end of pagination)")
            break

        print(f"     +{comics_added_this_page} komik (total: {len(all_comics)})")

        page += 1
        time.sleep(0.5)  # Delay antara request

    print(f" Ditemukan {len(all_comics)} komik")
    return all_comics

def scrape_comic_detail(url: str) -> dict | None:
    """Scrape detail komik dari halaman individual."""
    soup = get_soup(url)
    if not soup:
        return None

    try:
        result = {}

        # Title - h1.entry-title
        title_elem = soup.find('h1', class_='entry-title')
        if title_elem:
            title_text = title_elem.get_text(strip=True)
            # Remove "Komik " prefix and normalize whitespace
            title_text = re.sub(r'^Komik\s*', '', title_text)
            title_text = ' '.join(title_text.split())  # Normalize whitespace
            title_text = title_text.replace("'", "")  # Remove apostrophe
            title_text = re.sub(r"[''`''""\u2018\u2019\u201B\u201C\u201D]", "", title_text)  # Remove all quote variants
            result['title'] = title_text
        else:
            result['title'] = 'Tanpa Judul'

        # Cover image - div.thumb img
        thumb = soup.find('div', class_='thumb')
        if thumb:
            img = thumb.find('img')
            if img:
                result['cover_url'] = img.get('src') or img.get('data-src') or ''

        # Rating - div.archiveanime-rating i[itemprop="ratingValue"]
        rating_elem = soup.find('i', itemprop='ratingValue')
        if rating_elem:
            result['rating'] = rating_elem.get_text(strip=True)
        else:
            result['rating'] = '0'

        # Info dari div.spe
        spe = soup.find('div', class_='spe')
        if spe:
            spans = spe.find_all('span')
            for span in spans:
                text = span.get_text(strip=True)

                # Status
                if 'Status:' in text:
                    status_text = text.replace('Status:', '').strip()
                    result['status'] = status_text

                # Jenis Komik (Type)
                if 'Jenis Komik:' in text:
                    type_link = span.find('a')
                    if type_link:
                        result['type'] = type_link.get_text(strip=True)
                    else:
                        type_text = text.replace('Jenis Komik:', '').strip()
                        result['type'] = type_text

                # Pengarang (Author)
                if 'Pengarang:' in text:
                    pengarang_text = text.replace('Pengarang:', '').strip()
                    result['pengarang'] = pengarang_text

                # Ilustrator
                if 'Ilustrator:' in text:
                    ilustrator_text = text.replace('Ilustrator:', '').strip()
                    result['ilustrator'] = ilustrator_text

        # Set defaults
        if 'status' not in result:
            result['status'] = 'Ongoing'
        if 'type' not in result:
            result['type'] = 'Manhwa'

        # Genres - div.genre-info a
        genre_info = soup.find('div', class_='genre-info')
        genres = []
        if genre_info:
            genre_links = genre_info.find_all('a')
            genres = [a.get_text(strip=True) for a in genre_links]
        result['genres'] = genres
        result['genre'] = ', '.join(genres)

        # Chapters - div#chapter_list ul li
        chapters = []
        chapter_list = soup.find('div', id='chapter_list')
        if chapter_list:
            ul = chapter_list.find('ul')
            if ul:
                lis = ul.find_all('li')
                for li in lis:
                    try:
                        ch = {}

                        # Chapter link and title
                        lchx = li.find('span', class_='lchx')
                        if lchx:
                            a = lchx.find('a')
                            if a:
                                ch['link'] = a.get('href', '')
                                ch['title'] = a.get_text(strip=True)

                                # Extract chapter number
                                chapter_elem = a.find('chapter')
                                if chapter_elem:
                                    ch['chapter_num'] = chapter_elem.get_text(strip=True)

                                # Fix title: add space between Chapter and number
                                ch['title'] = re.sub(r'Chapter\s*(\d+)', r'Chapter \1', ch['title'])

                                # Slug from link
                                ch['slug'] = ch['link'].rstrip('/').split('/')[-1] if ch['link'] else ''

                        # Release date
                        dt = li.find('span', class_='dt')
                        if dt:
                            raw_date = dt.get_text(strip=True)
                            ch['waktu_rilis'] = parse_relative_time_indonesian(raw_date)

                        if ch.get('title'):
                            chapters.append(ch)
                    except Exception as e:
                        pass

        # Chapters di HTML sudah urut dari terbaru, kita reverse untuk urut dari awal
        chapters.reverse()
        result['chapters'] = chapters
        result['total_chapters'] = len(chapters)

        return result

    except Exception as e:
        print(f"      Error parsing detail: {e}")
        return None

def main():
    """
    Fungsi utama untuk scrape data dari komikindo.ch
    dan menghasilkan all-manhwa-metadata.json
    """
    print(" Memulai proses scraping dari komikindo.ch...")
    print(f" Mode: Testing dengan {MAX_COMICS} komik\n")

    # 1. Ambil daftar komik
    comics_list = get_comics_list(max_comics=MAX_COMICS)
    if not comics_list:
        print(" Tidak ada komik yang ditemukan. Berhenti.")
        return

    print(f"\n Memproses detail untuk {len(comics_list)} komik...\n")

    all_metadata = []

    # 2. Loop setiap komik untuk mengambil detailnya
    for index, comic in enumerate(comics_list):
        print(f"  -> ({index + 1}/{len(comics_list)}) {comic['title']}")

        try:
            # Scrape detail page
            detail = scrape_comic_detail(comic['link'])
            if not detail:
                print(f"      Skipping: gagal mengambil detail")
                continue

            # Get latest 2 chapters
            all_chapters = detail.get('chapters', [])
            latest_chapters_formatted = []

            if all_chapters:
                # Ambil 2 chapter terakhir
                latest_chapters_data = all_chapters[-2:]
                latest_chapters_formatted = [
                    {
                        "title": ch.get('title'),
                        "waktu_rilis": ch.get('waktu_rilis'),  # Already in ISO 8601
                        "slug": ch.get('slug')
                    }
                    for ch in reversed(latest_chapters_data)
                ]

            # Tentukan lastUpdateTime dari waktu_rilis chapter terbaru
            # Prioritas: waktu_rilis chapter terbaru → waktu scraping saat ini (fallback)
            if latest_chapters_formatted and latest_chapters_formatted[0].get('waktu_rilis'):
                last_update = latest_chapters_formatted[0]['waktu_rilis']
            else:
                last_update = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+07:00')

            # Susun metadata
            manhwa_data = {
                "slug": comic['slug'],
                "title": detail.get('title', comic['title']),
                "cover_url": detail.get('cover_url', ''),
                "pengarang": detail.get('pengarang', ''),
                "ilustrator": detail.get('ilustrator', ''),
                "genres": detail.get('genres', []),
                "genre": detail.get('genre', ''),
                "type": detail.get('type', 'Manhwa'),
                "status": detail.get('status', 'Ongoing'),
                "rating": detail.get('rating', '0'),
                "total_chapters": detail.get('total_chapters', 0),
                "latestChapters": latest_chapters_formatted,
                "lastUpdateTime": last_update  # ISO 8601 - berdasar waktu rilis chapter terbaru
            }

            all_metadata.append(manhwa_data)
            print(f"      Berhasil: {manhwa_data['total_chapters']} chapters")

            # Delay untuk tidak overload server
            time.sleep(0.5)

        except Exception as e:
            print(f"      Error: {e}")

    print(f"\n Selesai memproses {len(all_metadata)} manhwa.")

    # 3. Pre-sort berdasarkan waktu rilis chapter terbaru (descending)
    # Ini memastikan JSON yang disimpan sudah terurut "Update Terbaru" di atas
    def get_sort_key(item):
        """Ambil timestamp chapter terbaru untuk sorting."""
        chapters = item.get('latestChapters', [])
        if chapters and chapters[0].get('waktu_rilis'):
            return chapters[0]['waktu_rilis']
        return item.get('lastUpdateTime', '1970-01-01T00:00:00+07:00')

    all_metadata.sort(key=get_sort_key, reverse=True)
    print(f" Data telah di-sort berdasarkan chapter terbaru (newest first)")

    # 4. Simpan ke file JSON lokal
    if all_metadata:
        print(f"\n Menyimpan ke '{OUTPUT_FILE}'...")
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_metadata, f, ensure_ascii=False, indent=2)
        print(f" Berhasil menyimpan {len(all_metadata)} item ke {OUTPUT_FILE}")

        # Print sample
        print("\n Sample data:")
        for item in all_metadata[:3]:
            print(f"  - {item['title']} ({item['type']}) - {item['total_chapters']} chapters")

        # 5. Upload ke Supabase
        if supabase:
            print(f"\n Meng-upload ke Supabase Storage...")
            upload_json("all-manhwa-metadata.json", all_metadata)
        else:
            print("\n Supabase tidak dikonfigurasi, skip upload.")
    else:
        print(" Tidak ada data untuk disimpan.")

if __name__ == "__main__":
    main()