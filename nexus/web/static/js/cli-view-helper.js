
// Helper to safely parse JSON
function parseJsonSafe(str) {
    try {
        return JSON.parse(str);
    } catch (e) {
        return str; // Return original string if parse fails
    }
}
