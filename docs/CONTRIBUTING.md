# Contributing to Nexus

## Development Guidelines

### Code Quality Standards

#### Error Message Clarity (CRITICAL)

**Rule: All error messages must be clear, actionable, and avoid "undefined" or generic failures.**

Error messages should balance brevity with informativeness. Users should immediately understand:
1. **What** went wrong
2. **Why** it happened (when possible)
3. **How** to fix it (when applicable)

##### ✅ Good Error Messages

```javascript
// Good: Specific, actionable
throw new Error('Node "kitchen-pi" is offline and cannot accept deployments. Check agent status.');

// Good: Clear cause and solution
if (!deployment.container_id) {
    throw new HTTPException(
        status_code=400,
        detail="Deployment has no container ID. The container may have failed to start. Check agent logs."
    );
}

// Good: User-friendly with context
<div class="error-message">
    ⚠️ Storage information unavailable
    <div class="details">Agent needs to be updated with new storage detection feature.</div>
    <div class="solution">Run: ./scripts/update-agent.sh</div>
</div>
```

##### ❌ Bad Error Messages

```javascript
// Bad: Shows "undefined" to user
<span x-text="deployment.status"></span>  // Shows "undefined" if null

// Bad: Generic and unhelpful
throw new Error('Operation failed');

// Bad: Technical jargon without context
detail="500 Internal Server Error"

// Bad: Silent failure
try {
    await loadData();
} catch (e) {
    // Error swallowed, user sees nothing
}
```

##### Frontend Error Handling Checklist

When working with Alpine.js templates:

1. **Always provide fallback values:**
   ```javascript
   // Bad
   x-text="node.temperature"

   // Good
   x-text="node.temperature || 'N/A'"
   x-text="node.temperature ? node.temperature.toFixed(1) + '°C' : 'N/A'"
   ```

2. **Check data existence before operations:**
   ```javascript
   // Bad
   x-text="deployment.status.toUpperCase()"  // Crashes if status is null

   // Good
   x-text="deployment?.status ? deployment.status.toUpperCase() : 'Unknown'"
   ```

3. **Show error states explicitly:**
   ```html
   <!-- Bad: Shows nothing when error occurs -->
   <template x-if="data.length > 0">
       <div x-for="item in data">...</div>
   </template>

   <!-- Good: Shows helpful message on error -->
   <template x-if="error">
       <div class="error">Failed to load data: <span x-text="errorMessage"></span></div>
   </template>
   <template x-if="!error && data.length > 0">
       <div x-for="item in data">...</div>
   </template>
   <template x-if="!error && data.length === 0">
       <div class="empty">No data available</div>
   </template>
   ```

4. **Track error state in component data:**
   ```javascript
   function myComponent() {
       return {
           data: [],
           loading: false,
           error: null,
           errorMessage: '',

           async loadData() {
               this.loading = true;
               this.error = false;
               try {
                   const response = await fetch('/api/data');
                   if (!response.ok) {
                       throw new Error(`Server returned ${response.status}: ${response.statusText}`);
                   }
                   this.data = await response.json();
               } catch (e) {
                   this.error = true;
                   this.errorMessage = e.message || 'Unknown error occurred';
                   console.error('Failed to load data:', e);
               } finally {
                   this.loading = false;
               }
           }
       };
   }
   ```

##### Backend Error Handling Checklist

1. **Use appropriate HTTP status codes:**
   ```python
   # Good: Specific status codes
   raise HTTPException(status_code=404, detail="Node not found")
   raise HTTPException(status_code=503, detail="Agent is offline")
   raise HTTPException(status_code=400, detail="Invalid deployment configuration")
   ```

2. **Include context in error messages:**
   ```python
   # Bad
   if not node:
       raise HTTPException(status_code=404, detail="Not found")

   # Good
   if not node:
       raise HTTPException(
           status_code=404,
           detail=f"Node {node_id} not found. It may have been deleted."
       )
   ```

3. **Log errors with full context:**
   ```python
   try:
       result = await send_to_agent(node_ip, data)
   except httpx.HTTPError as e:
       logger.error(f"Failed to communicate with agent {node_ip}: {e}")
       raise HTTPException(
           status_code=503,
           detail=f"Cannot communicate with agent at {node_ip}. Agent may be offline."
       )
   ```

##### Testing Error Handling

When implementing features, test these scenarios:
- ✓ API returns 404
- ✓ API returns 500
- ✓ Network timeout
- ✓ Malformed response data
- ✓ Missing/null fields in response
- ✓ Empty arrays/lists
- ✓ Agent offline
- ✓ Invalid user input

##### Error Message Templates

Use these patterns for common scenarios:

```python
# Resource not found
f"{resource_type} '{resource_id}' not found"

# Service unavailable
f"Cannot communicate with {service_name}. Service may be offline."

# Invalid input
f"Invalid {field_name}: {reason}. Expected: {expected_format}"

# Prerequisites not met
f"Cannot {action} because {prerequisite} is {state}. {suggested_action}"

# Operation failed
f"Failed to {action}: {specific_reason}. {suggested_fix}"
```

### Code Review Checklist

Before submitting code, verify:
- [ ] No "undefined" can appear in the UI
- [ ] All error states have user-friendly messages
- [ ] Error messages include actionable next steps when possible
- [ ] API errors are logged with full context
- [ ] Frontend catches and displays backend errors properly
- [ ] Loading states are shown during async operations
- [ ] Empty states are distinct from error states

---

## Development Setup

See [README.md](../README.md) for installation instructions.

## Architecture

See [docs/architecture.md](architecture.md) for system architecture details.

## API Documentation

See [docs/api.md](api.md) for API endpoint documentation.
