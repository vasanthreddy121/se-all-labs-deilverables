import pygame

class Basket:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.width = 90
        self.height = 26
        self.speed = 8
        self.x = (screen_width // 2) - (self.width // 2)
        self.y = screen_height - self.height - 25

    def move_left(self):
        self.x -= self.speed
        if self.x < 10:
            self.x = 10

    def move_right(self):
        self.x += self.speed
        if self.x > self.screen_width - self.width - 10:
            self.x = self.screen_width - self.width - 10

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    def render(self, surface):
        basket_rect = pygame.Rect(int(self.x), int(self.y), self.width, self.height)
        pygame.draw.rect(surface, (170, 105, 55), basket_rect, border_radius=6)
        pygame.draw.rect(surface, (230, 175, 120), basket_rect, width=2, border_radius=6)
        rim_rect = pygame.Rect(int(self.x) - 4, int(self.y), self.width + 8, 7)
        pygame.draw.rect(surface, (135, 80, 40), rim_rect, border_radius=3)