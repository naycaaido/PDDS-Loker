import streamlit as st
import pandas as pd
import plotly.express as px
from collections import Counter

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Dashboard Lowongan Kerja IT",
    page_icon="💼",
    layout="wide"
)

# --- 2. FUNGSI LOAD DATA ---
@st.cache_data # Cache agar tidak loading ulang terus menerus
def load_data():
    # Ganti nama file sesuai file CSV kamu yang paling baru
    df = pd.read_csv("data/GLINTS_FIXED_SKILLS.csv")
    
    # Bersihkan data (Handling Missing Value)
    df = df.fillna("Tidak Disebutkan")
    return df

# Load data awal
try:
    df = load_data()
except FileNotFoundError:
    st.error("File CSV tidak ditemukan! Pastikan ada di folder 'data/'.")
    st.stop()

# --- 3. SIDEBAR (FILTER) ---
st.sidebar.header("🔍 Filter Lowongan")

# Filter A: Lokasi
lokasi_list = sorted(df['Lokasi'].unique().tolist())
selected_lokasi = st.sidebar.multiselect("Pilih Lokasi", lokasi_list, default=lokasi_list[:5])

# Filter B: Pendidikan
pendidikan_list = sorted(df['Pendidikan'].unique().tolist())
selected_pendidikan = st.sidebar.multiselect("Pilih Pendidikan", pendidikan_list, default=pendidikan_list)

# Terapkan Filter
filtered_df = df[
    (df['Lokasi'].isin(selected_lokasi)) & 
    (df['Pendidikan'].isin(selected_pendidikan))
]

# --- 4. DASHBOARD UTAMA ---
st.title("📊 Analisis Pasar Kerja IT (Glints/JobStreet)")
st.markdown(f"Menampilkan **{len(filtered_df)}** lowongan dari total **{len(df)}** data.")

# A. KPI (Key Performance Indicator)
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Lowongan", len(filtered_df))
with col2:
    top_company = filtered_df['Perusahaan'].mode()[0] if not filtered_df.empty else "-"
    st.metric("Perusahaan Terbanyak", top_company)
with col3:
    # Contoh hitung rata-rata gaji jika datanya angka (ini agak tricky krn data gajimu string range)
    st.metric("Lokasi Terpopuler", filtered_df['Lokasi'].mode()[0] if not filtered_df.empty else "-")

st.divider()

# B. ANALISIS SKILL (Paling Penting!)
st.subheader("🛠️ Skill Paling Dicari")

# Logika untuk memecah string "Python, SQL, Java" menjadi list
all_skills = []
for skills in filtered_df['Skill_Teknis']:
    if skills != "-" and skills != "Tidak Disebutkan":
        # Pecah berdasarkan koma, lalu bersihkan spasi
        skill_list = [s.strip() for s in skills.split(',')]
        all_skills.extend(skill_list)

# Hitung frekuensi skill
skill_counts = pd.DataFrame(Counter(all_skills).most_common(15), columns=['Skill', 'Jumlah'])

# Buat Bar Chart Horizontal
if not skill_counts.empty:
    fig_skill = px.bar(
        skill_counts, 
        x='Jumlah', 
        y='Skill', 
        orientation='h', 
        title="Top 15 Technical Skills",
        text='Jumlah',
        color='Jumlah'
    )
    fig_skill.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_skill, use_container_width=True)
else:
    st.warning("Tidak ada data skill untuk filter ini.")

# C. ANALISIS LAIN (Dua Kolom)
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("🎓 Kualifikasi Pendidikan")
    edu_counts = filtered_df['Pendidikan'].value_counts().reset_index()
    edu_counts.columns = ['Pendidikan', 'Jumlah']
    fig_edu = px.pie(edu_counts, values='Jumlah', names='Pendidikan', hole=0.4)
    st.plotly_chart(fig_edu, use_container_width=True)

with col_right:
    st.subheader("📍 Sebaran Lokasi")
    loc_counts = filtered_df['Lokasi'].value_counts().head(10).reset_index()
    loc_counts.columns = ['Lokasi', 'Jumlah']
    fig_loc = px.bar(loc_counts, x='Lokasi', y='Jumlah', color='Lokasi')
    st.plotly_chart(fig_loc, use_container_width=True)

st.divider()

# D. TABEL DATA MENTAH
st.subheader("📄 Detail Lowongan")
st.dataframe(filtered_df, use_container_width=True)