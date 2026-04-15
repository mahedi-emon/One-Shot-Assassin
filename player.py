"""
player.py — Player class for One Shot Assassin.
=========================================================
PURPOSE:
    The player is an aiming turret at the bottom of the screen.
    They can ROTATE their aim (left/right arrow keys) and
    FIRE bullets (space bar). The player cannot move position.

KEY FEATURES:
    1. AIM ROTATION: Angle clamped between 185°–355° (upper half
       only — can't aim downward behind yourself).
    2. BULLET FIRING: Decrements bullet count and creates a Bullet
       object traveling in the aim direction.
    3. AIM PREDICTION: Real-time RAYCASTING shows where the bullet
       will go, including bounce points, as a dotted line.

VISUAL:
    - Cyan triangle pointing in the aim direction (gradient tip)
    - Glow aura around the player
    - Dotted aim prediction line with bounce markers

RAYCASTING ALGORITHM:
    Parametric ray-line intersection:
    For each wall face (and screen edge), solve:
        t = (face_position - ray_origin) / ray_direction
    The smallest positive t gives the nearest hit point.
    At the hit point, reverse dx or dy (bounce) and repeat.
=========================================================
"""

import math
from renderer import draw_triangle, draw_glow, draw_dotted_line, draw_circle
from bullet import Bullet  # Bullet class to create when firing
from settings import (
    AIM_SPEED, AIM_MIN, AIM_MAX, AIM_START,  # Aim rotation parameters
    PLAYER_SIZE, COL_PLAYER, COL_PLAYER_GLOW, COL_AIM_LINE,  # Visual constants
)


class Player:
    """
    The player character — an aiming turret at the bottom of the screen.

    The player CANNOT move position; they only rotate their aim
    and fire bullets. A dotted line with bounce prediction helps
    the player plan ricochet shots.
    """

    def __init__(self, x, y, bullets):
        """
        Create a player at (x, y) with a given number of bullets.

        Args:
            x, y:    Center position (typically bottom-center of play area).
            bullets: Number of bullets available for this level.
        """
        self.x = float(x)              # Fixed x position (doesn't change)
        self.y = float(y)              # Fixed y position
        self.aim_angle = AIM_START      # Starting aim = 270° (straight up)
        self.bullets_remaining = bullets # Bullets left to fire
        self.size = PLAYER_SIZE         # Triangle size (22px)

    def rotate_aim(self, direction):
        """
        Rotate the aim direction by AIM_SPEED degrees.

        Called every frame while the left/right arrow key is HELD.
        The angle is clamped to [AIM_MIN, AIM_MAX] = [185°, 355°]
        so the player can only aim upward (not behind themselves).

        ANGLE CONVENTION:
            0° = right, 90° = down, 180° = left, 270° = up

        Args:
            direction: -1 for left (counter-clockwise),
                       +1 for right (clockwise).
        """
        self.aim_angle += direction * AIM_SPEED  # ±2° per frame
        # Clamp to valid range (can't aim below horizontal)
        self.aim_angle = max(AIM_MIN, min(AIM_MAX, self.aim_angle))

    def shoot(self):
        """
        Fire a bullet in the current aim direction.

        Creates a new Bullet object at the player's position,
        traveling in the direction of self.aim_angle.

        Returns:
            Bullet object if a bullet was available, else None.
        """
        if self.bullets_remaining > 0:
            self.bullets_remaining -= 1     # Consume one bullet
            # Create a bullet at player's position, aimed at current angle
            return Bullet(self.x, self.y, self.aim_angle)
        return None  # No bullets remaining

    # -----------------------------------------------------------------
    # RENDERING
    # -----------------------------------------------------------------

    def draw(self, walls, play_area):
        """
        Render the player: glow aura → triangle body → aim prediction.

        RENDERING ORDER (back to front):
            1. Glow aura (faint cyan halo behind the player)
            2. Player triangle (cyan, pointing in aim direction)
            3. Aim prediction line (dotted, with bounce markers)

        Args:
            walls:     List of Wall objects (needed for aim raycasting).
            play_area: Play area bounds dict (for edge bouncing prediction).
        """
        # 1. Glow aura (provides subtle depth and highlights the player)
        draw_glow(self.x, self.y, self.size * 1.8,
                  COL_PLAYER_GLOW, layers=3)

        # 2. Player body (gradient cyan triangle)
        draw_triangle(self.x, self.y, self.size,
                      self.aim_angle, COL_PLAYER)

        # 3. Aim prediction line showing where bullet will go
        self._draw_aim_prediction(walls, play_area)

    def _draw_aim_prediction(self, walls, play_area, max_bounces=2,
                              max_length=500):
        """
        Draw the aim prediction line showing the predicted bullet path.

        Uses raycasting to find bounce points, then draws dotted lines
        between them. Each segment after a bounce is fainter (lower alpha)
        to indicate decreasing prediction confidence.

        Small white circles mark bounce points.

        Args:
            max_bounces: How many bounces to predict (default 2).
            max_length:  Maximum total ray length in pixels (default 500).
        """
        # Get the list of points along the predicted path
        points = self._raycast(walls, play_area, max_bounces, max_length)

        # Draw dotted lines between consecutive points
        for i in range(len(points) - 1):
            # Each bounce segment is 30% fainter than the previous
            alpha = COL_AIM_LINE[3] * (1.0 - i * 0.30)
            if alpha <= 0.05:
                break   # Too faint to see — stop drawing
            color = (COL_AIM_LINE[0], COL_AIM_LINE[1],
                     COL_AIM_LINE[2], max(0.05, alpha))

            # Draw dotted line from point[i] to point[i+1]
            draw_dotted_line(
                points[i][0], points[i][1],
                points[i + 1][0], points[i + 1][1],
                color, 8, 6,    # 8px dashes, 6px gaps
            )

            # Draw a small circle at each bounce point (not at the origin)
            if i > 0:
                draw_circle(points[i][0], points[i][1], 3,
                            (1.0, 1.0, 1.0, alpha * 0.5))

    def _raycast(self, walls, play_area, max_bounces=2, max_length=500):
        """
        Trace a ray from the player in the aim direction, computing
        bounce points off walls and screen edges.

        ALGORITHM:
            1. Start at player position with aim direction (dx, dy)
            2. For each surface (4 screen edges + all wall faces):
               - Solve: t = (surface_position - ray_origin) / ray_direction
               - This gives the distance along the ray to the intersection
            3. Take the SMALLEST positive t (nearest hit)
            4. Move to the hit point, reverse dx or dy (bounce), repeat

        WHY PARAMETRIC INTERSECTION:
            The formula t = (surface - origin) / direction works because
            any point on the ray can be expressed as:
                point = origin + t * direction
            Solving for t when point.x = surface.x (vertical wall) or
            point.y = surface.y (horizontal wall) gives the intersection.

        Returns:
            List of (x, y) points: [start, bounce1, bounce2, ..., end]
        """
        points = [(self.x, self.y)]  # Start at player position

        # Direction vector (cos/sin of aim angle)
        dx = math.cos(math.radians(self.aim_angle))
        dy = math.sin(math.radians(self.aim_angle))
        x, y = self.x, self.y      # Current ray position
        remaining = float(max_length)  # Remaining ray length budget

        for _ in range(max_bounces + 1):
            min_t = remaining       # Distance to nearest hit (start = max)
            hit_type = None         # 'v' = vertical surface, 'h' = horizontal

            # ─── Check play area boundaries ───────────────────────────
            # RIGHT boundary (vertical surface)
            if dx > 0:  # Ray moving rightward
                t = (play_area["right"] - x) / dx   # Distance to right edge
                if 0.01 < t < min_t:                 # 0.01 avoids self-intersection
                    hy = y + t * dy                  # y-coordinate at intersection
                    if play_area["top"] <= hy <= play_area["bottom"]:  # Within bounds?
                        min_t = t
                        hit_type = "v"   # Vertical surface → reverse dx
            # LEFT boundary
            elif dx < 0:  # Ray moving leftward
                t = (play_area["left"] - x) / dx
                if 0.01 < t < min_t:
                    hy = y + t * dy
                    if play_area["top"] <= hy <= play_area["bottom"]:
                        min_t = t
                        hit_type = "v"

            # TOP boundary (horizontal surface)
            if dy < 0:  # Ray moving upward
                t = (play_area["top"] - y) / dy
                if 0.01 < t < min_t:
                    hx = x + t * dx                  # x-coordinate at intersection
                    if play_area["left"] <= hx <= play_area["right"]:
                        min_t = t
                        hit_type = "h"   # Horizontal surface → reverse dy
            # BOTTOM boundary
            elif dy > 0:  # Ray moving downward
                t = (play_area["bottom"] - y) / dy
                if 0.01 < t < min_t:
                    hx = x + t * dx
                    if play_area["left"] <= hx <= play_area["right"]:
                        min_t = t
                        hit_type = "h"

            # ─── Check internal walls ─────────────────────────────────
            for wall in walls:
                wr = wall.rect
                # Left face of wall (hit when ray travels rightward)
                if dx > 0:
                    t = (wr.left - x) / dx
                    if 0.01 < t < min_t:
                        hy = y + t * dy
                        if wr.top <= hy <= wr.bottom:
                            min_t = t
                            hit_type = "v"
                # Right face of wall (hit when ray travels leftward)
                elif dx < 0:
                    t = (wr.right - x) / dx
                    if 0.01 < t < min_t:
                        hy = y + t * dy
                        if wr.top <= hy <= wr.bottom:
                            min_t = t
                            hit_type = "v"

                # Top face of wall (hit when ray travels downward)
                if dy > 0:
                    t = (wr.top - y) / dy
                    if 0.01 < t < min_t:
                        hx = x + t * dx
                        if wr.left <= hx <= wr.right:
                            min_t = t
                            hit_type = "h"
                # Bottom face of wall (hit when ray travels upward)
                elif dy < 0:
                    t = (wr.bottom - y) / dy
                    if 0.01 < t < min_t:
                        hx = x + t * dx
                        if wr.left <= hx <= wr.right:
                            min_t = t
                            hit_type = "h"

            # ─── Advance ray to the hit point ─────────────────────────
            x += dx * min_t
            y += dy * min_t
            points.append((x, y))       # Record this point
            remaining -= min_t          # Deduct used ray length

            # Stop if we ran out of ray length or didn't hit anything
            if remaining <= 0 or hit_type is None:
                break

            # ─── Bounce ───────────────────────────────────────────────
            # Vertical surface hit → reverse horizontal direction
            # Horizontal surface hit → reverse vertical direction
            if hit_type == "v":
                dx *= -1    # Bounce off vertical wall (reverse x)
            else:
                dy *= -1    # Bounce off horizontal wall (reverse y)

        return points
