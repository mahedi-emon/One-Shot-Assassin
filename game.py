"""
game.py — Main Game class for One Shot Assassin.
=========================================================
PURPOSE:
    This is the CENTRAL CONTROLLER ("Game Manager") that ties
    everything together. It owns:
      - The Pygame window + OpenGL rendering context
      - The state machine (which screen is currently active)
      - All game objects (player, bullets, enemies, walls)
      - The main loop (events → update → render → display)

STATE MACHINE:
    The game is always in exactly ONE state:
      MENU → INSTRUCTIONS → PLAYING → LEVEL_COMPLETE → WIN/GAME_OVER
    The current state determines:
      - Which keys are active
      - What update logic runs
      - What gets drawn on screen

MAIN LOOP PATTERN:
    Every frame (60 times per second):
      1. handle_events() — Process keyboard/mouse/quit events
      2. update()         — Update game logic (physics, AI, particles)
      3. render()         — Draw everything to the OpenGL framebuffer
      4. pygame.display.flip() — Show the framebuffer on screen

FADE TRANSITIONS:
    When switching between states, the screen smoothly fades to
    black and back. This is controlled by fade_alpha (0→1→0),
    fade_direction (+1=fading out, -1=fading in, 0=no fade),
    and a pending_state/pending_action that execute at the midpoint.
=========================================================
"""

import pygame  # Window management, input handling, timing
from renderer import (
    init_gl,        # Set up OpenGL projection and blending
    clear_screen,   # Clear framebuffer each frame
    draw_grid,      # Background grid pattern
    draw_play_area_border,  # Rectangular play area outline
    draw_fade_overlay,      # Black overlay for fade transitions
    TextRenderer,   # Pygame fonts → OpenGL textures
)
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, GAME_TITLE, PLAY_AREA,
    SCORE_ENEMY, SCORE_BULLET_PENALTY, SCORE_LEVEL_BONUS,
    RETRY_COUNTS, RETRY_PENALTIES,                  # Retry system constants
    FADE_SPEED,                                     # Fade transition speed
    STATE_MENU, STATE_INSTRUCTIONS, STATE_PLAYING,  # State constants
    STATE_LEVEL_COMPLETE, STATE_WIN, STATE_GAME_OVER,
)
from player import Player          # Player turret (aim + shoot)
from enemy import Enemy            # Enemy targets (static + moving)
from wall import Wall              # Rectangular obstacles
from level import LEVELS           # Level data (positions, enemies, walls)
from particles import ParticleSystem  # Visual particle effects
from ui import UI                  # Screen renderers (menu, HUD, etc.)
import audio                       # Procedural sound effects


class Game:
    """
    Top-level game controller.

    Owns the Pygame window, the OpenGL context, all game objects,
    and the state machine. Call run() to start the game.
    """

    def __init__(self):
        """
        Initialize Pygame, OpenGL, and all sub-systems.

        This runs ONCE when the game starts. It sets up:
          - Pygame library + display window
          - OpenGL rendering context
          - Text renderer (Pygame fonts → OpenGL textures)
          - UI manager (screen renderers)
          - Fade transition system
          - Demo bullets and ambient particles (for menu)
        """
        # ─── Initialize Pygame ────────────────────────────────────────
        pygame.init()                               # Start all Pygame sub-systems
        pygame.display.set_caption(GAME_TITLE)      # Window title: "One Shot Assassin"
        
        # Initialize Audio System (Generates .wav files if missing)
        audio.init()

        # ─── Create window with OpenGL context ────────────────────────
        # OPENGL flag tells Pygame to create an OpenGL rendering context
        # DOUBLEBUF enables double-buffering (draw to back buffer, then flip)
        self.screen = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT),           # 900 × 700 pixels
            pygame.OPENGL | pygame.DOUBLEBUF,
        )
        # Set up OpenGL projection, blending, line smoothing
        init_gl(SCREEN_WIDTH, SCREEN_HEIGHT)

        # ─── Timing ──────────────────────────────────────────────────
        self.clock = pygame.time.Clock()    # Used to limit to 60 FPS
        self.running = True                 # Set to False to exit main loop
        self.frame = 0                      # Frame counter (for animations)

        # ─── UI / Text ───────────────────────────────────────────────
        self.text_renderer = TextRenderer()     # Pygame fonts → GL textures
        self.ui = UI(self.text_renderer)         # All screen renderers

        # ─── Game State Machine ──────────────────────────────────────
        # The game starts at the MENU state
        self.state = STATE_MENU

        # ─── Fade Transition System ──────────────────────────────────
        # Provides smooth fade-out → black → fade-in between screens
        self.fade_alpha = 1.0           # Start fully black (fade in on launch)
        self.fade_direction = -1        # -1 = fading in (becoming visible)
        self.pending_state = None       # State to switch to after fade-out
        self.pending_action = None      # Function to call at transition midpoint

        # ─── Game Objects ────────────────────────────────────────────
        # These are populated when a level is loaded via _load_level()
        self.player = None              # Player turret instance
        self.bullets = []               # Active bullet instances
        self.enemies = []               # Active enemy instances
        self.walls = []                 # Wall instances
        self.particles = ParticleSystem()  # Gameplay particle effects

        # ─── Score and Level Tracking ────────────────────────────────
        self.score = 0                  # Current total score
        self.current_level = 0          # Current level index (0-based)
        self.best_score = 0             # Best score this session (persists until restart)

        # ─── Retry System ────────────────────────────────────────────
        # Extra chances per level before falling back to Level 1
        self.retries_left = 0           # Remaining retries for current level

        # ─── Menu Demo Bullets ───────────────────────────────────────
        # Two bullets bouncing around the menu background for visual style
        # Each has position (x, y), velocity (vx, vy), and a trail list
        self.demo_bullets = [
            {"x": 200.0, "y": 300.0, "vx": 3.5, "vy": 2.5, "trail": []},
            {"x": 650.0, "y": 450.0, "vx": -2.8, "vy": -3.2, "trail": []},
        ]

        # ─── Menu Ambient Particles ──────────────────────────────────
        # Slow floating particles on non-gameplay screens for atmosphere
        self.menu_particles = ParticleSystem()

    # =================================================================
    # FADE TRANSITION SYSTEM
    # =================================================================

    def _start_fade_to(self, new_state, action=None):
        """
        Start a smooth fade transition to a new state.

        SEQUENCE:
            1. Screen fades to black (fade_alpha: 0 → 1)
            2. At blackout: execute action (e.g., load level), switch state
            3. Screen fades back in (fade_alpha: 1 → 0)

        Args:
            new_state: The game state to transition to.
            action:    Optional function to call at the midpoint
                       (e.g., self._do_start_new_game to reset score
                       and load level 1).
        """
        self.fade_direction = 1         # Start fading out (alpha increasing)
        self.pending_state = new_state  # Remember target state
        self.pending_action = action    # Remember action to execute

    def _update_fade(self):
        """
        Update the fade overlay alpha each frame.

        LOGIC:
            - If fading out (direction=+1): increase alpha by FADE_SPEED
              When alpha reaches 1.0 (fully black):
                → Execute pending action
                → Switch to pending state
                → Start fading in (direction=-1)

            - If fading in (direction=-1): decrease alpha by FADE_SPEED
              When alpha reaches 0.0 (fully visible):
                → Stop fading (direction=0)
        """
        if self.fade_direction == 0:
            return  # No active fade — nothing to do

        # Advance fade alpha by FADE_SPEED (0.04) per frame
        self.fade_alpha += self.fade_direction * FADE_SPEED

        # Fade-out complete (screen is fully black)
        if self.fade_alpha >= 1.0 and self.fade_direction == 1:
            self.fade_alpha = 1.0
            # Execute the pending action (e.g., load a level)
            if self.pending_action:
                self.pending_action()
                self.pending_action = None
            # Switch to the new state
            if self.pending_state:
                self.state = self.pending_state
                self.pending_state = None
            # Start fading back in
            self.fade_direction = -1

        # Fade-in complete (screen is fully visible)
        elif self.fade_alpha <= 0.0 and self.fade_direction == -1:
            self.fade_alpha = 0.0
            self.fade_direction = 0     # Stop fading

    # =================================================================
    # MAIN LOOP — The heart of the game
    # =================================================================

    def run(self):
        """
        Run the main game loop until the player quits.

        LOOP PATTERN (runs 60 times per second):
            1. clock.tick(60) — Wait to maintain 60 FPS
            2. handle_events() — Process input (keyboard, quit)
            3. update() — Run game logic (physics, AI, transitions)
            4. render() — Draw everything to the framebuffer
            5. display.flip() — Swap buffers (show the frame)

        When the loop exits, cleanup OpenGL textures and quit Pygame.
        """
        while self.running:
            self.clock.tick(FPS)         # Limit to 60 FPS
            self.frame += 1              # Increment animation counter

            self.handle_events()         # Process input
            self.update()                # Run game logic
            self.render()                # Draw everything

            pygame.display.flip()        # Show the frame on screen

        # ─── Cleanup ─────────────────────────────────────────────────
        self.text_renderer.cleanup()     # Free OpenGL textures from GPU
        pygame.quit()                    # Shut down Pygame

    # =================================================================
    # EVENT HANDLING — Keyboard input per state
    # =================================================================

    def handle_events(self):
        """
        Process all Pygame events (quit, key presses).

        Input is BLOCKED during fade transitions (fade_direction != 0)
        to prevent accidental double-presses.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:       # Window close button
                self.running = False
            elif event.type == pygame.KEYDOWN:
                # Only accept input when not in the middle of a fade
                if self.fade_direction == 0:
                    self._on_key_down(event.key)

    def _on_key_down(self, key):
        """
        Handle a single key-press event.

        Different keys are active depending on the current game state.
        All state transitions use fade animations for smooth polish.
        """
        # ─── MENU STATE ──────────────────────────────────────────────
        if self.state == STATE_MENU:
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                audio.play('select')
                # Start game: fade out → reset score & load level 1 → fade in
                self._start_fade_to(STATE_PLAYING, self._do_start_new_game)
            elif key == pygame.K_i:
                audio.play('select')
                # Show instructions with fade transition
                self._start_fade_to(STATE_INSTRUCTIONS)
            elif key == pygame.K_ESCAPE:
                self.running = False    # Quit the game immediately

        # ─── INSTRUCTIONS STATE ──────────────────────────────────────
        elif self.state == STATE_INSTRUCTIONS:
            if key in (pygame.K_ESCAPE, pygame.K_BACKSPACE,
                       pygame.K_RETURN):
                audio.play('select')
                # Return to menu with fade
                self._start_fade_to(STATE_MENU)

        # ─── PLAYING STATE ───────────────────────────────────────────
        elif self.state == STATE_PLAYING:
            if key == pygame.K_SPACE:
                self._shoot()   # Fire a bullet (no fade needed)
            elif key == pygame.K_r:
                audio.play('select')
                # Restart: fade out → reset all → fade in
                self._start_fade_to(STATE_PLAYING, self._do_start_new_game)
            elif key == pygame.K_ESCAPE:
                audio.play('select')
                # Return to menu with fade
                self._start_fade_to(STATE_MENU)

        # ─── LEVEL COMPLETE STATE ────────────────────────────────────
        elif self.state == STATE_LEVEL_COMPLETE:
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                audio.play('select')
                # Next level: fade out → load next level → fade in
                self._start_fade_to(STATE_PLAYING, self._do_advance_level)
            elif key == pygame.K_ESCAPE:
                audio.play('select')
                self._start_fade_to(STATE_MENU)

        # ─── WIN STATE ────────────────────────────────────────────────
        elif self.state == STATE_WIN:
            if key == pygame.K_r:
                audio.play('select')
                self._start_fade_to(STATE_PLAYING, self._do_start_new_game)
            elif key == pygame.K_ESCAPE:
                audio.play('select')
                self._start_fade_to(STATE_MENU)

        # ─── GAME OVER STATE (with retry system) ─────────────────────
        elif self.state == STATE_GAME_OVER:
            if key == pygame.K_r:
                audio.play('select')
                if self.retries_left > 0:
                    # Retry same level with score penalty
                    self._start_fade_to(STATE_PLAYING, self._do_retry_level)
                else:
                    # No retries left → back to Level 1
                    self._start_fade_to(STATE_PLAYING, self._do_start_new_game)
            elif key == pygame.K_ESCAPE:
                audio.play('select')
                self._start_fade_to(STATE_MENU)

    # =================================================================
    # GAME ACTIONS — Shooting, starting, advancing levels
    # =================================================================

    def _shoot(self):
        """
        Fire a bullet from the player.

        Only fires if the player has bullets remaining.
        Creates a new Bullet object and adds it to self.bullets.
        Deducts SCORE_BULLET_PENALTY (-2) from the score.
        """
        if self.player and self.player.bullets_remaining > 0:
            bullet = self.player.shoot()    # Create Bullet in aim direction
            if bullet:
                audio.play('shoot')
                self.bullets.append(bullet)     # Add to active bullets list
                self.score -= SCORE_BULLET_PENALTY  # -2 points per shot

    def _do_start_new_game(self):
        """
        Reset everything and start from level 1.

        Called at the MIDPOINT of a fade transition (screen is black).
        This ensures the player doesn't see the level loading.
        """
        self.best_score = max(self.best_score, self.score)  # Save best
        self.score = 0              # Reset score to zero
        self.current_level = 0      # Back to level 1 (index 0)
        self.retries_left = RETRY_COUNTS[0]  # Set retries for Level 1
        self._load_level(0)         # Load level 1 data

    def start_new_game(self):
        """Public method — begin a new game with fade transition."""
        self._start_fade_to(STATE_PLAYING, self._do_start_new_game)

    def _do_advance_level(self):
        """
        Load the next level (called at fade transition midpoint).

        Increments current_level and loads the next level's data.
        Sets retries for the new level.
        """
        self.current_level += 1
        if self.current_level < len(LEVELS):
            self.retries_left = RETRY_COUNTS[self.current_level]
            self._load_level(self.current_level)

    def _do_retry_level(self):
        """
        Retry the current level with a score penalty.

        Deducts the retry penalty and reloads the same level.
        Decrements retries_left so the player has fewer chances.
        """
        penalty = RETRY_PENALTIES[self.current_level]
        self.score -= penalty                # Deduct retry penalty
        self.retries_left -= 1               # One fewer retry remaining
        self._load_level(self.current_level)  # Reload same level

    def _load_level(self, index):
        """
        Load a level by index from the LEVELS data.

        Reads the level dictionary from level.py and creates
        fresh game objects (player, enemies, walls).
        Clears any in-flight bullets and resets the particle system.

        PROCESS:
            1. Read level data (player position, bullet count, etc.)
            2. Create Player at specified position with bullet count
            3. Create Enemy objects (static or moving)
            4. Create Wall objects
            5. Clear bullets and particles from previous level
        """
        data = LEVELS[index]    # Get level dictionary

        # ─── Create Player ───────────────────────────────────────────
        px, py = data["player_pos"]     # e.g., (450, 650) = bottom-center
        self.player = Player(px, py, data["bullets"])

        # ─── Clear previous bullets ──────────────────────────────────
        self.bullets = []   # Remove any in-flight bullets

        # ─── Create Enemies ──────────────────────────────────────────
        self.enemies = []
        for e in data["enemies"]:
            self.enemies.append(Enemy(
                x=e["x"],                            # Center x position
                y=e["y"],                            # Center y position
                enemy_type=e.get("type", "static"),  # "static" or "moving"
                move_axis=e.get("axis", "x"),        # "x" or "y" (moving only)
                move_range=tuple(e.get("range", (0, 0))),  # (min, max) bounds
                move_speed=e.get("speed", 2),        # Pixels per frame
            ))

        # ─── Create Walls ────────────────────────────────────────────
        self.walls = []
        for w in data["walls"]:
            self.walls.append(Wall(w["x"], w["y"], w["w"], w["h"]))

        # ─── Fresh particle system ───────────────────────────────────
        self.particles = ParticleSystem()    # Clear all explosion/spark particles

    # =================================================================
    # UPDATE — Game logic (called every frame)
    # =================================================================

    def update(self):
        """
        Update game logic based on the current state.

        The fade transition is ALWAYS updated (regardless of state).
        Then, state-specific logic runs:
          - PLAYING: Physics, collisions, win/lose checks
          - Everything else: Demo bullets + ambient particles
        """
        # Always update fade animation
        self._update_fade()

        if self.state == STATE_PLAYING:
            self._update_playing()
        elif self.state in (STATE_MENU, STATE_WIN, STATE_GAME_OVER,
                            STATE_INSTRUCTIONS, STATE_LEVEL_COMPLETE):
            self._update_menu_effects()

    def _update_playing(self):
        """
        Update gameplay: aim rotation, bullets, enemies, particles.

        CALLED 60 TIMES PER SECOND during gameplay.

        STEPS:
            1. Check held keys for continuous aim rotation
            2. Update each bullet (move, bouncing, enemy hits)
            3. Update enemies (movement for moving type)
            4. Update particles (move, fade, remove dead)
            5. Check WIN condition (all enemies dead)
            6. Check LOSE condition (no bullets left)
        """
        # ─── 1. Smooth aim rotation ──────────────────────────────────
        # get_pressed() returns True for keys currently HELD DOWN
        # (unlike KEYDOWN events which fire once per press)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.player.rotate_aim(-1)    # Rotate counter-clockwise
        if keys[pygame.K_RIGHT]:
            self.player.rotate_aim(1)     # Rotate clockwise

        # ─── 2. Update bullets ───────────────────────────────────────
        # Iterate over a COPY of the list (self.bullets[:]) because
        # we may remove bullets during iteration
        for bullet in self.bullets[:]:
            # bullet.update() returns number of enemies hit this frame
            hits = bullet.update(
                self.walls, self.enemies, self.particles, PLAY_AREA,
            )
            self.score += hits * SCORE_ENEMY    # +10 per enemy killed
            if not bullet.alive:
                self.bullets.remove(bullet)     # Remove dead bullets

        # ─── 3. Update enemies ───────────────────────────────────────
        for enemy in self.enemies:
            enemy.update()  # Move if moving type, advance pulse animation

        # ─── 4. Update particles ─────────────────────────────────────
        self.particles.update()  # Move, fade, remove dead particles

        # ─── 5. WIN condition check ──────────────────────────────────
        alive_count = sum(1 for e in self.enemies if e.alive)

        if alive_count == 0:
            # All enemies destroyed → level complete!
            self.score += SCORE_LEVEL_BONUS  # +50 level bonus
            if self.current_level >= len(LEVELS) - 1:
                if self.state != STATE_WIN:
                    audio.play('win')
                    self.best_score = max(self.best_score, self.score)
                self.state = STATE_WIN          # Last level → VICTORY!
            else:
                if self.state != STATE_LEVEL_COMPLETE:
                    audio.play('win')
                self.state = STATE_LEVEL_COMPLETE  # More levels → show summary

        # ─── 6. LOSE condition check ─────────────────────────────────
        elif self.player.bullets_remaining == 0 and len(self.bullets) == 0:
            # No bullets left AND no bullets in flight → GAME OVER
            if self.state != STATE_GAME_OVER:
                audio.play('game_over')
                self.best_score = max(self.best_score, self.score)
            self.state = STATE_GAME_OVER

    def _update_menu_effects(self):
        """
        Update demo bullets and ambient particles for non-gameplay screens.

        DEMO BULLETS:
            Two bullets bounce around the screen behind the menu text.
            They reverse direction when hitting the window edges.
            A trail of recent positions is stored for the trail effect.

        AMBIENT PARTICLES:
            Every 6 frames, one faint blue particle is spawned.
            They drift slowly across the screen for atmosphere.
        """
        # ─── Update demo bullets ─────────────────────────────────────
        for db in self.demo_bullets:
            # Save current position to trail (for visual effect)
            db["trail"].append((db["x"], db["y"]))
            if len(db["trail"]) > 40:
                db["trail"].pop(0)      # Keep only last 40 positions

            # Move the demo bullet
            db["x"] += db["vx"]
            db["y"] += db["vy"]

            # Bounce off window edges (simple velocity reversal)
            if db["x"] < 15 or db["x"] > SCREEN_WIDTH - 15:
                db["vx"] *= -1
            if db["y"] < 15 or db["y"] > SCREEN_HEIGHT - 15:
                db["vy"] *= -1

        # ─── Spawn ambient particles ─────────────────────────────────
        # Every 6 frames ≈ 10 particles per second at 60 FPS
        if self.frame % 6 == 0:
            self.menu_particles.spawn_ambient(
                SCREEN_WIDTH, SCREEN_HEIGHT, 1,
            )
        self.menu_particles.update()    # Move and remove dead particles

    # =================================================================
    # RENDER — Drawing (called every frame after update)
    # =================================================================

    def render(self):
        """
        Render the current state to the screen.

        STEPS:
            1. Clear the screen (dark navy background)
            2. Draw the background grid
            3. Draw state-specific content (menu OR gameplay OR win, etc.)
            4. Draw fade overlay on top (if fading between screens)
        """
        # ─── 1. Clear screen to dark navy ────────────────────────────
        clear_screen()

        # ─── 2. Background grid (on all screens) ────────────────────
        draw_grid(SCREEN_WIDTH, SCREEN_HEIGHT)

        # ─── 3. State-specific rendering ─────────────────────────────
        if self.state == STATE_MENU:
            self.menu_particles.draw()      # Ambient particles (behind text)
            for db in self.demo_bullets:    # Demo bullets (behind text)
                self.ui.draw_demo_bullet(db["trail"], db["x"], db["y"])
            self.ui.draw_menu(self.frame, self.best_score)

        elif self.state == STATE_INSTRUCTIONS:
            self.menu_particles.draw()
            self.ui.draw_instructions(self.frame)

        elif self.state == STATE_PLAYING:
            self._render_playing()          # Full gameplay rendering

        elif self.state == STATE_LEVEL_COMPLETE:
            self.menu_particles.draw()
            self.ui.draw_level_complete(
                self.current_level + 1, self.score, self.frame, self.best_score
            )

        elif self.state == STATE_WIN:
            self.menu_particles.draw()
            self.ui.draw_win(self.score, self.frame, self.best_score)

        elif self.state == STATE_GAME_OVER:
            self.menu_particles.draw()
            self.ui.draw_game_over(self.score, self.frame,
                                   self.retries_left,
                                   RETRY_PENALTIES[self.current_level],
                                   self.best_score)

        # ─── 4. Fade overlay (drawn ON TOP of everything) ────────────
        # During transitions, this black rectangle gradually covers
        # or reveals the screen content
        if self.fade_alpha > 0.0:
            draw_fade_overlay(self.fade_alpha)

    def _render_playing(self):
        """
        Render the gameplay screen with all game objects.

        DRAW ORDER (back to front):
            1. Play area border (rectangle outline)
            2. Walls (3D-beveled rectangles)
            3. Enemies (pulsing squares with glow)
            4. Bullets (trail + glow + white core)
            5. Player (glow + cyan triangle + aim line)
            6. Particles (explosions and sparks ON TOP)
            7. HUD bar (level name, score, bullets — always on top)
        """
        # 1. Play area border
        draw_play_area_border(PLAY_AREA)

        # 2. Walls
        for wall in self.walls:
            wall.draw()

        # 3. Enemies
        for enemy in self.enemies:
            enemy.draw()

        # 4. Bullets (with trails)
        for bullet in self.bullets:
            bullet.draw()

        # 5. Player + aim prediction line
        self.player.draw(self.walls, PLAY_AREA)

        # 6. Particles (drawn on top of gameplay objects)
        self.particles.draw()

        # 7. HUD bar (always on top of everything)
        level_name = LEVELS[self.current_level]["name"]
        self.ui.draw_hud(level_name, self.score,
                         self.player.bullets_remaining,
                         self.best_score)
