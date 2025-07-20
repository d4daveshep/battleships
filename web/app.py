"""
FastAPI web application for Fox The Navy game.
"""

import uuid
from typing import Dict, Optional
from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from game.models import Coordinate, ShipType, Direction
from game.player import Player
from game.game_state import GameState, GamePhase
from game.computer_player import create_computer_player

app = FastAPI(title="Fox The Navy", description="Naval Battle Game")

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key="fox-the-navy-secret-key-change-in-production")

# Mount static files
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Templates with custom filters
templates = Jinja2Templates(directory="web/templates")

# Add custom filters and functions
def chr_filter(n):
    """Convert number to character"""
    return chr(n)

def find_ship_at_position(player, row, col):
    """Find ship at given position"""
    for ship in player.board.ships:
        for pos in ship.positions:
            if pos.row == row and pos.col == col:
                return ship
    return None

def find_shot_received_at_position(player, row, col):
    """Find shot received at given position"""
    for shot_coord, round_num in player.board.shots_received.items():
        if shot_coord.row == row and shot_coord.col == col:
            return round_num
    return None

def find_shot_fired_at_position(player, row, col):
    """Find shot fired at given position"""
    for shot_coord, round_num in player.board.shots_fired.items():
        if shot_coord.row == row and shot_coord.col == col:
            return round_num
    return None

def find_player_ship_by_type(player, ship_type):
    """Find player's ship by ship type"""
    for ship in player.board.ships:
        if ship.ship_type == ship_type:
            return ship
    return None

# Register filters and functions
templates.env.filters['chr'] = chr_filter
templates.env.globals['find_ship_at_position'] = find_ship_at_position
templates.env.globals['find_shot_received_at_position'] = find_shot_received_at_position  
templates.env.globals['find_shot_fired_at_position'] = find_shot_fired_at_position
templates.env.globals['find_player_ship_by_type'] = find_player_ship_by_type

# In-memory game storage (use Redis/database in production)
games: Dict[str, GameState] = {}


class GameManager:
    """Manages game sessions and state"""
    
    @staticmethod
    def get_game_id(request: Request) -> str:
        """Get or create game ID for session"""
        if "game_id" not in request.session:
            request.session["game_id"] = str(uuid.uuid4())
        return request.session["game_id"]
    
    @staticmethod
    def get_game(request: Request) -> Optional[GameState]:
        """Get game state for session"""
        game_id = GameManager.get_game_id(request)
        return games.get(game_id)
    
    @staticmethod
    def create_game(request: Request, player1_name: str, player2_name: str, vs_computer: bool = True) -> GameState:
        """Create new game for session"""
        game_id = GameManager.get_game_id(request)
        game = GameState(player1_name, player2_name, player2_is_computer=vs_computer)
        games[game_id] = game
        return game
    
    @staticmethod
    def delete_game(request: Request):
        """Delete game for session"""
        game_id = GameManager.get_game_id(request)
        if game_id in games:
            del games[game_id]
        if "game_id" in request.session:
            del request.session["game_id"]


def get_game_or_404(request: Request) -> GameState:
    """Dependency to get game or raise 404"""
    game = GameManager.get_game(request)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main game page"""
    game = GameManager.get_game(request)
    return templates.TemplateResponse("index.html", {"request": request, "game": game})


@app.post("/game/new")
async def new_game(
    request: Request, 
    player1_name: str = Form(...), 
    player2_name: str = Form(default="Computer"),
    vs_computer: bool = Form(default=True)
):
    """Create a new game"""
    GameManager.delete_game(request)  # Clear any existing game
    game = GameManager.create_game(request, player1_name, player2_name, vs_computer)
    return JSONResponse({"status": "success", "game_id": GameManager.get_game_id(request)})


@app.get("/game/status")
async def game_status(request: Request, game: GameState = Depends(get_game_or_404)):
    """Get current game status"""
    return {
        "phase": game.phase.value,
        "current_round": game.current_round,
        "player1": {
            "name": game.player1.name,
            "shots_available": game.player1.get_available_shots(),
            "ships_placed": len(game.player1.board.ships) == len(ShipType)
        },
        "player2": {
            "name": game.player2.name,
            "shots_available": game.player2.get_available_shots(),
            "ships_placed": len(game.player2.board.ships) == len(ShipType)
        },
        "winner": game.winner.name if game.winner else None
    }


@app.get("/game/board/{player_name}")
async def get_board(request: Request, player_name: str, game: GameState = Depends(get_game_or_404)):
    """Get board state for a player"""
    if player_name == game.player1.name:
        player = game.player1
    elif player_name == game.player2.name:
        player = game.player2
    else:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Return board data as HTML template
    return templates.TemplateResponse(
        "components/game_board.html", 
        {
            "request": request,
            "player": player,
            "show_ships": True,
            "show_shots_fired": False
        }
    )


@app.get("/game/shots-fired/{player_name}")
async def get_shots_fired_board(request: Request, player_name: str, game: GameState = Depends(get_game_or_404)):
    """Get shots fired board for a player"""
    if player_name == game.player1.name:
        player = game.player1
    elif player_name == game.player2.name:
        player = game.player2
    else:
        raise HTTPException(status_code=404, detail="Player not found")
    
    return templates.TemplateResponse(
        "components/shots_board.html",
        {
            "request": request, 
            "player": player
        }
    )


@app.get("/game/hits-made/{player_name}")
async def get_hits_made(request: Request, player_name: str, game: GameState = Depends(get_game_or_404)):
    """Get hits made on opponent ships for a player"""
    if player_name == game.player1.name:
        player = game.player1
    elif player_name == game.player2.name:
        player = game.player2
    else:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Import ShipType here to avoid circular imports
    from game.models import ShipType
    
    return templates.TemplateResponse(
        "components/hits_made.html",
        {
            "request": request,
            "player": player,
            "ship_types": list(ShipType)
        }
    )


@app.get("/game/fleet-status/{player_name}")
async def get_fleet_status(request: Request, player_name: str, game: GameState = Depends(get_game_or_404)):
    """Get fleet status for a player"""
    if player_name == game.player1.name:
        player = game.player1
    elif player_name == game.player2.name:
        player = game.player2
    else:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Import ShipType here to avoid circular imports
    from game.models import ShipType
    
    return templates.TemplateResponse(
        "components/fleet_status.html",
        {
            "request": request,
            "player": player,
            "ship_types": list(ShipType)
        }
    )


@app.post("/game/place-ship")
async def place_ship(
    request: Request,
    ship_type: str = Form(...),
    row: int = Form(...),
    col: int = Form(...),
    direction: str = Form(...),
    game: GameState = Depends(get_game_or_404)
):
    """Place a ship for the current player"""
    try:
        # Parse ship type
        ship_type_enum = ShipType[ship_type.upper()]
        
        # Parse direction
        direction_enum = Direction[direction.upper()]
        
        # Create coordinate
        coord = Coordinate(row, col)
        
        # Place ship for player 1 (assuming human player for now)
        success = game.player1.place_ship(ship_type_enum, coord, direction_enum)
        
        if success:
            # Check if all ships are placed
            if len(game.player1.board.ships) == len(ShipType):
                # Start game if ready
                if not game.player2.is_computer or len(game.player2.board.ships) == len(ShipType):
                    game.start_game()
                else:
                    # Auto-place computer ships
                    success = game.start_game()
                    if not success:
                        return JSONResponse({"status": "error", "message": "Failed to auto-place computer ships"})
            
            return JSONResponse({"status": "success"})
        else:
            return JSONResponse({"status": "error", "message": "Invalid ship placement"})
            
    except (KeyError, ValueError) as e:
        return JSONResponse({"status": "error", "message": f"Invalid parameters: {e}"})


@app.post("/game/auto-place-ships")
async def auto_place_ships(request: Request, game: GameState = Depends(get_game_or_404)):
    """Auto-place all ships for current player"""
    temp_player = Player(game.player1.name, is_computer=True)
    success = temp_player.auto_place_ships()
    
    if success:
        # Copy ships to actual player
        game.player1.board.ships = temp_player.board.ships
        
        # Start game
        game.start_game()
        return JSONResponse({"status": "success"})
    else:
        return JSONResponse({"status": "error", "message": "Failed to auto-place ships"})


@app.post("/game/submit-shots")
async def submit_shots(
    request: Request,
    shots: str = Form(...),
    game: GameState = Depends(get_game_or_404)
):
    """Submit shots for current player"""
    try:
        # Parse shots (format: "A1,B2,C3")
        shot_coords = []
        for shot_str in shots.split(","):
            shot_str = shot_str.strip()
            if shot_str:
                # Parse coordinate (e.g., "A1")
                row = ord(shot_str[0].upper()) - ord('A')
                col = int(shot_str[1:]) - 1
                shot_coords.append(Coordinate(row, col))
        
        # Validate shot count
        expected_shots = game.player1.get_available_shots()
        if len(shot_coords) != expected_shots:
            return JSONResponse({
                "status": "error", 
                "message": f"Must fire exactly {expected_shots} shots"
            })
        
        # Submit shots
        success = game.submit_shots(game.player1.name, shot_coords)
        
        if success:
            # Handle computer turn if needed
            if game.player2.is_computer and not game.is_player_turn_complete(game.player2.name):
                # Simple computer AI
                available_shots = game.player2.get_available_shots()
                if available_shots > 0:
                    import random
                    available_positions = []
                    for row in range(10):
                        for col in range(10):
                            coord = Coordinate(row, col)
                            if coord not in game.player2.board.shots_fired:
                                available_positions.append(coord)
                    
                    computer_shots = random.sample(
                        available_positions, 
                        min(available_shots, len(available_positions))
                    )
                    game.submit_shots(game.player2.name, computer_shots)
            
            return JSONResponse({"status": "success"})
        else:
            return JSONResponse({"status": "error", "message": "Failed to submit shots"})
            
    except (ValueError, IndexError) as e:
        return JSONResponse({"status": "error", "message": f"Invalid shot format: {e}"})


@app.get("/game/round-results")
async def get_round_results(request: Request, game: GameState = Depends(get_game_or_404)):
    """Get results of the last round"""
    if not game.round_history:
        return JSONResponse({"status": "no_rounds"})
    
    round_result = game.round_history[-1]
    return templates.TemplateResponse(
        "components/round_results.html",
        {
            "request": request,
            "round_result": round_result,
            "game": game
        }
    )


@app.get("/game/shot-controls")
async def shot_controls(request: Request, game: GameState = Depends(get_game_or_404)):
    """Get shot controls component"""
    return templates.TemplateResponse(
        "components/shot_controls.html",
        {
            "request": request,
            "game": game
        }
    )


@app.get("/game/ship-placement")
async def ship_placement_form(request: Request, game: GameState = Depends(get_game_or_404)):
    """Get ship placement form"""
    # Get next ship to place
    placed_ships = {ship.ship_type for ship in game.player1.board.ships}
    remaining_ships = [ship_type for ship_type in ShipType if ship_type not in placed_ships]
    
    if not remaining_ships:
        return JSONResponse({"status": "all_placed"})
    
    return templates.TemplateResponse(
        "components/ship_placement.html",
        {
            "request": request,
            "next_ship": remaining_ships[0],
            "player": game.player1,
            "remaining_count": len(remaining_ships)
        }
    )


@app.delete("/game")
async def delete_game(request: Request):
    """Delete current game"""
    GameManager.delete_game(request)
    return JSONResponse({"status": "success"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)