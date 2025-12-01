/**
 * WebSocket Client for Real-time Updates
 *
 * Connects to the Core WebSocket endpoint and handles real-time events.
 * Falls back to polling if WebSocket connection fails.
 */

class NexusWebSocket {
    constructor() {
        this.ws = null;
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 2000; // Start with 2 seconds
        this.pingInterval = null;
        this.listeners = new Map();

        this.connect();
    }

    connect() {
        // Determine WebSocket protocol (ws or wss)
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/api/ws`;

        console.log('[WebSocket] Connecting to:', wsUrl);

        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('[WebSocket] Connected');
                this.connected = true;
                this.reconnectAttempts = 0;
                this.reconnectDelay = 2000;

                // Start ping interval to keep connection alive
                this.startPing();

                // Emit connection event
                this.emit('connected', {});
            };

            this.ws.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    console.log('[WebSocket] Message:', message.type);

                    // Emit event to listeners
                    this.emit(message.type, message.data);
                } catch (error) {
                    console.error('[WebSocket] Failed to parse message:', error);
                }
            };

            this.ws.onerror = (error) => {
                console.error('[WebSocket] Error:', error);
                this.emit('error', { error });
            };

            this.ws.onclose = () => {
                console.log('[WebSocket] Disconnected');
                this.connected = false;
                this.stopPing();

                // Emit disconnection event
                this.emit('disconnected', {});

                // Attempt to reconnect
                this.reconnect();
            };

        } catch (error) {
            console.error('[WebSocket] Connection error:', error);
            this.reconnect();
        }
    }

    reconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.warn('[WebSocket] Max reconnection attempts reached. Falling back to polling.');
            this.emit('fallback_to_polling', {});
            return;
        }

        this.reconnectAttempts++;
        const delay = this.reconnectDelay * this.reconnectAttempts;

        console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

        setTimeout(() => {
            this.connect();
        }, delay);
    }

    startPing() {
        // Send ping every 30 seconds to keep connection alive
        this.pingInterval = setInterval(() => {
            if (this.connected && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send('ping');
            }
        }, 30000);
    }

    stopPing() {
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
            this.pingInterval = null;
        }
    }

    on(eventType, callback) {
        if (!this.listeners.has(eventType)) {
            this.listeners.set(eventType, []);
        }
        this.listeners.get(eventType).push(callback);
    }

    off(eventType, callback) {
        if (this.listeners.has(eventType)) {
            const callbacks = this.listeners.get(eventType);
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        }
    }

    emit(eventType, data) {
        if (this.listeners.has(eventType)) {
            this.listeners.get(eventType).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`[WebSocket] Error in listener for ${eventType}:`, error);
                }
            });
        }
    }

    send(message) {
        if (this.connected && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        } else {
            console.warn('[WebSocket] Not connected. Message not sent:', message);
        }
    }

    disconnect() {
        this.stopPing();
        if (this.ws) {
            this.ws.close();
        }
    }
}

// Create global WebSocket instance
window.nexusWS = new NexusWebSocket();

// Log connection status
window.nexusWS.on('connected', () => {
    console.log('[Nexus] Real-time updates enabled');
});

window.nexusWS.on('disconnected', () => {
    console.log('[Nexus] Real-time updates disconnected');
});

window.nexusWS.on('fallback_to_polling', () => {
    console.log('[Nexus] Falling back to polling mode');
    // Pages should handle this event and re-enable their polling intervals
});

console.log('[WebSocket Client] Loaded successfully');
