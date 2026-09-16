# 🤖 Asisten Mahasiswa UNJANI - Discord Bot

Bot asisten virtual berbasis kecerdasan buatan (**Google Gemini**) yang dirancang untuk membantu mahasiswa Program Studi Informatika, Universitas Jenderal Achmad Yani (UNJANI). Bot ini siap mendampingi mahasiswa dalam memahami materi perkuliahan, pemecahan masalah (*debugging*) kodingan, pemodelan sistem (UML), serta memberikan panduan cepat seputar alur Tugas Akhir (SIMTA).

---

## ✨ Fitur Utama

1. **AI Q&A Cerdas (`/tanya` & Mention):**  
   Mahasiswa dapat menanyakan konsep perkuliahan, materi teori, rekayasa perangkat lunak, maupun solusi kode error secara interaktif.
2. **Knowledge Base SIMTA (`/simta`):**  
   Akses cepat aturan resmi tugas akhir:
   - Syarat pendaftaran TA1 (minimal 128 SKS, bebas tunggakan, matkul wajib min C).
   - Syarat pendaftaran TA2 (sidang skripsi).
   - Aturan batas bimbingan (minimal 6 kali TA1 dan 8 kali TA2).
   - Formula pembobotan nilai akhir kumulatif (40% bimbingan + 50% pengujian + 10% administrasi).
   - Kebijakan bypass nilai indeks A (Sinta 3 / Scopus) dan penahanan nilai LoA (maksimal 1 bulan).
   - Batas kuota bimbingan dosen berdasarkan jabatan fungsional.
3. **Slash Commands Modern:**  
   Mendukung `/tanya`, `/simta`, `/bantuan`, dan `/ping` lengkap dengan menu pilihan otomatis.
4. **Respon Mention di Channel:**  
   Cukup tag `@bot` di obrolan umum untuk mendapatkan jawaban langsung dari AI.

---

## 🛠️ Prasyarat

- Python versi 3.10 atau yang lebih baru.
- Token Bot dari [Discord Developer Portal](https://discord.com/developers/applications).
- *(Direkomendasikan)* API Key Google Gemini gratis dari [Google AI Studio](https://aistudio.google.com/).

---

## 🚀 Panduan Instalasi & Menjalankan Bot

### 1. Kloning Repositori
```bash
git clone https://github.com/<username>/bot-qna-matkul-discord.git
cd discord-student-bot
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
Buka file `.env` lalu masukkan kredensial Anda:
```env
DISCORD_BOT_TOKEN=token_bot_anda_disini
GEMINI_API_KEY=api_key_gemini_anda_disini
```

> **PENTING:** Pastikan opsi **Message Content Intent** dan **Server Members Intent** sudah diaktifkan di tab **Bot** pada [Discord Developer Portal](https://discord.com/developers/applications).

### 5. Jalankan Bot
```bash
python bot.py
```

---

## 📁 Struktur Direktori

```text
discord-student-bot/
├── .env.example       # Contoh template variabel lingkungan
├── .gitignore          # Daftar file yang diabaikan Git (token aman)
├── requirements.txt    # Dependensi library Python
├── config.py           # Konfigurasi sistem, persona AI & warna embed
├── knowledge_base.py   # Basis data FAQ akademik & pedoman SIMTA
├── bot.py              # Logika utama bot Discord & integrasi AI
└── README.md           # Dokumentasi proyek
```

---

## 📄 Lisensi & Kontribusi
Proyek ini bersifat open-source dan bebas digunakan serta dikembangkan untuk mendukung keperluan pembelajaran dan komunitas akademik.
