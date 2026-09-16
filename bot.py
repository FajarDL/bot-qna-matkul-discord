import discord
from discord.ext import commands
from discord import app_commands
import config
from knowledge_base import MATKUL_CATEGORIES

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

async def ask_gemini(prompt: str, custom_instruction: str = None) -> str:
    """Fungsi pembantu untuk memanggil Gemini API."""
    if not ai_client:
        return (
            "⚠️ **API Key Gemini belum terpasang.**\n"
            "Silakan tambahkan `GEMINI_API_KEY` Anda di file `.env` untuk mengaktifkan AI Q&A."
        )
    try:
        instruction = custom_instruction if custom_instruction else config.SYSTEM_PROMPT
        response = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "system_instruction": instruction,
                "temperature": 0.7,
            }
        )
        return response.text
    except Exception as e:
        return f"Terjadi kesalahan pada server AI: `{str(e)}`"

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

    # Menjawab mention langsung dari pengguna
    if bot.user in message.mentions:
        query = message.clean_content.replace(f"@{bot.user.name}", "").strip()
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
            if len(jawaban) <= 2000:
                await message.reply(jawaban)
            else:
                chunks = [jawaban[i:i+1900] for i in range(0, len(jawaban), 1900)]
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
    
    embed = discord.Embed(
        title="💡 Tanya Jawab Materi Kuliah",
        description=jawaban[:4000],
        color=config.COLOR_PRIMARY
    )
    embed.set_footer(text=f"Ditanyakan oleh {interaction.user.display_name} • Bot QnA Matkul")
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="debug", description="Bantu analisis dan temukan solusi untuk kode yang error")
@app_commands.describe(
    bahasa="Bahasa pemrograman (misal: Python, C++, Java, SQL)",
    kode="Tuliskan kode program atau pesan error yang dialami"
)
async def slash_debug(interaction: discord.Interaction, bahasa: str, kode: str):
    await interaction.response.defer(thinking=True)
    prompt = f"Tolong bantu saya menganalisis dan memperbaiki kode berikut dalam bahasa {bahasa}:\n```\n{kode}\n```\nJelaskan letak error, penyebabnya, dan berikan kode yang sudah diperbaiki."
    jawaban = await ask_gemini(prompt)
    
    embed = discord.Embed(
        title=f"🛠️ Bantuan Debugging ({bahasa})",
        description=jawaban[:4000],
        color=config.COLOR_WARNING
    )
    embed.set_footer(text="Bot QnA Matkul • Code Debugger")
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="ringkas", description="Ringkas materi atau catatan kuliah yang panjang menjadi poin-poin penting")
@app_commands.describe(teks_materi="Tempelkan teks materi kuliah yang ingin diringkas")
async def slash_ringkas(interaction: discord.Interaction, teks_materi: str):
    await interaction.response.defer(thinking=True)
    prompt = f"Tolong buat ringkasan komprehensif dan poin-poin penting (bullet points) dari materi kuliah berikut:\n\n{teks_materi}"
    jawaban = await ask_gemini(prompt)
    
    embed = discord.Embed(
        title="📝 Ringkasan Materi Kuliah",
        description=jawaban[:4000],
        color=config.COLOR_PURPLE
    )
    embed.set_footer(text="Bot QnA Matkul • Summary Helper")
    await interaction.followup.send(embed=embed)

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

@bot.tree.command(name="bantuan", description="Menampilkan panduan penggunaan dan daftar fitur Bot QnA Matkul")
async def slash_bantuan(interaction: discord.Interaction):
    embed = discord.Embed(
        title=f"📖 Panduan {config.BOT_NAME}",
        description="Bot asisten tanya-jawab untuk mendampingi mahasiswa dalam belajar dan mengerjakan tugas perkuliahan.",
        color=config.COLOR_PRIMARY
    )
    embed.add_field(
        name="💡 `/tanya <pertanyaan>`",
        value="Tanyakan konsep materi kuliah apa pun, penjelasan rumus, atau teori algoritma.",
        inline=False
    )
    embed.add_field(
        name="🛠️ `/debug <bahasa> <kode>`",
        value="Konsultasikan kode program yang error atau tidak berjalan sesuai ekspektasi.",
        inline=False
    )
    embed.add_field(
        name="📝 `/ringkas <teks_materi>`",
        value="Meringkas materi kuliah panjang menjadi poin-poin inti yang mudah dihafal.",
        inline=False
    )
    embed.add_field(
        name="📚 `/matkul`",
        value="Melihat fokus bahasan dan tips belajar per bidang mata kuliah inti.",
        inline=False
    )
    embed.add_field(
        name="💬 Mention Langsung",
        value="Tag `@Bot` di channel mana pun untuk bertanya secara santai.",
        inline=False
    )
    embed.set_footer(text="Bot QnA Matkul • Belajar Lebih Mudah")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ping", description="Cek latensi koneksi bot")
async def slash_ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"🏓 Pong! Latensi bot: **{latency} ms**", ephemeral=True)

# ================= TEXT COMMANDS (FALLBACK) =================

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

@bot.command(name="ping")
async def cmd_ping(ctx):
    await ctx.send(f"🏓 Pong! `{round(bot.latency * 1000)} ms`")

@bot.command(name="bantuan", aliases=["help"])
async def cmd_bantuan(ctx):
    embed = discord.Embed(
        title="Daftar Perintah Bot QnA Matkul",
        description="Gunakan slash command `/` untuk pengalaman terbaik:",
        color=config.COLOR_PRIMARY
    )
    embed.add_field(name="!tanya <pertanyaan>", value="Tanya materi kuliah via prefix teks", inline=False)
    embed.add_field(name="!ping", value="Cek kecepatan respon", inline=False)
    embed.add_field(name="Slash Commands", value="Gunakan `/tanya`, `/debug`, `/ringkas`, `/matkul`, atau `/bantuan`", inline=False)
    await ctx.reply(embed=embed)

if __name__ == "__main__":
    if not config.DISCORD_BOT_TOKEN:
        print("[Error] DISCORD_BOT_TOKEN belum diisi di file .env!")
        print("Silakan buka file .env lalu tempelkan Token Bot Discord Anda.")
    else:
        bot.run(config.DISCORD_BOT_TOKEN)
