# 📸 Panduan Scrape Image Links Only

## 🎯 Tujuan

Scrape **link gambar** dari manga/komik **tanpa download/upload** gambar. Hasil disimpan dalam format JSON.

---

## 🚀 Cara Menggunakan

### 1. Jalankan Script

```bash
python scrape_links_only.py
```

### 2. Output

Script akan membuat file **`manga_image_links.json`** dengan struktur:

```json
[
  {
    "slug": "piquant",
    "title": "Piquant",
    "url": "https://komikcast03.com/komik/piquant/",
    "cover_url": "https://komikcast03.com/wp-content/uploads/2019/12/cover.jpg",
    "genres": ["Action", "Drama", "Romance"],
    "synopsis": "Synopsis komik...",
    "metadata": {
      "Type": "Manhwa",
      "Status": "Ongoing",
      "Author": "Author Name"
    },
    "total_chapters": 50,
    "chapters": [
      {
        "slug": "chapter-01",
        "title": "Chapter 01",
        "url": "https://komikcast03.com/chapter/piquant-chapter-01/",
        "waktu_rilis": "2 days ago",
        "total_images": 25,
        "images": [
          "https://sv3.imgkc3.my.id/wp-content/img/00/-PIQUANT-/001/001.jpg",
          "https://sv3.imgkc3.my.id/wp-content/img/00/-PIQUANT-/001/002.jpg",
          "https://sv3.imgkc3.my.id/wp-content/img/00/-PIQUANT-/001/003.jpg"
        ]
      },
      {
        "slug": "chapter-02",
        "title": "Chapter 02",
        "url": "https://komikcast03.com/chapter/piquant-chapter-02/",
        "waktu_rilis": "1 day ago",
        "total_images": 23,
        "images": [
          "https://sv3.imgkc3.my.id/wp-content/img/00/-PIQUANT-/002/001.jpg",
          "https://sv3.imgkc3.my.id/wp-content/img/00/-PIQUANT-/002/002.jpg"
        ]
      }
    ]
  }
]
```

---

## 📊 Struktur Data Output

### Root Level (Array of Comics)

| Field | Type | Description |
|-------|------|-------------|
| `slug` | string | Nama komik (sanitized, lowercase, dash-separated) |
| `title` | string | Judul komik original |
| `url` | string | URL halaman detail komik |
| `cover_url` | string | URL cover image |
| `genres` | array | List genre |
| `synopsis` | string | Sinopsis komik |
| `metadata` | object | Metadata (Type, Status, Author, dll) |
| `total_chapters` | number | Jumlah total chapter |
| `chapters` | array | Array of chapters |

### Chapter Level

| Field | Type | Description |
|-------|------|-------------|
| `slug` | string | Nama chapter (sanitized) |
| `title` | string | Judul chapter original |
| `url` | string | URL halaman chapter |
| `waktu_rilis` | string | Waktu rilis chapter |
| `total_images` | number | Jumlah gambar di chapter |
| `images` | array | Array of image URLs |

---

## ⚙️ Konfigurasi

Edit `scrape_links_only.py` baris 9-12:

```python
JSON_FILE = 'komikcast_scrape_results.json'  # Input file
OUTPUT_FILE = 'manga_image_links.json'  # Output file
MAX_COMICS_TO_PROCESS = 5  # Jumlah komik per run
PROGRESS_FILE = 'scrape_links_progress.json'  # Progress tracking
```

---

## 🔍 Selector yang Digunakan

Script menggunakan selector `.main-reading-area` untuk scrape gambar:

```python
reading_area = soup.select_one('.main-reading-area')
images = reading_area.find_all('img')

for img in images:
    image_url = img.get('src')
    if image_url and image_url.startswith('http'):
        image_urls.append(image_url)
```

**HTML yang di-scrape:**
```html
<div class="main-reading-area">
    <img src="https://sv3.imgkc3.my.id/.../001.jpg">
    <img src="https://sv3.imgkc3.my.id/.../002.jpg">
    <img src="https://sv3.imgkc3.my.id/.../003.jpg">
</div>
```

---

## 📈 Output Console

```
============================================================
MANGA IMAGE LINKS SCRAPER
============================================================

→ Akan memproses 5 komik
→ Index: 0 hingga 4
→ Total komik di database: 841

============================================================
[1] Memproses: Piquant
============================================================
  → Mengambil detail dari: https://komikcast03.com/komik/piquant/
  📊 Status: Ongoing | Total Chapters: 50

📸 Scraping image links dari 50 chapters...

  Chapter [1/50]: Chapter 01
    ✅ Ditemukan 25 gambar

  Chapter [2/50]: Chapter 02
    ✅ Ditemukan 23 gambar

  Chapter [3/50]: Chapter 03
    ✅ Ditemukan 27 gambar

============================================================
✓ Komik 'Piquant' selesai di-scrape!
  📊 Total chapters: 50
  📸 Total image links: 1,250
============================================================

💾 Progress saved: 1/841

============================================================
✅ SCRAPING SELESAI!
============================================================
📁 Output file: manga_image_links.json
📊 Total komik di-scrape: 5
📚 Total chapters: 250
📸 Total image links: 6,250
============================================================
```

---

## 🔄 Resume Support

Script support resume jika di-stop:

1. **Progress disimpan** di `scrape_links_progress.json`
2. **Output incremental** - setiap komik selesai langsung disave
3. **Jalankan lagi** - otomatis lanjut dari terakhir

**Progress file:**
```json
{
  "last_processed_index": 4,
  "scraped_comics": [
    "Piquant",
    "Kimetsu no Yaiba",
    "One Piece"
  ]
}
```

---

## 💡 Use Cases

### 1. **Backend API**
Gunakan JSON untuk serve image links via API:

```javascript
// Express.js example
app.get('/api/manga/:slug/chapter/:chapterSlug', (req, res) => {
  const data = require('./manga_image_links.json');
  const manga = data.find(m => m.slug === req.params.slug);
  const chapter = manga.chapters.find(c => c.slug === req.params.chapterSlug);
  res.json(chapter.images);
});
```

### 2. **Frontend Reader**
Load images on-demand:

```javascript
// React example
const images = chapter.images;
images.map((url, idx) => (
  <img key={idx} src={url} loading="lazy" />
));
```

### 3. **Batch Download**
Download nanti dengan script terpisah:

```python
import requests
data = json.load(open('manga_image_links.json'))
for comic in data:
    for chapter in comic['chapters']:
        for url in chapter['images']:
            # Download logic here
```

### 4. **Database Import**
Import ke database:

```sql
INSERT INTO manga (slug, title, cover_url, ...)
VALUES (?, ?, ?, ...);

INSERT INTO chapters (manga_id, slug, title, ...)
VALUES (?, ?, ?, ...);

INSERT INTO images (chapter_id, url, position)
VALUES (?, ?, ?);
```

---

## ⚡ Performa

### Kecepatan
- **Scrape only** (no download): ~2-3 detik per chapter
- **1 komik (50 chapters)**: ~2-3 menit
- **100 komik**: ~3-5 jam

### Bandwidth
- **Minimal** - hanya HTML scraping
- **No image download** - hemat bandwidth
- **~1-2 KB per chapter** (HTML only)

### Storage
- **JSON file size**: ~100-500 KB per 100 komik
- **No images stored** - hanya links

---

## 🎯 Keuntungan

| Aspect | Scrape Links Only | Download & Upload |
|--------|-------------------|-------------------|
| **Speed** | ⚡ Very Fast (2-3 sec/chapter) | 🐌 Slow (30-60 sec/chapter) |
| **Bandwidth** | 💚 Minimal (~1 KB/chapter) | 🔴 Heavy (~5-10 MB/chapter) |
| **Storage** | 💚 Tiny (JSON only) | 🔴 Large (images stored) |
| **Flexibility** | ✅ Download later if needed | ❌ Must download now |
| **Cost** | 💚 Free (no storage cost) | 💰 Paid (Supabase storage) |

---

## 🔧 Customization

### Scrape Lebih Banyak Komik

```python
MAX_COMICS_TO_PROCESS = 100  # Scrape 100 komik per run
```

### Ubah Output File

```python
OUTPUT_FILE = 'my_manga_links.json'
```

### Tambah Delay (Avoid Rate Limit)

```python
time.sleep(2)  # 2 detik delay antar chapter
```

---

## 📞 Troubleshooting

### Error: "Tidak menemukan .main-reading-area"

**Penyebab:** Selector berubah atau halaman berbeda

**Solusi:** Cek HTML source dan update selector

### Image URLs Tidak Lengkap

**Penyebab:** Lazy loading atau JavaScript rendering

**Solusi:** Gunakan Selenium untuk dynamic content

### Rate Limited

**Penyebab:** Terlalu banyak request

**Solusi:** Tambah delay di `time.sleep()`

---

## 🚀 Next Steps

Setelah punya JSON links, Anda bisa:

1. **Build API** - Serve links via REST API
2. **Create Reader** - Frontend manga reader
3. **Batch Download** - Download images nanti
4. **Database Import** - Import ke PostgreSQL/MySQL
5. **CDN Upload** - Upload ke CDN dengan script terpisah

---

**Happy Scraping! 📸**
