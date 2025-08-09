from game.player import PlayerNum
from game.game_controller import Game, GameController


# Component test to game model objects in game play
def test_game_play():
    # Alice and Bob decide to start a game
    game: Game = GameController.create_game(player_1_name="Alice", player_2_name="Bob")

    # Alice and Bob place thier ships on their game boards
    GameController.place_ships(
        game=game, player_num=PlayerNum.PLAYER_1, ships=ship_layout_1
    )
    # When they are both done placing ships the game is ready to start
    # Alice and Bob both have 5 shots available to fire
    # They both aim (place) their shots and fire them at each others ships
    # This completes the round and thei game reports the results of the round
    # The game informs them of any ships they've hit with their shots in this round
    # The game informs them on any hits on their ships and if any have been sunk
    # The game informs then of the number of shots available for the next round
    #
