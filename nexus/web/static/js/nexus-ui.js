/**
 * Nexus UI Shared Logic
 * 
 * Contains shared controllers and utilities for Nexus web pages.
 */

/**
 * Endpoint Controller
 * Handles WebSocket events and Polling fallback for a page.
 */
class NexusPageController {
    /**
     * @param {Object} options Configuration options
     * @param {Function} options.onRefresh Callback function to refresh page data
     * @param {Function} options.onMetricUpdate Callback for metric updates (optional)
     * @param {string} options.pageName Name of the page for logging (optional)
     */
    constructor(options) {
        this.onRefresh = options.onRefresh;
        this.onMetricUpdate = options.onMetricUpdate;
        this.pageName = options.pageName || 'Page';
        this.pollingInterval = null;
        this.pollingDuration = 30000; // 30 seconds

        this.init();
    }

    init() {
        console.log(`[${this.pageName}] Controller initialized`);
        this.setupWebSocketListeners();
    }

    setupWebSocketListeners() {
        if (!window.nexusWS) {
            console.error('nexusWS not found. Make sure websocket-client.js is loaded first.');
            return;
        }

        // Handle metric updates
        window.nexusWS.on('metric_update', (data) => {
            if (this.onMetricUpdate) {
                this.onMetricUpdate(data);
            } else {
                console.log(`[${this.pageName}] Metric update received, refreshing...`);
                this.refresh();
            }
        });

        // Handle WebSocket fallback to polling
        window.nexusWS.on('fallback_to_polling', () => {
            this.enablePolling();
        });

        // Re-disable polling if WebSocket reconnects
        window.nexusWS.on('connected', () => {
            this.disablePolling();
        });
    }

    refresh() {
        if (this.onRefresh) {
            this.onRefresh();
        }
    }

    enablePolling() {
        if (!this.pollingInterval) {
            console.log(`[${this.pageName}] Polling mode enabled`);
            this.pollingInterval = setInterval(() => {
                this.refresh();
            }, this.pollingDuration);
        }
    }

    disablePolling() {
        if (this.pollingInterval) {
            console.log(`[${this.pageName}] Polling mode disabled`);
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    }
}

// Make it globally available
window.NexusPageController = NexusPageController;
