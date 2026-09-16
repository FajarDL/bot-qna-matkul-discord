# 🤖 Bot QnA Mata Kuliah - Discord Bot

Bot asisten virtual tanya-jawab (Q&A) cerdas berbasis AI (**Google Gemini**) yang dirancang khusus untuk mendampingi mahasiswa dalam memahami materi perkuliahan, membantu *debugging* kode program, dan meringkas materi studi di server Discord.

---

## ✨ Fitur Utama

1. **💡 Tanya Jawab Materi Kuliah (`/tanya` & Mention):**  
   Mahasiswa dapat menanyakan konsep materi kuliah apa pun, seperti Algoritma, Struktur Data, Basis Data, Jaringan Komputer, Rekayasa Perangkat Lunak, Sistem Operasi, hingga Matematika Diskrit. Pertanyaan pengguna kini juga otomatis ditampilkan dalam jawaban!
2. **🛠️ Asisten Debugging Kode (`/debug`):**  
   Menganalisis kode program yang error (Python, C++, Java, PHP, JavaScript, SQL, dll), menjelaskan letak kesalahan, dan memberikan solusi perbaikan kode secara otomatis.
3. **📝 Ringkas Materi Kuliah (`/ringkas`):**  
   Meringkas teks modul atau materi kuliah yang panjang menjadi poin-poin inti yang ringkas dan padat.
4. **🎮 Game Kuis Berhadiah Poin (`/kuis-mulai` & `/kuis-stop`):**  
   Sesi kuis interaktif dengan sistem **Siapa Cepat Dia Dapat** (kuota 1 pemenang tercepat per game). Dibatasi khusus untuk pemilik bot / admin server.
5. **🏆 Klasemen & Profil Poin (`/leaderboard` & `/poin`):**  
   Melihat 10 besar peringkat klasemen skor mahasiswa di server dan memeriksa saldo poin serta rekor juara pribadi.
6. **📚 Panduan Bidang Matkul (`/matkul`):**  
   Pilihan panduan dan tips belajar praktis untuk berbagai mata kuliah inti komputasi.
7. **📖 Menu Panduan Lengkap (`/help`):**  
   Menampilkan panduan ringkas dan daftar semua perintah yang dapat dijalankan.
8. **💬 Interaksi Fleksibel:**  
   Mendukung *Slash Commands* Discord modern serta respons otomatis saat bot di-mention di channel obrolan.

---

## 🛠️ Prasyarat

- Python versi 3.10 atau lebih baru.
- Token Bot dari [Discord Developer Portal](https://discord.com/developers/applications).
- API Key Google Gemini (gratis) dari [Google AI Studio](https://aistudio.google.com/) (menggunakan model terkini `gemini-3.6-flash`).

---

## 🚀 Panduan Instalasi & Menjalankan Bot

### 1. Kloning Repositori
```bash
git clone https://github.com/FajarDL/bot-qna-matkul-discord.git
cd bot-qna-matkul-discord
```

### 2. Buat & Aktifkan Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Pasang Dependensi
```bash
pip install -r requirements.txt
```

### 4. Konfigurasi File `.env`
Buka file `.env` di folder proyek, lalu masukkan kredensial:
```env
DISCORD_BOT_TOKEN=masukkan_token_discord_anda_disini
GEMINI_API_KEY=masukkan_api_key_gemini_disini

# Opsional: ID Discord Anda untuk hak akses eksklusif game kuis
OWNER_DISCORD_ID=masukkan_user_id_discord_anda
```

> **Catatan Pengaturan Discord:**  
> Pastikan opsi **Message Content Intent** sudah diaktifkan pada tab **Bot** di [Discord Developer Portal](https://discord.com/developers/applications).

### 5. Jalankan Bot
```bash
python bot.py
```

---

## 📁 Struktur Direktori

```text
bot-qna-matkul-discord/
├── .env.example       # Template variabel lingkungan
├── .gitignore         # Proteksi Git (token & database lokal aman)
├── requirements.txt   # Daftar dependensi library
├── config.py          # Konfigurasi sistem & instruksi persona AI
├── knowledge_base.py  # Panduan materi kuliah & tips belajar
├── dosen_lore.json    # File arsip profil & kata keramat dosen killer
├── dosen_manager.py   # Pengelola data dosen killer & embed Discord
├── game_manager.py    # Logika game kuis & penyimpanan poin
├── data/              # Folder penyimpanan database skor lokal
├── bot.py             # Logika bot Discord (Slash commands & QnA)
└── README.md          # Dokumentasi proyek
```

---

## 📄 Lisensi & Kontribusi
Proyek ini bersifat *open-source* dan bebas digunakan serta dikembangkan untuk mendukung keperluan pembelajaran dan komunitas akademik.
