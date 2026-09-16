import discord
from discord.ext import commands
from discord import app_commands
import config
from knowledge_base import FAQ_DATA

# Inisialisasi Klien Gemini jika API Key tersedia
ai_client = None
if config.GEMINI_API_KEY:
    try:
        from google import genai
        ai_client = genai.Client(api_key=config.GEMINI_API_KEY)
        print("[AI] Google Gemini API client berhasil diinisialisasi.")
    except Exception as e:
        print(f"[AI Warning] Gagal menginisialisasi Google Gemini SDK: {e}")
else:
    print("[AI Notice] GEMINI_API_KEY belum diatur di file .env. Fitur AI akan dialihkan ke mode fallback.")

# Inisialisasi Intents Discord
intents = discord.Intents.default()
intents.message_content = True  # Izin membaca teks pesan
intents.members = True

bot = commands.Bot(command_prefix=config.BOT_PREFIX, intents=intents, help_command=None)

async def ask_gemini(prompt: str) -> str:
    """Fungsi pembantu untuk memanggil Gemini API."""
    if not ai_client:
        return (
            "Mohon maaf, API Key Google Gemini belum diatur di file `.env`.\n"
            "Silakan tambahkan `GEMINI_API_KEY` Anda untuk mengaktifkan kecerdasan AI."
        )
    try:
        response = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "system_instruction": config.SYSTEM_PROMPT,
                "temperature": 0.7,
            }
        )
        return response.text
    except Exception as e:
        return f"Terjadi kesalahan saat menghubungi layanan AI: `{str(e)}`"

@bot.event
async def on_ready():
    print("=" * 50)
    print(f"Bot Online sebagai: {bot.user.name} ({bot.user.id})")
    print(f"Prefix Perintah: {config.BOT_PREFIX}")
    print("=" * 50)
    
    # Sinkronisasi Slash Commands ke Discord
    try:
        synced = await bot.tree.sync()
        print(f"[Slash Commands] Berhasil menyinkronkan {len(synced)} slash commands.")
    except Exception as e:
        print(f"[Slash Commands Error] Gagal menyinkronkan: {e}")

    # Set status aktivitas bot
    activity = discord.Game(name="Membantu Mahasiswa | /tanya")
    await bot.change_presence(status=discord.Status.online, activity=activity)

@bot.event
async def on_message(message: discord.Message):
    # Abaikan pesan dari bot itu sendiri
    if message.author.bot:
        return

    # Jika bot di-mention secara langsung di obrolan
    if bot.user in message.mentions:
        user_query = message.clean_content.replace(f"@{bot.user.name}", "").strip()
        if not user_query:
            embed = discord.Embed(
                title=f"Halo, {message.author.display_name}!",
                description=(
                    "Saya adalah **Asisten Mahasiswa UNJANI**.\n"
                    "Silakan ketik pertanyaan Anda bersamaan dengan mention, atau gunakan perintah `/tanya <pertanyaan>`."
                ),
                color=config.COLOR_PRIMARY
            )
            await message.reply(embed=embed)
            return

        async with message.channel.typing():
            jawaban = await ask_gemini(user_query)
            
            # Memecah pesan jika melebihi batas 2000 karakter Discord
            if len(jawaban) <= 2000:
                await message.reply(jawaban)
            else:
                chunks = [jawaban[i:i+1900] for i in range(0, len(jawaban), 1900)]
                for chunk in chunks:
                    await message.reply(chunk)
        return

    # Memproses perintah ber-prefix teks (seperti !tanya atau !bantuan)
    await bot.process_commands(message)

# ================= SLASH COMMANDS =================

@bot.tree.command(name="tanya", description="Tanyakan materi kuliah, konsep kode, atau panduan akademik ke AI")
@app_commands.describe(pertanyaan="Ketikkan pertanyaan yang ingin Anda ajukan")
async def slash_tanya(interaction: discord.Interaction, pertanyaan: str):
    await interaction.response.defer(thinking=True)
    jawaban = await ask_gemini(pertanyaan)
    
    embed = discord.Embed(
        title="Tanya Jawab Akademik",
        description=jawaban[:4000],
        color=config.COLOR_PRIMARY
    )
    embed.set_footer(text=f"Ditanyakan oleh {interaction.user.display_name} • Didukung oleh Google Gemini")
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="simta", description="Informasi cepat mengenai pedoman Tugas Akhir SIMTA Informatika UNJANI")
@app_commands.describe(topik="Pilih topik informasi Tugas Akhir yang ingin dicari")
@app_commands.choices(topik=[
    app_commands.Choice(name="Syarat Pendaftaran TA1 (Sempro)", value="syarat_ta1"),
    app_commands.Choice(name="Syarat Pendaftaran TA2 (Sidang)", value="syarat_ta2"),
    app_commands.Choice(name="Aturan Bimbingan & Logbook", value="bimbingan"),
    app_commands.Choice(name="Formula Bobot Penilaian Akhir", value="penilaian"),
    app_commands.Choice(name="Publikasi Ilmiah & Penahanan Nilai", value="publikasi"),
    app_commands.Choice(name="Ketentuan Kuota Dosen Pembimbing", value="kuota_dosen"),
])
async def slash_simta(interaction: discord.Interaction, topik: app_commands.Choice[str]):
    info = FAQ_DATA.get(topik.value)
    if info:
        embed = discord.Embed(
            title=info["title"],
            description=info["description"],
            color=config.COLOR_SUCCESS
        )
        embed.set_footer(text="SIMTA Informatika UNJANI • Pedoman Resmi")
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("Topik tidak ditemukan.", ephemeral=True)

@bot.tree.command(name="bantuan", description="Menampilkan panduan penggunaan dan daftar perintah bot")
async def slash_bantuan(interaction: discord.Interaction):
    embed = discord.Embed(
        title=f"Panduan Penggunaan {config.BOT_NAME}",
        description="Bot ini dirancang untuk mendampingi mahasiswa Informatika UNJANI dalam studi dan tugas akhir.",
        color=config.COLOR_PRIMARY
    )
    embed.add_field(
        name="1. Tanya AI Langsung (`/tanya`)",
        value="Gunakan `/tanya <pertanyaan>` atau mention `@bot` di channel obrolan untuk tanya materi kuliah, konsep logika, atau debugging kode.",
        inline=False
    )
    embed.add_field(
        name="2. Pedoman Tugas Akhir SIMTA (`/simta`)",
        value="Gunakan `/simta` lalu pilih topik (Syarat TA1, TA2, Bimbingan, Nilai Akhir, Publikasi Sinta/Scopus, Kuota Dosen).",
        inline=False
    )
    embed.add_field(
        name="3. Cek Status Koneksi (`/ping`)",
        value="Memeriksa kecepatan respons bot ke server Discord.",
        inline=False
    )
    embed.set_footer(text="Asisten Virtual Mahasiswa • Informatika UNJANI")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ping", description="Mengecek status latensi bot")
async def slash_ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"Pong! Latensi bot saat ini adalah **{latency} ms**.", ephemeral=True)

# ================= TEXT COMMANDS (FALLBACK) =================

@bot.command(name="ping")
async def cmd_ping(ctx):
    await ctx.send(f"Pong! `{round(bot.latency * 1000)} ms`")

@bot.command(name="tanya")
async def cmd_tanya(ctx, *, query: str):
    async with ctx.typing():
        jawaban = await ask_gemini(query)
        if len(jawaban) <= 2000:
            await ctx.reply(jawaban)
        else:
            chunks = [jawaban[i:i+1900] for i in range(0, len(jawaban), 1900)]
            for chunk in chunks:
                await ctx.reply(chunk)

@bot.command(name="bantuan", aliases=["help"])
async def cmd_bantuan(ctx):
    embed = discord.Embed(
        title="Daftar Perintah Asisten Mahasiswa",
        description="Gunakan slash command `/` atau prefix `!` untuk berinteraksi:",
        color=config.COLOR_PRIMARY
    )
    embed.add_field(name="!tanya <pertanyaan>", value="Mengajukan pertanyaan akademik ke AI", inline=False)
    embed.add_field(name="!ping", value="Cek latensi koneksi bot", inline=False)
    embed.add_field(name="Slash Commands", value="Gunakan `/tanya`, `/simta`, `/bantuan`, atau `/ping`", inline=False)
    await ctx.reply(embed=embed)

if __name__ == "__main__":
    if not config.DISCORD_BOT_TOKEN:
        print("[Error] DISCORD_BOT_TOKEN belum diisi di file .env!")
        print("Silakan buka file .env lalu tempelkan Token Bot Discord Anda.")
    else:
        bot.run(config.DISCORD_BOT_TOKEN)
