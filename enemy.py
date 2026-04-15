"""
enemy.py — Enemy class for One Shot Assassin.
=========================================================
PURPOSE:
    Enemies are the targets the player must destroy.
    The player wins a level when ALL enemies are hit.

TWO ENEMY TYPES:
    1. STATIC — stays in one place (easier to hit)
    2. MOVING — patrols back and forth along one axis (harder to hit)

VISUAL DESIGN:
    - 3D-beveled square (like walls, but colored magenta/orange)
    - Pulsing glow animation (sin wave) makes enemies feel "alive"
    - Different colors distinguish static vs moving types

COLLISION:
    Uses pygame.Rect (.rect property) for hitbox detection.
    When a bullet's rect overlaps an enemy's rect → enemy is hit.
=========================================================
"""

import math
import random
import pygame  # Used ONLY for pygame.Rect (hitbox collision math)
from renderer import draw_rect_3d, draw_glow  # OpenGL rendering functions
from settings import COL_ENEMY, COL_ENEMY_MOVING, ENEMY_SIZE


class Enemy:
    """
    An enemy target that the player must destroy.

    Static enemies remain stationary.
    Moving enemies oscillate back and forth along one axis.
    Both types have a pulsing glow effect for visual polish.
    """

    def __init__(self, x, y, enemy_type="static",
                 move_axis="x", move_range=(0, 0), move_speed=2):
        """
        Create an enemy at position (x, y).

        Args:
            x, y:        CENTER position of the enemy (not top-left).
            enemy_type:  "static" (stays still) or "moving" (patrols).
            move_axis:   "x" (horizontal) or "y" (vertical) patrol.
            move_range:  (min, max) pixel bounds for patrol movement.
            move_speed:  Pixels per frame movement speed.
        """
        self.x = float(x)          # Center x-position
        self.y = float(y)          # Center y-position
        self.enemy_type = enemy_type
        self.size = ENEMY_SIZE      # Width/height of the enemy square (28px)
        self.alive = True           # Set to False when hit by a bullet

        # ─── Pulsing animation ────────────────────────────────────────
        # Each enemy starts with a random phase so they don't all
        # pulse in sync (looks more natural/organic).
        self.pulse_phase = random.uniform(0, math.pi * 2)

        # ─── Movement (only used when enemy_type == "moving") ─────────
        self.move_axis = move_axis      # "x" = left-right, "y" = up-down
        self.move_range = move_range    # (min_pos, max_pos) travel bounds
        self.move_speed = move_speed    # Pixels per frame
        self.move_dir = 1               # +1 = forward, -1 = backward

    @property
    def rect(self):
        """
        Bounding rectangle for collision detection.

        Returns a pygame.Rect centered on the enemy's position.
        This is used by bullet.py: bullet_rect.colliderect(enemy.rect)

        WHY A PROPERTY:
            The rect is recalculated every time it's accessed because
            moving enemies change position each frame. A stored rect
            would become stale.
        """
        half = self.size / 2
        return pygame.Rect(self.x - half, self.y - half,
                           self.size, self.size)

    def update(self):
        """
        Update the enemy each frame.

        For ALL enemies:
            - Advance the pulse animation phase (+0.05 radians/frame)

        For MOVING enemies:
            - Move along the patrol axis by move_speed pixels
            - Reverse direction when reaching the patrol bounds
        """
        # Advance pulse animation (used for glow alpha variation)
        self.pulse_phase += 0.05

        # Only move if this is a "moving" type enemy and still alive
        if self.enemy_type == "moving" and self.alive:
            if self.move_axis == "x":
                # Move horizontally
                self.x += self.move_speed * self.move_dir
                # Reverse at patrol bounds
                if self.x <= self.move_range[0]:
                    self.x = self.move_range[0]
                    self.move_dir = 1       # Start moving right
                elif self.x >= self.move_range[1]:
                    self.x = self.move_range[1]
                    self.move_dir = -1      # Start moving left
            else:  # move_axis == "y"
                # Move vertically
                self.y += self.move_speed * self.move_dir
                if self.y <= self.move_range[0]:
                    self.y = self.move_range[0]
                    self.move_dir = 1       # Start moving down
                elif self.y >= self.move_range[1]:
                    self.y = self.move_range[1]
                    self.move_dir = -1      # Start moving up

    def hit(self):
        """
        Mark the enemy as destroyed (called when a bullet hits).

        Returns True to confirm the hit was registered.
        After this, alive=False and the enemy will no longer
        be drawn or considered for collision.
        """
        self.alive = False
        return True

    def draw(self):
        """
        Render the enemy with a pulsing glow and 3D-looking body.

        RENDERING ORDER (back to front):
            1. GLOW: Additive-blended glow whose alpha pulses
               using sin(pulse_phase) — creates a "breathing" effect.
            2. BODY: 3D-beveled rectangle (lighter top, darker bottom)
               colored magenta for static, orange for moving.

        Dead enemies (alive=False) are not drawn.
        """
        if not self.alive:
            return  # Don't draw destroyed enemies

        # Choose color based on enemy type
        # Static = magenta (COL_ENEMY), Moving = orange (COL_ENEMY_MOVING)
        color = COL_ENEMY if self.enemy_type == "static" else COL_ENEMY_MOVING

        # ─── Pulsing glow ────────────────────────────────────────────
        # sin() oscillates between -1 and 1; we map it to 0–1 for pulse
        pulse = 0.5 + 0.5 * math.sin(self.pulse_phase)  # 0.0 → 1.0
        glow_alpha = 0.08 + 0.14 * pulse   # Glow alpha ranges 0.08–0.22
        glow_color = (color[0], color[1], color[2], glow_alpha)
        # Draw glow slightly larger than the enemy (1.2x)
        draw_glow(self.x, self.y, self.size * 1.2, glow_color, layers=3)

        # ─── 3D beveled body ─────────────────────────────────────────
        half = self.size / 2
        # draw_rect_3d expects top-left corner, so offset from center
        draw_rect_3d(self.x - half, self.y - half,
                     self.size, self.size, color)
