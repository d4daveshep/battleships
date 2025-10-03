import asyncio
from datetime import datetime
from game.player import GameRequest, Player, PlayerStatus


class Lobby:
    def __init__(self):
        self.players: dict[str, Player] = {}
        self.game_requests: dict[str, GameRequest] = {}
        self.version: int = 0
        self.change_event: asyncio.Event = asyncio.Event()

    def add_player(self, name: str, status: PlayerStatus) -> None:
        self.players[name] = Player(name, status)
        self.version += 1
        self.change_event.set()

    def remove_player(self, name: str) -> None:
        if name in self.players:
            del self.players[name]
            self.version += 1
            self.change_event.set()
        else:
            raise ValueError(f"Player '{name}' not found in lobby")

    def clear_all_except(self, player_name: str) -> None:
        # Keep only the specified player in the lobby
        if player_name in self.players:
            player = self.players[player_name]
            self.players.clear()
            self.players[player_name] = player
        else:
            self.players.clear()

    def get_available_players(self) -> list[Player]:
        return [
            player
            for player in self.players.values()
            if player.status == PlayerStatus.AVAILABLE
        ]

    def update_player_status(self, name: str, status: PlayerStatus) -> None:
        if name not in self.players:
            raise ValueError(f"Player '{name}' not found in lobby")
        self.players[name].status = status
        self.version += 1
        self.change_event.set()

    def get_player_status(self, name: str) -> PlayerStatus:
        if name not in self.players:
            raise ValueError(f"Player '{name}' not found in lobby")
        return self.players[name].status

    def send_game_request(self, sender: str, receiver: str) -> None:
        # Validate that both players exist
        if sender not in self.players:
            raise ValueError(f"Player '{sender}' not found in lobby")
        if receiver not in self.players:
            raise ValueError(f"Player '{receiver}' not found in lobby")

        # Validate that sender is available
        if self.players[sender].status != PlayerStatus.AVAILABLE:
            raise ValueError(f"Sender {sender} is not available")

        # Validate that receiver is available
        if self.players[receiver].status != PlayerStatus.AVAILABLE:
            raise ValueError(f"Receiver {receiver} is not available")

        # Create the game request
        request = GameRequest(
            sender=sender, receiver=receiver, timestamp=datetime.now()
        )

        # Store the request
        self.game_requests[receiver] = request

        # Update player statuses
        self.players[sender].status = PlayerStatus.REQUESTING_GAME
        self.players[receiver].status = PlayerStatus.PENDING_RESPONSE
        self.version += 1
        self.change_event.set()

    def get_pending_request(self, receiver: str) -> GameRequest | None:
        return self.game_requests.get(receiver)

    def get_pending_request_by_sender(self, sender: str) -> GameRequest | None:
        for request in self.game_requests.values():
            if request.sender == sender:
                return request
        return None

    def accept_game_request(self, receiver: str) -> tuple[str, str]:
        # Check if there's a pending request
        if receiver not in self.game_requests:
            raise ValueError(f"No pending game request for {receiver}")

        request = self.game_requests[receiver]
        sender = request.sender

        # Update both players to IN_GAME
        self.players[sender].status = PlayerStatus.IN_GAME
        self.players[receiver].status = PlayerStatus.IN_GAME

        # Remove the request
        del self.game_requests[receiver]

        self.version += 1
        self.change_event.set()

        return sender, receiver

    def decline_game_request(self, receiver: str) -> str:
        # Check if there's a pending request
        if receiver not in self.game_requests:
            raise ValueError(f"No pending game request for {receiver}")

        request = self.game_requests[receiver]
        sender = request.sender

        # Return both players to AVAILABLE
        self.players[sender].status = PlayerStatus.AVAILABLE
        self.players[receiver].status = PlayerStatus.AVAILABLE

        # Remove the request
        del self.game_requests[receiver]

        self.version += 1
        self.change_event.set()

        return sender

    def get_version(self) -> int:
        """Return the current version of the lobby state"""
        return self.version

    async def wait_for_change(self, since_version: int) -> None:
        """Wait for lobby state to change from the given version.

        Args:
            since_version: The version to wait for changes from

        Returns immediately if the current version is different from since_version.
        Otherwise, waits for the change_event to be set.
        """
        # If version already changed, return immediately
        if self.get_version() != since_version:
            return

        # Clear the event for this wait cycle
        self.change_event.clear()

        # Check version again after clearing (in case it changed)
        if self.get_version() != since_version:
            return

        # Wait for the event to be set
        await self.change_event.wait()
