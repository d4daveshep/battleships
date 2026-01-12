"""Unit tests for GameplayService - shot aiming and validation."""

import pytest
from game.model import Coord, ShipType, Ship, Orientation, GameBoard
from game.round import Round
from services.gameplay_service import GameplayService, AimShotResult, CellState


def create_board_with_all_ships() -> GameBoard:
    """Helper to create a board with all 5 ships placed."""
    board = GameBoard()
    board.place_ship(Ship(ShipType.CARRIER), Coord.A1, Orientation.HORIZONTAL)
    board.place_ship(Ship(ShipType.BATTLESHIP), Coord.C1, Orientation.HORIZONTAL)
    board.place_ship(Ship(ShipType.CRUISER), Coord.E1, Orientation.HORIZONTAL)
    board.place_ship(Ship(ShipType.SUBMARINE), Coord.G1, Orientation.HORIZONTAL)
    board.place_ship(Ship(ShipType.DESTROYER), Coord.I1, Orientation.HORIZONTAL)
    return board


class TestAimShot:
    """Tests for aiming shots in a round."""

    def test_aim_shot_valid_first_shot(self) -> None:
        """Test aiming a valid shot when no shots have been aimed yet."""
        # Arrange
        service = GameplayService()
        game_id = "game123"
        player_id = "player1"
        round_number = 1
        coord = Coord.A1

        board = create_board_with_all_ships()

        # Create a round for this game
        service.create_round(game_id=game_id, round_number=round_number)
        service.register_player_board(game_id=game_id, player_id=player_id, board=board)

        # Act
        result = service.aim_shot(game_id=game_id, player_id=player_id, coord=coord)

        # Assert
        assert result.success is True
        assert result.error_message is None
        assert result.aimed_count == 1

    def test_aim_shot_multiple_shots(self) -> None:
        """Test aiming multiple shots in sequence."""
        # Arrange
        service = GameplayService()
        game_id = "game123"
        player_id = "player1"
        round_number = 1

        board = create_board_with_all_ships()

        service.create_round(game_id=game_id, round_number=round_number)
        service.register_player_board(game_id=game_id, player_id=player_id, board=board)

        # Act - aim 3 shots
        result1 = service.aim_shot(game_id=game_id, player_id=player_id, coord=Coord.A1)
        result2 = service.aim_shot(game_id=game_id, player_id=player_id, coord=Coord.B2)
        result3 = service.aim_shot(game_id=game_id, player_id=player_id, coord=Coord.C3)

        # Assert
        assert result1.success is True
        assert result1.aimed_count == 1
        assert result2.success is True
        assert result2.aimed_count == 2
        assert result3.success is True
        assert result3.aimed_count == 3

    def test_aim_shot_no_active_round(self) -> None:
        """Test aiming a shot when no round exists for the game."""
        # Arrange
        service = GameplayService()
        game_id = "game123"
        player_id = "player1"

        # Act - try to aim without creating a round
        result = service.aim_shot(game_id=game_id, player_id=player_id, coord=Coord.A1)

        # Assert
        assert result.success is False
        assert result.error_message == "No active round for this game"
        assert result.aimed_count == 0


class TestDuplicateShotValidation:
    """Tests for preventing duplicate shots in the same round."""

    def test_aim_shot_duplicate_in_same_round(self) -> None:
        """Test that aiming at the same coordinate twice in a round is rejected."""
        # Arrange
        service = GameplayService()
        game_id = "game123"
        player_id = "player1"
        round_number = 1
        coord = Coord.A1

        board = create_board_with_all_ships()

        service.create_round(game_id=game_id, round_number=round_number)
        service.register_player_board(game_id=game_id, player_id=player_id, board=board)

        # Act - aim at A1 twice
        result1 = service.aim_shot(game_id=game_id, player_id=player_id, coord=coord)
        result2 = service.aim_shot(game_id=game_id, player_id=player_id, coord=coord)

        # Assert
        assert result1.success is True
        assert result1.aimed_count == 1

        assert result2.success is False
        assert "already selected" in result2.error_message.lower()
        assert result2.aimed_count == 1  # Count doesn't increase

    def test_aim_shot_different_coords_allowed(self) -> None:
        """Test that aiming at different coordinates is allowed."""
        # Arrange
        service = GameplayService()
        game_id = "game123"
        player_id = "player1"
        round_number = 1

        board = create_board_with_all_ships()

        service.create_round(game_id=game_id, round_number=round_number)
        service.register_player_board(game_id=game_id, player_id=player_id, board=board)

        # Act - aim at different coordinates
        result1 = service.aim_shot(game_id=game_id, player_id=player_id, coord=Coord.A1)
        result2 = service.aim_shot(game_id=game_id, player_id=player_id, coord=Coord.B2)
        result3 = service.aim_shot(game_id=game_id, player_id=player_id, coord=Coord.C3)

        # Assert - all should succeed
        assert result1.success is True
        assert result2.success is True
        assert result3.success is True
        assert result3.aimed_count == 3


class TestShotLimitValidation:
    """Tests for enforcing shot limits based on unsunk ships."""

    def test_aim_shot_within_limit(self) -> None:
        """Test that aiming shots within the available limit succeeds."""
        # Arrange
        service = GameplayService()
        game_id = "game123"
        player_id = "player1"
        round_number = 1

        board = create_board_with_all_ships()

        service.create_round(game_id=game_id, round_number=round_number)
        service.register_player_board(game_id=game_id, player_id=player_id, board=board)

        # Act - aim 6 shots (the maximum available)
        results = []
        coords = [Coord.A1, Coord.B2, Coord.C3, Coord.D4, Coord.E5, Coord.F6]
        for coord in coords:
            result = service.aim_shot(game_id=game_id, player_id=player_id, coord=coord)
            results.append(result)

        # Assert - all 6 should succeed
        for i, result in enumerate(results):
            assert result.success is True, f"Shot {i + 1} should succeed"
            assert result.aimed_count == i + 1

    def test_aim_shot_exceeds_limit(self) -> None:
        """Test that aiming more shots than available is rejected."""
        # Arrange
        service = GameplayService()
        game_id = "game123"
        player_id = "player1"
        round_number = 1

        board = create_board_with_all_ships()

        service.create_round(game_id=game_id, round_number=round_number)
        service.register_player_board(game_id=game_id, player_id=player_id, board=board)

        # Act - aim 6 shots successfully, then try a 7th
        coords = [Coord.A1, Coord.B2, Coord.C3, Coord.D4, Coord.E5, Coord.F6]
        for coord in coords:
            service.aim_shot(game_id=game_id, player_id=player_id, coord=coord)

        # Try 7th shot
        result = service.aim_shot(game_id=game_id, player_id=player_id, coord=Coord.G7)

        # Assert
        assert result.success is False
        assert (
            "limit" in result.error_message.lower()
            or "maximum" in result.error_message.lower()
        )
        assert result.aimed_count == 6  # Count stays at 6

    def test_aim_shot_limit_with_fewer_ships(self) -> None:
        """Test shot limit with only 2 ships (3 shots available)."""
        # Arrange
        service = GameplayService()
        game_id = "game123"
        player_id = "player1"
        round_number = 1

        # Create a board with only Carrier (2 shots) and Destroyer (1 shot) = 3 total
        board = GameBoard()
        board.place_ship(Ship(ShipType.CARRIER), Coord.A1, Orientation.HORIZONTAL)
        board.place_ship(Ship(ShipType.DESTROYER), Coord.C1, Orientation.HORIZONTAL)

        service.create_round(game_id=game_id, round_number=round_number)
        service.register_player_board(game_id=game_id, player_id=player_id, board=board)

        # Act - aim 3 shots successfully
        result1 = service.aim_shot(game_id=game_id, player_id=player_id, coord=Coord.A1)
        result2 = service.aim_shot(game_id=game_id, player_id=player_id, coord=Coord.B2)
        result3 = service.aim_shot(game_id=game_id, player_id=player_id, coord=Coord.C3)

        # Try 4th shot
        result4 = service.aim_shot(game_id=game_id, player_id=player_id, coord=Coord.D4)

        # Assert
        assert result1.success is True
        assert result2.success is True
        assert result3.success is True
        assert result4.success is False
        assert result4.aimed_count == 3


class TestCellState:
    """Tests for determining cell state on the Shots Fired board."""

    def test_get_cell_state_available(self) -> None:
        """Test that an unmarked cell with shots available is AVAILABLE."""
        # Arrange
        service = GameplayService()
        game_id = "game123"
        player_id = "player1"
        round_number = 1

        board = create_board_with_all_ships()

        service.create_round(game_id=game_id, round_number=round_number)
        service.register_player_board(game_id=game_id, player_id=player_id, board=board)

        # Act
        state = service.get_cell_state(
            game_id=game_id, player_id=player_id, coord=Coord.A1
        )

        # Assert
        assert state == CellState.AVAILABLE

    def test_get_cell_state_aimed(self) -> None:
        """Test that a cell with an aimed shot is AIMED."""
        # Arrange
        service = GameplayService()
        game_id = "game123"
        player_id = "player1"
        round_number = 1

        board = create_board_with_all_ships()

        service.create_round(game_id=game_id, round_number=round_number)
        service.register_player_board(game_id=game_id, player_id=player_id, board=board)

        # Aim at A1
        service.aim_shot(game_id=game_id, player_id=player_id, coord=Coord.A1)

        # Act
        state = service.get_cell_state(
            game_id=game_id, player_id=player_id, coord=Coord.A1
        )

        # Assert
        assert state == CellState.AIMED

    def test_get_cell_state_unavailable_limit_reached(self) -> None:
        """Test that cells are UNAVAILABLE when shot limit is reached."""
        # Arrange
        service = GameplayService()
        game_id = "game123"
        player_id = "player1"
        round_number = 1

        board = create_board_with_all_ships()

        service.create_round(game_id=game_id, round_number=round_number)
        service.register_player_board(game_id=game_id, player_id=player_id, board=board)

        # Aim 6 shots (the maximum)
        coords = [Coord.A1, Coord.B2, Coord.C3, Coord.D4, Coord.E5, Coord.F6]
        for coord in coords:
            service.aim_shot(game_id=game_id, player_id=player_id, coord=coord)

        # Act - check a cell that hasn't been aimed at
        state = service.get_cell_state(
            game_id=game_id, player_id=player_id, coord=Coord.G7
        )

        # Assert
        assert state == CellState.UNAVAILABLE

    def test_get_cell_state_fired(self) -> None:
        """Test that a previously fired cell is FIRED."""
        # Arrange
        service = GameplayService()
        game_id = "game123"
        player_id = "player1"
        round_number = 1

        board = create_board_with_all_ships()

        service.create_round(game_id=game_id, round_number=round_number)
        service.register_player_board(game_id=game_id, player_id=player_id, board=board)

        # Simulate a shot being fired in a previous round
        # For now, we'll manually add to the fired shots tracking
        # (This will be updated when we implement round resolution)
        if not hasattr(service, "fired_shots"):
            service.fired_shots = {}  # game_id -> player_id -> coord -> round_number

        if game_id not in service.fired_shots:
            service.fired_shots[game_id] = {}
        if player_id not in service.fired_shots[game_id]:
            service.fired_shots[game_id][player_id] = {}

        service.fired_shots[game_id][player_id][Coord.A1] = 1  # Fired in round 1

        # Act
        state = service.get_cell_state(
            game_id=game_id, player_id=player_id, coord=Coord.A1
        )

        # Assert
        assert state == CellState.FIRED

    def test_get_cell_state_fired_takes_precedence_over_aimed(self) -> None:
        """Test that FIRED state takes precedence if a cell was fired in a previous round."""
        # Arrange
        service = GameplayService()
        game_id = "game123"
        player_id = "player1"
        round_number = 2  # Round 2

        board = create_board_with_all_ships()

        service.create_round(game_id=game_id, round_number=round_number)
        service.register_player_board(game_id=game_id, player_id=player_id, board=board)

        # Simulate A1 being fired in round 1
        if not hasattr(service, "fired_shots"):
            service.fired_shots = {}
        if game_id not in service.fired_shots:
            service.fired_shots[game_id] = {}
        if player_id not in service.fired_shots[game_id]:
            service.fired_shots[game_id][player_id] = {}

        service.fired_shots[game_id][player_id][Coord.A1] = 1

        # Act - check state (even though we could theoretically aim at it again)
        state = service.get_cell_state(
            game_id=game_id, player_id=player_id, coord=Coord.A1
        )

        # Assert
        assert state == CellState.FIRED


class TestFireShots:
    """Tests for firing shots and entering waiting state."""

    def test_fire_shots_first_player_enters_waiting_state(self) -> None:
        """Test that when the first player fires, they enter a waiting state."""
        # Arrange
        service = GameplayService()
        game_id = "game123"
        player1_id = "player1"
        player2_id = "player2"
        round_number = 1

        board1 = create_board_with_all_ships()
        board2 = create_board_with_all_ships()

        service.create_round(game_id=game_id, round_number=round_number)
        service.register_player_board(game_id=game_id, player_id=player1_id, board=board1)
        service.register_player_board(game_id=game_id, player_id=player2_id, board=board2)

        # Aim some shots for player1
        service.aim_shot(game_id=game_id, player_id=player1_id, coord=Coord.A1)
        service.aim_shot(game_id=game_id, player_id=player1_id, coord=Coord.B2)

        # Act - player1 fires their shots
        result = service.fire_shots(game_id=game_id, player_id=player1_id)

        # Assert
        assert result.success is True
        assert result.waiting_for_opponent is True
        assert "waiting" in result.message.lower() or "fired" in result.message.lower()

        # Verify player1 is in submitted_players
        round_obj = service.active_rounds[game_id]
        assert player1_id in round_obj.submitted_players

        # Verify aimed shots are still in the round (not cleared yet)
        assert len(round_obj.aimed_shots[player1_id]) == 2

    def test_fire_shots_no_shots_aimed_fails(self) -> None:
        """Test that firing without aiming any shots fails."""
        # Arrange
        service = GameplayService()
        game_id = "game123"
        player_id = "player1"
        round_number = 1

        board = create_board_with_all_ships()

        service.create_round(game_id=game_id, round_number=round_number)
        service.register_player_board(game_id=game_id, player_id=player_id, board=board)

        # Act - try to fire without aiming
        result = service.fire_shots(game_id=game_id, player_id=player_id)

        # Assert
        assert result.success is False
        assert "no shots" in result.message.lower()

    def test_fire_shots_already_submitted_fails(self) -> None:
        """Test that firing shots twice in the same round fails."""
        # Arrange
        service = GameplayService()
        game_id = "game123"
        player_id = "player1"
        round_number = 1

        board = create_board_with_all_ships()

        service.create_round(game_id=game_id, round_number=round_number)
        service.register_player_board(game_id=game_id, player_id=player_id, board=board)

        # Aim and fire shots
        service.aim_shot(game_id=game_id, player_id=player_id, coord=Coord.A1)
        service.fire_shots(game_id=game_id, player_id=player_id)

        # Act - try to fire again
        result = service.fire_shots(game_id=game_id, player_id=player_id)

        # Assert
        assert result.success is False
        assert "already" in result.message.lower() or "submitted" in result.message.lower()


class TestRoundResolution:
    """Tests for resolving rounds when both players fire."""

    def test_resolve_round_when_both_players_fire(self) -> None:
        """Test that round is resolved when both players have fired."""
        # Arrange
        service = GameplayService()
        game_id = "game123"
        player1_id = "player1"
        player2_id = "player2"
        round_number = 1

        board1 = create_board_with_all_ships()
        board2 = create_board_with_all_ships()

        service.create_round(game_id=game_id, round_number=round_number)
        service.register_player_board(game_id=game_id, player_id=player1_id, board=board1)
        service.register_player_board(game_id=game_id, player_id=player2_id, board=board2)

        # Player 1 aims and fires
        service.aim_shot(game_id=game_id, player_id=player1_id, coord=Coord.A1)
        service.aim_shot(game_id=game_id, player_id=player1_id, coord=Coord.B2)
        service.fire_shots(game_id=game_id, player_id=player1_id)

        # Player 2 aims and fires
        service.aim_shot(game_id=game_id, player_id=player2_id, coord=Coord.C3)
        service.aim_shot(game_id=game_id, player_id=player2_id, coord=Coord.D4)
        result = service.fire_shots(game_id=game_id, player_id=player2_id)

        # Assert - second player should trigger resolution
        assert result.success is True
        assert result.waiting_for_opponent is False  # Round is resolved, not waiting

        # Verify round is marked as resolved
        round_obj = service.active_rounds[game_id]
        assert round_obj.is_resolved is True
        assert round_obj.result is not None

    def test_resolve_round_creates_round_result(self) -> None:
        """Test that resolving a round creates a RoundResult object."""
        # Arrange
        service = GameplayService()
        game_id = "game123"
        player1_id = "player1"
        player2_id = "player2"
        round_number = 1

        board1 = create_board_with_all_ships()
        board2 = create_board_with_all_ships()

        service.create_round(game_id=game_id, round_number=round_number)
        service.register_player_board(game_id=game_id, player_id=player1_id, board=board1)
        service.register_player_board(game_id=game_id, player_id=player2_id, board=board2)

        # Both players aim and fire
        service.aim_shot(game_id=game_id, player_id=player1_id, coord=Coord.A1)
        service.fire_shots(game_id=game_id, player_id=player1_id)

        service.aim_shot(game_id=game_id, player_id=player2_id, coord=Coord.B2)
        service.fire_shots(game_id=game_id, player_id=player2_id)

        # Assert - check RoundResult was created
        round_obj = service.active_rounds[game_id]
        assert round_obj.result is not None
        assert round_obj.result.round_number == round_number
        assert player1_id in round_obj.result.player_shots
        assert player2_id in round_obj.result.player_shots
        assert len(round_obj.result.player_shots[player1_id]) == 1
        assert len(round_obj.result.player_shots[player2_id]) == 1


class TestHitDetection:
    """Tests for detecting hits on opponent ships."""

    def test_detect_hits_on_opponent_ships(self) -> None:
        """Test that hits are correctly detected when shots hit opponent ships."""
        # Arrange
        service = GameplayService()
        game_id = "game123"
        player1_id = "player1"
        player2_id = "player2"
        round_number = 1

        # Create boards with ships at known positions
        board1 = GameBoard()
        board1.place_ship(Ship(ShipType.CARRIER), Coord.A1, Orientation.HORIZONTAL)  # A1-E1
        board1.place_ship(Ship(ShipType.DESTROYER), Coord.C3, Orientation.HORIZONTAL)  # C3-D3

        board2 = GameBoard()
        board2.place_ship(Ship(ShipType.BATTLESHIP), Coord.B2, Orientation.HORIZONTAL)  # B2-E2
        board2.place_ship(Ship(ShipType.CRUISER), Coord.F5, Orientation.VERTICAL)  # F5-F7

        service.create_round(game_id=game_id, round_number=round_number)
        service.register_player_board(game_id=game_id, player_id=player1_id, board=board1)
        service.register_player_board(game_id=game_id, player_id=player2_id, board=board2)

        # Player 1 aims at player 2's ships (B2 hits Battleship, F5 hits Cruiser, A1 misses)
        service.aim_shot(game_id=game_id, player_id=player1_id, coord=Coord.B2)
        service.aim_shot(game_id=game_id, player_id=player1_id, coord=Coord.F5)
        service.aim_shot(game_id=game_id, player_id=player1_id, coord=Coord.A1)  # Miss
        service.fire_shots(game_id=game_id, player_id=player1_id)

        # Player 2 aims at player 1's ships (A1 hits Carrier, C3 hits Destroyer, J10 misses)
        service.aim_shot(game_id=game_id, player_id=player2_id, coord=Coord.A1)
        service.aim_shot(game_id=game_id, player_id=player2_id, coord=Coord.C3)
        service.aim_shot(game_id=game_id, player_id=player2_id, coord=Coord.J10)  # Miss
        service.fire_shots(game_id=game_id, player_id=player2_id)

        # Assert - check hits were detected
        round_obj = service.active_rounds[game_id]
        result = round_obj.result

        # Player 1 should have 2 hits (B2 on Battleship, F5 on Cruiser)
        assert player1_id in result.hits_made
        assert len(result.hits_made[player1_id]) == 2
        hit_coords_p1 = {hit.coord for hit in result.hits_made[player1_id]}
        assert Coord.B2 in hit_coords_p1
        assert Coord.F5 in hit_coords_p1

        # Player 2 should have 2 hits (A1 on Carrier, C3 on Destroyer)
        assert player2_id in result.hits_made
        assert len(result.hits_made[player2_id]) == 2
        hit_coords_p2 = {hit.coord for hit in result.hits_made[player2_id]}
        assert Coord.A1 in hit_coords_p2
        assert Coord.C3 in hit_coords_p2

    def test_detect_hits_includes_ship_type(self) -> None:
        """Test that hit results include the correct ship type."""
        # Arrange
        service = GameplayService()
        game_id = "game123"
        player1_id = "player1"
        player2_id = "player2"
        round_number = 1

        board1 = GameBoard()
        board1.place_ship(Ship(ShipType.CARRIER), Coord.A1, Orientation.HORIZONTAL)

        board2 = GameBoard()
        board2.place_ship(Ship(ShipType.DESTROYER), Coord.B2, Orientation.HORIZONTAL)

        service.create_round(game_id=game_id, round_number=round_number)
        service.register_player_board(game_id=game_id, player_id=player1_id, board=board1)
        service.register_player_board(game_id=game_id, player_id=player2_id, board=board2)

        # Player 1 hits player 2's Destroyer at B2
        service.aim_shot(game_id=game_id, player_id=player1_id, coord=Coord.B2)
        service.fire_shots(game_id=game_id, player_id=player1_id)

        # Player 2 hits player 1's Carrier at A1
        service.aim_shot(game_id=game_id, player_id=player2_id, coord=Coord.A1)
        service.fire_shots(game_id=game_id, player_id=player2_id)

        # Assert - check ship types
        round_obj = service.active_rounds[game_id]
        result = round_obj.result

        # Player 1 hit Destroyer
        p1_hit = result.hits_made[player1_id][0]
        assert p1_hit.ship_type == ShipType.DESTROYER
        assert p1_hit.coord == Coord.B2

        # Player 2 hit Carrier
        p2_hit = result.hits_made[player2_id][0]
        assert p2_hit.ship_type == ShipType.CARRIER
        assert p2_hit.coord == Coord.A1

    def test_detect_hits_no_hits_when_all_miss(self) -> None:
        """Test that no hits are detected when all shots miss."""
        # Arrange
        service = GameplayService()
        game_id = "game123"
        player1_id = "player1"
        player2_id = "player2"
        round_number = 1

        board1 = GameBoard()
        board1.place_ship(Ship(ShipType.CARRIER), Coord.A1, Orientation.HORIZONTAL)

        board2 = GameBoard()
        board2.place_ship(Ship(ShipType.DESTROYER), Coord.B2, Orientation.HORIZONTAL)

        service.create_round(game_id=game_id, round_number=round_number)
        service.register_player_board(game_id=game_id, player_id=player1_id, board=board1)
        service.register_player_board(game_id=game_id, player_id=player2_id, board=board2)

        # Both players aim at empty cells
        service.aim_shot(game_id=game_id, player_id=player1_id, coord=Coord.J10)
        service.fire_shots(game_id=game_id, player_id=player1_id)

        service.aim_shot(game_id=game_id, player_id=player2_id, coord=Coord.J9)
        service.fire_shots(game_id=game_id, player_id=player2_id)

        # Assert - no hits
        round_obj = service.active_rounds[game_id]
        result = round_obj.result

        assert len(result.hits_made[player1_id]) == 0
        assert len(result.hits_made[player2_id]) == 0
