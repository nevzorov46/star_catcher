"""Главный класс игры: экраны, игровой цикл, подсчёт очков."""

import random

import pygame

from database import Database
from settings import (
    WIDTH, HEIGHT, FPS, TITLE, BG_COLOR, WHITE, GRAY, YELLOW, GOLD, RED, GREEN,
    WIN_SCORE, START_LIVES, SPAWN_DELAY, MIN_SPAWN_DELAY,
    BOMB_CHANCE, GOLD_CHANCE, DB_NAME,
)
from sprites import Player, Star, GoldStar, Bomb, star_points

# Названия экранов (состояний) игры
NAME_INPUT = "name_input"
RULES = "rules"
PLAYING = "playing"
PAUSED = "paused"
GAME_OVER = "game_over"

FONT_NAMES = ["arial", "segoeui", "dejavusans", "freesans"]
MAX_NAME_LENGTH = 15


class Game:
    """Управляет всей игрой: от ввода имени до таблицы рекордов."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()

        self.font_big = pygame.font.SysFont(FONT_NAMES, 48, bold=True)
        self.font = pygame.font.SysFont(FONT_NAMES, 28)
        self.font_small = pygame.font.SysFont(FONT_NAMES, 20)

        self.db = Database(DB_NAME)
        self.state = NAME_INPUT
        self.player_name = ""
        self.name_error = ""
        self.running = True

        # Фоновые звёздочки для красоты
        self.background = [
            (random.randint(0, WIDTH), random.randint(0, HEIGHT), random.randint(1, 2))
            for _ in range(80)
        ]
        self.reset()

    # ---------- подготовка новой партии ----------

    def reset(self):
        """Сбрасывает очки, жизни и предметы перед новой игрой."""
        self.player = Player()
        self.stars = pygame.sprite.Group()
        self.bombs = pygame.sprite.Group()
        self.all_sprites = pygame.sprite.Group(self.player)
        self.score = 0
        self.lives = START_LIVES
        self.is_win = False
        self.top = []
        self.last_spawn = 0
        self.messages = []  # всплывающие подсказки: [текст, цвет, время исчезновения]

    def show_message(self, text, color=WHITE, duration=1500):
        """Показывает подсказку в центре экрана на duration миллисекунд."""
        self.messages = [[text, color, pygame.time.get_ticks() + duration]]

    # ---------- главный цикл ----------

    def run(self):
        while self.running:
            self.clock.tick(FPS)
            self.handle_events()
            if self.state == PLAYING:
                self.update()
            self.draw()
        self.db.close()
        pygame.quit()

    # ---------- обработка нажатий ----------

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif self.state == NAME_INPUT:
                self.handle_name_input(event)
            elif event.type == pygame.KEYDOWN:
                self.handle_key(event.key)

    def handle_name_input(self, event):
        """Ввод имени. TEXTINPUT корректно принимает и русские буквы."""
        if event.type == pygame.TEXTINPUT:
            if len(self.player_name) < MAX_NAME_LENGTH:
                self.player_name += event.text
                self.name_error = ""
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.player_name = self.player_name[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.player_name.strip():
                    self.player_name = self.player_name.strip()
                    self.state = RULES
                else:
                    self.name_error = "Имя не может быть пустым"
            elif event.key == pygame.K_ESCAPE:
                self.running = False

    def handle_key(self, key):
        if self.state == RULES:
            if key == pygame.K_SPACE:
                self.start_game()
            elif key == pygame.K_ESCAPE:
                self.running = False
        elif self.state == PLAYING:
            if key == pygame.K_p:
                self.state = PAUSED
            elif key == pygame.K_ESCAPE:
                self.finish(is_win=False)
        elif self.state == PAUSED:
            if key == pygame.K_p:
                self.state = PLAYING
        elif self.state == GAME_OVER:
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.state = RULES
            elif key == pygame.K_n:
                # Сменить игрока
                self.player_name = ""
                self.state = NAME_INPUT
            elif key == pygame.K_ESCAPE:
                self.running = False

    def start_game(self):
        self.reset()
        self.state = PLAYING
        self.last_spawn = pygame.time.get_ticks()
        self.show_message(f"Удачи, {self.player_name}! Лови звёзды!", YELLOW, 2000)

    # ---------- игровая логика ----------

    def spawn_object(self):
        """Создаёт новый падающий предмет. Чем больше очков, тем быстрее."""
        speed = 3 + self.score // 6 + random.random() * 2
        roll = random.random()
        if roll < BOMB_CHANCE:
            obj = Bomb(speed)
            self.bombs.add(obj)
        elif roll < BOMB_CHANCE + GOLD_CHANCE:
            obj = GoldStar(speed)
            self.stars.add(obj)
        else:
            obj = Star(speed)
            self.stars.add(obj)
        self.all_sprites.add(obj)

    def update(self):
        now = pygame.time.get_ticks()
        delay = max(MIN_SPAWN_DELAY, SPAWN_DELAY - self.score * 12)
        if now - self.last_spawn > delay:
            self.spawn_object()
            self.last_spawn = now

        self.all_sprites.update()

        # Поймали звёзды
        for star in pygame.sprite.spritecollide(self.player, self.stars, dokill=True):
            old_score = self.score
            self.score += star.points
            if isinstance(star, GoldStar):
                self.show_message("Золотая звезда! +3", GOLD, 1000)
            # Подсказка на полпути к победе
            if old_score < WIN_SCORE // 2 <= self.score:
                self.show_message("Половина пути! Скорость растёт", GREEN, 1800)

        # Поймали бомбу
        if pygame.sprite.spritecollide(self.player, self.bombs, dokill=True):
            self.lives -= 1
            if self.lives == 1:
                self.show_message("Осторожно! Осталась последняя жизнь", RED, 1800)
            elif self.lives > 0:
                self.show_message("Бомба! Минус жизнь", RED, 1200)

        if self.score >= WIN_SCORE:
            self.finish(is_win=True)
        elif self.lives <= 0:
            self.finish(is_win=False)

    def finish(self, is_win):
        """Конец партии: сохраняем результат в БД и загружаем топ-5."""
        self.is_win = is_win
        self.db.add_result(self.player_name, self.score, is_win)
        self.top = self.db.get_top(5)
        self.state = GAME_OVER

    # ---------- отрисовка ----------

    def text(self, text, font, color, center):
        surface = font.render(text, True, color)
        self.screen.blit(surface, surface.get_rect(center=center))

    def draw_background(self):
        self.screen.fill(BG_COLOR)
        for x, y, r in self.background:
            pygame.draw.circle(self.screen, GRAY, (x, y), r)

    def draw(self):
        self.draw_background()
        if self.state == NAME_INPUT:
            self.draw_name_input()
        elif self.state == RULES:
            self.draw_rules()
        elif self.state in (PLAYING, PAUSED):
            self.draw_game()
            if self.state == PAUSED:
                self.draw_pause()
        elif self.state == GAME_OVER:
            self.draw_game_over()
        pygame.display.flip()

    def draw_name_input(self):
        pygame.draw.polygon(self.screen, YELLOW, star_points(WIDTH // 2, 110, 45, 20))
        self.text(TITLE, self.font_big, YELLOW, (WIDTH // 2, 200))
        self.text("Введите своё имя и нажмите Enter", self.font, WHITE, (WIDTH // 2, 280))

        box = pygame.Rect(0, 0, 400, 56)
        box.center = (WIDTH // 2, 350)
        pygame.draw.rect(self.screen, WHITE, box, 2, border_radius=8)
        cursor = "|" if pygame.time.get_ticks() // 500 % 2 == 0 else " "
        self.text(self.player_name + cursor, self.font, YELLOW, box.center)

        if self.name_error:
            self.text(self.name_error, self.font_small, RED, (WIDTH // 2, 410))
        self.text(f"До {MAX_NAME_LENGTH} символов. Esc — выход",
                  self.font_small, GRAY, (WIDTH // 2, 450))

    def draw_rules(self):
        self.text(f"Привет, {self.player_name}!", self.font_big, YELLOW, (WIDTH // 2, 80))
        lines = [
            ("Как играть:", WHITE),
            ("← →  двигают корзину", WHITE),
            ("Лови жёлтые звёзды: +1 очко", YELLOW),
            ("Золотая большая звезда: +3 очка", GOLD),
            ("Бомбы отнимают жизнь — уворачивайся!", RED),
            (f"ПОБЕДА: набери {WIN_SCORE} очков", GREEN),
            (f"ПОРАЖЕНИЕ: потеряй все {START_LIVES} жизни", RED),
            ("P — пауза,  Esc — закончить игру", GRAY),
        ]
        for i, (line, color) in enumerate(lines):
            self.text(line, self.font, color, (WIDTH // 2, 160 + i * 42))
        if pygame.time.get_ticks() // 600 % 2 == 0:
            self.text("Нажми ПРОБЕЛ, чтобы начать", self.font, WHITE, (WIDTH // 2, 520))

    def draw_game(self):
        self.all_sprites.draw(self.screen)

        # Панель сверху: очки, прогресс, жизни
        score_text = self.font.render(f"Очки: {self.score} / {WIN_SCORE}", True, WHITE)
        self.screen.blit(score_text, (15, 10))
        bar = pygame.Rect(15, 48, 200, 10)
        pygame.draw.rect(self.screen, GRAY, bar, 1)
        filled = bar.copy()
        filled.width = int(200 * min(self.score, WIN_SCORE) / WIN_SCORE)
        pygame.draw.rect(self.screen, GREEN, filled)

        lives_text = self.font.render("Жизни:", True, WHITE)
        self.screen.blit(lives_text, (WIDTH - 245, 10))
        for i in range(self.lives):
            pygame.draw.circle(self.screen, RED, (WIDTH - 120 + i * 32, 28), 11)

        self.text("← → движение   P пауза   Esc выход", self.font_small, GRAY,
                  (WIDTH // 2, 80))

        # Всплывающие подсказки
        now = pygame.time.get_ticks()
        self.messages = [m for m in self.messages if m[2] > now]
        for text, color, _ in self.messages:
            self.text(text, self.font, color, (WIDTH // 2, HEIGHT // 2 - 60))

    def draw_pause(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))
        self.text("ПАУЗА", self.font_big, WHITE, (WIDTH // 2, HEIGHT // 2 - 20))
        self.text("Нажми P, чтобы продолжить", self.font, GRAY, (WIDTH // 2, HEIGHT // 2 + 40))

    def draw_game_over(self):
        if self.is_win:
            self.text("ПОБЕДА!", self.font_big, GREEN, (WIDTH // 2, 60))
        else:
            self.text("ИГРА ОКОНЧЕНА", self.font_big, RED, (WIDTH // 2, 60))
        self.text(f"{self.player_name}, твой счёт: {self.score}", self.font, WHITE,
                  (WIDTH // 2, 120))

        self.text("Топ-5 игроков", self.font, YELLOW, (WIDTH // 2, 185))
        for i, (name, best) in enumerate(self.top):
            color = YELLOW if name == self.player_name else WHITE
            y = 235 + i * 40
            self.text(f"{i + 1}.", self.font, color, (WIDTH // 2 - 170, y))
            self.text(name, self.font, color, (WIDTH // 2 - 20, y))
            self.text(str(best), self.font, color, (WIDTH // 2 + 160, y))

        self.text("Enter — играть ещё   N — другой игрок   Esc — выход",
                  self.font_small, GRAY, (WIDTH // 2, HEIGHT - 50))
