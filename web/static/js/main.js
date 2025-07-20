// Fox The Navy - Client-side JavaScript

// Notification system
class NotificationManager {
    constructor() {
        this.container = document.getElementById('notifications');
    }

    show(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        this.container.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, duration);
    }
}

const notifications = new NotificationManager();

// HTMX Event Handlers
document.addEventListener('DOMContentLoaded', function() {
    
    // Handle HTMX responses
    document.body.addEventListener('htmx:afterRequest', function(evt) {
        const response = evt.detail.xhr;
        const url = evt.detail.requestConfig.path;
        
        if (response.status === 200) {
            try {
                const data = JSON.parse(response.responseText);
                
                if (data.status === 'success') {
                    notifications.show('Action completed successfully!', 'success');
                    
                    // Handle specific endpoints
                    if (url.includes('/auto-place-ships')) {
                        // Auto-place ships completed - trigger refresh events
                        htmx.trigger('body', 'shipPlaced');
                        // Check if we need to reload to enter playing phase
                        setTimeout(() => {
                            fetch('/game/status')
                                .then(r => r.json())
                                .then(status => {
                                    if (status.phase === 'playing') {
                                        location.reload();
                                    }
                                });
                        }, 1000);
                    } else if (url.includes('/submit-shots')) {
                        // Shots submitted - trigger refresh events
                        htmx.trigger('body', 'shotsSubmitted');
                    } else if (url.includes('/place-ship')) {
                        // Single ship placed - trigger refresh events
                        htmx.trigger('body', 'shipPlaced');
                    }
                    
                } else if (data.status === 'error') {
                    notifications.show(data.message || 'An error occurred', 'error');
                }
            } catch (e) {
                // Not JSON response, probably HTML - this is normal for templates
            }
        } else {
            notifications.show(`Request failed: ${response.status}`, 'error');
        }
    });

    // Handle form submissions
    document.body.addEventListener('htmx:responseError', function(evt) {
        notifications.show('Network error occurred', 'error');
    });

    // Handle ship placement success
    document.body.addEventListener('shipPlaced', function(evt) {
        notifications.show('Ship placed successfully!', 'success');
        
        // Force refresh of player board
        const playerBoard = document.getElementById('player-board');
        const shipPlacementForm = document.getElementById('ship-placement-form');
        if (playerBoard) {
            htmx.trigger(playerBoard, 'load');
        }
        if (shipPlacementForm) {
            htmx.trigger(shipPlacementForm, 'load');
        }
    });

    // Handle shots submission
    document.body.addEventListener('shotsSubmitted', function(evt) {
        notifications.show('Shots fired!', 'success');
        
        // Force refresh of both boards
        const shipsBoard = document.getElementById('player-ships-board');
        const shotsBoard = document.getElementById('shots-fired-board');
        const roundResults = document.getElementById('round-results');
        
        if (shipsBoard) {
            htmx.trigger(shipsBoard, 'load');
        }
        if (shotsBoard) {
            htmx.trigger(shotsBoard, 'load');
        }
        if (roundResults) {
            htmx.trigger(roundResults, 'load');
        }
    });

    // Auto-refresh game state during play
    let refreshInterval;
    
    function startGameRefresh() {
        refreshInterval = setInterval(() => {
            const gameStatus = document.getElementById('game-status');
            if (gameStatus) {
                htmx.trigger(gameStatus, 'load');
            }
            
            // Refresh boards based on current phase
            const setupPhase = document.getElementById('setup-phase');
            const playingPhase = document.getElementById('playing-phase');
            
            if (setupPhase) {
                const playerBoard = document.getElementById('player-board');
                if (playerBoard) {
                    htmx.trigger(playerBoard, 'load');
                }
            }
            
            if (playingPhase) {
                const shipsBoard = document.getElementById('player-ships-board');
                const shotsBoard = document.getElementById('shots-fired-board');
                
                if (shipsBoard) htmx.trigger(shipsBoard, 'load');
                if (shotsBoard) htmx.trigger(shotsBoard, 'load');
            }
        }, 2000);
    }
    
    function stopGameRefresh() {
        if (refreshInterval) {
            clearInterval(refreshInterval);
            refreshInterval = null;
        }
    }
    
    // Start refresh when game is active
    if (document.getElementById('game-interface')) {
        startGameRefresh();
    }
    
    // Stop refresh when game ends
    document.body.addEventListener('htmx:afterSettle', function(evt) {
        if (document.getElementById('finished-phase')) {
            stopGameRefresh();
        } else if (document.getElementById('playing-phase') && !refreshInterval) {
            startGameRefresh();
        }
    });
});

// Form validation helpers
function validateShotInput(input) {
    const shots = input.split(',').map(s => s.trim()).filter(s => s);
    const shotPattern = /^[A-J]([1-9]|10)$/i;
    
    for (const shot of shots) {
        if (!shotPattern.test(shot)) {
            return { valid: false, message: `Invalid shot format: ${shot}. Use A1, B2, etc.` };
        }
    }
    
    return { valid: true, shots: shots };
}

// Enhanced shot input handling
document.body.addEventListener('input', function(evt) {
    if (evt.target.name === 'shots') {
        const input = evt.target;
        const validation = validateShotInput(input.value);
        
        // Remove any existing validation message
        const existingMsg = input.parentNode.querySelector('.validation-message');
        if (existingMsg) {
            existingMsg.remove();
        }
        
        if (input.value && !validation.valid) {
            const msg = document.createElement('div');
            msg.className = 'validation-message';
            msg.style.color = '#dc2626';
            msg.style.fontSize = '0.8rem';
            msg.style.marginTop = '0.25rem';
            msg.textContent = validation.message;
            input.parentNode.appendChild(msg);
        }
    }
});

// Board interaction helpers
function highlightValidPlacements(shipType, shipLength) {
    // This could be enhanced to show valid placement positions
    // when hovering over the board during ship placement
}

// Coordinate conversion utilities
function coordToString(row, col) {
    return String.fromCharCode(65 + row) + (col + 1);
}

function stringToCoord(coordStr) {
    const row = coordStr.charCodeAt(0) - 65;
    const col = parseInt(coordStr.substring(1)) - 1;
    return { row, col };
}

// Game state utilities
function isValidCoordinate(coordStr) {
    const pattern = /^[A-J]([1-9]|10)$/i;
    return pattern.test(coordStr);
}

// Enhanced error handling
window.addEventListener('error', function(evt) {
    console.error('Client error:', evt.error);
    notifications.show('An unexpected error occurred', 'error');
});

// Keyboard shortcuts
document.addEventListener('keydown', function(evt) {
    // ESC to close notifications
    if (evt.key === 'Escape') {
        const notifications = document.querySelectorAll('.notification');
        notifications.forEach(n => n.remove());
    }
    
    // Enter to submit forms (if focused)
    if (evt.key === 'Enter' && evt.target.tagName === 'INPUT') {
        const form = evt.target.closest('form');
        if (form) {
            evt.preventDefault();
            form.requestSubmit();
        }
    }
});

// Debug helpers (remove in production)
window.gameDebug = {
    showNotification: (msg, type) => notifications.show(msg, type),
    triggerEvent: (element, event) => htmx.trigger(element, event),
    validateShot: validateShotInput
};