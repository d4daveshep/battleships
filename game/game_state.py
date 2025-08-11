from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import json
from pathlib import Path

from .models import Coordinate, ShipType
from .player import Player


class GamePhase(Enum): SETUP = "setup"
    PLAYING = "playing"
    FINISHED = "finished"
    ABANDONED = "abandoned"


class GameResult(Enum):
    PLAYER1_WINS = "player1_wins"
    PLAYER2_WINS = "player2_wins"
    DRAW = "draw"
    ABANDONED = "abandoned"


@dataclass
class RoundResult:
    round_number: int
    player1_shots: List[Coordinate]
    player2_shots: List[Coordinate]
    player1_hits: Dict[ShipType, int]  # ship_type -> number of hits made
    player2_hits: Dict[ShipType, int]
    ships_sunk_this_round: List[Tuple[str, ShipType]]  # (player_name, ship_type)


class GameState:
    def __init__(self, player1_name: str = "Player 1", player2_name: str = "Player 2", 
                 player2_is_computer: bool = False):
        self.game_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.created_at = datetime.now()
        
        self.player1 = Player(player1_name, is_computer=False)
        self.player2 = Player(player2_name, is_computer=player2_is_computer)
        
        self.current_round = 0
        self.phase = GamePhase.SETUP
        self.result: Optional[GameResult] = None
        self.winner: Optional[Player] = None
        
        self.round_history: List[RoundResult] = []
        
        # Track pending shots for current round
        self.pending_player1_shots: List[Coordinate] = []
        self.pending_player2_shots: List[Coordinate] = []
        self.player1_shots_submitted = False
        self.player2_shots_submitted = False
    
    def start_game(self) -> bool:
        """Start the game if both players have placed all ships"""
        # Auto-place ships for computer players if they haven't been placed yet
        if self.player2.is_computer and not self.player2.has_all_ships_placed():
            if not self.player2.auto_place_ships():
                return False
        
        if not (self.player1.has_all_ships_placed() and self.player2.has_all_ships_placed()):
            return False
        
        self.phase = GamePhase.PLAYING
        self.current_round = 1
        return True
    
    def submit_shots(self, player_name: str, shots: List[Coordinate]) -> bool:
        """Submit shots for a player in the current round"""
        if self.phase != GamePhase.PLAYING:
            raise ValueError("Game is not in playing phase")
        
        player = self.get_player_by_name(player_name)
        if not player:
            raise ValueError(f"Player {player_name} not found")
        
        if len(shots) != player.get_available_shots():
            raise ValueError(f"Must fire exactly {player.get_available_shots()} shots")
        
        # Validate shots haven't been fired before
        for shot in shots:
            if shot in player.board.shots_fired:
                raise ValueError(f"Already fired at {shot.to_string()}")
        
        if player == self.player1:
            if self.player1_shots_submitted:
                raise ValueError("Player 1 has already submitted shots this round")
            self.pending_player1_shots = shots
            self.player1_shots_submitted = True
        else:
            if self.player2_shots_submitted:
                raise ValueError("Player 2 has already submitted shots this round")
            self.pending_player2_shots = shots
            self.player2_shots_submitted = True
        
        # Process round if both players have submitted
        if self.player1_shots_submitted and self.player2_shots_submitted:
            self._process_round()
        
        return True
    
    def _process_round(self) -> None:
        """Process the current round with both players' shots"""
        # Record shots fired
        self.player1.fire_shots(self.pending_player1_shots, self.current_round)
        self.player2.fire_shots(self.pending_player2_shots, self.current_round)
        
        # Process shots received and track hits
        player1_hits_made = {}  # ShipType -> hit count
        player2_hits_made = {}
        ships_sunk_this_round = []
        
        # Player 1's shots hit Player 2's ships
        hit_ships = self.player2.receive_shots(self.pending_player1_shots, self.current_round)
        for ship in hit_ships:
            ship_type = ship.ship_type
            player1_hits_made[ship_type] = player1_hits_made.get(ship_type, 0) + 1
            
            # Check if ship was just sunk
            if ship.is_sunk and ship_type not in self.player1.opponent_ships_sunk:
                ships_sunk_this_round.append((self.player2.name, ship_type))
                self.player1.record_opponent_ship_sunk(ship_type)
        
        # Player 2's shots hit Player 1's ships
        hit_ships = self.player1.receive_shots(self.pending_player2_shots, self.current_round)
        for ship in hit_ships:
            ship_type = ship.ship_type
            player2_hits_made[ship_type] = player2_hits_made.get(ship_type, 0) + 1
            
            # Check if ship was just sunk
            if ship.is_sunk and ship_type not in self.player2.opponent_ships_sunk:
                ships_sunk_this_round.append((self.player1.name, ship_type))
                self.player2.record_opponent_ship_sunk(ship_type)
        
        # Record hits made by each player
        self.player1.record_hits_made(player1_hits_made, self.current_round)
        self.player2.record_hits_made(player2_hits_made, self.current_round)
        
        # Create round result
        round_result = RoundResult(
            round_number=self.current_round,
            player1_shots=self.pending_player1_shots.copy(),
            player2_shots=self.pending_player2_shots.copy(),
            player1_hits=player1_hits_made,
            player2_hits=player2_hits_made,
            ships_sunk_this_round=ships_sunk_this_round
        )
        self.round_history.append(round_result)
        
        # Check for game end conditions
        player1_defeated = self.player1.is_defeated()
        player2_defeated = self.player2.is_defeated()
        
        if player1_defeated and player2_defeated:
            self._end_game(GameResult.DRAW)
        elif player1_defeated:
            self._end_game(GameResult.PLAYER2_WINS, self.player2)
        elif player2_defeated:
            self._end_game(GameResult.PLAYER1_WINS, self.player1)
        else:
            # Continue to next round
            self._start_next_round()
    
    def _start_next_round(self) -> None:
        """Prepare for the next round"""
        self.current_round += 1
        self.pending_player1_shots = []
        self.pending_player2_shots = []
        self.player1_shots_submitted = False
        self.player2_shots_submitted = False
    
    def _end_game(self, result: GameResult, winner: Optional[Player] = None) -> None:
        """End the game with the specified result"""
        self.phase = GamePhase.FINISHED
        self.result = result
        self.winner = winner
        self.save_game()
    
    def abandon_game(self) -> None:
        """Abandon the current game"""
        self.phase = GamePhase.ABANDONED
        self.result = GameResult.ABANDONED
        self.save_game()
    
    def get_player_by_name(self, name: str) -> Optional[Player]:
        """Get player by name"""
        if self.player1.name == name:
            return self.player1
        elif self.player2.name == name:
            return self.player2
        return None
    
    def get_opponent(self, player: Player) -> Player:
        """Get the opponent of the given player"""
        return self.player2 if player == self.player1 else self.player1
    
    def is_player_turn_complete(self, player_name: str) -> bool:
        """Check if player has completed their turn in current round"""
        if player_name == self.player1.name:
            return self.player1_shots_submitted
        elif player_name == self.player2.name:
            return self.player2_shots_submitted
        return False
    
    def save_game(self) -> None:
        """Save game state to JSON file"""
        game_data = self.to_dict()
        
        # Create games directory if it doesn't exist
        games_dir = Path("games")
        games_dir.mkdir(exist_ok=True)
        
        filename = f"{self.game_id}_{self.player1.name}_{self.player2.name}.json"
        filepath = games_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(game_data, f, indent=2, default=str)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert game state to dictionary for serialization"""
        return {
            "game_id": self.game_id,
            "created_at": self.created_at.isoformat(),
            "player1_name": self.player1.name,
            "player2_name": self.player2.name,
            "player2_is_computer": self.player2.is_computer,
            "current_round": self.current_round,
            "phase": self.phase.value,
            "result": self.result.value if self.result else None,
            "winner": self.winner.name if self.winner else None,
            "round_history": [
                {
                    "round_number": r.round_number,
                    "player1_shots": [shot.to_string() for shot in r.player1_shots],
                    "player2_shots": [shot.to_string() for shot in r.player2_shots],
                    "player1_hits": {st.value[0]: count for st, count in r.player1_hits.items()},
                    "player2_hits": {st.value[0]: count for st, count in r.player2_hits.items()},
                    "ships_sunk": [(player, st.value[0]) for player, st in r.ships_sunk_this_round]
                }
                for r in self.round_history
            ]
        }
