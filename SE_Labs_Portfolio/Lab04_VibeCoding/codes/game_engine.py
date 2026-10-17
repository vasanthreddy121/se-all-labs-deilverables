import pygame
import random
import math

from game.basket import Basket
from game.fruit import Fruit


class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y

        # Random outward direction
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(2.0, 5.0)

        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

        self.color = color

        # Particle lifetime
        self.lifetime = random.randint(20, 35)
        self.max_lifetime = self.lifetime

        # Particle size
        self.size = random.randint(2, 4)

    def update(self):
        self.x += self.vx
        self.y += self.vy

        # Gravity
        self.vy += 0.15

        # Slight horizontal resistance
        self.vx *= 0.98

        # Reduce lifetime
        self.lifetime -= 1

    def is_dead(self):
        return self.lifetime <= 0

    def render(self, surface):
        # Fade particle as its lifetime decreases
        alpha = int(
            255 *
            (self.lifetime / self.max_lifetime)
        )

        alpha = max(0, min(255, alpha))

        particle_surface = pygame.Surface(
            (self.size * 2, self.size * 2),
            pygame.SRCALPHA
        )

        pygame.draw.circle(
            particle_surface,
            (
                self.color[0],
                self.color[1],
                self.color[2],
                alpha
            ),
            (self.size, self.size),
            self.size
        )

        surface.blit(
            particle_surface,
            (
                int(self.x - self.size),
                int(self.y - self.size)
            )
        )


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        # Game objects
        self.basket = Basket(width, height)
        self.fruits = []
        self.particles = []

        # Game state
        self.score = 0
        self.lives = 3
        self.game_state = "PLAYING"

        # --------------------------------------------------
        # Dynamic difficulty settings
        # --------------------------------------------------

        self.spawn_delay = 750
        self.min_spawn_delay = 300

        self.base_speed = 0
        self.max_base_speed = 4.0

        # --------------------------------------------------
        # Guaranteed first hazard
        # --------------------------------------------------

        self.first_hazard_spawned = False

        self.last_spawn_time = pygame.time.get_ticks()

        # Fonts
        self.font_big = pygame.font.SysFont(None, 48)
        self.font_medium = pygame.font.SysFont(None, 28)

    def handle_event(self, event):
        if self.game_state == "GAME_OVER":

            if (
                event.type == pygame.KEYDOWN
                and event.key == pygame.K_r
            ):
                self.reset()

    def update(self):

        # Do not update the game after GAME OVER
        if self.game_state != "PLAYING":
            return

        # --------------------------------------------------
        # Basket movement
        # --------------------------------------------------

        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.basket.move_left()

        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.basket.move_right()

        # --------------------------------------------------
        # Dynamic difficulty
        # --------------------------------------------------

        # Reduce spawn delay as score increases.
        # Minimum spawn delay = 300 ms.
        self.spawn_delay = max(
            self.min_spawn_delay,
            750 - (self.score * 30)
        )

        # Increase falling speed as score increases.
        # Maximum additional speed = 4.0.
        self.base_speed = min(
            self.max_base_speed,
            self.score * 0.25
        )

        # --------------------------------------------------
        # Spawn fruits
        # --------------------------------------------------

        now = pygame.time.get_ticks()

        if now - self.last_spawn_time >= self.spawn_delay:

            # Guarantee the first spawned object is a hazard.
            force_hazard = not self.first_hazard_spawned

            new_fruit = Fruit(
                self.width,
                base_speed=self.base_speed,
                force_hazard=force_hazard
            )

            self.fruits.append(new_fruit)

            if force_hazard:
                self.first_hazard_spawned = True

            self.last_spawn_time = now

        # --------------------------------------------------
        # Update fruits
        # --------------------------------------------------

        basket_rect = self.basket.rect

        for fruit in self.fruits[:]:

            fruit.update()

            # --------------------------------------------------
            # Basket collision
            # --------------------------------------------------

            if basket_rect.colliderect(fruit.rect):

                # ----------------------------------------------
                # Hazard caught
                # ----------------------------------------------

                if fruit.is_hazard:

                    self.lives -= 1

                    if self.lives <= 0:
                        self.game_state = "GAME_OVER"

                # ----------------------------------------------
                # Normal fruit caught
                # ----------------------------------------------

                else:

                    self.score += 1

                    # Create splash particles
                    self.create_splash(
                        fruit.x,
                        fruit.y,
                        fruit.color
                    )

                self.fruits.remove(fruit)
                continue

            # --------------------------------------------------
            # Fruit reaches bottom
            # --------------------------------------------------

            if fruit.is_missed(self.height):

                # IMPORTANT:
                # Missing a normal fruit costs one life.
                # Missing a hazard has NO penalty.
                if not fruit.is_hazard:

                    self.lives -= 1

                    if self.lives <= 0:
                        self.game_state = "GAME_OVER"

                self.fruits.remove(fruit)

        # --------------------------------------------------
        # Update particles
        # --------------------------------------------------

        for particle in self.particles[:]:

            particle.update()

            if particle.is_dead():
                self.particles.remove(particle)

    def create_splash(self, x, y, color):
        """
        Create a splash of particles when a normal
        fruit is successfully caught.
        """

        for _ in range(15):

            particle = Particle(
                x,
                y,
                color
            )

            self.particles.append(particle)

    def reset(self):

        # Reset basket
        self.basket = Basket(
            self.width,
            self.height
        )

        # Remove fruits
        self.fruits.clear()

        # Remove particles
        self.particles.clear()

        # Reset score
        self.score = 0

        # Reset lives
        self.lives = 3

        # Reset difficulty
        self.spawn_delay = 750
        self.base_speed = 0

        # Allow another guaranteed first hazard
        self.first_hazard_spawned = False

        # Reset spawn timer
        self.last_spawn_time = pygame.time.get_ticks()

        # Resume game
        self.game_state = "PLAYING"

    def render(self, screen):

        # --------------------------------------------------
        # Background
        # --------------------------------------------------

        screen.fill(
            (28, 32, 40)
        )

        # --------------------------------------------------
        # Ground
        # --------------------------------------------------

        ground_y = self.height - 25

        pygame.draw.rect(
            screen,
            (45, 50, 60),
            (
                0,
                ground_y,
                self.width,
                25
            )
        )

        # --------------------------------------------------
        # Basket
        # --------------------------------------------------

        self.basket.render(screen)

        # --------------------------------------------------
        # Fruits
        # --------------------------------------------------

        for fruit in self.fruits:
            fruit.render(screen)

        # --------------------------------------------------
        # Particles
        # --------------------------------------------------

        for particle in self.particles:
            particle.render(screen)

        # --------------------------------------------------
        # Score
        # --------------------------------------------------

        score_surf = self.font_medium.render(
            f"Score: {self.score}",
            True,
            (255, 220, 80)
        )

        screen.blit(
            score_surf,
            (25, 20)
        )

        # --------------------------------------------------
        # Lives
        # --------------------------------------------------

        lives_surf = self.font_medium.render(
            f"Lives: {self.lives}",
            True,
            (240, 80, 80)
        )

        screen.blit(
            lives_surf,
            (
                self.width -
                lives_surf.get_width() -
                25,
                20
            )
        )

        # --------------------------------------------------
        # Game Over screen
        # --------------------------------------------------

        if self.game_state == "GAME_OVER":

            overlay = pygame.Surface(
                (
                    self.width,
                    self.height
                ),
                pygame.SRCALPHA
            )

            overlay.fill(
                (0, 0, 0, 190)
            )

            screen.blit(
                overlay,
                (0, 0)
            )

            # GAME OVER
            over_surf = self.font_big.render(
                "GAME OVER",
                True,
                (235, 70, 70)
            )

            screen.blit(
                over_surf,
                (
                    self.width // 2 -
                    over_surf.get_width() // 2,
                    self.height // 2 - 40
                )
            )

            # Final score
            final_surf = self.font_medium.render(
                f"Final Score: {self.score}",
                True,
                (255, 255, 255)
            )

            screen.blit(
                final_surf,
                (
                    self.width // 2 -
                    final_surf.get_width() // 2,
                    self.height // 2 + 10
                )
            )

            # Restart message
            restart_surf = self.font_medium.render(
                "Press [R] to Play Again",
                True,
                (200, 200, 200)
            )

            screen.blit(
                restart_surf,
                (
                    self.width // 2 -
                    restart_surf.get_width() // 2,
                    self.height // 2 + 50
                )
            )
