"""
settings.py — Configuration and constants for One Shot Assassin.
=========================================================
PURPOSE:
    Centralizes ALL game settings in one place so they are
    easy to find, tune, and explain during a viva.

    Nothing in this file "runs" — it only defines values.
    Every other module imports the constants it needs from here.

WHY SEPARATE FILE:
    - ONE place to change window size, speeds, colors, etc.
    - Prevents "magic numbers" scattered across the codebase.
    - Makes the game easy to rebalance without touching logic.

COLOR FORMAT:
    All colors are RGBA floats (0.0–1.0) because OpenGL's
    glColor4f() expects this format.  Pygame uses 0–255 integers,
    so we convert when needed (e.g., in TextRenderer).
=========================================================
"""

# =============================================================================
# WINDOW — Size and frame rate of the game window
# =============================================================================
SCREEN_WIDTH = 900      # Window width in pixels
SCREEN_HEIGHT = 700     # Window height in pixels
FPS = 60                # Target frames per second (smooth animation = 60)
GAME_TITLE = "One Shot Assassin"  # Text shown in the window title bar

# =============================================================================
# PLAY AREA — The rectangular region where gameplay happens
# =============================================================================
# The play area is offset from the window edges:
#   - Top: below the HUD bar
#   - All sides: 10px margin for visual breathing room
HUD_HEIGHT = 50         # Height of the top HUD bar in pixels
PLAY_AREA = {
    "left": 10,                     # Left boundary (10px from window edge)
    "top": HUD_HEIGHT + 10,         # Top boundary (below HUD + 10px gap)
    "right": SCREEN_WIDTH - 10,     # Right boundary (10px from window edge)
    "bottom": SCREEN_HEIGHT - 10,   # Bottom boundary (10px from window edge)
}

# =============================================================================
# COLORS — Neon Cyberpunk Palette (RGBA floats for OpenGL)
# =============================================================================
# Each color is a tuple: (Red, Green, Blue, Alpha)
# Alpha: 1.0 = fully opaque, 0.0 = fully transparent

# --- Background ---
COL_BG        = (0.04, 0.04, 0.12, 1.0)    # Very dark navy (almost black)
COL_GRID      = (0.07, 0.07, 0.17, 0.5)    # Faint blue grid lines

# --- Player — Electric Cyan ---
COL_PLAYER      = (0.0, 0.90, 1.0, 1.0)    # Bright cyan (player triangle)
COL_PLAYER_GLOW = (0.0, 0.90, 1.0, 0.12)   # Same cyan, very transparent (glow aura)
COL_AIM_LINE    = (0.0, 0.90, 1.0, 0.45)   # Semi-transparent cyan (aim prediction line)

# --- Bullet — Gold / White core ---
COL_BULLET_CORE  = (1.0, 1.0, 0.95, 1.0)   # Almost white (bullet center)
COL_BULLET_GLOW  = (1.0, 0.84, 0.0, 0.30)  # Gold, semi-transparent (glow halo)
COL_BULLET_TRAIL = (1.0, 0.55, 0.0, 0.60)  # Orange (fading trail behind bullet)

# --- Enemy — Neon Magenta (static) / Orange (moving) ---
COL_ENEMY        = (1.0, 0.0, 0.40, 1.0)   # Bright magenta (stationary enemies)
COL_ENEMY_GLOW   = (1.0, 0.0, 0.40, 0.15)  # Same, low alpha (enemy glow)
COL_ENEMY_MOVING = (1.0, 0.45, 0.0, 1.0)   # Bright orange (moving enemies)

# --- Walls — Steel blue-gray with bevel ---
COL_WALL           = (0.29, 0.35, 0.43, 1.0)   # Base wall color
COL_WALL_HIGHLIGHT = (0.42, 0.48, 0.58, 1.0)   # Lighter edge (top/left bevel)
COL_WALL_SHADOW    = (0.16, 0.19, 0.25, 1.0)   # Darker edge (bottom/right bevel)

# --- UI Text ---
COL_TEXT     = (1.0, 1.0, 1.0, 1.0)        # Pure white (main text)
COL_TITLE    = (1.0, 0.84, 0.0, 1.0)       # Gold (title and score)
COL_SUBTITLE = (0.65, 0.65, 0.75, 1.0)     # Light gray-blue (secondary text)
COL_SUCCESS  = (0.0, 1.0, 0.53, 1.0)       # Emerald green (level complete)
COL_DANGER   = (1.0, 0.20, 0.27, 1.0)      # Hot red (game over, 0 bullets)
COL_HUD_BG   = (0.0, 0.0, 0.0, 0.70)       # Black, 70% opacity (HUD background)

# --- Footer / Subtle text ---
COL_FOOTER   = (0.35, 0.35, 0.45, 1.0)     # Dim gray (university footer)
COL_DIM      = (0.25, 0.25, 0.35, 1.0)     # Very dim (tech credits, hints)

# --- Crosshair / decoration ---
COL_CROSSHAIR = (0.0, 0.90, 1.0, 0.20)     # Faint cyan (animated crosshair on menu)

# --- Particles ---
COL_SPARK     = (1.0, 0.90, 0.30, 1.0)     # Bright yellow-gold (wall bounce sparks)
COL_EXPLOSION = (1.0, 0.40, 0.10, 1.0)     # Orange-red (enemy destruction burst)

# =============================================================================
# PHYSICS — Movement and aiming parameters
# =============================================================================
BULLET_SPEED = 7        # Pixels per frame the bullet moves
MAX_BOUNCES  = 6        # Maximum wall bounces before bullet disappears
AIM_SPEED    = 2.0      # Degrees per frame the aim rotates (arrow keys held)

# Aim angle limits (in degrees, 0° = right, 270° = straight up)
# These prevent the player from aiming downward (behind themselves)
AIM_MIN      = 185.0    # Leftmost aim angle (slightly past left)
AIM_MAX      = 355.0    # Rightmost aim angle (slightly past right)
AIM_START    = 270.0    # Default aim at game start (straight up)

# =============================================================================
# SIZES — Visual dimensions of game objects (in pixels)
# =============================================================================
PLAYER_SIZE   = 22      # Radius of the player triangle
BULLET_RADIUS = 5       # Radius of a bullet circle
ENEMY_SIZE    = 28      # Width/height of enemy squares
TRAIL_LENGTH  = 25      # Max number of trail positions stored per bullet

# =============================================================================
# SCORING — Points awarded/deducted during gameplay
# =============================================================================
SCORE_ENEMY          = 10   # Points per enemy destroyed (+10)
SCORE_BULLET_PENALTY = 2    # Points deducted per bullet fired (-2)
SCORE_LEVEL_BONUS    = 50   # Bonus for completing a level (+50)

# =============================================================================
# GAME STATES — String identifiers for the state machine
# =============================================================================
# The game is always in exactly one of these states.
# The state determines which update/render/input logic runs.
STATE_MENU           = "MENU"           # Main menu screen
STATE_INSTRUCTIONS   = "INSTRUCTIONS"   # How-to-play screen
STATE_PLAYING        = "PLAYING"        # Active gameplay
STATE_LEVEL_COMPLETE = "LEVEL_COMPLETE" # Between levels (score summary)
STATE_WIN            = "WIN"            # All levels cleared (victory)
STATE_GAME_OVER      = "GAME_OVER"     # Out of bullets (failure)

# =============================================================================
# TRANSITIONS — Fade animation speed for screen changes
# =============================================================================
FADE_SPEED = 0.04      # Alpha increment per frame for fade-in/out
                        # At 60 FPS: 1.0/0.04 = 25 frames ≈ 0.4 seconds per fade
