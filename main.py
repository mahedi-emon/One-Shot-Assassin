"""
main.py — Entry point for One Shot Assassin.
=========================================================
PURPOSE:
    This is the file you run to start the game:
        python main.py

    It simply creates a Game object (which sets up the window,
    OpenGL, and all game systems) and then calls game.run()
    to enter the main loop.

WHY THIS FILE:
    Separating the entry point from the Game class keeps
    the code modular. If we wanted to add command-line
    arguments (e.g., --fullscreen, --level 2), we'd parse
    them here before passing to Game().
=========================================================
"""

# Import the Game class from game.py — it contains the entire game logic
from game import Game


def main():
    """
    Create the game instance and start the main loop.

    The Game() constructor initializes:
      - Pygame window + OpenGL context
      - All managers (text renderer, UI, particles)
      - Default state = MENU

    game.run() enters the infinite loop:
      handle_events() → update() → render() → flip()
    ...and only exits when the player quits.
    """
    game = Game()   # Initialize everything (window, OpenGL, objects)
    game.run()      # Enter the main game loop (runs until quit)


# Python convention: only run main() when this file is executed directly,
# not when it's imported by another module (e.g., during testing).
if __name__ == "__main__":
    main()
