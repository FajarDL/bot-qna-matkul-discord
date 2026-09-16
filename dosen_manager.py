import os
import json
import discord
import config

LORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dosen_lore.json")

def load_dosen_lore() -> dict:
    """Membaca data profil dosen killer dari dosen_lore.json."""
    default_lore = {
        "nama": "",
        "alias": "Sosok Dosen Sepuh IF UNJANI (The Curse of Knowledge)",
        "institusi": "Informatika (IF) Universitas Jenderal Achmad Yani (UNJANI)",
        "perawakan": "Beliau adalah sosok dosen sepuh IF UNJANI, berperawakan bak seorang yang polos, energik nan tanpa dosa, namun di balik semua itu ada rahasia kelam bagi para mahasiswa sepuh di IF UNJANI.",
        "reputasi": "Bisa dibilang beliau adalah dosen yang sangat berpengalaman, pintar, dan bahkan sering menjuarai banyak sekali penelitian di bawah naungannya. Namun, segalanya akan terasa sangat berbeda ketika sudah berada di dalam kelas.",
        "alasan_killer": "Cara mengajar beliau bak seorang dosen tingkat S2, itulah yang membuatnya dijuluki sebagai 'dosen killer'. Kemungkinan besar hal ini disebabkan oleh 'Curse of Knowledge' yang membuatnya tidak lagi berpikir ke ranah yang paling dasar. Bagi mahasiswa Informatika UNJANI yang sudah sepuh, beliau adalah sosok yang menyeramkan sehingga beberapa mahasiswa memilih menghindari kelasnya daripada berurusan dengan sesuatu hal yang mengerikan.",
        "kata_keramat": "HARI INI KITA POST TES YA! 💀",
        "catatan_mahasiswa": "Bila kalimat keramat tersebut sudah terucap di awal atau akhir kelas, seketika seisi ruangan hening dan aura kepanikan langsung menyelimuti setiap sudut lab/kelas."
    }
    
    if os.path.exists(LORE_FILE):
        try:
            with open(LORE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                default_lore.update(data)
        except Exception as e:
            print(f"[DosenManager] Gagal membaca {LORE_FILE}: {e}")
            
    return default_lore

def get_dosen_info() -> dict:
    """Mengambil informasi dosen lengkap dengan resolusi nama dari .env / config."""
    data = load_dosen_lore()
    
    # Cek apakah nama diatur via .env (prioritas agar aman tanpa commit ke git)
    env_name = getattr(config, "DOSEN_KILLER_NAME", "").strip()
    nama = env_name if env_name else data.get("nama", "").strip()
    
    display_name = nama if nama else "Dosen Sepuh IF UNJANI (Anonim / Belum Diset)"
    data["resolved_nama"] = display_name
    data["is_named"] = bool(nama)
    return data

def build_dosen_embed() -> discord.Embed:
    """Membuat Discord Embed bertema misterius dan dramatis tentang Dosen Killer IF UNJANI."""
    info = get_dosen_info()
    
    title = f"💀 Arsip Rahasia: {info['resolved_nama']}"
    embed = discord.Embed(
        title=title,
        description=f"*{info['alias']}*\n🏛️ **Institusi:** {info['institusi']}",
        color=getattr(config, "COLOR_DANGER", 0xDC2626)
    )
    
    embed.add_field(
        name="🎭 Perawakan & Aura",
        value=info["perawakan"],
        inline=False
    )
    
    embed.add_field(
        name="🏆 Reputasi & Prestasi",
        value=info["reputasi"],
        inline=False
    )
    
    embed.add_field(
        name="⚡ Mengapa Dijuluki 'Dosen Killer'? (*Curse of Knowledge*)",
        value=info["alasan_killer"],
        inline=False
    )
    
    embed.add_field(
        name="💀 KATA KERAMAT YANG DITAKUTI SELURUH MAHASISWA:",
        value=f"```fix\n\"{info['kata_keramat']}\"\n```\n_{info['catatan_mahasiswa']}_",
        inline=False
    )
    
    footer_text = "Informatika UNJANI Lore | 'Curse of Knowledge' is Real 🥶"
    if not info["is_named"]:
        footer_text += " • Nama dosen dapat diatur di file dosen_lore.json atau .env (DOSEN_KILLER_NAME)"
    embed.set_footer(text=footer_text)
    
    return embed

def get_dosen_ai_context() -> str:
    """Menghasilkan konteks ringkas untuk disisipkan ke AI Gemini."""
    info = get_dosen_info()
    return f"""
Konteks Khusus - Dosen Killer Informatika (IF) UNJANI:
- Nama/Status: {info['resolved_nama']} ({info['alias']}).
- Ciri & Karakter: Beliau berpenampilan polos, ramah, energik, dan tanpa dosa. Merupakan dosen sepuh yang sangat pintar, berpengalaman, dan sering juara penelitian.
- Julukan Dosen Killer & Alasannya: Cara mengajarnya sangat tinggi bak level S2 karena mengidap 'Curse of Knowledge' (sudah terlalu paham sampai lupa bahwa mahasiswa S1 masih butuh pemahaman tingkat paling dasar). Mahasiswa sepuh sangat segan dan banyak yang menghindari kelasnya.
- Kata Keramat Paling Ditakuti: "{info['kata_keramat']}".
- Peranmu jika ditanya tentang dosen killer / post test di IF UNJANI: Jelaskan lore ini dengan bumbu humor khas mahasiswa, nada sedikit dramatis/merinding namun tetap sopan dan menghormati kehebatan akademis beliau.
"""
