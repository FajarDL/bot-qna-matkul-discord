import os
import re
import json
import discord
from discord.ext import commands
from discord import app_commands
import config
from knowledge_base import MATKUL_CATEGORIES
from game_manager import game_mgr

# Inisialisasi Klien Gemini AI
ai_client = None
if config.GEMINI_API_KEY:
    try:
        from google import genai
        ai_client = genai.Client(api_key=config.GEMINI_API_KEY)
        print("[AI] Google Gemini API client berhasil diaktifkan.")
    except Exception as e:
        print(f"[AI Warning] Gagal inisialisasi Gemini: {e}")
else:
    print("[AI Notice] GEMINI_API_KEY belum diisi di .env. Fitur AI membutuhkan API key.")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=config.BOT_PREFIX, intents=intents, help_command=None)

MODELS_TO_TRY = [
    getattr(config, "GEMINI_MODEL", "gemini-3.6-flash"),
    "gemini-3.1-flash-lite",
]

async def ask_gemini(prompt: str, custom_instruction: str = None) -> str:
    """Fungsi pembantu untuk memanggil Gemini API dengan mekanisme fallback otomatis."""
    if not ai_client:
        return (
            "⚠️ **API Key Gemini belum terpasang.**\n"
            "Silakan tambahkan `GEMINI_API_KEY` Anda di file `.env` untuk mengaktifkan AI Q&A."
        )
    instruction = custom_instruction if custom_instruction else config.SYSTEM_PROMPT
    last_error = None
    for model_name in MODELS_TO_TRY:
        try:
            response = ai_client.models.generate_content(
                model=model_name,
                contents=prompt,
                config={
                    "system_instruction": instruction,
                    "temperature": 0.7,
                }
            )
            if response and response.text:
                return response.text
        except Exception as e:
            last_error = e
            continue
    return f"Terjadi kesalahan pada server AI: `{str(last_error)}`"

def is_owner_or_admin(interaction: discord.Interaction) -> bool:
    """Cek apakah pengguna adalah pemilik bot atau administrator."""
    owner_id = getattr(config, "OWNER_DISCORD_ID", "").strip()
    if owner_id and str(interaction.user.id) == owner_id:
        return True
    if interaction.guild and interaction.user.guild_permissions.administrator:
        return True
    return False

async def generate_quiz_question(category: str) -> dict:
    """Meminta Gemini untuk membuat 1 pertanyaan kuis dan kunci jawabannya dalam format JSON."""
    prompt = f"""Kamu adalah pembuat soal kuis akademik untuk mahasiswa bidang Ilmu Komputer dan Informatika.
Tolong buatkan 1 buah soal kuis/trivia seputar topik: '{category}'.
Kriteria soal:
1. Menarik, mendidik, dan relevan dengan materi perkuliahan.
2. Jawabannya HARUS berupa kata tunggal atau frasa pendek yang pasti (maksimal 1-3 kata), bukan kalimat panjang!
   Contoh pertanyaan & jawaban:
   - "Struktur data apa yang beroperasi dengan prinsip LIFO (Last-In First-Out)?" -> Jawaban: "Stack"
   - "Keyword SQL apa yang digunakan untuk mengurutkan hasil query?" -> Jawaban: "ORDER BY"
   - "Protokol apa yang digunakan untuk mentransfer data halaman web secara aman?" -> Jawaban: "HTTPS"
3. Berikan variasi jawaban atau sinonim umum pada 'alternatif'.

Balas HANYA dalam format JSON baku berikut (tanpa markdown tambahan):
{{
    "pertanyaan": "Teks soal kuis...",
    "jawaban": "Kunci jawaban utama",
    "alternatif": ["variasi 1", "variasi 2"]
}}"""
    resp_text = await ask_gemini(prompt)
    clean_json = re.sub(r"^```(json)?", "", resp_text.strip(), flags=re.IGNORECASE)
    clean_json = re.sub(r"```$", "", clean_json.strip()).strip()
    try:
        data = json.loads(clean_json)
        if isinstance(data, dict) and "pertanyaan" in data and "jawaban" in data:
            return data
    except Exception:
        pass
    
    return {
        "pertanyaan": f"Sebutkan salah satu istilah atau konsep dasar penting dalam topik {category}!",
        "jawaban": category,
        "alternatif": []
    }

@bot.event
async def on_ready():
    print("=" * 50)
    print(f"Bot QnA Matkul Online sebagai: {bot.user.name} ({bot.user.id})")
    print(f"Prefix: {config.BOT_PREFIX}")
    print("=" * 50)
    
    try:
        # Sync instan ke setiap server (guild) agar langsung muncul seketika
        for guild in bot.guilds:
            bot.tree.copy_global_to(guild=guild)
            await bot.tree.sync(guild=guild)
            print(f"[Slash Commands] Sinkronisasi instan ke server: {guild.name} ({guild.id})")
        
        synced = await bot.tree.sync()
        print(f"[Slash Commands] Berhasil menyinkronkan {len(synced)} global slash commands.")
    except Exception as e:
        print(f"[Slash Commands Error] Gagal menyinkronkan: {e}")

    activity = discord.Game(name="Q&A Materi Kuliah | /tanya")
    await bot.change_presence(status=discord.Status.online, activity=activity)

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # 1. Cek apakah ada game kuis aktif di channel ini (Siapa Cepat Dia Dapat)
    active_game = game_mgr.get_active_game(message.channel.id)
    if active_game:
        is_correct, points, correct_ans = game_mgr.check_guess(
            channel_id=message.channel.id,
            user_id=message.author.id,
            username=message.author.display_name,
            guess=message.content
        )
        if is_correct:
            stats = game_mgr.get_user_stats(message.author.id)
            embed = discord.Embed(
                title="🎉 BINGO! JAWABAN BENAR!",
                description=(
                    f"🏆 Selamat kepada {message.author.mention}!\n\n"
                    f"✅ **Jawaban Tepat:** `{correct_ans}`\n"
                    f"🎁 **Hadiah:** `+{points} Poin`\n\n"
                    f"📊 **Statistik Poin Kamu Saat Ini:**\n"
                    f"• Total Poin: **{stats['points']} Poin**\n"
                    f"• Total Menang: **{stats['wins']}x Juara**\n\n"
                    f"*Gunakan `/leaderboard` untuk melihat peringkat klasemen server!*"
                ),
                color=config.COLOR_SUCCESS
            )
            embed.set_footer(text="Game Selesai • Kuota 1 Pemenang Terpenuhi!")
            await message.reply(embed=embed)
            return

    # 2. Menjawab hanya jika bot di-tag secara eksplisit dalam teks pesan (bukan sekadar reply)
    is_explicit_tag = (
        bot.user in message.mentions and 
        (f"<@{bot.user.id}>" in message.content or f"<@!{bot.user.id}>" in message.content)
    )
    if is_explicit_tag:
        query = re.sub(rf"<@!?{bot.user.id}>", "", message.content).strip()
        if not query:
            embed = discord.Embed(
                title=f"Halo, {message.author.display_name}! 👋",
                description=(
                    "Ada materi kuliah atau kodingan yang ingin ditanyakan?\n\n"
                    "Gunakan perintah `/tanya <pertanyaan>` atau ketik pertanyaan langsung sambil me-mention saya!"
                ),
                color=config.COLOR_PRIMARY
            )
            await message.reply(embed=embed)
            return

        async with message.channel.typing():
            jawaban = await ask_gemini(query)
            pertanyaan_quoted = "\n> ".join(query.strip().splitlines())
            pesan = f"**❓ Pertanyaan:**\n> {pertanyaan_quoted}\n\n**💬 Jawaban:**\n{jawaban}"
            if len(pesan) <= 2000:
                await message.reply(pesan)
            else:
                chunks = [pesan[i:i+1900] for i in range(0, len(pesan), 1900)]
                for chunk in chunks:
                    await message.reply(chunk)
        return

    await bot.process_commands(message)

# ================= SLASH COMMANDS =================

@bot.tree.command(name="tanya", description="Tanyakan materi kuliah, konsep teori, atau logika algoritma")
@app_commands.describe(pertanyaan="Pertanyaan seputar materi kuliah yang ingin dibahas")
async def slash_tanya(interaction: discord.Interaction, pertanyaan: str):
    await interaction.response.defer(thinking=True)
    jawaban = await ask_gemini(pertanyaan)
    
    # Tampilkan pertanyaan user secara terstruktur
    pertanyaan_quoted = "\n> ".join(pertanyaan.strip().splitlines())
    header = f"**❓ Pertanyaan:**\n> {pertanyaan_quoted}\n\n**💬 Jawaban:**\n"
    
    max_ans_len = 4000 - len(header)
    if len(jawaban) <= max_ans_len:
        desc = header + jawaban
        remaining = ""
    else:
        desc = header + jawaban[:max_ans_len]
        remaining = jawaban[max_ans_len:]
    
    embed = discord.Embed(
        title="💡 Tanya Jawab Materi Kuliah",
        description=desc,
        color=config.COLOR_PRIMARY
    )
    embed.set_footer(text=f"Ditanyakan oleh {interaction.user.display_name} • Bot QnA Matkul")
    await interaction.followup.send(embed=embed)
    
    while remaining:
        chunk = remaining[:1950]
        remaining = remaining[1950:]
        await interaction.followup.send(chunk)

@bot.tree.command(name="debug", description="Bantu analisis dan temukan solusi untuk kode yang error")
@app_commands.describe(
    bahasa="Bahasa pemrograman (misal: Python, C++, Java, SQL)",
    kode="Tuliskan kode program atau pesan error yang dialami"
)
async def slash_debug(interaction: discord.Interaction, bahasa: str, kode: str):
    await interaction.response.defer(thinking=True)
    prompt = f"Tolong bantu saya menganalisis dan memperbaiki kode berikut dalam bahasa {bahasa}:\n```\n{kode}\n```\nJelaskan letak error, penyebabnya, dan berikan kode yang sudah diperbaiki."
    jawaban = await ask_gemini(prompt)
    
    kode_snippet = kode if len(kode) <= 600 else kode[:600] + "\n// ... (kode dipotong)"
    header = f"**💻 Bahasa:** `{bahasa}`\n**⚠️ Kode/Kasus:**\n```{bahasa.lower()}\n{kode_snippet}\n```\n**🛠️ Solusi & Penjelasan:**\n"
    
    max_ans_len = 4000 - len(header)
    if len(jawaban) <= max_ans_len:
        desc = header + jawaban
        remaining = ""
    else:
        desc = header + jawaban[:max_ans_len]
        remaining = jawaban[max_ans_len:]

    embed = discord.Embed(
        title=f"🛠️ Bantuan Debugging ({bahasa})",
        description=desc,
        color=config.COLOR_WARNING
    )
    embed.set_footer(text=f"Ditanyakan oleh {interaction.user.display_name} • Bot QnA Matkul")
    await interaction.followup.send(embed=embed)
    
    while remaining:
        chunk = remaining[:1950]
        remaining = remaining[1950:]
        await interaction.followup.send(chunk)

@bot.tree.command(name="ringkas", description="Ringkas materi atau catatan kuliah yang panjang menjadi poin-poin penting")
@app_commands.describe(teks_materi="Tempelkan teks materi kuliah yang ingin diringkas")
async def slash_ringkas(interaction: discord.Interaction, teks_materi: str):
    await interaction.response.defer(thinking=True)
    prompt = f"Tolong buat ringkasan komprehensif dan poin-poin penting (bullet points) dari materi kuliah berikut:\n\n{teks_materi}"
    jawaban = await ask_gemini(prompt)
    
    materi_snippet = teks_materi if len(teks_materi) <= 350 else teks_materi[:350] + "..."
    materi_quoted = "\n> ".join(materi_snippet.strip().splitlines())
    header = f"**📄 Cuplikan Materi:**\n> {materi_quoted}\n\n**📝 Hasil Ringkasan:**\n"
    
    max_ans_len = 4000 - len(header)
    if len(jawaban) <= max_ans_len:
        desc = header + jawaban
        remaining = ""
    else:
        desc = header + jawaban[:max_ans_len]
        remaining = jawaban[max_ans_len:]

    embed = discord.Embed(
        title="📝 Ringkasan Materi Kuliah",
        description=desc,
        color=config.COLOR_PURPLE
    )
    embed.set_footer(text=f"Diminta oleh {interaction.user.display_name} • Bot QnA Matkul")
    await interaction.followup.send(embed=embed)
    
    while remaining:
        chunk = remaining[:1950]
        remaining = remaining[1950:]
        await interaction.followup.send(chunk)

@bot.tree.command(name="matkul", description="Panduan bidang mata kuliah utama dan tips belajarnya")
@app_commands.describe(kategori="Pilih bidang mata kuliah yang ingin dilihat")
@app_commands.choices(kategori=[
    app_commands.Choice(name="Algoritma & Pemrograman", value="alpro"),
    app_commands.Choice(name="Struktur Data", value="strukdat"),
    app_commands.Choice(name="Basis Data & SQL", value="basisdata"),
    app_commands.Choice(name="Jaringan Komputer", value="jarkom"),
    app_commands.Choice(name="Rekayasa Perangkat Lunak & UML", value="rpl"),
    app_commands.Choice(name="Sistem Operasi", value="sisop"),
])
async def slash_matkul(interaction: discord.Interaction, kategori: app_commands.Choice[str]):
    info = MATKUL_CATEGORIES.get(kategori.value)
    if info:
        embed = discord.Embed(
            title=info["title"],
            description=info["description"],
            color=config.COLOR_SUCCESS
        )
        embed.set_footer(text="Bot QnA Matkul • Pedoman Studi")
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("Kategori tidak ditemukan.", ephemeral=True)

@bot.tree.command(name="kuis-mulai", description="[Owner/Admin] Mulai game kuis berhadiah poin (Siapa Cepat Dia Dapat)")
@app_commands.describe(
    kategori="Pilih topik materi kuis",
    hadiah_poin="Jumlah poin hadiah untuk 1 pemenang pertama (default: 10)",
    soal_custom="Tulis soal kuis kustom buatan sendiri (opsional)",
    jawaban_custom="Kunci jawaban dari soal kuis kustom (opsional)"
)
@app_commands.choices(kategori=[
    app_commands.Choice(name="Algoritma & Pemrograman", value="Algoritma dan Pemrograman"),
    app_commands.Choice(name="Struktur Data", value="Struktur Data"),
    app_commands.Choice(name="Basis Data & SQL", value="Basis Data dan SQL"),
    app_commands.Choice(name="Jaringan Komputer", value="Jaringan Komputer"),
    app_commands.Choice(name="Rekayasa Perangkat Lunak", value="Rekayasa Perangkat Lunak dan UML"),
    app_commands.Choice(name="Sistem Operasi", value="Sistem Operasi"),
    app_commands.Choice(name="Tebak Output Kode", value="Tebak Output Kode Program"),
    app_commands.Choice(name="Soal Kustom Sendiri", value="custom")
])
async def slash_kuis_mulai(
    interaction: discord.Interaction,
    kategori: app_commands.Choice[str],
    hadiah_poin: int = 10,
    soal_custom: str = None,
    jawaban_custom: str = None
):
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message(
            "⛔ **Akses Ditolak!**\nPerintah memulai kuis saat ini hanya dapat dijalankan oleh pemilik bot / administrator server.",
            ephemeral=True
        )
        return

    if game_mgr.get_active_game(interaction.channel_id):
        await interaction.response.send_message(
            "⚠️ **Kuis Masih Aktif!**\nSudah ada kuis yang sedang berjalan di channel ini. Tunggu terjawab atau gunakan `/kuis-stop` untuk membatalkannya.",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    if kategori.value == "custom":
        if not soal_custom or not jawaban_custom:
            await interaction.followup.send(
                "⚠️ Jika memilih kategori **Soal Kustom Sendiri**, Anda wajib mengisi kolom `soal_custom` dan `jawaban_custom`.",
                ephemeral=True
            )
            return
        pertanyaan = soal_custom.strip()
        jawaban = jawaban_custom.strip()
        alternatif = []
        kategori_label = "Soal Kustom Pemilik"
    else:
        kategori_label = kategori.name
        quiz_data = await generate_quiz_question(kategori.value)
        pertanyaan = quiz_data.get("pertanyaan", "")
        jawaban = quiz_data.get("jawaban", "")
        alternatif = quiz_data.get("alternatif", [])

    session = game_mgr.start_game(
        channel_id=interaction.channel_id,
        question=pertanyaan,
        answer=jawaban,
        points=hadiah_poin,
        started_by=interaction.user.id,
        alternatives=alternatif
    )

    embed = discord.Embed(
        title="🎮 KUIS MATKUL: SIAPA CEPAT DIA DAPAT!",
        description=(
            f"📚 **Topik:** `{kategori_label}`\n"
            f"🎁 **Hadiah:** `+{hadiah_poin} Poin` *(Khusus 1 Pemenang Tercepat!)*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"**❓ SOAL:**\n"
            f"### {pertanyaan}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"⚡ **Aturan Main:**\n"
            f"• Langsung **ketik jawabanmu di chat channel ini**!\n"
            f"• Hanya **1 orang tercepat** dengan jawaban benar yang akan merebut hadiah poin.\n"
            f"• Game akan langsung selesai otomatis saat ada yang menjawab tepat!"
        ),
        color=config.COLOR_GAME
    )
    embed.set_footer(text=f"Kuis dimulai oleh {interaction.user.display_name} • Bot QnA Matkul")
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="kuis-stop", description="[Owner/Admin] Hentikan paksa sesi kuis yang sedang aktif di channel ini")
async def slash_kuis_stop(interaction: discord.Interaction):
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message(
            "⛔ **Akses Ditolak!** Hanya pemilik bot / administrator yang dapat menghentikan kuis.",
            ephemeral=True
        )
        return

    session = game_mgr.stop_game(interaction.channel_id)
    if session:
        embed = discord.Embed(
            title="⏹️ Kuis Telah Dihentikan",
            description=(
                f"Sesi kuis di channel ini telah dihentikan oleh {interaction.user.mention}.\n\n"
                f"💡 **Kunci Jawaban Sebenarnya:** `{session.answer}`"
            ),
            color=config.COLOR_WARNING
        )
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message(
            "Tidak ada sesi kuis yang sedang aktif di channel ini.",
            ephemeral=True
        )

@bot.tree.command(name="leaderboard", description="Lihat papan peringkat klasemen poin kuis di server")
async def slash_leaderboard(interaction: discord.Interaction):
    leaders = game_mgr.get_leaderboard(limit=10)
    if not leaders:
        await interaction.response.send_message(
            "📋 Belum ada perolehan poin kuis yang tercatat. Ayo menangkan kuis berikutnya!",
            ephemeral=True
        )
        return

    medals = ["🥇", "🥈", "🥉"]
    lines = []
    for idx, u in enumerate(leaders, start=1):
        icon = medals[idx - 1] if idx <= 3 else f"`#{idx}`"
        lines.append(f"{icon} **{u['username']}** — **{u['points']} Poin** ({u['wins']}x Juara)")

    embed = discord.Embed(
        title="🏆 Klasemen Skor Kuis Matkul",
        description="\n".join(lines),
        color=config.COLOR_GAME
    )
    embed.set_footer(text="Kumpulkan poin dengan menjawab kuis tercepat!")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="poin", description="Cek jumlah poin kuis dan total kemenangan Anda atau anggota lain")
@app_commands.describe(pengguna="Pilih anggota yang ingin dicek poinnya (opsional)")
async def slash_poin(interaction: discord.Interaction, pengguna: discord.Member = None):
    target = pengguna if pengguna else interaction.user
    stats = game_mgr.get_user_stats(target.id)

    embed = discord.Embed(
        title=f"🎖️ Profil Kuis: {target.display_name}",
        color=config.COLOR_PRIMARY
    )
    if target.display_avatar:
        embed.set_thumbnail(url=target.display_avatar.url)

    embed.add_field(name="💰 Total Poin", value=f"**{stats['points']} Poin**", inline=True)
    embed.add_field(name="🏆 Total Juara 1", value=f"**{stats['wins']}x Menang**", inline=True)
    if stats.get("last_win"):
        embed.add_field(name="🕒 Kemenangan Terakhir", value=f"`{stats['last_win']}`", inline=False)

    embed.set_footer(text="Bot QnA Matkul • Sistem Kuis Berhadiah")
    await interaction.response.send_message(embed=embed)

def build_help_embed() -> discord.Embed:
    embed = discord.Embed(
        title=f"📖 Panduan & Daftar Perintah {config.BOT_NAME}",
        description=(
            "Bot asisten cerdas untuk membantu sesi tanya jawab materi perkuliahan, koding, "
            "dan kuis interaktif berhadiah poin di Discord!"
        ),
        color=config.COLOR_PRIMARY
    )
    
    embed.add_field(
        name="💡 Tanya Jawab & AI",
        value=(
            "• `/tanya <pertanyaan>` : Tanya materi kuliah, rumus, konsep, atau teori.\n"
            "• `/debug <bahasa> <kode>` : Analisis kode error dan dapatkan solusinya.\n"
            "• `/ringkas <teks>` : Ringkas materi kuliah panjang jadi poin-poin penting.\n"
            "• `@Bot <pertanyaan>` : Tag bot langsung di channel untuk bertanya santai."
        ),
        inline=False
    )
    
    embed.add_field(
        name="🎮 Game Kuis (Siapa Cepat Dia Dapat)",
        value=(
            "• `/kuis-mulai` : *[Owner/Admin]* Mulai kuis berhadiah poin (kuota 1 pemenang).\n"
            "• `/kuis-stop` : *[Owner/Admin]* Hentikan kuis aktif & bocorkan jawaban.\n"
            "• `/leaderboard` : Lihat papan klasemen peringkat skor kuis di server.\n"
            "• `/poin [user]` : Cek perolehan poin dan rekor juara kuis."
        ),
        inline=False
    )
    
    embed.add_field(
        name="📚 Informasi & Utilitas",
        value=(
            "• `/matkul` : Panduan topik dan tips belajar mata kuliah inti.\n"
            "• `/ping` : Cek kecepatan respons / latensi koneksi bot.\n"
            "• `/shutdown` : *[Owner/Admin]* Matikan proses bot agar offline.\n"
            "• `/help` atau `/bantuan` : Menampilkan menu panduan perintah ini."
        ),
        inline=False
    )
    
    embed.set_footer(text="Bot QnA Matkul • Belajar Lebih Cepat & Menyenangkan")
    return embed

@bot.tree.command(name="help", description="Menampilkan panduan dan daftar semua perintah Bot QnA Matkul")
async def slash_help(interaction: discord.Interaction):
    await interaction.response.send_message(embed=build_help_embed())

@bot.tree.command(name="bantuan", description="Menampilkan panduan dan daftar semua perintah Bot QnA Matkul")
async def slash_bantuan(interaction: discord.Interaction):
    await interaction.response.send_message(embed=build_help_embed())

@bot.tree.command(name="ping", description="Cek latensi koneksi bot")
async def slash_ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"🏓 Pong! Latensi bot: **{latency} ms**", ephemeral=True)

@bot.tree.command(name="shutdown", description="[Owner/Admin] Matikan proses bot agar offline")
async def slash_shutdown(interaction: discord.Interaction):
    if not is_owner_or_admin(interaction):
        await interaction.response.send_message(
            "⛔ **Akses Ditolak!** Hanya pemilik bot / administrator yang dapat mematikan bot.",
            ephemeral=True
        )
        return
    await interaction.response.send_message("🔌 **Bot dimatikan.** Status bot sekarang offline. Sampai jumpa! 👋")
    await bot.close()

# ================= TEXT COMMANDS (FALLBACK) =================

@bot.command(name="tanya")
async def cmd_tanya(ctx, *, query: str):
    async with ctx.typing():
        jawaban = await ask_gemini(query)
        pertanyaan_quoted = "\n> ".join(query.strip().splitlines())
        pesan = f"**❓ Pertanyaan:**\n> {pertanyaan_quoted}\n\n**💬 Jawaban:**\n{jawaban}"
        if len(pesan) <= 2000:
            await ctx.reply(pesan)
        else:
            chunks = [pesan[i:i+1900] for i in range(0, len(pesan), 1900)]
            for chunk in chunks:
                await ctx.reply(chunk)

@bot.command(name="ping")
async def cmd_ping(ctx):
    await ctx.send(f"🏓 Pong! `{round(bot.latency * 1000)} ms`")

@bot.command(name="bantuan", aliases=["help"])
async def cmd_bantuan(ctx):
    await ctx.reply(embed=build_help_embed())

if __name__ == "__main__":
    if not config.DISCORD_BOT_TOKEN:
        print("[Error] DISCORD_BOT_TOKEN belum diisi di file .env!")
        print("Silakan buka file .env lalu tempelkan Token Bot Discord Anda.")
    else:
        bot.run(config.DISCORD_BOT_TOKEN)
