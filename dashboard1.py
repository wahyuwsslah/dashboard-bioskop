import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2
from psycopg2 import Error

# Koneksi ke PostgreSQL
try:
    conn = psycopg2.connect(
        database="sistem_bioskop1",
        user="postgres",
        password="NUHNUwEkZJrPHlklGDjAvhzYozOKHTZr",
  	host="nozomi.proxy.rlwy.net",
        port="5432"
    )
    cursor = conn.cursor()
except Error as e:
    st.error(f"Error connecting to PostgreSQL: {e}")
    st.stop()

# Tema Profesional
st.set_page_config(page_title="Sistem Informasi Penjualan Bioskop", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
    <style>
    .main {background-color: #f0f2f5;}
    .stButton>button {background-color: #4CAF50; color: white; border-radius: 5px;}
    .stSelectbox>select {background-color: #ffffff; border-radius: 5px;}
    .stMetric {text-align: center; padding: 10px;}
    </style>
""", unsafe_allow_html=True)

# Judul Dashboard
st.title("Sistem Informasi Penjualan Bioskop")

# Ringkasan Utama
st.header("Ringkasan Utama")
total_pelanggan = pd.read_sql("SELECT COUNT(*) as total FROM pelanggan", conn).iloc[0]['total']
total_transaksi = pd.read_sql("SELECT COUNT(*) as total FROM transaksi", conn).iloc[0]['total']
total_tiket = pd.read_sql("SELECT COUNT(*) as total FROM tiket", conn).iloc[0]['total']
total_kapasitas = pd.read_sql("SELECT SUM(kapasitas) as total FROM studio", conn).iloc[0]['total']
total_karyawan = pd.read_sql("SELECT COUNT(*) as total FROM karyawan", conn).iloc[0]['total']

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Pelanggan", total_pelanggan, delta=None, help="Jumlah pelanggan terdaftar")
col2.metric("Total Transaksi", total_transaksi, delta=None, help="Jumlah transaksi selesai")
col3.metric("Total Tiket Terjual", total_tiket, delta=None, help="Jumlah tiket yang terjual")
col4.metric("Total Kapasitas Studio", total_kapasitas, delta=None, help="Kapasitas total studio")
col5.metric("Total Karyawan", total_karyawan, delta=None, help="Jumlah karyawan aktif")

# Visualisasi Jadwal Tayang per Film
st.header("Jadwal Tayang per Film")
jadwal_data = pd.read_sql("""
    SELECT f.judul, COUNT(j.id) as jumlah
    FROM jadwal_tayang j
    JOIN film f ON j.id_film = f.id
    GROUP BY f.judul
""", conn)
fig_jadwal = px.bar(jadwal_data, x='judul', y='jumlah', title="Jumlah Jadwal per Film", 
                    color='judul', color_discrete_sequence=px.colors.qualitative.Pastel)
fig_jadwal.update_layout(showlegend=False, xaxis_title="Film", yaxis_title="Jumlah Jadwal")
st.plotly_chart(fig_jadwal)

# Analisis Transaksi
st.header("Analisis Transaksi")
transaksi_data = pd.read_sql("""
    SELECT tanggal_transaksi, SUM(total_bayar) as pendapatan
    FROM transaksi
    GROUP BY tanggal_transaksi
    ORDER BY tanggal_transaksi
""", conn)
fig_transaksi = px.line(transaksi_data, x='tanggal_transaksi', y='pendapatan', title="Pendapatan Harian",
                        markers=True, color_discrete_sequence=['#FF9999'])
fig_transaksi.update_layout(xaxis_title="Tanggal", yaxis_title="Pendapatan (Rp)")
st.plotly_chart(fig_transaksi)

# Status Studio
st.header("Status Studio")
studio_data = pd.read_sql("""
    SELECT s.nama_studio, s.kapasitas, COUNT(t.id) as tiket_terjual
    FROM studio s
    LEFT JOIN jadwal_tayang j ON s.id = j.id_studio
    LEFT JOIN tiket t ON j.id = t.id_jadwal
    GROUP BY s.id, s.nama_studio, s.kapasitas
""", conn)
studio_data['kapasitas_tersedia'] = studio_data['kapasitas'] - studio_data['tiket_terjual'].fillna(0)
fig_studio = px.pie(studio_data, names='nama_studio', values='tiket_terjual', title="Kapasitas Terpakai per Studio",
                    color_discrete_sequence=px.colors.qualitative.Pastel1)
fig_studio.update_traces(textinfo='percent+label')
st.plotly_chart(fig_studio)

# Distribusi Tiket per Nomor Kursi
st.header("Distribusi Tiket per Nomor Kursi")
tiket_data = pd.read_sql("SELECT nomor_kursi, COUNT(*) as jumlah FROM tiket GROUP BY nomor_kursi", conn)
fig_tiket = px.bar(tiket_data, x='nomor_kursi', y='jumlah', title="Jumlah Tiket per Nomor Kursi",
                   color='jumlah', color_continuous_scale='Viridis')
fig_tiket.update_layout(xaxis_title="Nomor Kursi", yaxis_title="Jumlah")
st.plotly_chart(fig_tiket)

# Performa Karyawan
st.header("Performa Karyawan")
karyawan_data = pd.read_sql("""
    SELECT k.nama_karyawan, COUNT(t.id) as jumlah_transaksi
    FROM karyawan k
    LEFT JOIN tiket t ON k.id = t.id_karyawan
    GROUP BY k.nama_karyawan
""", conn)
fig_karyawan = px.bar(karyawan_data, x='nama_karyawan', y='jumlah_transaksi', title="Jumlah Transaksi per Karyawan",
                      color='jumlah_transaksi', color_continuous_scale='Blues')
fig_karyawan.update_layout(xaxis_title="Karyawan", yaxis_title="Jumlah Transaksi")
st.plotly_chart(fig_karyawan)

# Panel Interaktif
st.header("Filter Data")
tanggal = st.date_input("Pilih Tanggal", pd.to_datetime('2025-07-08'))
film = st.selectbox("Pilih Film", pd.read_sql("SELECT judul FROM film", conn)['judul'])
karyawan = st.selectbox("Pilih Karyawan", pd.read_sql("SELECT nama_karyawan FROM karyawan", conn)['nama_karyawan'])

# Menggunakan perbandingan tanggal langsung untuk menghindari error LIKE
filtered_transaksi = pd.read_sql(f"""
    SELECT t.id, t.id_pelanggan, t.nama_pelanggan, t.id_karyawan, t.id_tiket, t.id_jadwal, 
           t.film, t.studio, t.nomor_kursi, t.harga, t.total_bayar, t.tanggal_transaksi,
           k.nama_karyawan
    FROM transaksi t
    JOIN pelanggan p ON t.id_pelanggan = p.id
    JOIN karyawan k ON t.id_karyawan = k.id
    WHERE DATE(t.tanggal_transaksi) = '{tanggal.strftime('%Y-%m-%d')}'  -- Perbandingan tanggal
""", conn)
st.write("Transaksi pada Tanggal Terpilih:", filtered_transaksi.style.set_properties(**{'background-color': '#f9f9f9', 'border': '1px solid #ddd', 'padding': '5px'}))

# Tutup koneksi
conn.close()