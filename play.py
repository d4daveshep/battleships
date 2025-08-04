#!/usr/bin/env python3
"""
Main entry point for playing Fox The Navy game via Terminal User Interface.
"""

from tui.game_controller import TUIGameController


def main():
    """Start the Fox The Navy TUI game"""
    controller = TUIGameController()
    controller.run()


if __name__ == "__main__":
    main()