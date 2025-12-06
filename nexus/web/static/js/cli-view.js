/**
 * CLI View JavaScript
 *
 * Tracks UI actions and displays equivalent CLI commands + API calls.
 */

// Global function to add actions to CLI view
window.addCliAction = function (cliCommand, apiCall, response, summary) {
    const action = {
        id: `action-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        timestamp: new Date().toISOString(),
        cliCommand: cliCommand,
        apiCall: apiCall,
        response: response,
        summary: summary || ''
    };

    // Wait for Alpine.js to be ready
    const addAction = () => {
        if (window.Alpine) {
            // Find the root Alpine component
            const body = document.querySelector('body');
            if (body && body._x_dataStack && body._x_dataStack.length > 0) {
                const data = body._x_dataStack[0];
                data.cliActions.push(action);

                // Keep only last 50 actions
                if (data.cliActions.length > 50) {
                    data.cliActions = data.cliActions.slice(-50);
                }

                // Auto-scroll to bottom
                setTimeout(() => {
                    const cliContent = document.getElementById('cli-view-content');
                    if (cliContent) {
                        cliContent.scrollTop = 0; // Scroll to top (newest at top)
                    }
                }, 100);
            }
        } else {
            // Retry if Alpine not ready yet
            setTimeout(addAction, 50);
        }
    };

    addAction();
    console.log('[CLI View]', action);
};

// Intercept fetch requests to log API calls
(function () {
    const originalFetch = window.fetch;

    window.fetch = async function (...args) {
        const [url, options = {}] = args;
        const method = options.method || 'GET';
        const startTime = performance.now();

        try {
            const response = await originalFetch(...args);
            const endTime = performance.now();
            const timing = Math.round(endTime - startTime);

            // Clone response to read body
            const clonedResponse = response.clone();
            let body = null;
            try {
                body = await clonedResponse.json();
            } catch (e) {
                // Not JSON, skip
            }

            // Try to determine CLI command from URL
            const cliCommand = inferCliCommand(method, url, options.body);

            if (cliCommand) {
                addCliAction(
                    cliCommand,
                    {
                        method: method,
                        endpoint: url.replace(window.location.origin, ''),
                        headers: options.headers || {},
                        body: options.body ? parseJsonSafe(options.body) : null
                    },
                    {
                        status: response.status,
                        statusText: response.statusText,
                        timing: timing,
                        body: body
                    },
                    generateSummary(method, url, body)
                );
            }

            return response;
        } catch (error) {
            const endTime = performance.now();
            const timing = Math.round(endTime - startTime);

            const cliCommand = inferCliCommand(method, url, options.body);
            if (cliCommand) {
                addCliAction(
                    cliCommand,
                    {
                        method: method,
                        endpoint: url.replace(window.location.origin, ''),
                        headers: options.headers || {},
                        body: options.body ? parseJsonSafe(options.body) : null
                    },
                    {
                        status: 0,
                        statusText: 'Network Error',
                        timing: timing,
                        body: { error: error.message }
                    },
                    `Error: ${error.message}`
                );
            }

            throw error;
        }
    };
})();

// Infer CLI command from API call
function inferCliCommand(method, url, body) {
    const path = url.replace(window.location.origin, '').replace('/api', '');

    // Nodes endpoints
    if (path.match(/^\/nodes$/)) {
        if (method === 'GET') return 'nexus node list';
        if (method === 'POST') return 'nexus node register';
    }
    if (path.match(/^\/nodes\/([a-f0-9-]+)$/)) {
        const nodeId = path.match(/^\/nodes\/([a-f0-9-]+)$/)[1];
        if (method === 'GET') return `nexus node get ${nodeId}`;
        if (method === 'PUT') return `nexus node update ${nodeId}`;
        if (method === 'DELETE') return `nexus node delete ${nodeId}`;
    }
    if (path.match(/^\/nodes\/([a-f0-9-]+)\/health$/)) {
        const nodeId = path.match(/^\/nodes\/([a-f0-9-]+)\/health$/)[1];
        return `nexus metrics health ${nodeId}`;
    }

    // Jobs endpoints
    if (path.match(/^\/jobs$/)) {
        if (method === 'GET') return 'nexus job list';
        if (method === 'POST' && body) {
            try {
                const data = JSON.parse(body);
                return `nexus job submit --node ${data.node_id} --type ${data.type}`;
            } catch (e) {
                return 'nexus job submit';
            }
        }
    }
    if (path.match(/^\/jobs\/([a-f0-9-]+)$/)) {
        const jobId = path.match(/^\/jobs\/([a-f0-9-]+)$/)[1];
        if (method === 'GET') return `nexus job get ${jobId}`;
    }

    // Metrics endpoints
    if (path.match(/^\/metrics\/([a-f0-9-]+)$/)) {
        const nodeId = path.match(/^\/metrics\/([a-f0-9-]+)$/)[1];
        return `nexus metrics get ${nodeId}`;
    }
    if (path.match(/^\/metrics\/([a-f0-9-]+)\/stats$/)) {
        const nodeId = path.match(/^\/metrics\/([a-f0-9-]+)\/stats$/)[1];
        return `nexus metrics stats ${nodeId}`;
    }

    // Logs endpoints
    if (path.match(/^\/logs$/)) {
        return 'nexus logs list';
    }
    if (path.match(/^\/logs\/([a-f0-9-]+)$/)) {
        const nodeId = path.match(/^\/logs\/([a-f0-9-]+)$/)[1];
        return `nexus logs list ${nodeId}`;
    }

    return null;
}

// Generate human-readable summary
function generateSummary(method, url, responseBody) {
    const path = url.replace(window.location.origin, '').replace('/api', '');

    if (path.match(/^\/nodes$/)) {
        if (method === 'GET' && responseBody && responseBody.nodes) {
            return `Found ${responseBody.nodes.length} node(s)`;
        }
    }

    if (path.match(/^\/nodes\/([a-f0-9-]+)$/)) {
        if (method === 'GET' && responseBody && responseBody.name) {
            return `Node: ${responseBody.name} (${responseBody.status})`;
        }
    }

    if (path.match(/^\/jobs$/)) {
        if (method === 'POST' && responseBody && responseBody.id) {
            return `Job #${responseBody.id.substr(0, 8)} created`;
        }
        if (method === 'GET' && responseBody && responseBody.jobs) {
            return `Found ${responseBody.jobs.length} job(s)`;
        }
    }

    if (path.match(/^\/logs$/)) {
        if (responseBody && responseBody.logs) {
            return `Found ${responseBody.logs.length} log entries`;
        }
    }

    return '';
}

console.log('[CLI View] Loaded successfully');

// Helper to safely parse JSON
function parseJsonSafe(str) {
    try {
        return JSON.parse(str);
    } catch (e) {
        return str; // Return original string if parse fails
    }
}
