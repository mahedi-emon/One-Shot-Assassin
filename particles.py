"""
particles.py — Particle system for One Shot Assassin.
=========================================================
PURPOSE:
    Provides visual effects that make the game feel polished:
      - EXPLOSIONS: Burst of colored particles when enemies die
      - SPARKS: Small bright particles when bullets bounce off walls
      - AMBIENT: Slow floating particles for menu/background atmosphere

DESIGN:
    Each particle is a tiny object with position, velocity, color,
    and a countdown timer (lifetime). Every frame:
      1. Move the particle by its velocity
      2. Apply drag (slow it down gradually)
      3. Decrement the lifetime
      4. Fade out based on remaining lifetime
      5. Remove it when lifetime reaches zero

    All particles use ADDITIVE BLENDING (via draw_glow) so they
    brighten the area they're in — perfect for neon/fire effects.

PERFORMANCE:
    __slots__ prevents Python from creating a __dict__ per particle,
    saving memory when hundreds of particles exist simultaneously.
=========================================================
"""

import math
import random
from renderer import draw_circle, draw_glow  # OpenGL drawing functions
from settings import COL_SPARK  # Yellow-gold color for wall bounce sparks


class Particle:
    """
    A single particle with position, velocity, color, and lifetime.

    LIFECYCLE:
        1. Created by ParticleSystem (spawn_explosion/sparks/ambient)
        2. Updated every frame: move, drag, decrement lifetime
        3. Removed when lifetime reaches 0 (alive = False)

    __slots__ lists ALL attributes — prevents Python from creating
    the usual __dict__. This saves ~100 bytes per particle and makes
    attribute access slightly faster (important when updating hundreds).
    """

    __slots__ = ("x", "y", "vx", "vy", "color", "radius",
                 "lifetime", "max_lifetime", "alive")

    def __init__(self, x, y, vx, vy, color, radius, lifetime):
        self.x = x              # Current x position
        self.y = y              # Current y position
        self.vx = vx            # Horizontal velocity (px/frame)
        self.vy = vy            # Vertical velocity (px/frame)
        self.color = color      # RGBA color tuple
        self.radius = radius    # Starting radius (shrinks over time)
        self.lifetime = lifetime        # Frames remaining
        self.max_lifetime = lifetime    # Initial lifetime (for ratio calculations)
        self.alive = True       # Set to False when lifetime expires

    def update(self):
        """
        Move the particle, apply drag, and decrement lifetime.

        DRAG (0.97 multiplier):
            Each frame, velocity is multiplied by 0.97.
            This makes particles decelerate smoothly:
              Frame 0: speed = 5.0
              Frame 10: speed = 5.0 × 0.97^10 ≈ 3.7
              Frame 30: speed = 5.0 × 0.97^30 ≈ 2.0
            Creates a natural "explosion then settle" feel.
        """
        self.x += self.vx       # Move horizontally
        self.y += self.vy       # Move vertically
        self.vx *= 0.97         # Apply drag (slow down by 3% per frame)
        self.vy *= 0.97
        self.lifetime -= 1      # Count down
        if self.lifetime <= 0:
            self.alive = False  # Mark for removal

    @property
    def alpha(self):
        """
        Normalized remaining lifetime: 1.0 (just spawned) → 0.0 (about to die).

        Used to fade out the particle visually as it dies.
        """
        return max(0.0, self.lifetime / self.max_lifetime)

    @property
    def current_radius(self):
        """
        Current radius = starting radius × alpha.

        Particles SHRINK as they fade, creating a natural
        dissolving effect. A particle at half-life is half-size.
        """
        return self.radius * self.alpha


class ParticleSystem:
    """
    Manages a pool of particles — spawning, updating, and rendering.

    The game creates separate ParticleSystem instances for:
      - Gameplay (explosions + sparks during levels)
      - Menu effects (ambient floating particles)
    """

    def __init__(self):
        self.particles = []  # List of active Particle objects

    # -----------------------------------------------------------------
    # SPAWN METHODS — Create groups of particles at a location
    # -----------------------------------------------------------------

    def spawn_explosion(self, x, y, color, count=20):
        """
        Create an explosion burst of 20 particles at (x, y).

        USED WHEN: An enemy is destroyed by a bullet.

        HOW:
            Each particle gets a random direction (0–360°) and
            random speed (1.5–5.5). This creates a burst pattern
            radiating outward from the impact point.

            Color is slightly randomized per particle (±0.1) for
            visual richness — no two particles look exactly the same.
        """
        for _ in range(count):
            # Random direction (full 360°)
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1.5, 5.5)   # Random speed
            vx = math.cos(angle) * speed        # X velocity component
            vy = math.sin(angle) * speed        # Y velocity component
            r = random.uniform(2.0, 5.0)        # Random radius (2–5px)
            life = random.randint(20, 50)       # Random lifetime (20–50 frames)
            # Slight color variation (±0.1 on each RGB channel)
            c = (
                max(0, min(1, color[0] + random.uniform(-0.1, 0.1))),
                max(0, min(1, color[1] + random.uniform(-0.1, 0.1))),
                max(0, min(1, color[2] + random.uniform(-0.1, 0.1))),
                color[3],  # Alpha stays the same
            )
            self.particles.append(Particle(x, y, vx, vy, c, r, life))

    def spawn_sparks(self, x, y, count=8):
        """
        Create 8 bright sparks at (x, y).

        USED WHEN: A bullet bounces off a wall or screen edge.

        Sparks are:
            - Faster (2–7 px/frame) but shorter lived (8–22 frames)
            - Colored bright yellow-gold (COL_SPARK)
            - Create a quick "impact flash" at the bounce point
        """
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2.0, 7.0)   # Fast burst
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            life = random.randint(8, 22)        # Short lifespan
            r = random.uniform(1.0, 3.0)        # Small radius
            self.particles.append(
                Particle(x, y, vx, vy, COL_SPARK, r, life)
            )

    def spawn_ambient(self, width, height, count=1):
        """
        Spawn 1 slow-drifting ambient particle at a random position.

        USED FOR: Background atmosphere on menu, win, and game-over screens.

        Ambient particles are:
            - Very slow (±0.3 px/frame) — gentle floating
            - Low alpha (0.30) — barely visible, subtle
            - Long-lived (60–130 frames) — drift slowly across screen
            - Blue-tinted — matches the dark cyberpunk aesthetic
        """
        for _ in range(count):
            x = random.uniform(0, width)        # Random x position
            y = random.uniform(0, height)       # Random y position
            vx = random.uniform(-0.3, 0.3)      # Very slow drift
            vy = random.uniform(-0.3, 0.3)
            color = (0.20, 0.30, 0.55, 0.30)   # Faint blue
            r = random.uniform(1.0, 3.5)        # Small–medium radius
            life = random.randint(60, 130)      # Long lifespan
            self.particles.append(Particle(x, y, vx, vy, color, r, life))

    # -----------------------------------------------------------------
    # UPDATE & DRAW — Called every frame
    # -----------------------------------------------------------------

    def update(self):
        """
        Update all particles and remove dead ones.

        List comprehension creates a new list containing only
        particles where alive=True. Dead particles are garbage
        collected by Python automatically.
        """
        for p in self.particles:
            p.update()  # Move, drag, decrement lifetime
        # Filter out dead particles (alive=False)
        self.particles = [p for p in self.particles if p.alive]

    def draw(self):
        """
        Render all particles with glow effects.

        Larger particles (radius > 1.5px) get a glow effect
        using additive blending (draw_glow). Smaller particles
        are just drawn as simple circles (cheaper to render).
        """
        for p in self.particles:
            a = p.alpha * 0.8   # Slightly reduce alpha for subtlety
            color = (p.color[0], p.color[1], p.color[2], a)
            cr = p.current_radius
            if cr > 1.5:
                # Large particles: render with glow (2 concentric layers)
                draw_glow(p.x, p.y, cr, color, layers=2)
            else:
                # Small particles: simple circle (no glow, cheaper)
                draw_circle(p.x, p.y, max(0.5, cr), color)
