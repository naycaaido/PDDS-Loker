import streamlit as st
import pandas as pd
import plotly.express as px
import ast
from collections import Counter
import numpy as np
import pydeck as pdk 


# --- 1. KONFIGURASI HALAMAN (WAJIB PALING ATAS) ---
st.set_page_config(
    page_title="Dashboard Analisis Loker IT Jawa",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed" # Default sidebar tertutup
)

# --- 2. PERSIAPAN DATA ---

# A. DATABASE KOORDINAT (HARDCODED)
koordinat_kota = {
    "Jakarta Raya": [-6.2088, 106.8456],
    "Jakarta Selatan": [-6.2615, 106.8106],
    "Jakarta Barat": [-6.1674, 106.7637],
    "Jakarta Pusat": [-6.1751, 106.8650],
    "Jakarta Timur": [-6.2250, 106.9004],
    "Jakarta Utara": [-6.1384, 106.8645],
    "Bandung": [-6.9175, 107.6191],
    "Surabaya": [-7.2575, 112.7521],
    "Yogyakarta": [-7.7956, 110.3695],
    "DI Yogyakarta": [-7.7956, 110.3695],
    "Sleman": [-7.7128, 110.3541],
    "Semarang": [-6.9667, 110.4167],
    "Malang": [-7.9666, 112.6326],
    "Tangerang": [-6.1731, 106.6300],
    "Tangerang Selatan": [-6.2886, 106.7179],
    "Bekasi": [-6.2383, 106.9756],
    "Bogor": [-6.5971, 106.8060],
    "Depok": [-6.4025, 106.7942],
    "Banten": [-6.4058, 106.0640],
    "Jawa Barat": [-6.9147, 107.6098],
    "Jawa Tengah": [-7.1510, 110.1403],
    "Jawa Timur": [-7.5360, 112.2384],
    "Bali": [-8.4095, 115.1889],
    "Lokasi Lain": [-7.35, 110.00] 
}

def get_lat(kota):
    return koordinat_kota.get(kota, [None, None])[0]

def get_lon(kota):
    return koordinat_kota.get(kota, [None, None])[1]

# B. LOAD DATA CSV
@st.cache_data
def load_data():
    df = pd.read_csv("data/data_loker_super_bersih_jawa.csv")
    df['list_skill'] = df['list_skill'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else [])
    df['pendidikan_clean'] = df['pendidikan_clean'].fillna("Tidak Disebutkan")
    df['kota'] = df['kota'].fillna("Lokasi Lain")
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("File tidak ditemukan!")
    st.stop()

# --- 3. TITLE & FILTER (DI BAGIAN ATAS HALAMAN) ---
st.title("📊 Dashboard Pasar Kerja IT (Data Bersih)")

# Buat Container Filter yang rapi dengan Expander (Opsional, agar tidak menuhin layar)
# Atau bisa langsung st.columns jika ingin selalu terlihat.
with st.container():
    st.subheader("🔍 Filter Data")
    
    # Bagi layar jadi 3 kolom untuk filter
    col_filter1, col_filter2, col_filter3 = st.columns(3)

    kategori_list = sorted(df['kategori_posisi'].unique().tolist())
    kota_list = sorted(df['kota'].unique().tolist())
    pendidikan_list = sorted(df['pendidikan_clean'].unique().tolist())

    with col_filter1:
        selected_kategori = st.multiselect("Posisi / Kategori", kategori_list)
    
    with col_filter2:
        selected_kota = st.multiselect("Lokasi Kota", kota_list)
        
    with col_filter3:
        selected_pendidikan = st.multiselect("Pendidikan Terakhir", pendidikan_list)

# Logika Filter
if not selected_kategori: selected_kategori = kategori_list
if not selected_kota: selected_kota = kota_list
if not selected_pendidikan: selected_pendidikan = pendidikan_list

filtered_df = df[
    (df['kategori_posisi'].isin(selected_kategori)) & 
    (df['kota'].isin(selected_kota)) &
    (df['pendidikan_clean'].isin(selected_pendidikan))
]

st.divider() # Garis pembatas antara Filter dan Konten

# --- 4. DASHBOARD UTAMA ---
st.markdown(f"Menampilkan **{len(filtered_df)}** lowongan dari total **{len(df)}** data.")

# A. METRICS
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Lowongan", len(filtered_df))
with col2:
    df_gaji = filtered_df.dropna(subset=['gaji_angka'])
    avg_gaji = df_gaji['gaji_angka'].mean()
    val = f"Rp {avg_gaji/1_000_000:.1f} Juta" if pd.notna(avg_gaji) else "Data Kosong"
    st.metric("Rata-rata Gaji", val)
with col3:
    top_company = filtered_df['Perusahaan'].mode()[0] if not filtered_df.empty else "-"
    st.metric("Top Company", top_company)
with col4:
    top_posisi = filtered_df['Posisi'].mode()[0] if not filtered_df.empty else "-"
    st.metric("Posisi Terbanyak", top_posisi)

st.divider()

# B. PETA PERSEBARAN
st.subheader("🗺️ Peta Persebaran Lowongan (Pulau Jawa)")

def apply_jitter(coord, amount=0.015): 
    return coord + np.random.uniform(-amount, amount)

df_map = filtered_df.copy()
map_data = df_map.groupby(['kota', 'kategori_posisi']).size().reset_index(name='Jumlah')
map_data['lat'] = map_data['kota'].apply(get_lat)
map_data['lon'] = map_data['kota'].apply(get_lon)
map_data = map_data.dropna(subset=['lat', 'lon']) 

map_data['lat_jitter'] = map_data['lat'].apply(lambda x: apply_jitter(x))
map_data['lon_jitter'] = map_data['lon'].apply(lambda x: apply_jitter(x))

view_mode = st.radio("Mode Tampilan:", ["Total per Kota (3D)", "Detail (Scatter)"], horizontal=True)
center_java = {"lat": -7.35, "lon": 110.00}

if not map_data.empty:
     # --- LOGIKA TAMPILAN 3D PYDECK ---
    if view_mode == "Total per Kota (3D)":
        
        # 1. Agregasi data khusus untuk 3D (Group by Kota only)
        # Kita butuh total per kota agar batangnya cuma satu per kota
        data_3d = map_data.groupby(['kota', 'lat', 'lon'])['Jumlah'].sum().reset_index()
        
        # 2. Atur View State (Posisi Kamera Awal)
        view_state = pdk.ViewState(
            latitude=-7.2,      # Tengah Jawa
            longitude=110.0,
            zoom=6.5,
            pitch=50,           # Kemiringan kamera (biar kelihatan 3D)
            bearing=0
        )

        # 3. Definisikan Layer (Batang Hexagon/Column)
        layer = pdk.Layer(
            "ColumnLayer",      # Tipe layer batang
            data=data_3d,
            get_position=["lon", "lat"], # Hati-hati: PyDeck urutannya [Lon, Lat]
            get_elevation="Jumlah",      # Tinggi batang berdasarkan jumlah loker
            elevation_scale=100,         # Skala tinggi (sesuaikan biar gak kependekan)
            radius=3000,                 # Radius batang (dalam meter, 3km biar kelihatan)
            get_fill_color=[255, 69, 0, 180], # Warna Merah-Orange Transparan [R, G, B, Alpha]
            pickable=True,               # Agar bisa di-hover
            auto_highlight=True,
            elevation_range=[0, 1000],
        )

        # 4. Render Tooltip & Deck
        tooltip = {
            "html": "<b>{kota}</b><br>Jumlah Lowongan: <b>{Jumlah}</b>",
            "style": {"backgroundColor": "steelblue", "color": "white"}
        }

        r = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip=tooltip,
            
            # --- UBAH BARIS INI ---
            # HAPUS ATAU COMMENT BARIS MAPBOX INI:
            # map_style="mapbox://styles/mapbox/light-v9", 
            
            # GANTI DENGAN INI (GRATIS TANPA API KEY):
            map_style=pdk.map_styles.CARTO_DARK 
        )
        
        st.pydeck_chart(r)
        st.caption("ℹ️ **Tips:** Tahan klik kanan pada mouse untuk memutar (rotate) peta 3D.")
    else: 
        fig_map = px.scatter_mapbox(
            map_data, lat="lat_jitter", lon="lon_jitter", size="Jumlah", color="kategori_posisi",
            hover_name="kota", hover_data=["kategori_posisi", "Jumlah"],
            zoom=6.2, center=center_java, size_max=60, opacity=0.8,
            mapbox_style="carto-positron", height=600
        )
        st.plotly_chart(fig_map, use_container_width=True)
else:
    st.warning("Tidak ada data lokasi valid.")

st.divider()

# C. ANALISIS GAJI
st.subheader("💰 Analisis Gaji")
if not df_gaji.empty:
    col_gaji_1, col_gaji_2 = st.columns(2)
    with col_gaji_1:
        fig_hist = px.histogram(df_gaji, x="gaji_angka", nbins=20, title="Distribusi Gaji", color_discrete_sequence=['#2ecc71'])
        st.plotly_chart(fig_hist, use_container_width=True)
    with col_gaji_2:
        top_kategori = df_gaji['kategori_posisi'].value_counts().nlargest(10).index
        fig_box = px.box(df_gaji[df_gaji['kategori_posisi'].isin(top_kategori)], x="kategori_posisi", y="gaji_angka", title="Range Gaji per Kategori", color="kategori_posisi")
        st.plotly_chart(fig_box, use_container_width=True)
else:
    st.info("Tidak ada data gaji.")

st.divider()

# D. ANALISIS SKILL
st.subheader("🛠️ Skill Paling Dibutuhkan")
all_skills = [s for skills in filtered_df['list_skill'] for s in skills]
skill_counts = pd.DataFrame(Counter(all_skills).most_common(15), columns=['Skill', 'Jumlah'])

if not skill_counts.empty:
    fig_skill = px.bar(skill_counts, x='Jumlah', y='Skill', orientation='h', title="Top 15 Skills", color='Jumlah', color_continuous_scale='Bluered_r')
    fig_skill.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_skill, use_container_width=True)

st.divider()

# --- E. LOKASI & PENDIDIKAN ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📍 Top 10 Lokasi Lowongan")
    # Hitung jumlah per kota
    loc_data = filtered_df['kota'].value_counts().head(10).reset_index()
    # Rename kolom agar konsisten: Kolom 0 jadi 'Kota', Kolom 1 jadi 'Jumlah'
    loc_data.columns = ['Kota', 'Jumlah']
    
    # Perbaikan: Gunakan 'Kota' sebagai x, bukan 'index'
    fig_loc = px.bar(loc_data, x='Kota', y='Jumlah', color='Kota')
    st.plotly_chart(fig_loc, use_container_width=True)

with col_right:
    st.subheader("🎓 Kualifikasi Pendidikan")
    # Hitung jumlah per pendidikan
    edu_data = filtered_df['pendidikan_clean'].value_counts().reset_index()
    # Rename kolom agar konsisten
    edu_data.columns = ['Pendidikan', 'Jumlah']
    
    # Perbaikan: Gunakan 'Pendidikan' sebagai names, bukan 'index'
    fig_edu = px.pie(edu_data, values='Jumlah', names='Pendidikan', hole=0.4)
    st.plotly_chart(fig_edu, use_container_width=True)

# F. TABEL DATA
with st.expander("Lihat Data Mentah"):
    st.dataframe(filtered_df, use_container_width=True)