"""Unit tests for Round domain model."""

import pytest
from game.round import Round, Shot, HitResult, RoundResult
from game.model import Coord, ShipType


class TestRoundInitialization:
    """Test Round class initialization."""

    def test_round_initialization(self) -> None:
        """Test that a Round can be initialized with basic attributes."""
        round_obj = Round(round_number=1, game_id="game123")

        assert round_obj.round_number == 1
        assert round_obj.game_id == "game123"
        assert round_obj.aimed_shots == {}
        assert round_obj.submitted_players == set()
        assert round_obj.is_resolved is False
        assert round_obj.result is None

    def test_round_initialization_with_different_values(self) -> None:
        """Test Round initialization with different round numbers."""
        round_obj = Round(round_number=5, game_id="another_game")

        assert round_obj.round_number == 5
        assert round_obj.game_id == "another_game"


class TestShotDataclass:
    """Test Shot dataclass."""

    def test_shot_creation(self) -> None:
        """Test that a Shot can be created with required attributes."""
        shot = Shot(coord=Coord.A1, round_number=1, player_id="p1")

        assert shot.coord == Coord.A1
        assert shot.round_number == 1
        assert shot.player_id == "p1"

    def test_shot_with_different_coordinates(self) -> None:
        """Test Shot with various coordinates."""
        shot = Shot(coord=Coord.J10, round_number=3, player_id="player_2")

        assert shot.coord == Coord.J10
        assert shot.round_number == 3
        assert shot.player_id == "player_2"


class TestHitResultDataclass:
    """Test HitResult dataclass."""

    def test_hit_result_creation(self) -> None:
        """Test that a HitResult can be created."""
        hit = HitResult(
            ship_type=ShipType.CARRIER, coord=Coord.A1, is_sinking_hit=False
        )

        assert hit.ship_type == ShipType.CARRIER
        assert hit.coord == Coord.A1
        assert hit.is_sinking_hit is False

    def test_hit_result_sinking_hit(self) -> None:
        """Test HitResult with sinking hit."""
        hit = HitResult(
            ship_type=ShipType.DESTROYER, coord=Coord.B2, is_sinking_hit=True
        )

        assert hit.ship_type == ShipType.DESTROYER
        assert hit.is_sinking_hit is True


class TestRoundResultDataclass:
    """Test RoundResult dataclass."""

    def test_round_result_creation_minimal(self) -> None:
        """Test RoundResult with minimal attributes."""
        result = RoundResult(round_number=1)

        assert result.round_number == 1
        assert result.player_shots == {}
        assert result.hits_made == {}
        assert result.ships_sunk == {}
        assert result.game_over is False
        assert result.winner_id is None
        assert result.is_draw is False

    def test_round_result_with_shots(self) -> None:
        """Test RoundResult with player shots."""
        shot1 = Shot(coord=Coord.A1, round_number=1, player_id="p1")
        shot2 = Shot(coord=Coord.B2, round_number=1, player_id="p1")

        result = RoundResult(round_number=1, player_shots={"p1": [shot1, shot2]})

        assert len(result.player_shots["p1"]) == 2
        assert result.player_shots["p1"][0].coord == Coord.A1

    def test_round_result_with_hits(self) -> None:
        """Test RoundResult with hits made."""
        hit = HitResult(
            ship_type=ShipType.CARRIER, coord=Coord.A1, is_sinking_hit=False
        )

        result = RoundResult(round_number=1, hits_made={"p1": [hit]})

        assert len(result.hits_made["p1"]) == 1
        assert result.hits_made["p1"][0].ship_type == ShipType.CARRIER

    def test_round_result_game_over_win(self) -> None:
        """Test RoundResult with game over and winner."""
        result = RoundResult(
            round_number=5, game_over=True, winner_id="p1", is_draw=False
        )

        assert result.game_over is True
        assert result.winner_id == "p1"
        assert result.is_draw is False

    def test_round_result_game_over_draw(self) -> None:
        """Test RoundResult with draw condition."""
        result = RoundResult(
            round_number=10, game_over=True, winner_id=None, is_draw=True
        )

        assert result.game_over is True
        assert result.winner_id is None
        assert result.is_draw is True
