"""
renderer.py — OpenGL rendering engine for One Shot Assassin.
=========================================================
PURPOSE:
    Provides ALL drawing functions used by the game. Nothing
    is rendered directly in other files — they all call
    functions defined here.

WHY OpenGL (not Pygame's built-in drawing):
    1. ADDITIVE BLENDING — glBlendFunc(GL_SRC_ALPHA, GL_ONE)
       makes overlapping glow layers BRIGHTEN instead of covering
       each other. This creates real neon glow effects that are
       impossible with Pygame's software renderer.
    2. PER-VERTEX GRADIENTS — OpenGL interpolates colors between
       vertices automatically, giving shapes a 3D look for free.
    3. HARDWARE ACCELERATION — GPU renders hundreds of particles
       at 60fps without slowdown.

COORDINATE SYSTEM:
    Uses y-down matching Pygame: (0,0) = top-left
    Set up via glOrtho(0, width, height, 0, -1, 1)

TEXT RENDERING PIPELINE:
    Pygame font engine → Surface → RGBA bytes → OpenGL texture → quad
    This hybrid approach gives us TrueType fonts inside OpenGL.
=========================================================
"""

import math
import pygame

# ─── OpenGL imports ───────────────────────────────────────────────────
# We import specific functions/constants instead of "from OpenGL.GL import *"
# to make it clear exactly what OpenGL features we use.
from OpenGL.GL import (
    # --- Projection setup ---
    glViewport,         # Set the drawing viewport dimensions
    glMatrixMode,       # Switch between projection and modelview matrices
    glLoadIdentity,     # Reset the current matrix to identity
    glOrtho,            # Set up 2D orthographic projection (no perspective)

    # --- Rendering state ---
    glEnable,           # Turn on an OpenGL feature (e.g., blending)
    glDisable,          # Turn off an OpenGL feature
    glHint,             # Set quality hints (e.g., smooth lines)
    glBlendFunc,        # Configure how colors blend together
    glLineWidth,        # Set the width of drawn lines

    # --- Drawing ---
    glClearColor,       # Set the color used when clearing the screen
    glClear,            # Clear the screen with the clear color
    glColor4f,          # Set the current drawing color (RGBA floats)
    glBegin,            # Start defining a geometric primitive
    glEnd,              # End primitive definition
    glVertex2f,         # Define a 2D vertex position
    glTexCoord2f,       # Define texture coordinates for a vertex

    # --- Texture management (used by TextRenderer) ---
    glGenTextures,      # Create a new texture ID
    glBindTexture,      # Set the active texture
    glDeleteTextures,   # Free texture memory
    glTexParameteri,    # Set texture filtering/wrapping options
    glTexImage2D,       # Upload pixel data to a texture

    # --- Constants ---
    GL_PROJECTION,      # Projection matrix mode
    GL_MODELVIEW,       # Model/view matrix mode
    GL_BLEND,           # Blending feature flag
    GL_SRC_ALPHA,       # Blend using source alpha
    GL_ONE_MINUS_SRC_ALPHA,  # Standard transparency blending
    GL_ONE,             # Additive blending (for neon glow effects)
    GL_LINE_SMOOTH,     # Anti-aliased line rendering
    GL_LINE_SMOOTH_HINT,  # Quality hint for line smoothing
    GL_NICEST,          # Highest quality setting
    GL_DEPTH_TEST,      # 3D depth testing (we DISABLE this for 2D)
    GL_TEXTURE_2D,      # 2D texture feature
    GL_COLOR_BUFFER_BIT,  # Color buffer clear flag
    GL_TRIANGLE_FAN,    # Fan of triangles sharing a center vertex (circles)
    GL_TRIANGLES,       # Individual triangles
    GL_QUADS,           # Rectangles (4-vertex polygons)
    GL_LINES,           # Line segments
    GL_LINE_LOOP,       # Connected line loop (for borders)
    GL_TEXTURE_MIN_FILTER,  # Texture shrinking filter
    GL_TEXTURE_MAG_FILTER,  # Texture enlargement filter
    GL_LINEAR,          # Smooth (bilinear) texture filtering
    GL_TEXTURE_WRAP_S,  # Horizontal texture wrapping mode
    GL_TEXTURE_WRAP_T,  # Vertical texture wrapping mode
    GL_CLAMP_TO_EDGE,   # Prevent texture coordinate wrapping
    GL_RGBA,            # 4-channel color format (Red, Green, Blue, Alpha)
    GL_UNSIGNED_BYTE,   # 8-bit per channel data type
)

# Import game settings for default values
from settings import COL_BG, COL_GRID, COL_TEXT, SCREEN_WIDTH, SCREEN_HEIGHT


# =============================================================================
# INITIALIZATION — Called once at startup to configure OpenGL
# =============================================================================

def init_gl(width, height):
    """
    Set up OpenGL for 2D rendering with transparency.

    This is called ONCE when the game starts. It configures:
      1. Viewport — tells OpenGL the window dimensions
      2. Projection — sets up a 2D coordinate system (no 3D perspective)
      3. Blending — enables transparency for all drawn objects
      4. Line smoothing — anti-aliased lines for the aim indicator
      5. Disables depth test — not needed for 2D (everything is flat)
    """
    # Tell OpenGL the size of our drawing area
    glViewport(0, 0, width, height)

    # Set up ORTHOGRAPHIC (2D) projection
    # glOrtho(left, right, bottom, top, near, far)
    # We set bottom=height, top=0 to make y-axis go DOWNWARD (matching Pygame)
    glMatrixMode(GL_PROJECTION)     # Switch to projection matrix
    glLoadIdentity()                # Reset it
    glOrtho(0, width, height, 0, -1, 1)  # 2D: origin at top-left, y goes down
    glMatrixMode(GL_MODELVIEW)      # Switch back to model/view matrix
    glLoadIdentity()                # Reset it

    # Enable ALPHA BLENDING — required for transparency to work
    # Formula: final_color = src_color * src_alpha + dst_color * (1 - src_alpha)
    # This means semi-transparent objects blend with what's behind them
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    # Enable SMOOTH LINES — makes the aim prediction line anti-aliased
    glEnable(GL_LINE_SMOOTH)
    glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)  # Use highest quality smoothing

    # Disable DEPTH TEST — we don't need Z-depth sorting for 2D
    # (In 3D games, depth test prevents far objects from drawing over near ones)
    glDisable(GL_DEPTH_TEST)


def clear_screen(color=COL_BG):
    """
    Clear the entire screen to a solid color.

    Called at the start of every frame before drawing anything.
    Default color is the dark navy background (COL_BG).
    """
    glClearColor(*color)            # Set clear color (RGBA)
    glClear(GL_COLOR_BUFFER_BIT)    # Actually clear the framebuffer


# =============================================================================
# PRIMITIVE SHAPES — Building blocks for all game visuals
# =============================================================================

def draw_circle(cx, cy, radius, color, segments=32):
    """
    Draw a filled circle using GL_TRIANGLE_FAN.

    HOW IT WORKS:
        GL_TRIANGLE_FAN creates triangles that all share a center vertex.
        We place the center at (cx, cy), then add 32 vertices around the
        edge using trigonometry (cos/sin). OpenGL fills the triangles between
        consecutive edge vertices and the center.

    WHY 32 SEGMENTS:
        32 is enough to look perfectly round at game scale.
        More segments = smoother circle but more GPU work.

    USED FOR: Bullets, particles, bounce point markers, decorative dots
    """
    if radius <= 0:
        return
    glBegin(GL_TRIANGLE_FAN)        # Start fan from center
    glColor4f(*color)               # Set the fill color
    glVertex2f(cx, cy)              # Center vertex (shared by all triangles)
    for i in range(segments + 1):   # +1 to close the circle
        angle = 2.0 * math.pi * i / segments   # Angle for this vertex
        # Calculate edge point using unit circle formula:
        #   x = center_x + radius * cos(angle)
        #   y = center_y + radius * sin(angle)
        glVertex2f(cx + radius * math.cos(angle),
                    cy + radius * math.sin(angle))
    glEnd()


def draw_rect(x, y, w, h, color):
    """
    Draw a solid-color filled rectangle.

    Uses GL_QUADS (4 vertices) with the same color at all corners.
    Vertices are specified counter-clockwise starting from top-left.

    USED FOR: HUD background, fade overlay, wall bevel edges
    """
    glBegin(GL_QUADS)
    glColor4f(*color)       # Same color at all 4 corners = solid fill
    glVertex2f(x, y)        # Top-left
    glVertex2f(x + w, y)    # Top-right
    glVertex2f(x + w, y + h)  # Bottom-right
    glVertex2f(x, y + h)   # Bottom-left
    glEnd()


def draw_rect_gradient_v(x, y, w, h, color_top, color_bottom):
    """
    Draw a rectangle with a VERTICAL gradient (top color → bottom color).

    HOW IT WORKS:
        OpenGL automatically interpolates colors between vertices.
        By setting different colors for top and bottom vertices,
        OpenGL creates a smooth gradient for free.

    USED FOR: HUD background (dark top → transparent bottom)
    """
    glBegin(GL_QUADS)
    glColor4f(*color_top)           # Top-left: top color
    glVertex2f(x, y)
    glVertex2f(x + w, y)            # Top-right: top color
    glColor4f(*color_bottom)        # Bottom-left: bottom color
    glVertex2f(x + w, y + h)
    glVertex2f(x, y + h)           # Bottom-right: bottom color
    glEnd()


def draw_rect_3d(x, y, w, h, color):
    """
    Draw a 3D-looking BEVELED rectangle.

    HOW THE 3D EFFECT WORKS:
        1. GRADIENT FILL: Top half is lighter, bottom half is darker
           (simulates light coming from above).
        2. BEVEL EDGES: Thin bright strips on top/left edges (highlight)
           and thin dark strips on bottom/right edges (shadow).
        Together, these create the illusion of a raised 3D button.

    USED FOR: Walls and enemy bodies
    """
    # Calculate lighter (top) and darker (bottom) versions of the base color
    lighter = (min(1, color[0] * 1.3), min(1, color[1] * 1.3),
               min(1, color[2] * 1.3), color[3])
    darker  = (color[0] * 0.6, color[1] * 0.6,
               color[2] * 0.6, color[3])

    # Main body with vertical gradient (lighter top → darker bottom)
    glBegin(GL_QUADS)
    glColor4f(*lighter)             # Top edge: bright
    glVertex2f(x, y)
    glVertex2f(x + w, y)
    glColor4f(*darker)              # Bottom edge: dark
    glVertex2f(x + w, y + h)
    glVertex2f(x, y + h)
    glEnd()

    # --- BEVEL EDGES (thin strips to simulate 3D depth) ---
    bevel = 2   # Bevel strip thickness in pixels
    # Highlight color (very bright version of base color)
    highlight = (min(1, color[0] * 1.6), min(1, color[1] * 1.6),
                 min(1, color[2] * 1.6), 0.8)
    # Shadow color (very dark version of base color)
    shadow    = (color[0] * 0.3, color[1] * 0.3, color[2] * 0.3, 0.8)

    draw_rect(x, y, w, bevel, highlight)                    # Top edge (bright)
    draw_rect(x, y, bevel, h, (highlight[0], highlight[1],
                                highlight[2], 0.5))         # Left edge (bright)
    draw_rect(x, y + h - bevel, w, bevel, shadow)           # Bottom edge (dark)
    draw_rect(x + w - bevel, y, bevel, h,
              (shadow[0], shadow[1], shadow[2], 0.5))        # Right edge (dark)


def draw_triangle(cx, cy, size, angle_deg, color):
    """
    Draw a triangle pointing in a given direction.

    HOW THE ROTATION WORKS:
        We use trigonometry to calculate 3 vertices:
        - TIP: extends forward in the aim direction
        - BASE LEFT/RIGHT: two points behind the tip

        The direction is controlled by angle_deg:
          0° = pointing right, 90° = pointing down, 270° = pointing up

    PER-VERTEX GRADIENT:
        Tip vertex is bright, base vertices are darker.
        OpenGL smoothly interpolates between them → 3D look.

    USED FOR: Player character (cyan aiming triangle)
    """
    rad = math.radians(angle_deg)       # Convert degrees to radians for trig
    cos_a, sin_a = math.cos(rad), math.sin(rad)  # Direction vector components
    # Perpendicular direction (for base width)
    perp_cos = math.cos(rad + math.pi / 2)
    perp_sin = math.sin(rad + math.pi / 2)

    # TIP vertex: extends forward from center
    tip_x = cx + cos_a * size
    tip_y = cy + sin_a * size

    # BASE vertices: behind the center, spread perpendicular to aim
    back = size * 0.4   # How far back the base is from center
    base = size * 0.6   # How wide the base is (half-width)
    b1_x = cx - cos_a * back + perp_cos * base  # Base left
    b1_y = cy - sin_a * back + perp_sin * base
    b2_x = cx - cos_a * back - perp_cos * base  # Base right
    b2_y = cy - sin_a * back - perp_sin * base

    # Color gradient: bright tip → darker base
    bright = (min(1, color[0] * 1.4), min(1, color[1] * 1.4),
              min(1, color[2] * 1.4), color[3])
    dark   = (color[0] * 0.7, color[1] * 0.7,
              color[2] * 0.7, color[3])

    glBegin(GL_TRIANGLES)
    glColor4f(*bright)              # Tip: bright color
    glVertex2f(tip_x, tip_y)
    glColor4f(*dark)                # Base: darker color
    glVertex2f(b1_x, b1_y)
    glVertex2f(b2_x, b2_y)
    glEnd()


# =============================================================================
# EFFECTS — Glow, gradients, crosshair, and fade overlay
# =============================================================================

def draw_glow(cx, cy, radius, color, layers=3):
    """
    Draw a neon GLOW effect using additive blending.

    HOW IT WORKS:
        1. Switch to ADDITIVE blending: GL_SRC_ALPHA + GL_ONE
           This means overlapping semi-transparent layers BRIGHTEN
           instead of obscuring each other (key to neon effects).
        2. Draw multiple concentric circles, each larger and fainter.
        3. Switch back to normal blending.

    WHY ADDITIVE BLENDING:
        Normal blending: new_color = src * alpha + dst * (1-alpha)
        Additive blending: new_color = src * alpha + dst * 1
        The "+dst" means existing colors are preserved and new color
        is ADDED on top → creates a glowing, luminous look.

    USED FOR: Player aura, bullet halo, enemy pulse, title glow
    """
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)           # Switch to additive blending
    for i in range(layers, 0, -1):              # Draw from outermost to innermost
        # Each layer is fainter (lower alpha) and larger (bigger radius)
        alpha = color[3] * (i / layers) * 0.5   # Fade: outer = faintest
        r = radius * (0.5 + i * 0.4)            # Size: outer = largest
        draw_circle(cx, cy, r, (color[0], color[1], color[2], alpha))
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)  # Reset to normal blending


def draw_radial_gradient(cx, cy, radius, color, segments=48):
    """
    Draw a radial gradient: opaque at center, transparent at edges.

    HOW IT WORKS:
        Uses GL_TRIANGLE_FAN like draw_circle, but with DIFFERENT colors
        at center vs edge vertices. OpenGL interpolates automatically.
        - Center vertex: full color (with specified alpha)
        - Edge vertices: same color but alpha = 0.0 (transparent)

    Uses additive blending for a warm, luminous glow effect.

    USED FOR: Dramatic backdrop behind the title on the menu screen
    """
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)           # Additive for glow
    glBegin(GL_TRIANGLE_FAN)
    glColor4f(color[0], color[1], color[2], color[3])  # Center: opaque
    glVertex2f(cx, cy)
    glColor4f(color[0], color[1], color[2], 0.0)       # Edge: fully transparent
    for i in range(segments + 1):
        angle = 2.0 * math.pi * i / segments
        glVertex2f(cx + radius * math.cos(angle),
                    cy + radius * math.sin(angle))
    glEnd()
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)  # Reset blending


def draw_crosshair(cx, cy, size, color, rotation=0.0):
    """
    Draw a decorative animated crosshair/reticle.

    COMPONENTS:
        1. Four SPOKES radiating from center (fading outward)
        2. OUTER RING — large circle around the crosshair
        3. INNER RING — smaller circle, rotates opposite direction

    The rotation parameter increases each frame → continuous spin.

    USED FOR: Menu screen decoration behind the title (animated style element)
    """
    glLineWidth(1.5)   # Slightly thick lines

    # --- 4 SPOKES (one per quadrant, fading from center outward) ---
    for i in range(4):
        angle = math.pi / 2 * i            # 0°, 90°, 180°, 270°
        dx = math.cos(angle + rotation) * size  # Endpoint direction
        dy = math.sin(angle + rotation) * size
        inner = 0.35    # Start 35% out from center (gap in middle)

        glBegin(GL_LINES)
        # Inner end: brighter
        glColor4f(color[0], color[1], color[2], color[3] * 0.7)
        glVertex2f(cx + dx * inner, cy + dy * inner)
        # Outer end: nearly transparent
        glColor4f(color[0], color[1], color[2], color[3] * 0.15)
        glVertex2f(cx + dx, cy + dy)
        glEnd()

    # --- OUTER RING (80% of full size, rotates WITH the spokes) ---
    ring_segments = 48
    glBegin(GL_LINES)
    for i in range(ring_segments):
        a1 = 2.0 * math.pi * i / ring_segments + rotation
        a2 = 2.0 * math.pi * (i + 1) / ring_segments + rotation
        glColor4f(color[0], color[1], color[2], color[3] * 0.3)
        glVertex2f(cx + math.cos(a1) * size * 0.8,
                    cy + math.sin(a1) * size * 0.8)
        glVertex2f(cx + math.cos(a2) * size * 0.8,
                    cy + math.sin(a2) * size * 0.8)
    glEnd()

    # --- INNER RING (35% of full size, rotates OPPOSITE for visual interest) ---
    glBegin(GL_LINES)
    for i in range(ring_segments):
        a1 = 2.0 * math.pi * i / ring_segments - rotation * 0.5
        a2 = 2.0 * math.pi * (i + 1) / ring_segments - rotation * 0.5
        glColor4f(color[0], color[1], color[2], color[3] * 0.15)
        glVertex2f(cx + math.cos(a1) * size * 0.35,
                    cy + math.sin(a1) * size * 0.35)
        glVertex2f(cx + math.cos(a2) * size * 0.35,
                    cy + math.sin(a2) * size * 0.35)
    glEnd()

    glLineWidth(1.0)   # Reset line width


def draw_fade_overlay(alpha):
    """
    Draw a full-screen black rectangle with variable transparency.

    HOW FADE TRANSITIONS WORK:
        - alpha = 0.0 → fully transparent (screen visible)
        - alpha = 1.0 → fully black (screen hidden)

    The game.py gradually increases alpha (fade out), switches state,
    then gradually decreases alpha (fade in). This creates a smooth
    cinematic transition between screens.

    USED FOR: Transitions between menu, gameplay, win/lose screens
    """
    if alpha <= 0.0:
        return  # Nothing to draw if fully transparent
    # Draw a black rectangle covering the entire window
    draw_rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT,
              (0.0, 0.0, 0.0, min(1.0, alpha)))


# =============================================================================
# LINES — Solid, gradient, and dotted line drawing
# =============================================================================

def draw_line(x1, y1, x2, y2, color, width=1.0):
    """
    Draw a solid line between two points.

    USED FOR: Divider lines, section separators
    """
    glLineWidth(width)
    glBegin(GL_LINES)
    glColor4f(*color)
    glVertex2f(x1, y1)     # Start point
    glVertex2f(x2, y2)     # End point
    glEnd()
    glLineWidth(1.0)       # Reset to default width


def draw_line_gradient(x1, y1, x2, y2, color1, color2, width=1.0):
    """
    Draw a line with a color gradient from start to end.

    HOW IT WORKS:
        OpenGL interpolates between color1 (at start) and color2 (at end).
        We use this to make divider lines that FADE from transparent edges
        to opaque center, creating elegant separator effects.

    USED FOR: Menu dividers, HUD separator bars
    """
    glLineWidth(width)
    glBegin(GL_LINES)
    glColor4f(*color1)      # Start color
    glVertex2f(x1, y1)
    glColor4f(*color2)      # End color (OpenGL interpolates between)
    glVertex2f(x2, y2)
    glEnd()
    glLineWidth(1.0)


def draw_dotted_line(x1, y1, x2, y2, color, seg_len=8, gap_len=6):
    """
    Draw a dotted/dashed line between two points.

    HOW IT WORKS:
        Calculate the direction vector (ux, uy) of the line.
        Walk along the line in steps of (segment + gap), drawing
        only during the segment part and skipping the gap.

    USED FOR: Aim prediction line (showing where the bullet will go)
    """
    # Calculate direction and total length
    dx = x2 - x1
    dy = y2 - y1
    length = math.sqrt(dx * dx + dy * dy)
    if length < 0.01:       # Prevent division by zero
        return
    ux, uy = dx / length, dy / length   # Unit direction vector

    glLineWidth(1.5)
    glBegin(GL_LINES)
    glColor4f(*color)
    pos = 0.0               # Current distance along the line
    while pos < length:
        end = min(pos + seg_len, length)    # End of this dash
        # Draw a short segment (dash)
        glVertex2f(x1 + ux * pos, y1 + uy * pos)   # Dash start
        glVertex2f(x1 + ux * end, y1 + uy * end)   # Dash end
        pos += seg_len + gap_len    # Skip to the next dash
    glEnd()
    glLineWidth(1.0)


# =============================================================================
# BACKGROUND — Grid and play area border
# =============================================================================

def draw_grid(width, height, spacing=40, color=COL_GRID):
    """
    Draw a subtle background grid across the entire window.

    WHY A GRID:
        The grid adds visual depth and texture to the dark background.
        Without it, the background would be a flat, boring solid color.
        The grid is very faint (low alpha) so it doesn't distract.

    USED FOR: Background on all screens (menu, gameplay, etc.)
    """
    glLineWidth(1.0)
    glBegin(GL_LINES)
    glColor4f(*color)
    # Vertical lines (every 40px)
    for x in range(0, width + 1, spacing):
        glVertex2f(x, 0)
        glVertex2f(x, height)
    # Horizontal lines (every 40px)
    for y in range(0, height + 1, spacing):
        glVertex2f(0, y)
        glVertex2f(width, y)
    glEnd()


def draw_play_area_border(area, color=(0.15, 0.20, 0.30, 0.8)):
    """
    Draw the rectangular border of the play area.

    Uses GL_LINE_LOOP which automatically connects the last vertex
    back to the first, creating a closed rectangle.

    USED FOR: Visible boundary during gameplay showing where bullets bounce
    """
    x, y = area["left"], area["top"]
    w = area["right"] - area["left"]
    h = area["bottom"] - area["top"]
    glLineWidth(2.0)        # Slightly thick border
    glBegin(GL_LINE_LOOP)   # Closed loop of lines
    glColor4f(*color)
    glVertex2f(x, y)        # Top-left corner
    glVertex2f(x + w, y)    # Top-right corner
    glVertex2f(x + w, y + h)  # Bottom-right corner
    glVertex2f(x, y + h)   # Bottom-left corner
    glEnd()
    glLineWidth(1.0)


# =============================================================================
# TEXT RENDERER — Pygame fonts → OpenGL textures
# =============================================================================

class TextRenderer:
    """
    Renders text inside the OpenGL context.

    PROBLEM:
        OpenGL has no built-in text drawing. It only draws shapes.

    SOLUTION (hybrid pipeline):
        1. Use Pygame's font engine to render text onto a Surface (bitmap)
        2. Convert the Surface to raw RGBA pixel bytes
        3. Upload those bytes to an OpenGL texture (GPU memory)
        4. Draw a textured rectangle (quad) at the desired screen position

    CACHING:
        Creating a texture is expensive (CPU → GPU upload). We cache
        textures by (text, size, color) so the same text is only
        uploaded once. Cache is pruned when it exceeds 200 entries.

    USED BY: All UI text — title, score, bullets, menu options, footer
    """

    def __init__(self):
        self._cache = {}   # (text, size, color_key) → (tex_id, width, height)
        self._fonts = {}   # font_size → pygame.font.Font object

    def get_font(self, size):
        """
        Get or create a Pygame font at the given pixel size.

        Fonts are cached so we don't recreate them every frame.
        We use "Arial" system font — available on all Windows machines.
        """
        if size not in self._fonts:
            self._fonts[size] = pygame.font.SysFont("Arial", size)
        return self._fonts[size]

    def _make_texture(self, text, size, color):
        """
        Create (or retrieve from cache) an OpenGL texture for the given text.

        STEPS:
            1. Check cache — return immediately if already created
            2. Render text to Pygame Surface using font engine
            3. Convert to RGBA format (adds proper alpha channel)
            4. Upload raw bytes to OpenGL texture
            5. Store in cache for future frames
        """
        # Create a cache key from the text, size, and color (rounded to avoid float issues)
        cache_key = (text, size, (round(color[0], 2), round(color[1], 2),
                                  round(color[2], 2)))
        if cache_key in self._cache:
            return self._cache[cache_key]   # Already in cache — reuse!

        # Prune cache if too large (prevent memory leaks)
        if len(self._cache) > 200:
            old_keys = list(self._cache.keys())[:100]
            for k in old_keys:
                glDeleteTextures([self._cache[k][0]])   # Free GPU memory
                del self._cache[k]

        # Step 1: Render text to a Pygame Surface
        font = self.get_font(size)
        # Convert OpenGL floats (0.0–1.0) to Pygame ints (0–255)
        py_color = (int(color[0] * 255), int(color[1] * 255),
                     int(color[2] * 255))
        surface = font.render(text, True, py_color)  # True = anti-aliased

        # Step 2: Convert to RGBA surface (ensures proper transparency)
        w, h = surface.get_size()
        rgba = pygame.Surface((w, h), pygame.SRCALPHA)  # SRCALPHA = per-pixel alpha
        rgba.blit(surface, (0, 0))  # Copy text pixels onto RGBA surface

        # Step 3: Extract raw RGBA bytes from the surface
        tex_data = pygame.image.tostring(rgba, "RGBA", False)  # False = no vertical flip

        # Step 4: Create an OpenGL texture and upload the bytes
        tex_id = glGenTextures(1)               # Generate a new texture ID
        glBindTexture(GL_TEXTURE_2D, tex_id)    # Make it the active texture
        # Set filtering to LINEAR (smooth scaling, not pixelated)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        # Prevent texture wrapping (text should not repeat/tile)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        # Upload pixel data to the GPU
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE, tex_data)

        # Step 5: Store in cache
        self._cache[cache_key] = (tex_id, w, h)
        return (tex_id, w, h)

    def draw(self, text, x, y, size=24, color=COL_TEXT, centered=False,
             alpha=1.0):
        """
        Draw text at screen position (x, y).

        HOW IT WORKS:
            1. Get (or create) the OpenGL texture for this text
            2. Enable texturing
            3. Draw a rectangle with the texture mapped onto it
            4. Disable texturing

        PARAMETERS:
            centered: If True, (x, y) is the CENTER of the text.
                      If False, (x, y) is the TOP-LEFT corner.
            alpha:    Overall opacity (1.0 = solid, 0.0 = invisible).
                      Used for blinking/fading text animations.
        """
        if not text:
            return

        # Get the texture (from cache or freshly created)
        tex_id, w, h = self._make_texture(text, size, color)

        # If centered, offset x and y so the text is centered on the point
        if centered:
            x -= w // 2
            y -= h // 2

        # Enable 2D texturing and bind our text texture
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glColor4f(1.0, 1.0, 1.0, alpha)    # White tint (preserves texture colors)

        # Draw a textured quad (rectangle)
        # glTexCoord2f maps texture pixels to the quad corners
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(x,     y)       # Top-left       # noqa: E702
        glTexCoord2f(1, 0); glVertex2f(x + w, y)       # Top-right      # noqa: E702
        glTexCoord2f(1, 1); glVertex2f(x + w, y + h)   # Bottom-right   # noqa: E702
        glTexCoord2f(0, 1); glVertex2f(x,     y + h)   # Bottom-left    # noqa: E702
        glEnd()

        glDisable(GL_TEXTURE_2D)    # Disable texturing (so shapes draw normally)

    def get_text_size(self, text, size=24):
        """
        Return (width, height) of rendered text in pixels.

        Used to right-align text (e.g., bullet count in HUD).
        """
        return self.get_font(size).size(text)

    def cleanup(self):
        """
        Delete all cached OpenGL textures from GPU memory.

        Called when the game exits to prevent memory leaks.
        """
        for (tex_id, _, _) in self._cache.values():
            glDeleteTextures([tex_id])
        self._cache.clear()
