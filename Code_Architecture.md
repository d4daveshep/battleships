# Code Architecture

## Languages and Libraries

Use the following languages and libraries

- Python 3.13 for all game and UI logic
- HTMX and Ninja2 templates for the HTML UI. No handwritten javascript please.
- Rich library for the terminal interface.
- FastAPI for the API layer and Uvicorn for the HTTP / REST server
- If any data needs to be persisted then use a human readable text format e.g. JSON or similar suitable format.

## Application Architecture

Implement a clean API layer for the game logic and flow, independent of the UI layer.
Two human players can play via HTML interface, or one of the players can use a local terminal interface.
When playing against a computer opponent, either a HTML or terminal interface can be used.
This should be specified on game server startup.
The game server only needs to host one game at a time.
Game state should be persisted after each round and games should be stored in individual files, with date time and player names in the filenames, for later analysis.
Clearly separate the computer player strategy for selecting where to fire shots. This can be random at first and more complex strategies added later.

## Player Authentication

Players need to enter a name, defaults of Player 1, Player 2, Computer should be used.

## User Interfaces

It should be possible to select where shots are fired via the mouse or via the keyboard using alphanumeric characters.
Enter key or a submit button should send the players selected shots to the server.
It should be possible for a player to abandon a game. This will cancel the game and be recorded in the game state.
The UI should prevent a player from making illegal or incomplete moves. E.g. firing more or less than the available shots, firing into grid locations that have already been fired upon,

### Web interface

Implement a web HTML interface for players using either local or remote machine.
Use HATEOAS principles (via HTMX) for avoiding managing the game state in the HTML UI.
Web interface players only get updated once all of their shots have been entered and submitted.

### Terminal interface

Implement a terminal interface for a player using the local machine.
The terminal interface should can connect via direct Python imports.

## Network Discovery

When the game server starts up it should output the connections details for connecting via web/HTML and via local terminal. E.g. IP address, URL, port

## Deployment

I'd like to package the game application into a single Docker container that allows a local terminal interface for a local player and a HTML interface for any remote players on the same network.

## Python project management

Use uv for package and dependency management
