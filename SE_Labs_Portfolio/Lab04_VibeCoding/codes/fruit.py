import random
import math
import pygame


class Fruit:
    def __init__(self, screen_width, base_speed=0, force_hazard=False):
        self.screen_width = screen_width
        self.radius = 14

        self.x = random.randint(30, screen_width - 30)
        self.y = -self.radius * 2

        # First hazard can be forced for demonstration.
        # After that, hazards have a 20% random chance.
        self.is_hazard = force_hazard or random.random() < 0.20

        if self.is_hazard:
            self.speed = random.uniform(4.0, 6.5) + base_speed
            self.color = (40, 40, 40)

        else:
            minimum_speed = 4.0 + base_speed
            maximum_speed = 6.5 + base_speed

            self.speed = random.uniform(
                minimum_speed,
                maximum_speed
            )

            self.color = random.choice([
                (230, 45, 45),     # Apple
                (245, 140, 30),    # Orange
                (160, 60, 200),    # Grape
            ])

    def update(self):
        self.y += self.speed

    def is_missed(self, screen_height):
        return self.y > screen_height

    @property
    def rect(self):
        return pygame.Rect(
            int(self.x - self.radius),
            int(self.y - self.radius),
            self.radius * 2,
            self.radius * 2,
        )

    def render(self, surface):
        center = (
            int(self.x),
            int(self.y)
        )

        if self.is_hazard:
            # Dark hazard body
            pygame.draw.circle(
                surface,
                self.color,
                center,
                self.radius
            )

            # Green spikes
            points = []

            for i in range(8):
                angle = i * 45
                rad = math.radians(angle)

                points.append((
                    int(
                        self.x +
                        math.cos(rad) *
                        (self.radius + 5)
                    ),
                    int(
                        self.y +
                        math.sin(rad) *
                        (self.radius + 5)
                    )
                ))

            pygame.draw.polygon(
                surface,
                (80, 220, 80),
                points
            )

            # Red center
            pygame.draw.circle(
                surface,
                (220, 50, 50),
                center,
                5
            )

        else:
            # Normal fruit
            pygame.draw.circle(
                surface,
                self.color,
                center,
                self.radius
            )

            # Small highlight
            pygame.draw.circle(
                surface,
                (255, 255, 255),
                (
                    int(self.x - 4),
                    int(self.y - 4)
                ),
                3
            )
