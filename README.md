# 🎯 One Shot Assassin

A **2D strategy shooting puzzle game** built with **Python**, **Pygame**, and **PyOpenGL**.

The player has a **limited number of bullets** and must eliminate all enemies using
**ricochet/bounce mechanics**. Think carefully — every shot counts!

---

## 🛠️ Setup & Installation

### 1. Create Virtual Environment

```powershell
python -m venv venv
```

### 2. Activate Virtual Environment

```powershell
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Windows (CMD)
.\venv\Scripts\activate.bat
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

> **Dependencies explained:**
> | Package | Purpose |
> | --- | --- |
> | `pygame` | Window management, input handling, font rendering |
> | `PyOpenGL` | Hardware-accelerated OpenGL rendering (glow effects, gradients, 3D shapes) |
> | `PyOpenGL-accelerate` | Optional C-optimized extensions for better PyOpenGL performance |

---

## 🎮 How to Run

```powershell
python main.py
```

The game window (900×700) opens with the main menu.

---

## 🕹️ Controls

| Key               | Action                     |
| ----------------- | -------------------------- |
| **← / →**         | Rotate aim direction       |
| **SPACE**          | Fire bullet                |
| **R**              | Restart game               |
| **I**              | Instructions (from menu)   |
| **ENTER**          | Start game / Next level    |
| **ESC**            | Return to menu / Quit      |

---

## 📖 Game Rules

1. You have a **limited number of bullets** per level.
2. Bullets **bounce off walls and screen edges** — use ricochets to reach hidden enemies!
3. A single bullet can **hit multiple enemies** as it passes through them (multi-kill).
4. **Destroy all enemies** to complete the level.
5. If you run out of bullets with enemies remaining — **Game Over**.
6. An **aim prediction line** shows where your bullet will go, including bounce points.

---

## 📊 Scoring System

| Event                  | Points   |
| ---------------------- | -------- |
| Enemy destroyed        | **+10**  |
| Bullet fired           | **-2**   |
| Level completed        | **+50**  |

---

## 🗺️ Levels

| Level | Name            | Enemies | Bullets | Walls | Challenge                              |
| ----- | --------------- | ------- | ------- | ----- | -------------------------------------- |
| 1     | Warm Up         | 3       | 3       | 0     | Direct shots — tutorial                |
| 2     | Ricochet        | 4       | 3       | 2     | Must bounce bullets to hit targets     |
| 3     | Moving Targets  | 5       | 4       | 3     | Moving enemies + complex wall layout   |

---

## 📁 Project Structure

```
One Shot Assassin/
├── main.py            # Entry point — creates Game and runs main loop
├── game.py            # Game controller — state machine, main loop, fade transitions
├── settings.py        # All constants — colors, physics, sizes, game states
├── renderer.py        # OpenGL rendering — shapes, glow, gradients, text pipeline
├── player.py          # Player class — aim rotation, bullet firing, raycasting
├── bullet.py          # Bullet class — ricochet physics, AABB collision, trail
├── enemy.py           # Enemy class — static & moving types, pulsing glow
├── wall.py            # Wall class — collision rectangles with 3D bevel rendering
├── level.py           # Level definitions — data-driven (3 levels)
├── particles.py       # Particle system — explosions, sparks, ambient effects
├── ui.py              # UI screens — menu, instructions, HUD, win/lose screens
├── requirements.txt   # Python package dependencies
└── README.md          # This file
```

---

## 🧠 Technical Highlights (Viva Points)

### OpenGL Rendering
- **Orthographic 2D projection** via `glOrtho()` — y-axis goes downward (matching Pygame)
- **Additive blending** (`GL_SRC_ALPHA, GL_ONE`) for neon glow effects
- **Per-vertex color gradients** on OpenGL primitives for 3D depth illusion
- **GL_TRIANGLE_FAN** for circles, **GL_QUADS** for rectangles

### Text Rendering Pipeline
- Pygame font engine renders text onto a Surface (bitmap)
- Surface is converted to RGBA bytes
- RGBA bytes are uploaded to an OpenGL texture via `glTexImage2D()`
- Texture is drawn as a textured quad at the desired position
- Textures are **cached** to avoid re-uploading every frame

### Ricochet Physics
- **Velocity reversal** on axis-aligned collision
- **Minimum-overlap method** determines which wall face was hit
- Bullets have **6 max bounces** before being removed
- **Pass-through** on enemies enables multi-kills

### Aim Prediction (Raycasting)
- Real-time parametric ray-line intersection
- Formula: `t = (surface_position - ray_origin) / ray_direction`
- Shows predicted bounce path with **fading dotted lines**
- Bounce point markers at each reflection

### State Machine Architecture
- 6 states: `MENU → INSTRUCTIONS → PLAYING → LEVEL_COMPLETE → WIN / GAME_OVER`
- Clean separation of input handling, update logic, and rendering per state
- **Smooth fade transitions** between all screens

### Particle System
- Explosion bursts (20 particles) on enemy destruction
- Spark effects (8 particles) on wall bounces
- Ambient floating particles on menu screens
- `__slots__` optimization for memory efficiency
- Lifetime-based fading with **drag deceleration** (0.97×/frame)

### Visual Effects
- **Radial gradients** for dramatic backlighting
- **Animated crosshair** decoration (rotating reticle)
- **Pulsing glow** on enemies (sin wave animation)
- **Blinking text** for interactive prompts
- **Gradient divider lines** fading from center to edges
- **3D beveled rectangles** for walls and enemies

### Code Architecture
- **13 files** with clear single-responsibility separation
- **Data-driven levels** — add new levels by adding a dictionary
- **No external assets** — all visuals are generated by code using OpenGL

---

## ⚙️ System Requirements

- **Python** 3.10 or higher
- **OpenGL** compatible graphics (any modern GPU)
- **OS:** Windows 10/11 (tested)

---

## 👥 Team

Developed for the **Computer Graphics Course**
Department of Computer Science & Engineering
**Daffodil International University**, 2026

---

## 📜 License

Educational project — free to use and modify.
