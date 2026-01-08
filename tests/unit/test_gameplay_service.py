"""Unit tests for GameplayService - shot aiming and validation."""

import pytest
from game.model import Coord, ShipType, Ship, Orientation, GameBoard
from game.round import Round
from services.gameplay_service import GameplayService, AimShotResult


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
        result = service.aim_shot(
            game_id=game_id,
            player_id=player_id,
            coord=coord
        )
        
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
            assert result.success is True, f"Shot {i+1} should succeed"
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
        assert "limit" in result.error_message.lower() or "maximum" in result.error_message.lower()
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
