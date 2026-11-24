# Dashboard perbandingan model beban listrik Panama

Dashboard Streamlit untuk menjelajahi hasil yang sudah disimpan di `Hasil_csv`. Aplikasi tidak melatih ulang model dan tidak membutuhkan file Excel atau notebook untuk berjalan.

## Menjalankan secara lokal

Gunakan Python 3.10, lalu jalankan:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Deploy ke Streamlit Community Cloud

1. Buat repository GitHub baru. Upload `app.py`, `requirements.txt`, `.gitignore`, dan folder `Hasil_csv` beserta seluruh CSV di dalamnya. Nama dan kapitalisasi `Hasil_csv` harus sama persis. Notebook dan file Excel tidak diperlukan untuk dashboard.
2. Masuk ke https://share.streamlit.io dengan GitHub dan hubungkan akun GitHub Anda. Pastikan Streamlit dapat mengakses repository tersebut.
3. Pilih **Create app**, lalu **Yup, I have an app**. Pilih repository, branch yang berisi file (biasanya `main`), dan masukkan `app.py` sebagai main file path.
4. Di **Advanced settings**, pilih Python **3.10** agar sesuai dengan lingkungan pengujian. Opsional, tentukan subdomain pada kolom App URL.
5. Klik **Deploy** dan tunggu instalasi selesai. Buka URL `streamlit.app` yang diberikan dan uji filter serta grafik.

Struktur repository:

```text
├── app.py
├── requirements.txt
├── .gitignore
└── Hasil_csv/
    ├── 08_periode_uji.csv
    ├── 12_ramalan_semua_model.csv
    └── ... CSV hasil lainnya
```

Untuk memperbarui dashboard, ubah file dan upload/push ke branch yang sama. Community Cloud akan mendeteksi perubahan. Jika terjadi kesalahan, buka log aplikasi di Community Cloud dan pastikan semua CSV tersedia serta huruf besar-kecil nama folder tepat. Repository publik membuat file yang diupload dapat dilihat publik.

Filter di sidebar berlaku untuk semua tab. Evaluasi utama menggunakan origin 1, sedangkan validasi silang menggunakan hasil seluruh origin dalam CSV.
