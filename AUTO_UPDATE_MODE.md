# 🔄 Auto Update Mode - Cek Semua Komik Otomatis

## 🎯 Fitur Baru

**Auto Update Mode** = Otomatis cek semua komik dan hanya scrape yang ada chapter baru!

---

## 📋 Cara Menggunakan

### **Aktifkan Auto Update Mode:**

Edit `scrape_links_only.py`:

```python
# Auto Update Mode (cek semua komik yang ada chapter baru)
AUTO_UPDATE_MODE = True  # Aktifkan
AUTO_UPDATE_MAX_COMICS = 20  # Max komik yang di-cek per run
```

### **Run Script:**

```bash
python scrape_links_only.py
```

---

## 🔍 Cara Kerja

### **Step 1: Scan Komik**

Script akan cek setiap komik satu per satu:

```
🔄 AUTO UPDATE MODE AKTIF
→ Mengecek komik yang ada chapter baru...
→ Max komik per run: 20
→ Total komik di database: 142

  [1/20] Checking: Piquant ⏭️  No update (50 chapters)
  [2/20] Checking: Legend of the Northern Blade ✅ 5 chapter baru! (205 → 210)
  [3/20] Checking: Murim Login ⏭️  No update (100 chapters)
  [4/20] Checking: Eleceed ✅ 10 chapter baru! (373 → 383)
  ...
```

---

### **Step 2: Hasil Scan**

```
📊 Hasil scan:
   - Komik di-cek: 20
   - Komik dengan update: 2

→ Akan scrape 2 komik dengan chapter baru
→ Index: [1, 3]
```

---

### **Step 3: Scrape Chapter Baru**

Hanya scrape komik yang ada update:

```
============================================================
[2] Memproses: Legend of the Northern Blade
============================================================
  📁 Chapter yang sudah ada: 205

📸 Scraping image links dari 210 chapters...

  Chapter [1-205]: ✅ Skip (sudah ada)
  Chapter [206-210]: ✅ Scrape (baru!)

📤 Uploading ke Supabase...
  ✓ All chapters uploaded: chapters.json (210 chapters)
```

---

## 📊 Perbandingan Mode

### **Mode 1: Normal Mode**

```python
AUTO_UPDATE_MODE = False
RESCRAPE_MODE = False
MAX_COMICS_TO_PROCESS = 5
```

**Behavior:**
- Scrape 5 komik berikutnya dari progress
- Tidak peduli ada update atau tidak
- Cocok untuk scraping pertama kali

---

### **Mode 2: Re-scrape Mode (Manual)**

```python
AUTO_UPDATE_MODE = False
RESCRAPE_MODE = True
RESCRAPE_INDICES = [0, 1, 2]
```

**Behavior:**
- Scrape komik tertentu yang dipilih manual
- Harus tahu index komik mana yang ada update
- Cocok untuk update komik spesifik

---

### **Mode 3: Auto Update Mode (Recommended)** ⭐

```python
AUTO_UPDATE_MODE = True
AUTO_UPDATE_MAX_COMICS = 20
```

**Behavior:**
- **Otomatis cek** semua komik
- **Hanya scrape** yang ada chapter baru
- **Tidak perlu** pilih manual
- Cocok untuk **daily update**

---

## ⚙️ Konfigurasi

### **AUTO_UPDATE_MAX_COMICS**

Jumlah maksimal komik yang di-cek per run:

```python
AUTO_UPDATE_MAX_COMICS = 20  # Cek 20 komik pertama
```

**Kenapa perlu limit?**
- Avoid timeout (cek 142 komik = lama)
- Bisa run berkali-kali untuk cek semua

**Rekomendasi:**
- **Daily update:** 20-30 komik
- **Weekly update:** 50-100 komik

---

## 🧪 Testing

### **Test 1: Tidak Ada Update**

```bash
python scrape_links_only.py
```

**Output:**
```
🔄 AUTO UPDATE MODE AKTIF
→ Mengecek komik yang ada chapter baru...

  [1/20] Checking: Piquant ⏭️  No update (50 chapters)
  [2/20] Checking: Legend ⏭️  No update (205 chapters)
  ...
  [20/20] Checking: Nano Machine ⏭️  No update (150 chapters)

📊 Hasil scan:
   - Komik di-cek: 20
   - Komik dengan update: 0

✅ Tidak ada komik dengan chapter baru!
```

**Script selesai tanpa scraping** ✅

---

### **Test 2: Ada Update**

```bash
python scrape_links_only.py
```

**Output:**
```
🔄 AUTO UPDATE MODE AKTIF
→ Mengecek komik yang ada chapter baru...

  [1/20] Checking: Piquant ⏭️  No update (50 chapters)
  [2/20] Checking: Legend ✅ 5 chapter baru! (205 → 210)
  [3/20] Checking: Murim ⏭️  No update (100 chapters)
  [4/20] Checking: Eleceed ✅ 10 chapter baru! (373 → 383)
  ...

📊 Hasil scan:
   - Komik di-cek: 20
   - Komik dengan update: 2

→ Akan scrape 2 komik dengan chapter baru
→ Index: [1, 3]

============================================================
[2] Memproses: Legend of the Northern Blade
============================================================
  📁 Chapter yang sudah ada: 205
  
  Chapter [206-210]: ✅ Scrape (5 chapter baru)

============================================================
[4] Memproses: Eleceed
============================================================
  📁 Chapter yang sudah ada: 373
  
  Chapter [374-383]: ✅ Scrape (10 chapter baru)
```

**Hanya scrape 2 komik yang ada update** ✅

---

## 📈 Performance

### **Skenario: Daily Update (20 komik)**

#### **Tanpa Auto Update Mode:**

```
Scrape 20 komik (blind):
- 18 komik tidak ada update → buang waktu
- 2 komik ada update → berguna

Time: ~30 menit (scrape semua)
Efficiency: 10%
```

---

#### **Dengan Auto Update Mode:**

```
Check 20 komik:
- 18 komik tidak ada update → skip
- 2 komik ada update → scrape

Time: ~5 menit (check + scrape 2 komik)
Efficiency: 100%
```

**Hemat:** ~25 menit (83% faster) ⚡

---

## 🔄 Workflow Daily Update

### **Recommended Workflow:**

```bash
# Pagi (08:00)
# Cek 20 komik pertama
AUTO_UPDATE_MAX_COMICS = 20
python scrape_links_only.py

# Siang (12:00)
# Cek 20 komik berikutnya (21-40)
# Edit manhwa_list.json atau gunakan offset
python scrape_links_only.py

# Sore (16:00)
# Cek 20 komik berikutnya (41-60)
python scrape_links_only.py
```

**Atau gunakan cron job:**

```bash
# Linux/Mac crontab
0 8,12,16 * * * cd /path/to/scrape && python scrape_links_only.py

# Windows Task Scheduler
# Run at 08:00, 12:00, 16:00 daily
```

---

## 💡 Tips & Tricks

### **Tip 1: Prioritas Komik Populer**

Urutkan `manhwa_list.json` berdasarkan popularitas:

```json
[
  { "Title": "Solo Leveling", ... },      // Populer, sering update
  { "Title": "Tower of God", ... },       // Populer
  { "Title": "Obscure Comic", ... }       // Jarang update
]
```

Auto update akan cek dari atas, jadi komik populer di-cek duluan.

---

### **Tip 2: Adjust Max Comics**

```python
# Untuk komik yang sering update
AUTO_UPDATE_MAX_COMICS = 10  # Cek 10 komik populer

# Untuk cek semua
AUTO_UPDATE_MAX_COMICS = 100  # Cek banyak komik
```

---

### **Tip 3: Kombinasi dengan Re-scrape**

```python
# Hari biasa: Auto update
AUTO_UPDATE_MODE = True

# Hari tertentu: Manual re-scrape komik spesifik
AUTO_UPDATE_MODE = False
RESCRAPE_MODE = True
RESCRAPE_INDICES = [0, 1, 2]
```

---

### **Tip 4: Monitor Log**

Simpan log untuk tracking:

```bash
python scrape_links_only.py > log_$(date +%Y%m%d).txt 2>&1
```

---

## 🎯 Use Cases

### **Use Case 1: Daily Update**

```python
AUTO_UPDATE_MODE = True
AUTO_UPDATE_MAX_COMICS = 20
```

**Goal:** Update chapter baru setiap hari  
**Frequency:** 1-3x per hari  
**Time:** ~5-10 menit per run

---

### **Use Case 2: Weekly Batch**

```python
AUTO_UPDATE_MODE = True
AUTO_UPDATE_MAX_COMICS = 100
```

**Goal:** Update semua komik seminggu sekali  
**Frequency:** 1x per minggu  
**Time:** ~30-60 menit per run

---

### **Use Case 3: Specific Comics**

```python
AUTO_UPDATE_MODE = False
RESCRAPE_MODE = True
RESCRAPE_TITLES = ["Solo Leveling", "Tower of God"]
```

**Goal:** Update komik tertentu saja  
**Frequency:** On-demand  
**Time:** ~2-5 menit

---

## 📊 Statistics

### **Example Output:**

```
🔄 AUTO UPDATE MODE AKTIF
→ Mengecek komik yang ada chapter baru...
→ Max komik per run: 20
→ Total komik di database: 142

  [1/20] Checking: Piquant ⏭️  No update (50 chapters)
  [2/20] Checking: Legend ✅ 5 chapter baru! (205 → 210)
  [3/20] Checking: Murim ⏭️  No update (100 chapters)
  [4/20] Checking: Eleceed ✅ 10 chapter baru! (373 → 383)
  [5/20] Checking: Nano Machine ⏭️  No update (150 chapters)
  ...
  [20/20] Checking: Mercenary ✅ 3 chapter baru! (120 → 123)

📊 Hasil scan:
   - Komik di-cek: 20
   - Komik dengan update: 3
   - Update rate: 15%

→ Akan scrape 3 komik dengan chapter baru
→ Total chapter baru: 18 chapters (5 + 10 + 3)
```

---

## ⚠️ Limitations

### **1. Max Comics per Run**

Tidak bisa cek semua 142 komik sekaligus (timeout risk).

**Solusi:** Run berkali-kali atau naikkan limit.

---

### **2. Network Delay**

Setiap check butuh 1-2 detik (scrape detail).

**Solusi:** Sudah ada delay 0.5s antar check.

---

### **3. False Positive**

Jika website down, bisa detect sebagai "no update".

**Solusi:** Check error handling di log.

---

## 🎯 Kesimpulan

### **Sebelum (Manual):**
- ❌ Harus pilih komik manual
- ❌ Tidak tahu mana yang ada update
- ❌ Buang waktu scrape yang tidak perlu

### **Sesudah (Auto Update):**
- ✅ Otomatis cek semua komik
- ✅ Hanya scrape yang ada update
- ✅ Hemat waktu hingga 83%

---

**Perfect untuk Daily Update Workflow! 🔄⚡**
