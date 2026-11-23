"""Работа с базой данных SQLite: сохранение результатов и таблица рекордов."""

import sqlite3
from datetime import datetime

from logger import DbLogger


class Database:
    """Отвечает за всё общение игры с базой данных."""

    def __init__(self, db_name):
        self.logger = DbLogger()
        # Подключаемся к файлу базы (если его нет, SQLite создаст его сам)
        self.connection = sqlite3.connect(db_name)
        self.logger.log("ПОДКЛЮЧЕНИЕ", db_name)
        self.create_table()

    def create_table(self):
        """Создаёт таблицу результатов, если её ещё нет."""
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                score INTEGER NOT NULL,
                is_win INTEGER NOT NULL,
                played_at TEXT NOT NULL
            )
            """
        )
        self.connection.commit()
        self.logger.log("ТАБЛИЦА", "results готова")

    def add_result(self, name, score, is_win):
        """Сохраняет результат одной игры."""
        played_at = datetime.now().strftime("%d.%m.%Y %H:%M")
        # Знаки ? защищают от SQL-инъекций: значения подставляет сам sqlite3
        self.connection.execute(
            "INSERT INTO results (name, score, is_win, played_at) VALUES (?, ?, ?, ?)",
            (name, score, int(is_win), played_at),
        )
        self.connection.commit()
        result = "победа" if is_win else "поражение"
        self.logger.log("СОХРАНЕНИЕ", f"{name}, {score} очков, {result}")

    def get_top(self, limit=5):
        """Возвращает лучших игроков: лучший результат каждого имени."""
        cursor = self.connection.execute(
            """
            SELECT name, MAX(score) AS best
            FROM results
            GROUP BY name
            ORDER BY best DESC
            LIMIT ?
            """,
            (limit,),
        )
        top = cursor.fetchall()
        self.logger.log("ТОП", f"загружено записей: {len(top)}")
        return top

    def close(self):
        """Закрывает соединение с базой."""
        self.connection.close()
        self.logger.log("ОТКЛЮЧЕНИЕ", "соединение закрыто")
