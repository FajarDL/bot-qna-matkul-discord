import os
import re
import json
from datetime import datetime
from typing import Optional, Dict, List, Tuple

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
        self.valid_answers = [self.normalize_text(self.answer)]
        if alternatives:
            for alt in alternatives:
                norm_alt = self.normalize_text(alt)
                if norm_alt and norm_alt not in self.valid_answers:
                    self.valid_answers.append(norm_alt)

    @staticmethod
    def normalize_text(text: str) -> str:
        """Menghapus tanda baca, spasi berlebih, dan mengubah ke huruf kecil."""
        if not text:
            return ""
        text = text.lower().strip()
        # Hilangkan simbol/tanda baca non-alfanumerik
        text = re.sub(r"[^\w\s]", "", text)
        # Hilangkan spasi berulang
        text = re.sub(r"\s+", " ", text)
        return text

    def is_correct(self, guess: str) -> bool:
        """Cek apakah tebakan pengguna cocok dengan salah satu jawaban yang benar."""
        norm_guess = self.normalize_text(guess)
        if not norm_guess:
            return False
        
        # Cek kesesuaian tepat
        if norm_guess in self.valid_answers:
            return True
        
        # Cek jika jawaban utama terkandung dalam tebakan (jika tebakan adalah kalimat pendek)
        for valid in self.valid_answers:
            # Jika kata kunci jawaban memiliki panjang >= 4 huruf dan ada di dalam tebakan
            if len(valid) >= 4 and f" {valid} " in f" {norm_guess} ":
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

# Singleton instance
game_mgr = GameManager()
