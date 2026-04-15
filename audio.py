"""
audio.py — Procedural Sound System for One Shot Assassin.
=========================================================
PURPOSE:
    Generates and plays retro 8-bit sound effects.

    Instead of requiring the user to download external .wav files,
    this module GENERATES the audio files via math (sine waves,
    square waves, noise) on the first run.
    This keeps the game 100% standalone and minimal.

SOUND TYPES:
    - shoot: Fast frequency sweep down (square wave)
    - bounce: Short high-pitched ping (sine wave)
    - explosion: White noise burst (random)
    - select: Short UI blip
    - win: Arpeggio / ascending sweep
    - game_over: Descending low sweep
=========================================================
"""

import os
import math
import wave
import struct
import random
import pygame

# Dictionary holding loaded pygame.mixer.Sound objects
_sounds = {}
_initialized = False


def init():
    """
    Initialize Pygame mixer, generate sounds if missing, and load them.
    Called once when the game starts.
    """
    global _initialized
    if _initialized:
        return

    # Initialize mixer with standard audio settings
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    
    # Generate wav files into assets/sounds
    _generate_all_sounds()
    
    # Load them into memory
    sound_dir = os.path.join("assets", "sounds")
    for filename in os.listdir(sound_dir):
        if filename.endswith(".wav"):
            name = filename[:-4]
            path = os.path.join(sound_dir, filename)
            _sounds[name] = pygame.mixer.Sound(path)
            # Adjust volumes for balance
            if name == 'bounce':
                _sounds[name].set_volume(0.4)
            elif name in ('shoot', 'select'):
                _sounds[name].set_volume(0.3)
            else:
                _sounds[name].set_volume(0.6)
                
    _initialized = True


def play(name):
    """Play a loaded sound by name (e.g., 'shoot', 'bounce')."""
    if _initialized and name in _sounds:
        _sounds[name].play()


# =============================================================================
# PROCEDURAL AUDIO GENERATION MINIGAME!
# =============================================================================

def _generate_wav(filename, data, samplerate=44100):
    """Helper to pack float samples [-1.0, 1.0] into a valid 16-bit .wav file."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with wave.open(filename, 'w') as w:
        w.setnchannels(1)           # Mono
        w.setsampwidth(2)           # 16-bit
        w.setframerate(samplerate)
        
        packed = bytearray()
        for sample in data:
            # Clamp to [-1.0, 1.0] to avoid clipping artifacts
            v = int(max(-1.0, min(1.0, sample)) * 32767)
            packed.extend(struct.pack('<h', v))
        w.writeframes(packed)


def _generate_all_sounds():
    """Generate all sound effects using math equations."""
    sound_dir = os.path.join("assets", "sounds")
    os.makedirs(sound_dir, exist_ok=True)
    sr = 44100

    # 1. SHOOT (pew pew) — Fast descending square wave
    path = os.path.join(sound_dir, "shoot.wav")
    if not os.path.exists(path):
        length = int(sr * 0.15)  # 150ms
        data = []
        for i in range(length):
            t = i / sr
            freq = 1200 - 8000 * t    # Sweep from 1200Hz down
            if freq < 100: freq = 100
            env = 1.0 - (i / length)  # Fade out
            val = 1.0 if math.sin(2 * math.pi * freq * t) > 0 else -1.0
            data.append(val * env * 0.8)
        _generate_wav(path, data)

    # 2. BOUNCE (ping) — Short exponential decaying sine wave
    path = os.path.join(sound_dir, "bounce.wav")
    if not os.path.exists(path):
        length = int(sr * 0.05)  # 50ms (very short)
        data = []
        for i in range(length):
            t = i / sr
            env = math.exp(-i / (sr * 0.015))  # Sharp decay
            val = math.sin(2 * math.pi * 1000 * t)
            data.append(val * env * 0.8)
        _generate_wav(path, data)

    # 3. EXPLOSION (boom) — White noise with decay
    path = os.path.join(sound_dir, "explosion.wav")
    if not os.path.exists(path):
        length = int(sr * 0.3)  # 300ms
        data = []
        for i in range(length):
            env = 1.0 - (i / length)
            val = random.uniform(-1.0, 1.0) # White noise
            data.append(val * env * 0.8)
        _generate_wav(path, data)

    # 4. SELECT (blip) — Short interface confirmation
    path = os.path.join(sound_dir, "select.wav")
    if not os.path.exists(path):
        length = int(sr * 0.1)  # 100ms
        data = []
        for i in range(length):
            t = i / sr
            env = 1.0 - (i / length)
            val = math.sin(2 * math.pi * 600 * t)
            data.append(val * env * 0.8)
        _generate_wav(path, data)

    # 5. WIN (level up) — Ascending sweep
    path = os.path.join(sound_dir, "win.wav")
    if not os.path.exists(path):
        length = int(sr * 0.5)  # 500ms
        data = []
        for i in range(length):
            t = i / sr
            freq = 300 + 1000 * t
            env = 1.0 if i < length * 0.7 else 1.0 - ((i - length * 0.7) / (length * 0.3))
            val = math.sin(2 * math.pi * freq * t)
            data.append(val * env * 0.8)
        _generate_wav(path, data)

    # 6. GAME OVER (fail) — Slow descending low wave
    path = os.path.join(sound_dir, "game_over.wav")
    if not os.path.exists(path):
        length = int(sr * 0.8)  # 800ms
        data = []
        for i in range(length):
            t = i / sr
            freq = 250 - 200 * t
            if freq < 40: freq = 40
            env = 1.0 - (i / length)
            # Sawtooth-like wave for harsher sound
            val = math.sin(2 * math.pi * freq * t) + 0.5 * math.sin(2 * math.pi * freq * 2 * t)
            data.append(val * env * 0.8)
        _generate_wav(path, data)
