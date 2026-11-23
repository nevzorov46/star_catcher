"""Журнал (лог) обращений к базе данных."""

from datetime import datetime


class DbLogger:
    """Записывает каждое действие с базой данных в текстовый файл и в консоль."""

    def __init__(self, filename="db_log.txt"):
        self.filename = filename

    def log(self, action, details=""):
        """Добавляет в журнал строку вида: [время] ДЕЙСТВИЕ: подробности."""
        time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        line = f"[{time}] {action}: {details}"
        print(line)
        with open(self.filename, "a", encoding="utf-8") as file:
            file.write(line + "\n")
