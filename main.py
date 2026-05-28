"""Entry point for the Rat Swat Game."""

import os
import warnings


def main() -> None:
    """Start the game loop."""
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    warnings.filterwarnings(
        "ignore",
        message="pkg_resources is deprecated as an API.*",
        category=UserWarning,
    )

    from game import Game

    game = Game()
    game.run()


if __name__ == "__main__":
    main()
