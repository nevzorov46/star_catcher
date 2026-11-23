"""Игровые объекты: главный персонаж и падающие предметы."""

import math
import random

import pygame

from settings import (
    WIDTH, HEIGHT, PLAYER_WIDTH, PLAYER_HEIGHT, PLAYER_SPEED,
    YELLOW, GOLD, BLUE, WHITE, RED,
    STAR_POINTS, GOLD_STAR_POINTS,
)


def star_points(cx, cy, outer, inner):
    """Вершины пятиконечной звезды для pygame.draw.polygon."""
    points = []
    for i in range(10):
        radius = outer if i % 2 == 0 else inner
        angle = math.pi / 2 + i * math.pi / 5
        points.append((cx + radius * math.cos(angle), cy - radius * math.sin(angle)))
    return points


class Player(pygame.sprite.Sprite):
    """Главный персонаж — корзина, которой управляют стрелками."""

    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((PLAYER_WIDTH, PLAYER_HEIGHT + 20), pygame.SRCALPHA)
        self.draw_basket()
        self.rect = self.image.get_rect(midbottom=(WIDTH // 2, HEIGHT - 10))
        self.speed = PLAYER_SPEED

    def draw_basket(self):
        """Рисует корзину на собственной поверхности игрока."""
        w, h = self.image.get_size()
        pygame.draw.polygon(self.image, BLUE, [(0, 20), (w, 20), (w - 12, h), (12, h)])
        pygame.draw.rect(self.image, WHITE, (0, 16, w, 6), border_radius=3)

    def update(self):
        """Двигает корзину влево/вправо, пока зажата стрелка."""
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed
        # Не даём корзине уехать за край экрана
        self.rect.left = max(self.rect.left, 0)
        self.rect.right = min(self.rect.right, WIDTH)


class FallingObject(pygame.sprite.Sprite):
    """Общий родитель для всего, что падает сверху."""

    size = 30

    def __init__(self, speed):
        super().__init__()
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.draw()
        x = random.randint(self.size, WIDTH - self.size)
        self.rect = self.image.get_rect(center=(x, -self.size))
        self.speed = speed

    def draw(self):
        """Каждый потомок рисует себя сам."""
        raise NotImplementedError

    def update(self):
        self.rect.y += self.speed
        # Улетел за нижний край — удаляем из всех групп
        if self.rect.top > HEIGHT:
            self.kill()


class Star(FallingObject):
    """Обычная звезда: +1 очко."""

    color = YELLOW
    points = STAR_POINTS

    def draw(self):
        c = self.size / 2
        pygame.draw.polygon(self.image, self.color, star_points(c, c, c, c * 0.45))


class GoldStar(Star):
    """Редкая большая золотая звезда: +3 очка."""

    size = 40
    color = GOLD
    points = GOLD_STAR_POINTS


class Bomb(FallingObject):
    """Бомба: отнимает одну жизнь."""

    def draw(self):
        c = self.size // 2
        pygame.draw.circle(self.image, (90, 90, 105), (c, c + 2), c - 3)
        pygame.draw.circle(self.image, RED, (c, c + 2), c - 3, 3)
        pygame.draw.line(self.image, WHITE, (c, 5), (c + 5, 1), 2)
        pygame.draw.circle(self.image, YELLOW, (c + 6, 2), 3)
