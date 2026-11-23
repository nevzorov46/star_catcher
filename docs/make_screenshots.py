"""Делает скриншоты игры для README (без открытия окна и без изменения ваших рекордов)."""

import os
import random
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "screenshots")
sys.path.insert(0, ROOT)
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import settings  # noqa: E402

tmp = tempfile.mkdtemp()
os.chdir(tmp)  # временная база и журнал, чтобы не трогать настоящие
settings.DB_NAME = os.path.join(tmp, "demo.db")
random.seed(7)

import pygame  # noqa: E402
import game  # noqa: E402
from sprites import Star, GoldStar, Bomb  # noqa: E402

g = game.Game()


def save(name):
    pygame.image.save(g.screen, os.path.join(OUT, name + ".png"))


g.player_name = "Аня"
g.state = game.NAME_INPUT
g.draw()
save("1_name")

g.state = game.RULES
g.draw()
save("2_rules")

g.start_game()
g.score, g.lives = 17, 2
g.player.rect.centerx = 380
for cls, x, y in [(Star, 140, 150), (Star, 520, 260), (GoldStar, 300, 380), (Bomb, 660, 190),
                  (Bomb, 230, 470), (Star, 700, 420), (Star, 420, 110)]:
    obj = cls(4)
    obj.rect.center = (x, y)
    (g.bombs if cls is Bomb else g.stars).add(obj)
    g.all_sprites.add(obj)
g.show_message("Половина пути! Скорость растёт", settings.GREEN, 60000)
g.draw()
save("3_game")

for name, score in [("Макс", 24), ("Оля", 19), ("Игорь", 12), ("Лена", 8)]:
    g.db.add_result(name, score, False)
g.score = 30
g.finish(is_win=True)
g.draw()
save("4_win")
print("Скриншоты сохранены в", OUT)
