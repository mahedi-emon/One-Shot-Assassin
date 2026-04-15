"""
level.py — Level definitions for One Shot Assassin.
=========================================================
PURPOSE:
    Defines all game levels as a list of dictionaries.
    Each dictionary contains everything needed to build a level:
      - Player starting position and bullet count
      - Enemy positions, types, and movement patterns
      - Wall positions and dimensions

WHY DATA-DRIVEN:
    Levels are pure data (no code logic). This means:
      - Easy to add/modify levels without touching game logic
      - Easy to explain in a viva ("we just add a new dict")
      - The game.py _load_level() reads this data and creates objects

LEVEL DESIGN PHILOSOPHY:
    Level 1: Tutorial — direct shots, no walls, easy targets
    Level 2: Ricochet — walls block direct paths, must bounce bullets
    Level 3: Moving Targets — enemies move + complex wall layout

COORDINATE SYSTEM:
    (0, 0) = top-left of window
    x increases rightward, y increases downward
    Play area starts at y=60 (below HUD) and ends at y=690
=========================================================
"""

# Each level is a dictionary with these keys:
#   "name"       — Display name shown in the HUD
#   "bullets"    — Number of bullets the player gets
#   "player_pos" — (x, y) tuple where player starts (bottom-center typically)
#   "enemies"    — List of enemy dicts: {x, y, type, axis, range, speed}
#   "walls"      — List of wall dicts: {x, y, w, h}

LEVELS = [
    # =================================================================
    # LEVEL 1: "Warm Up" — Direct line of sight, no obstacles
    # =================================================================
    # Purpose: Teach the player how aiming and shooting works.
    # 3 enemies spread across the top, player at bottom-center with 3 bullets.
    # No walls — the player can hit all targets with straight shots.
    {
        "name": "Level 1 — Warm Up",
        "bullets": 3,                          # 3 bullets for 3 enemies (no margin for error)
        "player_pos": (450, 650),               # Bottom-center of the play area
        "enemies": [
            {"x": 200, "y": 150, "type": "static"},    # Left target
            {"x": 450, "y": 100, "type": "static"},    # Center target (directly above player)
            {"x": 700, "y": 150, "type": "static"},    # Right target
        ],
        "walls": [],    # No walls in the tutorial level
    },

    # =================================================================
    # LEVEL 2: "Ricochet" — Must bounce bullets off walls
    # =================================================================
    # Purpose: Teach the ricochet mechanic — direct shots are blocked.
    # Two horizontal walls create barriers. The player must angle shots
    # to bounce off screen edges and reach enemies behind walls.
    # 4 enemies, 3 bullets — must use ricochet efficiently.
    {
        "name": "Level 2 — Ricochet",
        "bullets": 3,                          # Only 3 bullets for 4 enemies (multi-kills needed)
        "player_pos": (450, 650),
        "enemies": [
            {"x": 150, "y": 120, "type": "static"},    # Top-left (behind wall)
            {"x": 400, "y": 200, "type": "static"},    # Mid-left
            {"x": 600, "y": 120, "type": "static"},    # Top-right (behind wall)
            {"x": 750, "y": 300, "type": "static"},    # Right side
        ],
        "walls": [
            # Horizontal wall on the left — blocks direct path to top-left enemy
            {"x": 100, "y": 280, "w": 250, "h": 18},
            # Horizontal wall on the right — blocks direct path to top-right enemy
            {"x": 550, "y": 280, "w": 250, "h": 18},
        ],
    },

    # =================================================================
    # LEVEL 3: "Moving Targets" — Moving enemies + complex walls
    # =================================================================
    # Purpose: Full challenge — combines everything learned.
    # 3 walls create a maze-like layout. 2 enemies move back and forth.
    # Player must time shots to hit moving targets through ricochet paths.
    # 5 enemies, 4 bullets — requires multi-kills and precision timing.
    {
        "name": "Level 3 — Moving Targets",
        "bullets": 4,                          # 4 bullets for 5 enemies
        "player_pos": (450, 650),
        "enemies": [
            {"x": 200, "y": 100, "type": "static"},    # Top-left (stationary)
            {"x": 700, "y": 100, "type": "static"},    # Top-right (stationary)
            {"x": 450, "y": 200, "type": "static"},    # Center (stationary)
            # Moving enemy: patrols horizontally between x=150 and x=400
            {
                "x": 250, "y": 350, "type": "moving",
                "axis": "x",                    # Moves along x-axis (left-right)
                "range": (150, 400),            # Bounces between x=150 and x=400
                "speed": 2,                     # 2 pixels per frame
            },
            # Moving enemy: patrols horizontally between x=500 and x=750
            {
                "x": 650, "y": 350, "type": "moving",
                "axis": "x",
                "range": (500, 750),
                "speed": 3,                     # Faster than the other moving enemy
            },
        ],
        "walls": [
            # Vertical wall in the center — splits the play area
            {"x": 440, "y": 250, "w": 18, "h": 150},
            # Horizontal wall on the left — shields the moving enemy
            {"x": 120, "y": 450, "w": 200, "h": 18},
            # Horizontal wall on the right — shields the other moving enemy
            {"x": 580, "y": 450, "w": 200, "h": 18},
        ],
    },
]
