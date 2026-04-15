"""
ui.py — Polished UI screen renderers for One Shot Assassin.
=========================================================
PURPOSE:
    Renders ALL non-gameplay screens and the in-game HUD.
    This is purely VISUAL — no game logic here.

SCREENS RENDERED:
    1. MAIN MENU — Title, subtitle, menu options, university footer
    2. INSTRUCTIONS — Controls, rules, and scoring breakdown
    3. HUD (Heads-Up Display) — Level name, score, bullet count
    4. LEVEL COMPLETE — Score summary, next-level prompt
    5. WIN — Victory message with final score
    6. GAME OVER — Failure message with retry prompt

DESIGN FEATURES:
    - Radial gradient backdrops for dramatic title lighting
    - Animated crosshair decoration (slowly rotating)
    - Pulsing title glow (sin wave animation)
    - Blinking "Press ENTER" text (sin wave alpha)
    - Gradient divider lines (fade from center to edges)
    - University footer fixed at the bottom of the menu
    - All animations driven by the 'frame' counter from game.py

WHY A SEPARATE UI CLASS:
    Separation of concerns — game.py handles logic,
    ui.py handles presentation. Easy to modify visuals
    without touching game mechanics.
=========================================================
"""

import math
from renderer import (
    draw_circle, draw_glow, draw_rect, draw_line, draw_line_gradient,
    draw_radial_gradient, draw_crosshair, draw_rect_gradient_v,
    draw_fade_overlay,
    TextRenderer,
)
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, HUD_HEIGHT, SCORE_LEVEL_BONUS,
    COL_TEXT, COL_TITLE, COL_SUBTITLE, COL_SUCCESS, COL_DANGER,
    COL_HUD_BG, COL_BULLET_CORE, COL_BULLET_GLOW, COL_BULLET_TRAIL,
    COL_FOOTER, COL_DIM, COL_CROSSHAIR, COL_PLAYER,
)


class UI:
    """
    Renders all UI screens and the in-game HUD.

    Requires a TextRenderer instance (passed at init) for all text drawing.
    All draw methods accept a 'frame' parameter for driving animations.
    """

    def __init__(self, text_renderer):
        """
        Initialize the UI renderer.

        Args:
            text_renderer: A renderer.TextRenderer instance.
                           Used for converting text strings into
                           OpenGL textures and drawing them on screen.
        """
        self.text = text_renderer

    # =================================================================
    # MENU SCREEN — Professional start screen with animations
    # =================================================================

    def draw_demo_bullet(self, trail, x, y):
        """
        Draw a bouncing demo bullet on the menu screen background.

        This bullet bounces around behind the menu text, hinting
        at the ricochet mechanic before the player starts.

        Args:
            trail: List of recent (x, y) positions (for trail effect).
            x, y:  Current position of the demo bullet.
        """
        # Draw trail: fading circles at previous positions
        n = len(trail)
        for i, (tx, ty) in enumerate(trail):
            t = (i + 1) / max(n, 1)    # 0→1 (oldest to newest)
            alpha = t * 0.20            # Newest = most visible
            r = 1.5 + t * 3.0          # Newest = largest
            draw_circle(tx, ty, r,
                        (COL_BULLET_TRAIL[0], COL_BULLET_TRAIL[1],
                         COL_BULLET_TRAIL[2], alpha))

        # Draw glow halo around the bullet
        draw_glow(x, y, 16, COL_BULLET_GLOW, layers=3)
        # Draw the solid bullet core
        draw_circle(x, y, 5, COL_BULLET_CORE)

    def draw_menu(self, frame, best_score=0):
        """
        Render the main menu screen with polished indie-game aesthetics.

        LAYOUT (top to bottom):
            1. Radial gradient backdrop (warm glow behind title area)
            2. Animated crosshair decoration (slowly rotating)
            3. Title: "ONE SHOT ASSASSIN" (gold, 54px, with pulsing glow)
            4. Subtitle: "A Ricochet Puzzle Game" (gray, 22px)
            5. Gradient divider line with center diamond
            6. Menu options: Start (blinking), Instructions, Quit
            7. Footer: University information

        Args:
            frame: Current frame counter (drives all animations).
                   Incremented by 1 each frame in game.py's main loop.
        """
        cx = SCREEN_WIDTH // 2  # Horizontal center of the screen

        # ─── 1. Radial gradient backdrop ─────────────────────────────
        # A soft warm light behind the title area, subtly pulsing
        # Using sin(frame * 0.015) for very slow oscillation
        grad_alpha = 0.06 + 0.02 * math.sin(frame * 0.015)
        draw_radial_gradient(cx, 200, 320,
                             (1.0, 0.75, 0.2, grad_alpha))

        # ─── 2. Decorative animated crosshair ────────────────────────
        # A slowly rotating reticle behind the title for visual flair
        # rotation increases by 0.008 radians per frame
        rotation = frame * 0.008
        draw_crosshair(cx, 195, 110, COL_CROSSHAIR, rotation)

        # ─── 3. Title with pulsing glow ──────────────────────────────
        # The glow alpha oscillates using sin() for a "breathing" effect
        # sin(frame * 0.04) = ~1 full cycle per 157 frames (~2.6 seconds)
        glow_alpha = 0.20 + 0.10 * math.sin(frame * 0.04)
        draw_glow(cx, 170, 160, (1.0, 0.84, 0.0, glow_alpha), layers=5)

        # Title text — large golden text, centered
        self.text.draw("ONE SHOT ASSASSIN", cx, 160,
                       54, COL_TITLE, centered=True)

        # ─── 4. Subtitle ─────────────────────────────────────────────
        self.text.draw("A Ricochet Puzzle Game", cx, 222,
                       22, COL_SUBTITLE, centered=True)

        # ─── 5. Decorative divider lines ─────────────────────────────
        # Two gradient lines that fade from transparent edges to
        # an opaque center, creating an elegant separator
        line_y = 255
        line_half = 160    # Half-width of the divider
        center_col = (0.5, 0.5, 0.65, 0.6)     # Opaque center
        edge_col   = (0.2, 0.2, 0.3, 0.0)      # Transparent edges
        # Left half: transparent → opaque (toward center)
        draw_line_gradient(cx - line_half, line_y, cx, line_y,
                           edge_col, center_col, 1.0)
        # Right half: opaque → transparent (away from center)
        draw_line_gradient(cx, line_y, cx + line_half, line_y,
                           center_col, edge_col, 1.0)
        # Small diamond dot at the exact center of the divider
        draw_circle(cx, line_y, 2.5, (0.5, 0.5, 0.7, 0.5))

        # ─── 6. Menu options ─────────────────────────────────────────
        menu_y = 310

        # "Press ENTER to Start" — BLINKING animation
        # sin(frame * 0.06) oscillates every ~105 frames (~1.7 seconds)
        # Maps from sin range [-1, 1] to alpha range [0.1, 1.0]
        blink = 0.55 + 0.45 * math.sin(frame * 0.06)
        self.text.draw("Press ENTER to Start", cx, menu_y,
                       28, COL_TEXT, centered=True, alpha=blink)

        # Other options — static (not blinking), dimmer colors
        self.text.draw("Press I for Instructions", cx, menu_y + 55,
                       21, COL_SUBTITLE, centered=True)
        self.text.draw("Press ESC to Quit", cx, menu_y + 100,
                       19, COL_DIM, centered=True)

        # ─── 7. Best Score (shown only if > 0) ──────────────────────
        if best_score > 0:
            self.text.draw(f"Best Score: {best_score}", cx, menu_y + 145,
                           20, COL_TITLE, centered=True)

        # ─── 8. Footer — University information ──────────────────────
        self._draw_footer(frame)

    def _draw_footer(self, frame):
        """
        Draw the professional university footer at the bottom of the menu.

        CONTENT:
            Line 1: "Developed for Computer Graphics Course"
            Line 2: "Department of Computer Science & Engineering"
            Line 3: "Daffodil International University, 2026"
            Line 4: "Developed using Python & Pygame + PyOpenGL" (very subtle)

        A subtle gradient divider line separates the footer from
        the menu options above.
        """
        cx = SCREEN_WIDTH // 2

        # ─── Subtle separator line before footer ─────────────────────
        sep_y = SCREEN_HEIGHT - 110
        sep_half = 120
        sep_col   = (0.3, 0.3, 0.4, 0.3)       # Center: faint
        sep_edge  = (0.1, 0.1, 0.15, 0.0)       # Edges: transparent
        draw_line_gradient(cx - sep_half, sep_y, cx, sep_y,
                           sep_edge, sep_col, 1.0)
        draw_line_gradient(cx, sep_y, cx + sep_half, sep_y,
                           sep_col, sep_edge, 1.0)

        # ─── University info (three lines, small and subtle) ─────────
        self.text.draw("Developed for Computer Graphics Course",
                       cx, SCREEN_HEIGHT - 90,
                       16, COL_FOOTER, centered=True)
        self.text.draw("Department of Computer Science & Engineering",
                       cx, SCREEN_HEIGHT - 68,
                       15, COL_FOOTER, centered=True)
        self.text.draw("Daffodil International University, 2026",
                       cx, SCREEN_HEIGHT - 46,
                       15, COL_FOOTER, centered=True)

        # ─── Tech credit (very dim, barely visible) ──────────────────
        self.text.draw("Developed using Python & Pygame + PyOpenGL",
                       cx, SCREEN_HEIGHT - 18,
                       12, COL_DIM, centered=True)

    # =================================================================
    # INSTRUCTIONS SCREEN — How to play
    # =================================================================

    def draw_instructions(self, frame=0):
        """
        Render the instructions / how-to-play screen.

        SECTIONS:
            1. CONTROLS — Key mappings in a clean table layout
            2. GAME RULES — Bullet behavior and objectives
            3. SCORING — Points for kills, penalties for bullets

        Args:
            frame: Frame counter for the blinking "back" hint.
        """
        cx = SCREEN_WIDTH // 2

        # ─── Title ───────────────────────────────────────────────────
        draw_glow(cx, 58, 80, (1.0, 0.84, 0.0, 0.08), layers=3)
        self.text.draw("HOW TO PLAY", cx, 55,
                       40, COL_TITLE, centered=True)

        # Gradient divider below title
        draw_line_gradient(cx - 100, 88, cx, 88,
                           (0.2, 0.2, 0.3, 0.0),
                           (0.4, 0.4, 0.55, 0.6), 1.0)
        draw_line_gradient(cx, 88, cx + 100, 88,
                           (0.4, 0.4, 0.55, 0.6),
                           (0.2, 0.2, 0.3, 0.0), 1.0)

        # ─── Controls section ────────────────────────────────────────
        y = 118
        self.text.draw("CONTROLS", cx, y,
                       22, COL_TEXT, centered=True)
        y += 38

        # Table-like layout: key on left, action on right
        controls = [
            ("LEFT / RIGHT", "Rotate Aim Direction"),
            ("SPACE", "Fire Bullet"),
            ("R", "Restart Game"),
            ("ESC", "Return to Menu"),
        ]
        for key, action in controls:
            self.text.draw(key, cx - 40, y, 18, COL_TITLE)     # Key name (gold)
            self.text.draw(action, cx + 80, y, 18, COL_SUBTITLE)  # Action (gray)
            y += 28

        # ─── Rules section ───────────────────────────────────────────
        y += 15
        draw_line(cx - 80, y, cx + 80, y, (0.25, 0.25, 0.35, 0.4), 1.0)
        y += 18
        self.text.draw("GAME RULES", cx, y,
                       22, COL_TEXT, centered=True)
        y += 38

        rules = [
            "Destroy all enemies with your limited bullets",
            "Bullets ricochet off walls — use this wisely!",
            "A single bullet can hit multiple enemies",
            "Plan your angles carefully before each shot",
        ]
        for line in rules:
            self.text.draw(line, cx, y, 18, COL_SUBTITLE, centered=True)
            y += 28

        # ─── Scoring section ─────────────────────────────────────────
        y += 15
        draw_line(cx - 80, y, cx + 80, y, (0.25, 0.25, 0.35, 0.4), 1.0)
        y += 18
        self.text.draw("SCORING", cx, y,
                       22, COL_TEXT, centered=True)
        y += 38

        # Color-coded scoring info: green=good, red=bad, gold=bonus
        self.text.draw("+10  per enemy destroyed", cx, y,
                       19, COL_SUCCESS, centered=True)    # Green
        y += 28
        self.text.draw("-2   per bullet used", cx, y,
                       19, COL_DANGER, centered=True)     # Red
        y += 28
        self.text.draw("+50  level completion bonus", cx, y,
                       19, COL_TITLE, centered=True)      # Gold

        # ─── Back hint (blinking) ────────────────────────────────────
        blink = 0.4 + 0.3 * math.sin(frame * 0.05)
        self.text.draw("Press ESC to go back", cx, SCREEN_HEIGHT - 35,
                       17, COL_DIM, centered=True, alpha=blink)

    # =================================================================
    # IN-GAME HUD — Shown during gameplay at the top of the screen
    # =================================================================

    def draw_hud(self, level_name, score, bullets_remaining):
        """
        Render the top HUD (Heads-Up Display) bar.

        LAYOUT:
            Left:   Level name (white)
            Center: Score (gold)
            Right:  Bullet count (white, turns RED when 0)

        The HUD has a gradient background (dark top → transparent bottom)
        and a gradient separator line at the bottom.
        """
        # ─── Gradient background bar ─────────────────────────────────
        # Darker at top, slightly transparent at bottom
        draw_rect_gradient_v(0, 0, SCREEN_WIDTH, HUD_HEIGHT,
                             (0.0, 0.0, 0.0, 0.85),     # Top: dark
                             (0.0, 0.0, 0.05, 0.50))    # Bottom: faded

        # ─── Level name (left side) ──────────────────────────────────
        self.text.draw(level_name, 15, 14, 20, COL_TEXT)

        # ─── Score (center) ──────────────────────────────────────────
        self.text.draw(f"Score: {score}", SCREEN_WIDTH // 2, 14,
                       24, COL_TITLE, centered=True)

        # ─── Bullets remaining (right side) ──────────────────────────
        # Color changes to RED when bullets = 0 (danger warning)
        col = COL_DANGER if bullets_remaining == 0 else COL_TEXT
        btext = f"Bullets: {bullets_remaining}"
        tw, _ = self.text.get_text_size(btext, 20)  # Get text width for right-alignment
        self.text.draw(btext, SCREEN_WIDTH - tw - 15, 14, 20, col)

        # ─── Gradient separator line at bottom of HUD ────────────────
        # Fades from transparent at edges to opaque at center
        draw_line_gradient(0, HUD_HEIGHT, SCREEN_WIDTH // 2, HUD_HEIGHT,
                           (0.15, 0.20, 0.30, 0.0),
                           (0.25, 0.35, 0.50, 0.8), 1.0)
        draw_line_gradient(SCREEN_WIDTH // 2, HUD_HEIGHT,
                           SCREEN_WIDTH, HUD_HEIGHT,
                           (0.25, 0.35, 0.50, 0.8),
                           (0.15, 0.20, 0.30, 0.0), 1.0)

    # =================================================================
    # LEVEL COMPLETE — Shown between levels
    # =================================================================

    def draw_level_complete(self, level_num, score, frame=0):
        """
        Render the level-complete transition screen.

        Shows the level number cleared, current score, level bonus,
        and options to continue or return to menu.

        Features a green radial glow and blinking "Next Level" prompt.
        """
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2

        # Green radial glow background
        draw_radial_gradient(cx, cy - 40, 200,
                             (0.0, 1.0, 0.5, 0.06))
        draw_glow(cx, cy - 60, 120, (0.0, 1.0, 0.5, 0.10), layers=4)

        # "LEVEL COMPLETE!" — large green text
        self.text.draw("LEVEL COMPLETE!", cx, cy - 80,
                       44, COL_SUCCESS, centered=True)
        self.text.draw(f"Level {level_num} Cleared", cx, cy - 25,
                       24, COL_SUBTITLE, centered=True)

        # Divider
        draw_line(cx - 60, cy + 5, cx + 60, cy + 5,
                  (0.3, 0.5, 0.4, 0.5), 1.0)

        # Score and bonus
        self.text.draw(f"Score: {score}", cx, cy + 25,
                       28, COL_TITLE, centered=True)
        self.text.draw(f"+{SCORE_LEVEL_BONUS} Level Bonus!", cx, cy + 65,
                       22, COL_TITLE, centered=True)

        # Blinking "Next Level" prompt
        blink = 0.5 + 0.5 * math.sin(frame * 0.06)
        self.text.draw("Press ENTER for Next Level", cx, cy + 140,
                       24, COL_TEXT, centered=True, alpha=blink)
        self.text.draw("Press ESC for Menu", cx, cy + 180,
                       20, COL_SUBTITLE, centered=True)

    # =================================================================
    # WIN SCREEN — Shown after all levels are cleared
    # =================================================================

    def draw_win(self, score, frame=0):
        """
        Render the victory screen after all levels are cleared.

        Features a golden radial glow, animated crosshair decoration,
        and the final score.
        """
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2

        # Golden radial glow
        draw_radial_gradient(cx, cy - 60, 250,
                             (1.0, 0.84, 0.0, 0.06))
        draw_glow(cx, cy - 80, 180, (1.0, 0.84, 0.0, 0.10), layers=5)

        # Animated crosshair decoration (slowly rotating)
        draw_crosshair(cx, cy - 70, 90, (1.0, 0.84, 0.0, 0.12),
                       frame * 0.005)

        # "VICTORY!" — large gold text
        self.text.draw("VICTORY!", cx, cy - 100,
                       56, COL_TITLE, centered=True)
        self.text.draw("All Levels Cleared!", cx, cy - 30,
                       26, COL_SUCCESS, centered=True)

        # Decorative gradient divider
        draw_line_gradient(cx - 100, cy + 5, cx, cy + 5,
                           (0.2, 0.2, 0.3, 0.0),
                           (0.5, 0.5, 0.65, 0.6), 1.0)
        draw_line_gradient(cx, cy + 5, cx + 100, cy + 5,
                           (0.5, 0.5, 0.65, 0.6),
                           (0.2, 0.2, 0.3, 0.0), 1.0)

        # Final score
        self.text.draw(f"Final Score: {score}", cx, cy + 30,
                       32, COL_TEXT, centered=True)

        # Blinking "Play Again" prompt
        blink = 0.5 + 0.5 * math.sin(frame * 0.06)
        self.text.draw("Press R to Play Again", cx, cy + 110,
                       24, COL_TEXT, centered=True, alpha=blink)
        self.text.draw("Press ESC for Menu", cx, cy + 155,
                       20, COL_SUBTITLE, centered=True)

    # =================================================================
    # GAME OVER SCREEN — Shown when bullets are exhausted
    # =================================================================

    def draw_game_over(self, score, frame=0, retries_left=0, retry_penalty=0):
        """
        Render the game-over screen when the player runs out of bullets.

        Shows retry count and penalty info.
        Features a red radial glow and the player's final score.
        """
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2

        # Red radial glow (danger/failure feeling)
        draw_radial_gradient(cx, cy - 60, 250,
                             (1.0, 0.1, 0.15, 0.06))
        draw_glow(cx, cy - 80, 160, (1.0, 0.10, 0.15, 0.10), layers=5)

        # "GAME OVER" — large red text
        self.text.draw("GAME OVER", cx, cy - 100,
                       56, COL_DANGER, centered=True)
        self.text.draw("Bullets Exhausted!", cx, cy - 30,
                       24, COL_SUBTITLE, centered=True)

        # Gradient divider
        draw_line_gradient(cx - 80, cy, cx, cy,
                           (0.2, 0.2, 0.3, 0.0),
                           (0.5, 0.3, 0.35, 0.6), 1.0)
        draw_line_gradient(cx, cy, cx + 80, cy,
                           (0.5, 0.3, 0.35, 0.6),
                           (0.2, 0.2, 0.3, 0.0), 1.0)

        # Score at the moment of failure
        self.text.draw(f"Score: {score}", cx, cy + 25,
                       28, COL_TEXT, centered=True)

        # Blinking "Retry" prompt with retry info
        blink = 0.5 + 0.5 * math.sin(frame * 0.06)

        if retries_left > 0:
            # Show retries remaining and penalty
            self.text.draw(f"Press R to Retry ({retries_left} left, -{retry_penalty} pts)",
                           cx, cy + 100,
                           24, COL_TEXT, centered=True, alpha=blink)
        else:
            # No retries — back to Level 1
            self.text.draw("Press R to Restart from Level 1",
                           cx, cy + 100,
                           24, COL_DANGER, centered=True, alpha=blink)

        self.text.draw("Press ESC for Menu", cx, cy + 150,
                       20, COL_SUBTITLE, centered=True)
