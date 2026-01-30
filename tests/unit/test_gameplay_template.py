"""
Unit tests for gameplay template rendering with shot markers.

Tests verify that shot data is properly rendered in the template.
"""

from jinja2 import Environment, FileSystemLoader
from pathlib import Path


class TestGameplayTemplateRendering:
    """Tests for gameplay.html template rendering"""

    def test_my_ships_board_shows_received_shot_round_numbers(self) -> None:
        """Test that My Ships board displays round numbers for received shots."""
        # Set up Jinja2 environment
        template_dir = Path(__file__).parent.parent.parent / "templates"
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        template = env.get_template("gameplay.html")

        # Create context with shots_received data
        context = {
            "player_name": "Alice",
            "opponent_name": "Bob",
            "game_id": "test-game-123",
            "player_board": {
                "ships": {"Destroyer": {"cells": ["A1", "A2"], "code": "D"}}
            },
            "opponent_board": {"ships": {}},
            "round_number": 2,
            "shots_available": 6,
            "aimed_count": 0,
            "aimed_coordinates": [],
            "status_message": None,
            "last_round_hits": {},
            "shots_received": {
                "A1": {"round_number": 1, "is_hit": True},
                "B1": {"round_number": 1, "is_hit": False},
            },
            "shots_fired_results": {},
        }

        # Render template
        html = template.render(**context)

        # Verify A1 cell has round number marker
        assert 'data-testid="player-cell-A1"' in html

        # A1 should have data-round attribute or show round number in cell
        # Extract the A1 cell content
        import re

        a1_match = re.search(r'data-testid="player-cell-A1"[^>]*>([^<]*)<', html)
        assert a1_match, "Should find A1 cell"

        # The cell should show round number or have data-round attribute
        assert 'data-round="1"' in html or "1" in a1_match.group(1), (
            f"A1 cell should show round number 1, but got: {a1_match.group(0)}"
        )

        # B1 should also show round number
        b1_match = re.search(r'data-testid="player-cell-B1"[^>]*>([^<]*)<', html)
        assert b1_match, "Should find B1 cell"
        assert 'data-round="1"' in html or "1" in b1_match.group(1), (
            f"B1 cell should show round number 1"
        )

    def test_shots_fired_board_shows_hit_miss_markers(self) -> None:
        """Test that Shots Fired board displays hit/miss results."""
        # Set up Jinja2 environment
        template_dir = Path(__file__).parent.parent.parent / "templates"
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        template = env.get_template("gameplay.html")

        # Create context with shots_fired_results data
        context = {
            "player_name": "Alice",
            "opponent_name": "Bob",
            "game_id": "test-game-123",
            "player_board": {"ships": {}},
            "opponent_board": {"ships": {}},
            "round_number": 2,
            "shots_available": 6,
            "aimed_count": 0,
            "aimed_coordinates": [],
            "status_message": None,
            "last_round_hits": {},
            "shots_received": {},
            "shots_fired_results": {
                "E1": {"round_number": 1, "is_hit": True},
                "F1": {"round_number": 1, "is_hit": False},
            },
        }

        # Render template
        html = template.render(**context)

        # Verify E1 shows as hit with round number
        assert 'data-testid="opponent-cell-E1"' in html

        # Extract E1 cell content
        import re

        e1_match = re.search(r'data-testid="opponent-cell-E1"[^>]*>([^<]*)<', html)
        assert e1_match, "Should find E1 cell"

        # E1 should show round number (it's a hit)
        assert 'data-round="1"' in html or "1" in e1_match.group(1), (
            f"E1 cell should show round number 1 (hit), but got: {e1_match.group(0)}"
        )

        # Verify F1 shows as miss with round number
        f1_match = re.search(r'data-testid="opponent-cell-F1"[^>]*>([^<]*)<', html)
        assert f1_match, "Should find F1 cell"
        assert 'data-round="1"' in html or "1" in f1_match.group(1), (
            f"F1 cell should show round number 1 (miss)"
        )

    def test_hits_made_area_displays_ship_tracking_grid(self) -> None:
        """Test that Hits Made area shows ship-level hit tracking with round numbers."""
        # Set up Jinja2 environment
        template_dir = Path(__file__).parent.parent.parent / "templates"
        env = Environment(loader=FileSystemLoader(str(template_dir)))
        template = env.get_template("gameplay.html")

        # Create context with hits_made data
        context = {
            "player_name": "Alice",
            "opponent_name": "Bob",
            "game_id": "test-game-123",
            "player_board": {"ships": {}},
            "opponent_board": {"ships": {}},
            "round_number": 3,
            "shots_available": 6,
            "aimed_count": 0,
            "aimed_coordinates": [],
            "status_message": None,
            "last_round_hits": {},
            "shots_received": {},
            "shots_fired_results": {},
            "hits_made": {
                "Carrier": {
                    "hits": [
                        {"coord": "A1", "round": 1},
                        {"coord": "A2", "round": 2},
                    ],
                    "is_sunk": False,
                },
                "Destroyer": {
                    "hits": [
                        {"coord": "E1", "round": 1},
                        {"coord": "E2", "round": 1},
                    ],
                    "is_sunk": True,
                },
                "Battleship": {"hits": [], "is_sunk": False},
                "Cruiser": {"hits": [], "is_sunk": False},
                "Submarine": {"hits": [], "is_sunk": False},
            },
        }

        # Render template
        html = template.render(**context)

        # Verify hits-made-area exists
        assert 'data-testid="hits-made-area"' in html

        # Verify Carrier shows 2 hits with round numbers
        assert 'data-testid="hit-track-carrier"' in html

        # Verify Destroyer shows as SUNK
        assert 'data-testid="hit-track-destroyer"' in html
        assert "SUNK" in html

        # Extract and verify round numbers are displayed
        import re

        # Look for the whole ship-hit-row div
        carrier_section = re.search(
            r'<div class="ship-hit-row" data-testid="hit-track-carrier">.*?</div>\s*</div>',
            html,
            re.DOTALL,
        )
        assert carrier_section, "Should find Carrier section"
        carrier_html = carrier_section.group(0)

        # Should show round numbers 1 and 2
        assert "1" in carrier_html, f"Carrier section should show round 1"
        assert "2" in carrier_html, f"Carrier section should show round 2"
