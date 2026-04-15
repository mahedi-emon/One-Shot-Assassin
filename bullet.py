"""
bullet.py — Bullet class for One Shot Assassin.
=========================================================
PURPOSE:
    This is the CORE MECHANIC of the game — the ricochet bullet.
    When the player fires, a Bullet object is created and travels
    in a straight line, bouncing off walls and screen edges.

KEY BEHAVIORS:
    1. MOVEMENT: Travels at BULLET_SPEED pixels per frame in the
       direction of the player's aim when fired.
    2. RICOCHET: Bounces off screen boundaries and internal walls
       by reversing the appropriate velocity component (vx or vy).
    3. MULTI-KILL: Passes THROUGH enemies after hitting them,
       so a single well-aimed ricochet can destroy multiple targets.
    4. TRAIL: Stores recent positions for a fading orange trail effect.
    5. LIFETIME: Removed after MAX_BOUNCES bounces to prevent
       infinite flight.

COLLISION DETECTION:
    Uses AXIS-ALIGNED BOUNDING BOX (AABB) overlap via pygame.Rect.
    For wall collisions, the MINIMUM-OVERLAP method determines which
    side was hit and which velocity component to reverse.
=========================================================
"""

import math
import pygame
from collections import deque  # Efficient fixed-size queue for trail positions
from renderer import draw_circle, draw_glow  # OpenGL drawing functions
import audio
from settings import (
    BULLET_SPEED, BULLET_RADIUS, MAX_BOUNCES, TRAIL_LENGTH,
    COL_BULLET_CORE, COL_BULLET_GLOW, COL_BULLET_TRAIL, COL_ENEMY,
    COL_ENEMY_MOVING,
)


class Bullet:
    """
    A bullet projectile with ricochet physics.

    The bullet travels in a straight line, bouncing off walls.
    It can hit (and pass through) multiple enemies on a single flight.
    A trail of recent positions is stored for visual rendering.
    """

    def __init__(self, x, y, angle_deg):
        """
        Create a bullet at (x, y) traveling in the given direction.

        VELOCITY CALCULATION:
            We convert the aim angle to velocity components using
            basic trigonometry:
              vx = cos(angle) * speed  → horizontal speed
              vy = sin(angle) * speed  → vertical speed

            Example: angle=270° (straight up)
              cos(270°) = 0  → no horizontal movement
              sin(270°) = -1 → moves upward (negative y in our coords)
        """
        rad = math.radians(angle_deg)       # Convert degrees → radians for math
        self.x = float(x)                   # Current x position (center of bullet)
        self.y = float(y)                   # Current y position
        self.vx = math.cos(rad) * BULLET_SPEED  # Horizontal velocity (px/frame)
        self.vy = math.sin(rad) * BULLET_SPEED  # Vertical velocity (px/frame)
        self.radius = BULLET_RADIUS         # Visual and collision radius (5px)
        self.bounces = 0                    # Bounce counter (removed at MAX_BOUNCES)
        self.alive = True                   # Set to False when bullet should be removed
        # deque with maxlen automatically removes old entries when full
        self.trail = deque(maxlen=TRAIL_LENGTH)  # Last 25 positions for trail effect

    def update(self, walls, enemies, particles, play_area):
        """
        Main update — called every frame while the bullet is alive.

        STEPS:
            1. Save current position to trail (for visual effect)
            2. Move bullet by (vx, vy)
            3. Check screen edge bouncing
            4. Check internal wall bouncing
            5. Check enemy collisions (pass-through multi-kill)
            6. Remove if max bounces exceeded

        Returns:
            int: Number of enemies destroyed THIS FRAME.
                 (Used by game.py to update the score)
        """
        # ─── Step 1: Save position to trail BEFORE moving ─────────────
        # This creates a path of "where the bullet has been"
        self.trail.append((self.x, self.y))

        # ─── Step 2: Move the bullet ─────────────────────────────────
        self.x += self.vx   # Move horizontally
        self.y += self.vy   # Move vertically

        # ─── Step 3: Screen edge bouncing ─────────────────────────────
        # If the bullet hits a screen boundary, reverse the appropriate
        # velocity component and push the bullet back inside.
        # This is the simplest form of collision response.

        # Hit LEFT edge → reverse horizontal velocity, push right
        if self.x - self.radius < play_area["left"]:
            self.x = play_area["left"] + self.radius    # Push back inside
            self.vx *= -1                               # Reverse horizontal direction
            self.bounces += 1
            audio.play('bounce')
            particles.spawn_sparks(self.x, self.y)      # Visual spark effect

        # Hit RIGHT edge → reverse horizontal velocity, push left
        elif self.x + self.radius > play_area["right"]:
            self.x = play_area["right"] - self.radius
            self.vx *= -1
            self.bounces += 1
            audio.play('bounce')
            particles.spawn_sparks(self.x, self.y)

        # Hit TOP edge → reverse vertical velocity, push down
        if self.y - self.radius < play_area["top"]:
            self.y = play_area["top"] + self.radius
            self.vy *= -1
            self.bounces += 1
            audio.play('bounce')
            particles.spawn_sparks(self.x, self.y)

        # Hit BOTTOM edge → reverse vertical velocity, push up
        elif self.y + self.radius > play_area["bottom"]:
            self.y = play_area["bottom"] - self.radius
            self.vy *= -1
            self.bounces += 1
            audio.play('bounce')
            particles.spawn_sparks(self.x, self.y)

        # ─── Step 4: Internal wall bouncing ───────────────────────────
        # Create a bounding rectangle for the bullet (center ± radius)
        bullet_rect = pygame.Rect(
            self.x - self.radius, self.y - self.radius,
            self.radius * 2, self.radius * 2,   # Width = Height = diameter
        )
        # Check collision against each wall
        for wall in walls:
            if bullet_rect.colliderect(wall.rect):  # AABB overlap test
                self._resolve_wall_collision(wall, particles)
                break  # Only handle ONE wall collision per frame
                       # (prevents glitching when touching two walls)

        # ─── Step 5: Enemy collision (pass-through) ───────────────────
        # Unlike walls, the bullet does NOT bounce off enemies.
        # It passes through them, allowing multi-kills with one shot.
        hits = 0
        # Recalculate bounding rect (position may have changed from wall bounce)
        bullet_rect = pygame.Rect(
            self.x - self.radius, self.y - self.radius,
            self.radius * 2, self.radius * 2,
        )
        for enemy in enemies:
            if enemy.alive and bullet_rect.colliderect(enemy.rect):
                enemy.hit()     # Mark enemy as destroyed
                audio.play('explosion')
                # Spawn explosion particles in the enemy's color
                exp_color = (COL_ENEMY if enemy.enemy_type == "static"
                             else COL_ENEMY_MOVING)
                particles.spawn_explosion(enemy.x, enemy.y, exp_color)
                hits += 1       # Count this kill

        # ─── Step 6: Remove if max bounces exceeded ───────────────────
        if self.bounces >= MAX_BOUNCES:
            self.alive = False  # Will be removed by game.py next frame

        return hits

    def _resolve_wall_collision(self, wall, particles):
        """
        Determine which side of the wall was hit and bounce accordingly.

        MINIMUM-OVERLAP METHOD:
            When the bullet overlaps a wall, calculate how much
            it overlaps on each of the 4 sides. The SMALLEST overlap
            tells us which side was actually penetrated (the others
            are just incidental overlaps).

            For a vertical surface hit (left/right):
                → Reverse vx (horizontal velocity)
            For a horizontal surface hit (top/bottom):
                → Reverse vy (vertical velocity)

            We also PUSH the bullet out of the wall to prevent
            it from getting stuck inside.
        """
        wr = wall.rect  # Wall's rectangle

        # Calculate how much the bullet overlaps each wall edge
        overlap_left   = (self.x + self.radius) - wr.left    # Overlap with left face
        overlap_right  = wr.right - (self.x - self.radius)   # Overlap with right face
        overlap_top    = (self.y + self.radius) - wr.top     # Overlap with top face
        overlap_bottom = wr.bottom - (self.y - self.radius)  # Overlap with bottom face

        # The MINIMUM overlap indicates the actual collision side
        min_overlap = min(overlap_left, overlap_right,
                          overlap_top, overlap_bottom)

        # Reverse the correct velocity component and push bullet outside
        if min_overlap == overlap_left:
            self.vx = -abs(self.vx)             # Force leftward
            self.x = wr.left - self.radius      # Push left of wall
        elif min_overlap == overlap_right:
            self.vx = abs(self.vx)              # Force rightward
            self.x = wr.right + self.radius     # Push right of wall
        elif min_overlap == overlap_top:
            self.vy = -abs(self.vy)             # Force upward
            self.y = wr.top - self.radius       # Push above wall
        else:  # overlap_bottom is minimum
            self.vy = abs(self.vy)              # Force downward
            self.y = wr.bottom + self.radius    # Push below wall

        self.bounces += 1                       # Count this bounce
        audio.play('bounce')
        particles.spawn_sparks(self.x, self.y)  # Visual spark at impact point

    def draw(self):
        """
        Render the bullet with its trail and glow effects.

        RENDERING ORDER (back to front):
            1. TRAIL: Small fading circles at recent positions.
               Older positions are smaller and more transparent.
               Creates a motion blur / comet tail effect.

            2. GLOW: Additive-blended golden halo around the bullet.
               Makes it feel luminous and important.

            3. CORE: Bright white circle at the bullet's current position.
               This is the "physical" bullet.
        """
        # ─── 1. Trail (oldest → newest, fading) ─────────────────────
        n = len(self.trail)
        for i, (tx, ty) in enumerate(self.trail):
            t = (i + 1) / max(n, 1)    # 0→1 (oldest=0, newest=1)
            alpha = t * 0.50            # Newest = most visible (0.5 alpha)
            r = self.radius * 0.4 * t + 0.5  # Newest = largest radius
            draw_circle(tx, ty, r,
                        (COL_BULLET_TRAIL[0], COL_BULLET_TRAIL[1],
                         COL_BULLET_TRAIL[2], alpha))

        # ─── 2. Glow halo (golden, additive-blended) ────────────────
        draw_glow(self.x, self.y, self.radius * 3.0,
                  COL_BULLET_GLOW, layers=3)

        # ─── 3. Core (bright white/yellow circle) ────────────────────
        draw_circle(self.x, self.y, self.radius, COL_BULLET_CORE)
