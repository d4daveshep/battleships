"""
Unit tests for gameplay context creation.

Tests verify that _create_gameplay_context() includes all necessary data
for rendering board visibility and hit feedback.
"""

from game.model import Coord, Game, GameBoard, Ship, ShipType, Orientation, GameMode
from game.player import Player, PlayerStatus
from routes.gameplay import _create_gameplay_context


class TestGameplayContext:
    """Tests for _create_gameplay_context function"""

    def test_context_includes_shots_received_data(self) -> None:
        """Test that context includes shots_received for displaying on My Ships board."""
        # Set up players
        player = Player(name="Alice", status=PlayerStatus.IN_GAME)
        opponent = Player(name="Bob", status=PlayerStatus.IN_GAME)

        # Set up game
        game = Game(player, GameMode.TWO_PLAYER, opponent)

        # Set up boards with ships
        player_board: GameBoard = game.board[player]
        opponent_board: GameBoard = game.board[opponent]

        player_board.place_ship(
            Ship(ShipType.DESTROYER), Coord.A1, Orientation.HORIZONTAL
        )
        opponent_board.place_ship(
            Ship(ShipType.CRUISER), Coord.E1, Orientation.HORIZONTAL
        )

        # Opponent fires at player's board
        player_board.receive_shots({Coord.A1, Coord.B1}, round_number=1)

        # Create context
        context = _create_gameplay_context(
            current_player=player,
            opponent=opponent,
            player_board=player_board,
            opponent_board=opponent_board,
            game_id=game.id,
            game=game,
        )

        # Assert shots_received is in context
        assert "shots_received" in context, "Context should include shots_received data"

        # Verify it contains the shot data
        shots_received = context["shots_received"]
        assert len(shots_received) == 2
        assert "A1" in shots_received
        assert "B1" in shots_received

        # Verify ShotInfo data is accessible
        assert shots_received["A1"]["round_number"] == 1
        assert shots_received["A1"]["is_hit"] is True
        assert shots_received["B1"]["is_hit"] is False

    def test_context_includes_shots_fired_with_results(self) -> None:
        """Test that context includes shots_fired enriched with hit/miss status."""
        # Set up players
        player = Player(name="Alice", status=PlayerStatus.IN_GAME)
        opponent = Player(name="Bob", status=PlayerStatus.IN_GAME)

        # Set up game
        game = Game(player, GameMode.TWO_PLAYER, opponent)

        # Set up boards with ships
        player_board: GameBoard = game.board[player]
        opponent_board: GameBoard = game.board[opponent]

        player_board.place_ship(
            Ship(ShipType.DESTROYER), Coord.A1, Orientation.HORIZONTAL
        )
        opponent_board.place_ship(
            Ship(ShipType.CRUISER), Coord.E1, Orientation.HORIZONTAL
        )

        # Player fires at opponent's board
        player_board.record_fired_shots({Coord.E1, Coord.F1}, round_number=1)
        opponent_board.receive_shots({Coord.E1, Coord.F1}, round_number=1)

        # Create context
        context = _create_gameplay_context(
            current_player=player,
            opponent=opponent,
            player_board=player_board,
            opponent_board=opponent_board,
            game_id=game.id,
            game=game,
        )

        # Assert shots_fired_results is in context
        assert "shots_fired_results" in context, (
            "Context should include shots_fired with results"
        )

        # Verify it contains the shot data with hit/miss status
        shots_fired = context["shots_fired_results"]
        assert len(shots_fired) == 2
        assert "E1" in shots_fired
        assert "F1" in shots_fired

        # E1 should be a hit (Cruiser is there)
        assert shots_fired["E1"]["round_number"] == 1
        assert shots_fired["E1"]["is_hit"] is True

        # F1 should be a miss
        assert shots_fired["F1"]["round_number"] == 1
        assert shots_fired["F1"]["is_hit"] is False

    def test_context_includes_hits_made_tracking(self) -> None:
        """Test that context includes cumulative hits made on opponent ships."""
        # Set up players
        player = Player(name="Alice", status=PlayerStatus.IN_GAME)
        opponent = Player(name="Bob", status=PlayerStatus.IN_GAME)

        # Set up game
        game = Game(player, GameMode.TWO_PLAYER, opponent)

        # Set up boards with ships
        player_board: GameBoard = game.board[player]
        opponent_board: GameBoard = game.board[opponent]

        player_board.place_ship(
            Ship(ShipType.DESTROYER), Coord.A1, Orientation.HORIZONTAL
        )
        opponent_board.place_ship(
            Ship(ShipType.CRUISER), Coord.E1, Orientation.HORIZONTAL
        )
        opponent_board.place_ship(
            Ship(ShipType.CARRIER), Coord.G1, Orientation.HORIZONTAL
        )

        # Player fires at opponent's ships across multiple rounds
        # Round 1: Hit Cruiser twice
        player_board.record_fired_shots({Coord.E1, Coord.E2}, round_number=1)
        opponent_board.receive_shots({Coord.E1, Coord.E2}, round_number=1)

        # Round 2: Hit Carrier once
        player_board.record_fired_shots({Coord.G1}, round_number=2)
        opponent_board.receive_shots({Coord.G1}, round_number=2)

        # Create context
        context = _create_gameplay_context(
            current_player=player,
            opponent=opponent,
            player_board=player_board,
            opponent_board=opponent_board,
            game_id=game.id,
            game=game,
        )

        # Assert hits_made is in context
        assert "hits_made" in context, "Context should include hits_made tracking"

        # Verify it contains cumulative hit data
        hits_made = context["hits_made"]
        assert "Cruiser" in hits_made
        assert "Carrier" in hits_made

        # Cruiser should have 2 hits from round 1
        assert len(hits_made["Cruiser"]["hits"]) == 2
        assert hits_made["Cruiser"]["is_sunk"] is False

        # Carrier should have 1 hit from round 2
        assert len(hits_made["Carrier"]["hits"]) == 1
        assert hits_made["Carrier"]["is_sunk"] is False
