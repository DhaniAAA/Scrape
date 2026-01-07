"""
GENERATE COMICS-LIST.JSON FROM SUPABASE BUCKET FOLDERS
=======================================================
Script untuk menggenerate daftar komik (comics-list.json) dari
semua folder yang ada di Supabase Storage bucket.

Logika:
1. List semua objek di bucket 'manga-data'
2. Extract nama folder unik (folder = slug komik)
3. Generate array JSON dengan semua slug
4. Upload ke Supabase sebagai 'comics-list.json'
"""

import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv

# Muat environment variables dari file .env
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
BUCKET_NAME = os.environ.get("BUCKET_NAME", "manga-data")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise EnvironmentError("Pastikan SUPABASE_URL dan SUPABASE_KEY ada di file .env Anda")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_all_folders_from_bucket():
    """
    Mendapatkan semua folder (slug komik) dari bucket Supabase.
    Folder diidentifikasi dari path file (prefix sebelum '/')
    """
    print("📂 Mengambil daftar folder dari bucket Supabase...")

    folders = set()  # Gunakan set untuk menghindari duplikat

    try:
        # List semua file di root bucket
        # Supabase Storage API menggunakan prefix untuk navigasi folder
        response = supabase.storage.from_(BUCKET_NAME).list(
            path="",  # Root path
            options={
                "limit": 1000,  # Maksimum item per request
                "offset": 0,
            }
        )

        if response:
            for item in response:
                name = item.get('name', '')

                # Cek apakah ini folder (biasanya folder memiliki metadata khusus)
                # atau kita bisa cek dari nama yang tidak memiliki ekstensi file
                if name and not name.endswith('.json'):
                    # Ini kemungkinan folder
                    folders.add(name)
                elif name and '/' in name:
                    # Extract folder name dari path
                    folder_name = name.split('/')[0]
                    folders.add(folder_name)

        # Jika tidak menemukan folder dengan cara di atas,
        # coba pendekatan lain - list dengan search pattern
        if not folders:
            print("⚠️  Mencoba pendekatan alternatif...")
            # Beberapa implementasi Supabase memerlukan pendekatan berbeda
            # List semua item dan extract folder dari path
            all_items = supabase.storage.from_(BUCKET_NAME).list()

            for item in all_items:
                name = item.get('name', '')
                # Folder di Supabase biasanya ditandai dengan id=None atau metadata khusus
                item_id = item.get('id')

                # Jika tidak ada id dan bukan file JSON di root, kemungkinan folder
                if name and not name.endswith('.json') and not name.endswith('.png'):
                    folders.add(name)

        print(f"✅ Ditemukan {len(folders)} folder")
        return sorted(list(folders))  # Return sebagai sorted list

    except Exception as e:
        print(f"❌ Error saat mengambil daftar folder: {e}")
        return []


def get_folders_by_listing_subfolders():
    """
    Mendapatkan folder dengan listing semua item di root bucket.
    Menggunakan pagination untuk handle lebih dari 100 folder.
    """
    print("📂 Mengambil daftar folder dari bucket...")

    folders = []
    offset = 0
    limit = 100  # Supabase default limit

    try:
        while True:
            print(f"   → Fetching offset {offset}...")

            # List root folder dengan pagination
            root_items = supabase.storage.from_(BUCKET_NAME).list(
                path="",
                options={
                    "limit": limit,
                    "offset": offset,
                    "sortBy": {"column": "name", "order": "asc"}
                }
            )

            if not root_items:
                # Tidak ada lagi item
                break

            items_found = 0
            for item in root_items:
                name = item.get('name', '')
                item_id = item.get('id')
                metadata = item.get('metadata')

                # Di Supabase Storage:
                # - Folder memiliki id=None dan metadata=None
                # - File memiliki id (UUID) dan metadata dengan mimetype

                if item_id is None and metadata is None and name:
                    # Ini adalah folder
                    folders.append(name)
                    items_found += 1
                elif name and '/' not in name and not any(name.endswith(ext) for ext in ['.json', '.png', '.jpg', '.webp', '.txt']):
                    # Fallback: jika tidak ada ekstensi file, anggap sebagai folder
                    folders.append(name)
                    items_found += 1

            print(f"      Found {items_found} folders in this batch")

            # Jika item yang dikembalikan kurang dari limit, berarti sudah habis
            if len(root_items) < limit:
                break

            # Lanjut ke batch berikutnya
            offset += limit

        # Hapus duplikat dan sort
        folders = sorted(list(set(folders)))
        print(f"✅ Total ditemukan {len(folders)} folder")
        return folders

    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def upload_comics_list(comics_list):
    """Upload comics-list.json ke Supabase Storage"""
    try:
        json_data = json.dumps(comics_list, indent=2, ensure_ascii=False)
        json_bytes = json_data.encode('utf-8')

        file_path = "comics-list.json"

        # Coba upload (akan error jika sudah ada)
        try:
            supabase.storage.from_(BUCKET_NAME).upload(
                file_path,
                json_bytes,
                {"content-type": "application/json"}
            )
            print(f"✅ Berhasil upload {file_path}")
        except Exception as e:
            if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                # Update jika sudah ada
                supabase.storage.from_(BUCKET_NAME).update(
                    file_path,
                    json_bytes,
                    {"content-type": "application/json"}
                )
                print(f"✅ Berhasil update {file_path}")
            else:
                raise e

    except Exception as e:
        print(f"❌ Gagal upload: {e}")


def save_local(comics_list, filename="comics-list.json"):
    """Simpan juga ke file lokal"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(comics_list, f, indent=2, ensure_ascii=False)
    print(f"💾 Disimpan ke lokal: {filename}")


def main():
    print("=" * 60)
    print("GENERATE COMICS-LIST.JSON FROM SUPABASE FOLDERS")
    print("=" * 60)
    print(f"📦 Bucket: {BUCKET_NAME}")
    print()

    # Coba metode utama
    comics_list = get_folders_by_listing_subfolders()

    # Jika gagal, coba metode alternatif
    if not comics_list:
        comics_list = get_all_folders_from_bucket()

    if not comics_list:
        print("\n❌ Tidak dapat mengambil daftar folder dari bucket.")
        print("   Pastikan bucket tidak kosong dan credentials benar.")
        return

    # Tampilkan sample
    print(f"\n📋 Sample folder (5 pertama):")
    for slug in comics_list[:5]:
        print(f"   - {slug}")

    if len(comics_list) > 5:
        print(f"   ... dan {len(comics_list) - 5} lainnya")

    print(f"\n📊 Total: {len(comics_list)} komik")

    # Simpan ke lokal
    save_local(comics_list)

    # Upload ke Supabase
    print("\n☁️  Mengupload ke Supabase...")
    upload_comics_list(comics_list)

    print("\n" + "=" * 60)
    print("✅ SELESAI!")
    print("=" * 60)


if __name__ == "__main__":
    main()
