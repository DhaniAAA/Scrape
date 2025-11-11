import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime

# Muat environment variables dari file .env
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") # Gunakan ANON key, atau SERVICE KEY jika perlu
BUCKET_NAME = os.environ.get("BUCKET_NAME", "manga-data")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise EnvironmentError("Pastikan SUPABASE_URL dan SUPABASE_KEY ada di file .env Anda")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def download_json(path: str):
    """Helper untuk men-download file JSON dari Supabase."""
    try:
        response = supabase.storage.from_(BUCKET_NAME).download(path)
        return json.loads(response.decode('utf-8'))
    except Exception as e:
        print(f"Gagal men-download {path}: {e}")
        return None

def upload_json(path: str, data: dict | list):
    """Helper untuk meng-upload file JSON ke Supabase (menimpa jika sudah ada)."""
    try:
        # Ubah data ke string JSON
        json_data = json.dumps(data, indent=2)
        # Ubah string ke bytes
        json_bytes = json_data.encode('utf-8')
        
        # Upload
        supabase.storage.from_(BUCKET_NAME).upload(
            path,
            json_bytes,
            {"content-type": "application/json", "upsert": "true"}
        )
        print(f"\n✅ Berhasil meng-upload {path}")
    except Exception as e:
        print(f"\n❌ Gagal meng-upload {path}: {e}")

def get_waktu_rilis_timestamp(chapter: dict) -> int:
    """Helper untuk mengubah 'waktu_rilis' menjadi timestamp epoch milidetik."""
    waktu_rilis_str = chapter.get('waktu_rilis')
    if not waktu_rilis_str:
        return 0
        
    try:
        # Coba parse format ISO 8601 (e.g., "2023-12-20T10:00:00Z")
        dt = datetime.fromisoformat(waktu_rilis_str.replace('Z', '+00:00'))
    except ValueError:
        try:
            # Coba format lain jika perlu, misal "January 10, 2024"
            # Ini harus disesuaikan dengan format 'waktu_rilis' Anda
            dt = datetime.strptime(waktu_rilis_str, '%B %d, %Y')
        except Exception:
            # Gagal parse, kembalikan 0
            return 0
            
    # Kembalikan sebagai epoch milidetik
    return int(dt.timestamp() * 1000)

def main():
    """
    Fungsi utama untuk mengambil semua data individual dan menggabungkannya
    menjadi 'all-manhwa-metadata.json'.
    """
    print("🚀 Memulai proses pembuatan metadata gabungan...")
    
    # 1. Ambil daftar komik (cara lama, yang dilakukan scraper)
    comics_list = download_json("comics-list.json")
    if not comics_list:
        print("❌ Gagal mengambil comics-list.json. Berhenti.")
        return

    print(f"📚 Ditemukan {len(comics_list)} komik. Memproses satu per satu...")

    all_metadata = []
    
    # 2. Loop setiap komik untuk mengambil datanya (N+1 query)
    # Ini lambat, tapi ini adalah tugas scraper, bukan aplikasi web
    for index, slug in enumerate(comics_list):
        print(f"  -> Memproses ({index + 1}/{len(comics_list)}): {slug}")
        
        try:
            # Ambil metadata individual
            metadata = download_json(f"{slug}/metadata.json")
            if not metadata:
                print(f"     ⚠️  Skipping: metadata.json tidak ditemukan untuk {slug}")
                continue

            # Ambil chapters individual
            chapters_data = download_json(f"{slug}/chapters.json")
            if not chapters_data or not chapters_data.get('chapters'):
                print(f"     ⚠️  Skipping: chapters.json tidak ditemukan untuk {slug}")
                continue
            
            all_chapters = chapters_data.get('chapters', [])
            
            # 3. Ekstrak data yang diperlukan
            latest_chapters_data = all_chapters[-2:] # Ambil 2 chapter terakhir
            latest_chapters_formatted = []
            
            if latest_chapters_data:
                latest_chapters_formatted = [
                    {
                        "title": ch.get('title'),
                        "waktu_rilis": ch.get('waktu_rilis'),
                        "slug": ch.get('slug')
                    }
                    for ch in reversed(latest_chapters_data) # Balik urutan (terbaru dulu)
                ]

            # Dapatkan timestamp rilis chapter terakhir
            last_update_time = 0
            if all_chapters:
                last_update_time = get_waktu_rilis_timestamp(all_chapters[-1])

            # 4. Susun objek metadata gabungan
            manhwa_data = {
                "slug": slug,
                "title": metadata.get('title', 'Tanpa Judul'),
                "cover_url": metadata.get('cover_url'),
                "genres": metadata.get('genres', []),
                "genre": ", ".join(metadata.get('genres', [])),
                "type": metadata.get('type') or metadata.get('metadata', {}).get('Type', 'manhwa'),
                "status": metadata.get('status') or metadata.get('metadata', {}).get('Status', 'Ongoing'),
                "rating": metadata.get('rating') or '9.0',
                "total_chapters": metadata.get('total_chapters', 0),
                "latestChapters": latest_chapters_formatted,
                "lastUpdateTime": last_update_time # Timestamp untuk sorting
            }
            
            all_metadata.append(manhwa_data)

        except Exception as e:
            print(f"     ❌ Error memproses {slug}: {e}")

    print(f"\n✨ Selesai memproses {len(all_metadata)} manhwa.")
    
    # 5. Upload file gabungan
    if all_metadata:
        print("☁️  Meng-upload 'all-manhwa-metadata.json' ke Supabase...")
        upload_json("all-manhwa-metadata.json", all_metadata)
    else:
        print("⚠️ Tidak ada data untuk di-upload.")

if __name__ == "__main__":
    main()