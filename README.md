# 📊 Dashboard Analisis Pasar Kerja IT (Pulau Jawa)

Project ini adalah sebuah **Dashboard Interaktif** yang dibangun menggunakan [Streamlit](https://streamlit.io/) untuk menganalisis tren lowongan kerja IT di Pulau Jawa. Data diambil secara **real-time** (live scraping) dari situs lowongan kerja terkemuka seperti **Loker.id** dan **Kalibrr**.

## 🚀 Fitur Utama

-   **📡 Live Scraping Multi-Source**:
    -   **Loker.id**: Scraping lowongan kerja IT terbaru atau berdasarkan kata kunci pencarian.
    -   **Kalibrr**: Scraping lowongan kerja IT dengan dukungan pencarian spesifik.
    -   Restriksi otomatis ke kategori **Information Technology** untuk memastikan relevansi data.

-   **🔍 Pencarian & Filter Canggih**:
    -   Cari lowongan berdasarkan **Kata Kunci** (misal: "Python", "Data Analyst", "Backend").
    -   Filter hasil visualisasi berdasarkan **Posisi**, **Provinsi**, dan **Pendidikan**.

-   **📈 Visualisasi Data Interaktif**:
    -   **Peta Sebaran 3D (PyDeck)**: Visualisasi lokasi lowongan kerja dalam bentuk Hexagon Layer 3D.
    -   **Distribusi Gaji**: Histogram rentang gaji yang ditawarkan.
    -   **Top Skill Analysis**: Grafik batang skill teknis yang paling banyak dibutuhkan (hasil text mining dari deskripsi pekerjaan).
    -   **Analisis Pendidikan**: Pie chart kualifikasi pendidikan yang diminta.

-   **💾 Manajemen Data (Scrape, Accumulate, Clean)**:
    -   **Akumulasi Data**: Data hasil scraping akan terus ditambahkan (append) selama sesi aktif, memungkinkan Anda mengumpulkan data dari berbagai pencarian (misal: Scrape "Python" di Loker.id lalu Scrape "Java" di Kalibrr).
    -   **Preview Data**: Lihat tabel preview data terbaru hasil scraping langsung di sidebar.
    -   **Pembersihan Data Otomatis**: Fitur **"Bersihkan & Gabung Data"** untuk menghapus duplikasi (berdasarkan link atau nama perusahaan/posisi) dan menstandarisasi format data (gaji numerik, dll).
    -   **Upload CSV**: Kemampuan untuk mengupload dataset eksternal (CSV) untuk dianalisis bersamaan.

## 🛠️ Instalasi & Cara Menjalankan

### Prasyarat
Pastikan Anda sudah menginstal [Python 3.8+](https://www.python.org/downloads/) dan [Google Chrome](https://www.google.com/chrome/) (untuk Selenium webdriver).

### 1. Clone Repository (atau Download)
Simpan semua file project dalam satu folder.

### 2. Install Dependensi
Jalankan perintah berikut di terminal/command prompt untuk menginstal library yang dibutuhkan:

```bash
pip install -r requirements.txt
```

### 3. Jalankan Aplikasi
Jalan aplikasi Streamlit dengan perintah:

```bash
streamlit run app.py
```

Aplikasi akan otomatis terbuka di browser Anda (biasanya di `http://localhost:8501`).

## 📂 Struktur Project

```
├── app.py                      # Main application file (Streamlit Dashboard)
├── requirements.txt            # List library python yang dibutuhkan
├── data/
│   └── data_loker_clean.csv    # (Opsional) Data awal/historis jika ada
└── scrapping/
    ├── lokerid_script.py       # Script scraping untuk Loker.id (Requests + BS4)
    └── kalibrr_script.py       # Script scraping untuk Kalibrr (Selenium + BS4)
```

## 📝 Catatan Penggunaan

-   **Scraping Kalibrr**: Menggunakan **Selenium** (Headless Chrome). Proses ini mungkin memakan waktu sedikit lebih lama dibandingkan Loker.id karena perlu merender JavaScript halaman web.
-   **Anti-Bot**: Script scraping dilengkapi dengan `time.sleep` random untuk menghindari pemblokiran IP. Jangan melakukan scraping terlalu agresif (jumlah data sangat besar dalam waktu singkat).
-   **Data Reset**: Jika Anda merefresh halaman browser (F5), data hasil scraping di sesi tersebut akan hilang. Pastikan untuk menganalisis data sebelum refresh.

## 👨‍💻 Teknologi yang Digunakan
-   **Python**: Bahasa pemrograman utama.
-   **Streamlit**: Framework untuk membuat dashboard web.
-   **Pandas**: Manipulasi dan analisis data frame.
-   **Plotly & PyDeck**: Visualisasi grafik dan peta interaktif.
-   **BeautifulSoup4**: Parsing HTML untuk scraping.
-   **Selenium**: Otomasi browser untuk scraping website dinamis (Kalibrr).

---
*Dibuat untuk Tugas Besar Pemrograman Dasar Sains Data.*
