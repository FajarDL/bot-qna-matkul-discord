import os
import re
import json
from datetime import datetime
from typing import Optional, Dict, List, Tuple

import random

WRONG_ANSWER_JOKES = [
    "❌ **Tetoot! Salah.** Dosen killer langsung tersenyum tipis melihat jawabanmu... 💀",
    "❌ **Kurang tepat {user}!** Waduh, jangan-jangan semalam begadang bukan belajar tapi push rank? 🎮",
    "❌ **Salah bung!** Nilai kuis terancam terjun bebas kalau begini caranya. Coba lagi! 📉",
    "❌ **Belum bener nih {user}.** Otakmu kayaknya butuh di-restart atau di-compile ulang dulu deh. 🔄",
    "❌ **Yah, melenceng jauh!** Jawabanmu sama materinya udah kayak beda universe. Ayo tebak lagi! 🚀",
    "❌ **Salah!** Malaikat pencatat amal baik pun bingung mau masukin jawaban ini ke mana... 🗿",
    "❌ **Salah euy {user}!** Belajar di mana kamu tadi malam? Jangan bikin dosen menangis di pojokan lab! 😭",
    "❌ **Masih belum tepat!** Tenang, kesempatan masih terbuka lebar sebelum direbut yang lain! 🏃‍♂️",
    "❌ **Waduh bukan itu!** Kode error aja ada solusinya di StackOverflow, masa jawaban ini zonk 🤣",
    "❌ **Bukan {user}!** Coba minum kopi dulu biar sinapsis otaknya nyambung kembali ☕",
    "❌ **Tetoot! Salah.** Aura *'Hari ini kita post-test ya!'* mendadak semakin terasa dingin... 💀",
    "❌ **Salah!** Tapi hargai usahanya, setidaknya jempolmu sudah berjuang keras mengetik 👍",
    "❌ **Masih salah!** Kalau di terminal Linux, ini udah keluar pesan `Segmentation fault (core dumped)` 💥",
    "❌ **Nggak kena!** Jawabanmu seperti WiFi kampus: kadang ada, tapi seringnya nggak nyambung! 📶",
    "❌ **Zonk!** Coba cek lagi catatannya, atau jangan-jangan bukunya masih segel plastik? 📦"
]

class GameSession:
    def __init__(self, channel_id: int, question: str, answer: str, points: int, started_by: int, alternatives: List[str] = None):
        self.channel_id = channel_id
        self.question = question
        self.answer = answer.strip()
        self.points = points
        self.started_by = started_by
        self.started_at = datetime.now()
        self.is_active = True
        
        # Kumpulkan semua variasi jawaban yang sah
        self.valid_answers = []
        self._add_valid_answer(self.answer)
        if alternatives:
            for alt in alternatives:
                self._add_valid_answer(alt)

    def _add_valid_answer(self, raw_text: str):
        if not raw_text:
            return
        cleaned = re.sub(r"[\*\_`\"']", "", str(raw_text))
        norm = self.normalize_text(cleaned)
        if norm and norm not in self.valid_answers:
            self.valid_answers.append(norm)

        # Pisahkan variasi jika ada pemisah seperti '/', '(', ',', 'atau', 'or'
        # contoh: "Stack (Tumpukan)" -> "stack", "tumpukan"
        parts = re.split(r"[\/,\(\)\|\;\-]|\batau\b|\bor\b", cleaned, flags=re.IGNORECASE)
        for part in parts:
            p_norm = self.normalize_text(part)
            if p_norm and len(p_norm) >= 2 and p_norm not in self.valid_answers:
                self.valid_answers.append(p_norm)

    @staticmethod
    def normalize_text(text: str) -> str:
        """Menghapus tanda baca, spasi berlebih, dan mengubah ke huruf kecil."""
        if not text:
            return ""
        text = text.lower().strip()
        text = re.sub(r"[\*\_`\"'.,!?:;()\[\]{}<>/\\|@#$%^&+=~-]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def is_correct(self, guess: str) -> bool:
        """Cek apakah tebakan pengguna cocok dengan salah satu jawaban yang benar."""
        norm_guess = self.normalize_text(guess)
        if not norm_guess:
            return False
        
        # 1. Cek kesesuaian tepat
        if norm_guess in self.valid_answers:
            return True
        
        # 2. Cek apakah salah satu kata kunci jawaban muncul sebagai kata utuh dalam tebakan
        for valid in self.valid_answers:
            if not valid:
                continue
            # Boundary pencarian kata
            pattern = rf"(?:^|\s){re.escape(valid)}(?:$|\s)"
            if re.search(pattern, norm_guess):
                return True
            # Jika tebakan adalah bagian dari kata kunci yang cukup panjang
            if len(norm_guess) >= 4 and norm_guess in valid:
                return True
        return False


class GameManager:
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        self.data_dir = data_dir
        self.scores_file = os.path.join(self.data_dir, "scores.json")
        self.active_games: Dict[int, GameSession] = {}
        
        # Pastikan direktori data tersedia
        os.makedirs(self.data_dir, exist_ok=True)
        self._ensure_storage()

    def _ensure_storage(self):
        if not os.path.exists(self.scores_file):
            with open(self.scores_file, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=2)

    def _load_scores(self) -> dict:
        try:
            with open(self.scores_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_scores(self, scores: dict):
        with open(self.scores_file, "w", encoding="utf-8") as f:
            json.dump(scores, f, indent=2, ensure_ascii=False)

    def start_game(self, channel_id: int, question: str, answer: str, points: int = 10, started_by: int = 0, alternatives: List[str] = None) -> GameSession:
        """Memulai sesi game kuis baru di suatu channel."""
        session = GameSession(
            channel_id=channel_id,
            question=question,
            answer=answer,
            points=points,
            started_by=started_by,
            alternatives=alternatives
        )
        self.active_games[channel_id] = session
        return session

    def get_active_game(self, channel_id: int) -> Optional[GameSession]:
        """Mengambil sesi game yang sedang aktif di channel."""
        session = self.active_games.get(channel_id)
        if session and session.is_active:
            return session
        return None

    def stop_game(self, channel_id: int) -> Optional[GameSession]:
        """Menghentikan sesi game yang sedang aktif di channel."""
        session = self.active_games.pop(channel_id, None)
        if session:
            session.is_active = False
            return session
        return None

    def check_guess(self, channel_id: int, user_id: int, username: str, guess: str) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Memeriksa tebakan pengguna.
        Return: (is_correct, points_awarded, correct_answer)
        """
        session = self.get_active_game(channel_id)
        if not session:
            return False, None, None

        if session.is_correct(guess):
            # Tutup sesi game seketika (1 game = 1 pemenang)
            session.is_active = False
            self.active_games.pop(channel_id, None)
            
            # Tambahkan poin ke database
            points = session.points
            self.add_points(user_id=user_id, username=username, points=points)
            return True, points, session.answer

        return False, None, None

    def add_points(self, user_id: int, username: str, points: int):
        """Menambahkan poin kemenangan ke profil pengguna."""
        scores = self._load_scores()
        uid_str = str(user_id)
        
        if uid_str not in scores:
            scores[uid_str] = {
                "username": username,
                "points": 0,
                "wins": 0,
                "last_win": None
            }
        
        scores[uid_str]["username"] = username  # Perbarui username terbaru
        scores[uid_str]["points"] += points
        scores[uid_str]["wins"] += 1
        scores[uid_str]["last_win"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self._save_scores(scores)

    def get_user_stats(self, user_id: int) -> dict:
        """Mengambil data poin dan jumlah menang pengguna."""
        scores = self._load_scores()
        return scores.get(str(user_id), {
            "username": "Pengguna",
            "points": 0,
            "wins": 0,
            "last_win": None
        })

    def get_leaderboard(self, limit: int = 10) -> List[dict]:
        """Mengambil daftar peringkat skor tertinggi."""
        scores = self._load_scores()
        ranked = sorted(
            [{"user_id": uid, **data} for uid, data in scores.items()],
            key=lambda x: (x.get("points", 0), x.get("wins", 0)),
            reverse=True
        )
        return ranked[:limit]

    def get_random_wrong_joke(self, user_mention: str) -> str:
        """Mengambil lelucon acak saat jawaban pengguna salah."""
        joke_template = random.choice(WRONG_ANSWER_JOKES)
        return joke_template.format(user=user_mention)

# Singleton instance
game_mgr = GameManager()
