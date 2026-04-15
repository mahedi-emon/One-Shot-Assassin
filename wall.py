"""
wall.py — Wall class for One Shot Assassin.
=========================================================
PURPOSE:
    Walls are rectangular obstacles in the play area.
    Bullets BOUNCE off walls (ricochet mechanic).
    Enemies hide BEHIND walls (forcing the player to use angles).

HOW COLLISION WORKS:
    Uses pygame.Rect for MATH ONLY (not for Pygame rendering).
    pygame.Rect provides colliderect() which checks if two
    rectangles overlap — perfect for axis-aligned collision.
    We don't use Pygame's draw functions at all — walls are
    rendered using OpenGL's draw_rect_3d() for the 3D bevel look.

WHY pygame.Rect INSTEAD OF MANUAL MATH:
    pygame.Rect handles edge cases (zero-width, negative coords)
    and is implemented in C (fast). We only use it as a data
    structure — the visual rendering is done by OpenGL.
=========================================================
"""

import pygame  # Used ONLY for pygame.Rect (collision math)
from renderer import draw_rect_3d  # OpenGL 3D-beveled rectangle
from settings import COL_WALL      # Steel blue-gray wall color


class Wall:
    """
    A rectangular wall obstacle.

    The wall has:
      - A pygame.Rect for collision detection (used by bullet.py)
      - An OpenGL draw method for visual rendering (3D bevel effect)

    Walls are STATIC — they don't move or change during gameplay.
    """

    def __init__(self, x, y, width, height):
        """
        Create a wall at (x, y) with given width and height.

        Args:
            x:      Left edge x-coordinate (pixels from left of window).
            y:      Top edge y-coordinate (pixels from top of window).
            width:  Width in pixels.
            height: Height in pixels.

        The pygame.Rect stores these values and provides
        .left, .right, .top, .bottom properties for collision checks.
        """
        # pygame.Rect(x, y, width, height) — stores the wall's bounding box
        # Used by bullet.py to detect and resolve bounce collisions
        self.rect = pygame.Rect(x, y, width, height)

    def draw(self):
        """
        Render the wall using OpenGL's 3D-beveled rectangle.

        draw_rect_3d() draws:
          1. A gradient fill (lighter on top, darker on bottom)
          2. Bright highlight strips on top/left edges
          3. Dark shadow strips on bottom/right edges
        This makes the wall look like a raised 3D block.
        """
        draw_rect_3d(
            self.rect.x, self.rect.y,           # Position (top-left corner)
            self.rect.width, self.rect.height,   # Size
            COL_WALL,                            # Steel blue-gray color
        )
