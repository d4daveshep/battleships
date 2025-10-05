## Notes on how to apply HATEOAS principles to the game play

HATEOAS = Hypermedia as the engine of application state.

To apply this principle to this game we should do the following:

1. Use a hypermedia (e.g. HTML+HTMX) to define the UI
2. The game state for the player whose turn it is should be fully represented by the hypermedia, there should be no out-of-band information required by the browser (i.e. no game rules in javascript on the client side)
3. All the actions the player could take in their turn i.e. aiming next shots should be represented by links or buttons on the UI.
4. Illegal and incomplete moves should be impossible
5. All state about the game, e.g. round number, shots available, fleet status, opponent's ships sunk etc should be represented in the HTML

This leads to some questions about the UI:

1. When entering (aiming) the shots for a round:
   - the player should be able to select these on the board, which would add the coordinates to the shots to fire list
   - the player should also be able to enter the shots as coordinates
   - the player can fire less shots that the maximum available but the UI should be prevent them from firing more shots than available
   - the player should be able to correct the shots they're aiming before submitting (firing) them
