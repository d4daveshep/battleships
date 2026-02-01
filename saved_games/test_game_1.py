import json


def build_object_graph() -> dict:
    game: dict = {"game_id": "test_game_1", "game_type": "two_player"}

    game["players"] = {"player_1": "Alison", "player_2": "David"}

    ship_layout: dict = {
        "player_1": [
            {
                "ship_type": "carrier",
                "coordinates": [
                    "G4",
                    "G5",
                    "G6",
                    "G7",
                    "G8",
                ],
            },
            {
                "ship_type": "battleship",
                "coordinates": [
                    "B3",
                    "C3",
                    "D3",
                    "E3",
                ],
            },
            {
                "ship_type": "submarine",
                "coordinates": [
                    "I3",
                    "I4",
                    "I5",
                ],
            },
            {
                "ship_type": "destroyer",
                "coordinates": [
                    "C7",
                    "B8",
                ],
            },
        ],
        "player_2": [
            {
                "ship_type": "carrier",
                "coordinates": [
                    "F1",
                    "E2",
                    "D3",
                    "C4",
                    "B5",
                ],
            },
            {
                "ship_type": "battleship",
                "coordinates": [
                    "E6",
                    "E7",
                    "E8",
                    "E9",
                ],
            },
            {
                "ship_type": "submarine",
                "coordinates": [
                    "G4",
                    "H4",
                    "I4",
                ],
            },
            {
                "ship_type": "destroyer",
                "coordinates": [
                    "H8",
                    "I9",
                ],
            },
        ],
    }
    game["ship_placements"] = ship_layout

    round_1: dict = {}
    round_1["shots_available"] = {"player_1": 5, "player_2": 5}
    round_1["shots_fired"]

    game["rounds"] = [{"round_num": 1, "round_data": round_1}]
    return game


if __name__ == "__main__":
    json_string = json.dumps(build_object_graph(), indent=2)
    print(json_string)
