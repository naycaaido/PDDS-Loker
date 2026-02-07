import streamlit as st
import pandas as pd
import plotly.express as px
import ast
from collections import Counter
import numpy as np
import pydeck as pdk 
from scrapping.kalibrr_script import run_scraper as run_scraper_kalibrr
import time 
import warnings

# Suppress PyDeck deprecation warnings in Streamlit logs
warnings.filterwarnings("ignore", category=UserWarning, module="streamlit")
warnings.filterwarnings("ignore", message=".*use_container_width.*") 

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Dashboard Loker IT Jawa",
    page_icon="💻",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. LOAD GOOGLE ICONS & CUSTOM CSS ---
# Kita inject Link Google Material Icons di sini
st.markdown("""
<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
<style>
    /* CSS untuk Google Icons agar sejajar dengan teks */
    .material-icons {
        vertical-align: middle;
        margin-right: 5px;
        font-size: 1.2em;
    }

    /* CSS Metric Cards (yg sebelumnya) */
    div[data-testid="stMetric"] {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.2);
        padding: 15px;
        border-radius: 10px;
        color: var(--text-color);
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    /* --- TAMBAHAN BARU DI SINI --- */
    
    /* 2. Chart Cards: Membuat Grafik punya frame "Kartu" */
    div[data-testid="stPlotlyChart"] {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.2);
        padding: 10px;              /* Jarak antara grafik dan tepi kartu */
        border-radius: 10px;        /* Sudut melengkung */
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1); /* Bayangan halus */
    }

    /* 3. Hover Effect: Efek interaktif saat mouse diarahkan ke grafik */
    div[data-testid="stPlotlyChart"]:hover {
        border-color: rgba(128, 128, 128, 0.5); /* Border jadi lebih tegas */
        box-shadow: 4px 4px 10px rgba(0,0,0,0.15); /* Bayangan membesar */
        transition: all 0.3s ease; /* Transisi halus */
    }

    /* 4. Merapikan Header di atas Grafik */
    h3 {
        padding-bottom: 10px; /* Memberi jarak antara Judul dan Grafik */
    }
    
    div[data-testid="stMetricLabel"] > label {
        color: var(--text-color) !important;
    }
    h1, h2, h3 { color: var(--text-color); }
    hr { margin-top: 1em; margin-bottom: 1em; border: 0; border-top: 1px solid rgba(128, 128, 128, 0.2); }
</style>
""", unsafe_allow_html=True)

# Helper Function biar gampang panggil icon
def icon(icon_name):
    return f'<span class="material-icons">{icon_name}</span>'
# --- 3. PERSIAPAN DATA ---

# --- 3. PERSIAPAN DATA ---

# A. DATABASE KOORDINAT
koordinat_kota = {
    "Jakarta Raya": [-6.2088, 106.8456], "Jakarta Selatan": [-6.2615, 106.8106],
    "Jakarta Barat": [-6.1674, 106.7637], "Jakarta Pusat": [-6.1751, 106.8650],
    "Jakarta Timur": [-6.2250, 106.9004], "Jakarta Utara": [-6.1384, 106.8645],
    "Bandung": [-6.9175, 107.6191], "Surabaya": [-7.2575, 112.7521],
    "Yogyakarta": [-7.7956, 110.3695], "DI Yogyakarta": [-7.7956, 110.3695],
    "Sleman": [-7.7128, 110.3541], "Semarang": [-6.9667, 110.4167],
    "Malang": [-7.9666, 112.6326], "Tangerang": [-6.1731, 106.6300],
    "Tangerang Selatan": [-6.2886, 106.7179], "Bekasi": [-6.2383, 106.9756],
    "Bogor": [-6.5971, 106.8060], "Depok": [-6.4025, 106.7942],
    "Banten": [-6.4058, 106.0640], "Jawa Barat": [-6.9147, 107.6098],
    "Jawa Tengah": [-7.1510, 110.1403], "Jawa Timur": [-7.5360, 112.2384],
    "Bali": [-8.4095, 115.1889], "Lokasi Lain": [-7.35, 110.00] 
}

def get_lat(kota): return koordinat_kota.get(kota, [None, None])[0]
def get_lon(kota): return koordinat_kota.get(kota, [None, None])[1]

# B. LOAD DATA
@st.cache_data
def load_base_data():
    try:
        df = pd.read_csv("./data/data_loker_clean.csv")
        return df
    except FileNotFoundError:
        return pd.DataFrame()

# Initialize Session State for extra data
if 'scraped_data' not in st.session_state:
    st.session_state.scraped_data = pd.DataFrame()
if 'uploaded_data' not in st.session_state:
    st.session_state.uploaded_data = pd.DataFrame()

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.markdown(f"## {icon('settings')} Pengaturan Data", unsafe_allow_html=True)
    
    # 1. Live Scraping
    st.subheader("Live Scraping")
    
    # Website Selection (Fixed to Kalibrr)
    scrape_source = "Kalibrr"
    
    # New: Search Query
    search_query = st.text_input("Kata Kunci (Opsional)", placeholder="Contoh: Python, Data Analyst...")
    
    target_scraping = st.number_input("Jumlah Data", min_value=1, max_value=50, value=5)
    
    if st.button("Mulai Scraping"):
        with st.spinner(f"Sedang scraping {scrape_source} {f'dengan kata kunci `{search_query}`' if search_query else ''}..."):
            
            # Select Scraper Function
            new_data = run_scraper_kalibrr(target_count=target_scraping, search_query=search_query)
                
            if not new_data.empty:
                # Accumulate data: Concatenate old session state with new data
                st.session_state.scraped_data = pd.concat([st.session_state.scraped_data, new_data], ignore_index=True)
                
                st.success(f"Berhasil mengambil {len(new_data)} data baru! Total sementara: {len(st.session_state.scraped_data)}")
                
                # --- PREVIEW DATA ---
                with st.expander("🔍 Preview Hasil Scraping (Terbaru)", expanded=True):
                    # use_container_width=True is deprecated in some versions, changed to width (or removed if auto)
                    st.dataframe(new_data[['Perusahaan', 'Posisi', 'gaji_angka']], hide_index=True)
            else:
                st.warning("Gagal mengambil data atau tidak ada data baru.")


    st.markdown("---")
    
    # 2. Upload CSV
    st.subheader("Upload CSV")
    uploaded_file = st.file_uploader("Upload file CSV", type=["csv"])
    if uploaded_file is not None:
        try:
            temp_df = pd.read_csv(uploaded_file)
            # Validasi Kolom
            required_cols = {'Perusahaan', 'Posisi', 'kategori_posisi', 'kota', 'gaji_angka', 'list_skill', 'pendidikan', 'jenis', 'provinsi', 'link'}
            if required_cols.issubset(temp_df.columns):
                st.session_state.uploaded_data = temp_df
                st.success(f"File valid! {len(temp_df)} data ditambahkan.")
            else:
                missing = required_cols - set(temp_df.columns)
                st.error(f"Format salah! Kolom hilang: {missing}")
        except Exception as e:
            st.error(f"Error membaca file: {e}")

    # Reset Data Button
    if st.button("Reset Tambahan Data"):
        st.session_state.scraped_data = pd.DataFrame()
        st.session_state.uploaded_data = pd.DataFrame()
        st.rerun()

    st.markdown("---")

    # 3. Data Cleaning
    st.subheader("Cleaning Data")
    if st.button("Bersihkan & Gabung Data"):
        with st.spinner("Membersihkan data..."):
            # Gabungkan dulu semua source
            combined = pd.concat([st.session_state.scraped_data, st.session_state.uploaded_data], ignore_index=True)
            
            if not combined.empty:
                # 1. Deduplikasi
                # Prioritas deduplikasi: Link (jika ada), atau kombinasi (Perusahaan, Posisi, Kota)
                initial_count = len(combined)
                
                # Buat temporary column untuk deduplikasi case-insensitive
                combined['dedup_key'] = combined.apply(
                    lambda x: str(x['link']) if pd.notna(x['link']) and x['link'] != '' 
                    else f"{str(x['Perusahaan']).lower()}|{str(x['Posisi']).lower()}", axis=1
                )
                
                combined = combined.drop_duplicates(subset=['dedup_key'])
                combined = combined.drop(columns=['dedup_key'])
                
                # 2. Standardisasi Gaji (Memastikan numerik)
                combined['gaji_angka'] = pd.to_numeric(combined['gaji_angka'], errors='coerce')
                
                # 3. Simpan kembali ke uploaded_data (sebagai wadah data bersih tambahan)
                # Kita kosongkan scraped_data agar tidak double, semua masuk ke uploaded/tambahan
                st.session_state.scraped_data = pd.DataFrame() 
                st.session_state.uploaded_data = combined
                
                removed_count = initial_count - len(combined)
                st.success(f"Pembersihan Selesai! {removed_count} data duplikat dihapus.")
                st.rerun()
            else:
                st.warning("Belum ada data tambahan untuk dibersihkan.")

# C. COMBINE DATA
base_df = load_base_data()
if base_df.empty:
    st.error("❌ File data utama (data_loker_clean.csv) tidak ditemukan!")
    st.stop()

# Gabungkan data utama + scraped + uploaded
# Note: Kita lakukan deduplikasi akhir juga dengan base_data untuk view
df = pd.concat([base_df, st.session_state.scraped_data, st.session_state.uploaded_data], ignore_index=True)

# Preprocessing ulang untuk data gabungan (terutama list_skill)
# Karena data scraped/upload mungkin belum di-eval
def clean_skill_column(x):
    if isinstance(x, list): return x
    if isinstance(x, str):
        try:
            return ast.literal_eval(x)
        except:
            return []
    return []

df['list_skill'] = df['list_skill'].apply(clean_skill_column)
df['pendidikan'] = df['pendidikan'].fillna("Tidak Disebutkan") # Note: base has pendidikan, new data has pendidikan
df['kota'] = df['kota'].fillna("Lokasi Lain")
df['gaji_angka'] = pd.to_numeric(df['gaji_angka'], errors='coerce')

# --- 4. HEADER & FILTER ---
# GANTI st.title BIASA DENGAN MARKDOWN AGAR BISA PAKAI ICON
st.markdown(f"# {icon('analytics')} Dashboard Analisis Pasar Kerja IT", unsafe_allow_html=True)
st.markdown("Analisis mendalam tren lowongan kerja IT di Pulau Jawa berdasarkan data scraping.")

with st.container(border=True): 
    st.markdown(f"### {icon('search')} Filter Data", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    
    kategori_list = sorted(df['kategori_posisi'].unique().tolist())
    provinsi_list = sorted(df['provinsi'].unique().tolist())
    pendidikan_list = sorted(df['pendidikan'].unique().tolist())

    with c1:
        st.markdown(f"**{icon('assignment')} Posisi / Kategori**", unsafe_allow_html=True)
        selected_kategori = st.multiselect("Posisi", kategori_list, label_visibility="collapsed")
    
    with c2:
        st.markdown(f"**{icon('location_on')} Provinsi**", unsafe_allow_html=True)
        selected_provinsi = st.multiselect("Provinsi", provinsi_list, label_visibility="collapsed")
        
    with c3:
        st.markdown(f"**{icon('school')} Pendidikan**", unsafe_allow_html=True)
        selected_pendidikan = st.multiselect("Pendidikan", pendidikan_list, label_visibility="collapsed")

# Logic Filter
if not selected_kategori: selected_kategori = kategori_list
if not selected_provinsi: selected_provinsi = provinsi_list
if not selected_pendidikan: selected_pendidikan = pendidikan_list

filtered_df = df[
    (df['kategori_posisi'].isin(selected_kategori)) & 
    (df['provinsi'].isin(selected_provinsi)) &
    (df['pendidikan'].isin(selected_pendidikan))
]

st.markdown("---") 

# --- 5. METRICS / KPI ---
# Header
st.markdown(f"### {icon('leaderboard')} Ringkasan Data ({len(filtered_df)} Lowongan)", unsafe_allow_html=True)

# BARIS 1: Tiga Kotak (Total, Gaji, Posisi)
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Lowongan", f"{len(filtered_df):,}".replace(",", "."))

with col2:
    df_gaji = filtered_df.dropna(subset=['gaji_angka'])
    avg_gaji = df_gaji['gaji_angka'].mean()
    val = f"Rp {avg_gaji/1_000_000:.1f} Juta" if pd.notna(avg_gaji) else "-"
    st.metric("Rata-rata Gaji", val)

with col3:
    top_pos = filtered_df['Posisi'].mode()[0] if not filtered_df.empty else "-"
    # Potong teks jika terlalu panjang agar kotak tidak rusak
    st.metric("Posisi Terbanyak", top_pos[:25] + "..." if len(top_pos) > 25 else top_pos)

# BARIS 2: Satu Kotak Full Width (Top Perusahaan)
# Kita beri jarak sedikit dengan spacer kosong
st.write("") 

top_comp = filtered_df['Perusahaan'].mode()[0] if not filtered_df.empty else "-"
st.metric("Top Perusahaan", top_comp)

st.markdown("---")

# --- 6. PETA VISUALISASI ---
# 1. Inisialisasi State (Tambahkan view_mode)
if 'map_theme' not in st.session_state: 
    st.session_state.map_theme = 'light'
if 'view_mode_peta' not in st.session_state:
    st.session_state.view_mode_peta = "Kepadatan Lowongan"

# 2. Header Peta + Tombol Tema (Kolom disesuaikan jadi 2 saja)
c_head, c_btn = st.columns([7, 1]) # Ratio 7:1 agar tombol ada di ujung kanan

with c_head:
    st.markdown(f"### {icon('public')} Sebaran Geografis", unsafe_allow_html=True)

with c_btn:
    # Tombol Tema
    if st.button("Tema Peta", icon=":material/contrast:", use_container_width=True):
        st.session_state.map_theme = 'dark' if st.session_state.map_theme == 'light' else 'light'
        st.rerun()

# 3. Konfigurasi Tema
if st.session_state.map_theme == 'dark':
    deck_style, plotly_style = pdk.map_styles.CARTO_DARK, "carto-darkmatter"
    deck_color = [255, 69, 0, 180] 
else:
    deck_style, plotly_style = pdk.map_styles.CARTO_LIGHT, "carto-positron"
    deck_color = [0, 100, 255, 180] 

# 4. Proses Data
def apply_jitter(coord, amount=0.015): return coord + np.random.uniform(-amount, amount)

df_map = filtered_df.copy()
map_data = df_map.groupby(['kota', 'kategori_posisi']).size().reset_index(name='Jumlah')
map_data['lat'] = map_data['kota'].apply(get_lat)
map_data['lon'] = map_data['kota'].apply(get_lon)
map_data = map_data.dropna(subset=['lat', 'lon']) 
map_data['lat_jitter'] = map_data['lat'].apply(lambda x: apply_jitter(x))
map_data['lon_jitter'] = map_data['lon'].apply(lambda x: apply_jitter(x))

# --- PERBAIKAN BUG ---
# Gunakan session_state sebagai value dan on_change untuk update
view_mode = st.radio(
    "Pilih Tampilan Peta:", 
    ["Kepadatan Lowongan", "Sebaran Kategori"], 
    horizontal=True,
    index=0 if st.session_state.view_mode_peta == "Kepadatan Lowongan" else 1,
    key="view_mode_radio",
    on_change=lambda: setattr(st.session_state, 'view_mode_peta', st.session_state.view_mode_radio)
)

center_java = {"lat": -7.35, "lon": 110.00}

# 5. Render Peta (gunakan st.session_state.view_mode_peta)
if not map_data.empty:
    with st.container(border=True):
        if st.session_state.view_mode_peta == "Kepadatan Lowongan":
            data_3d = map_data.groupby(['kota', 'lat', 'lon'])['Jumlah'].sum().reset_index()
            view_state = pdk.ViewState(latitude=-7.2, longitude=110.0, zoom=6.5, pitch=50)
            
            layer = pdk.Layer(
                "ColumnLayer", data=data_3d, get_position=["lon", "lat"], get_elevation="Jumlah",
                elevation_scale=100, radius=4000, get_fill_color=deck_color,
                pickable=True, auto_highlight=True, elevation_range=[0, 1000],
            )
            tooltip = {"html": "<b>{kota}</b><br>Jumlah: <b>{Jumlah}</b>", "style": {"backgroundColor": "#111", "color": "white"}}
            
            r = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip, map_style=deck_style)
            st.pydeck_chart(r, use_container_width=True)
            
        else: 
            fig_map = px.scatter_mapbox(
                map_data, lat="lat_jitter", lon="lon_jitter", size="Jumlah", color="kategori_posisi",
                hover_name="kota", hover_data=["kategori_posisi", "Jumlah"],
                zoom=6.2, center=center_java, size_max=40, opacity=0.7,
                mapbox_style=plotly_style, height=500, color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
            st.plotly_chart(fig_map, use_container_width=True)
else:
    st.warning("⚠️ Data lokasi tidak cukup.")

st.markdown("---")

# --- 7. ANALISIS GAJI, SKILL, LOKASI, PENDIDIKAN ---
col_left, col_right = st.columns([1, 1])

# === BARIS 1: GAJI & SKILL ===
with col_left:
    with st.container(border=True):
        # Icon: payments (Uang)
        st.markdown(f"### {icon('payments')} Distribusi Gaji", unsafe_allow_html=True)
        
        if not df_gaji.empty:
            fig_hist = px.histogram(
                df_gaji, x="gaji_angka", nbins=20, 
                color_discrete_sequence=['#4CAF50'],
                template="plotly" 
            )
            fig_hist.update_layout(
                xaxis_title="Gaji (Rupiah)", yaxis_title="Jumlah Lowongan",
                showlegend=False,
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("Data gaji tidak tersedia.")

with col_right:
    with st.container(border=True):
        # Icon: construction (Alat/Skill) atau engineering
        st.markdown(f"### {icon('construction')} Top 10 Skill Teknis", unsafe_allow_html=True)
        
        all_skills = [s for skills in filtered_df['list_skill'] for s in skills]
        if all_skills:
            skill_counts = pd.DataFrame(Counter(all_skills).most_common(10), columns=['Skill', 'Jumlah'])
            fig_skill = px.bar(
                skill_counts, x='Jumlah', y='Skill', orientation='h',
                text='Jumlah', color='Jumlah', 
                color_continuous_scale='Blues',
                template="plotly"
            )
            fig_skill.update_layout(
                yaxis={'categoryorder':'total ascending'},
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig_skill, use_container_width=True)
        else:
            st.info("Data skill tidak tersedia.")

# === BARIS 2: LOKASI & PENDIDIKAN ===
# Kita buka lagi col_left dan col_right untuk baris kedua grafik
with col_left:
    with st.container(border=True):
        # Icon: location_on (Pin Map)
        st.markdown(f"### {icon('location_on')} Top 10 Lokasi", unsafe_allow_html=True)

        loc_data = filtered_df['kota'].value_counts().head(10).reset_index()
        loc_data.columns = ['Kota', 'Jumlah']

        fig_loc = px.bar(loc_data, x='Kota', y='Jumlah', color='Kota')
        fig_loc.update_layout(showlegend=False, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_loc, use_container_width=True)

with col_right:
    with st.container(border=True):
        # Icon: school (Topi Wisuda)
        st.markdown(f"### {icon('school')} Kualifikasi Pendidikan", unsafe_allow_html=True)

        edu_data = filtered_df['pendidikan'].value_counts().reset_index()
        edu_data.columns = ['Pendidikan', 'Jumlah']

        fig_edu = px.pie(edu_data, values='Jumlah', names='Pendidikan', hole=0.4)
        fig_edu.update_layout(margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_edu, use_container_width=True)

# --- 8. TABEL DATA ---
# Icon: table_view (Grid/Tabel)
st.markdown(f"### {icon('table_view')} Data Detail Lowongan", unsafe_allow_html=True)

with st.expander("Klik untuk melihat tabel data lengkap", expanded=True):
    st.dataframe(
        filtered_df[['Perusahaan', 'Posisi', 'kota', 'gaji_angka', 'jenis']],
        use_container_width=True,
        column_config={
            "Perusahaan": st.column_config.TextColumn("Perusahaan", width="medium"),
            "Posisi": st.column_config.TextColumn("Posisi", width="large"),
            "gaji_angka": st.column_config.NumberColumn("Gaji (IDR)", format="Rp %d"),
            "jenis": st.column_config.TextColumn("Jenis Kerja"),
            "kota": st.column_config.TextColumn("Lokasi"),
        },
        hide_index=True
    )