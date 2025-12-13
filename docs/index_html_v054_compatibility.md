# index.html Compatibility with v0.54

## Current Status

**⚠️ PARTIAL COMPATIBILITY** - The current `index.html` and `nlweb-chat.js` will have **limited functionality** with v0.54 backend.

## Issues

### 1. Request Format Mismatch
**Current behavior** (`nlweb-chat.js` line 305-309):
```javascript
const url = new URL(`${this.baseUrl}/ask`);
url.searchParams.set('query', query);
url.searchParams.set('site', site);
url.searchParams.set('max_results', this.maxResults);
url.searchParams.set('mode', 'list');

this.currentStream = new EventSource(url.toString());
```

**Problem**:
- Sends **GET request** with flat query parameters
- v0.54 backend expects **POST request** with nested JSON structure
- EventSource (SSE) can only do GET requests

**Result**:
- Backend will **reject** these requests with error:
  ```json
  {
    "_meta": {"response_type": "Failure", "version": "0.54"},
    "error": {
      "code": "INVALID_REQUEST",
      "message": "Invalid request: missing 'query' object. Expected v0.54 format with nested structure."
    }
  }
  ```

### 2. Response Format Mismatch
**Current behavior** (`nlweb-chat.js` line 334-348):
```javascript
// Handle content array (NLWeb format)
if (data.content && Array.isArray(data.content)) {
    data.content.forEach((item, idx) => {
        // Only add resource items (skip text items)
        if (item.type === 'resource' && item.resource && item.resource.data) {
            assistantMessage.content.push(item.resource.data);
        }
    });
}
```

**Problem**:
- Expects old format with `content` array
- v0.54 backend sends `results` array (or `_meta` + `results` chunks)

**Result**:
- Results won't be displayed properly
- UI will show empty or loading state indefinitely

## Solutions

### Option 1: Add Backward Compatibility to Backend (Recommended)

Update the server to accept GET requests and convert them to v0.54 internally:

```python
# In server.py - ask_handler()

async def ask_handler(request):
    query_params = dict(request.query)

    # For POST, check JSON body too
    if request.method == 'POST':
        body = await request.json()
        query_params = {**query_params, **body}

    # Check if v0.54 format
    if 'query' in query_params and isinstance(query_params['query'], dict):
        # v0.54 format - use as is
        pass
    else:
        # Legacy GET format - convert to v0.54
        query_params = convert_legacy_to_v054(query_params)

    # ... rest of handler
```

**Helper function**:
```python
def convert_legacy_to_v054(legacy_params):
    """Convert legacy GET params to v0.54 format"""
    v054 = {
        'query': {
            'text': legacy_params.get('query', ''),
        },
        'prefer': {
            'streaming': True,  # GET requests are always streaming
            'response_format': 'conv_search'
        },
        'meta': {
            'api_version': '0.54'
        }
    }

    # Add optional fields
    if 'site' in legacy_params:
        v054['query']['site'] = legacy_params['site']
    if 'max_results' in legacy_params:
        v054['query']['num_results'] = legacy_params['max_results']
    if 'mode' in legacy_params:
        v054['prefer']['mode'] = legacy_params['mode']

    return v054
```

**Also update response format in handler**:
```python
# When sending results via SSE, also send in legacy format
async def send_results(self, results):
    # Send v0.54 format
    await self.output_method({"results": results})

    # ALSO send legacy format for backward compatibility
    legacy_content = []
    for result in results:
        legacy_content.append({
            "type": "resource",
            "resource": {"data": result}
        })
    await self.output_method({"content": legacy_content})
```

### Option 2: Update nlweb-chat.js to Use v0.54 (Full Update)

Replace the GET/SSE approach with POST + fetch for better v0.54 compatibility:

```javascript
async streamQuery(query, site) {
    const assistantMessage = {
        id: Date.now(),
        role: 'assistant',
        content: [],
        metadata: {}
    };
    this.currentConversation.messages.push(assistantMessage);
    this.renderMessages();

    try {
        // Build v0.54 request
        const request = {
            query: {
                text: query,
                site: site,
                num_results: this.maxResults
            },
            prefer: {
                streaming: false,  // Use non-streaming for simplicity
                response_format: 'conv_search'
            },
            meta: {
                api_version: '0.54'
            }
        };

        console.log('=== NLWeb v0.54 Request ===');
        console.log('Request:', request);

        // Send POST request
        const response = await fetch(`${this.baseUrl}/ask`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(request)
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        console.log('=== NLWeb v0.54 Response ===');
        console.log('Response:', data);

        // Handle v0.54 response types
        if (data._meta && data._meta.response_type === 'Answer') {
            // Extract results
            const results = data.results || [];

            // Add to message content
            assistantMessage.content = results;

            // Sort by score
            this.sortResultsByScore(assistantMessage.content);

            // Render
            this.renderMessages();

            // Save
            this.saveConversations();
        } else if (data._meta && data._meta.response_type === 'Failure') {
            // Handle error
            assistantMessage.content = [{
                type: 'text',
                content: `Error: ${data.error.message}`
            }];
            this.renderMessages();
        }

    } catch (err) {
        console.error('Query failed:', err);
        assistantMessage.content = [{
            type: 'text',
            content: `Error: ${err.message}`
        }];
        this.renderMessages();
    }
}
```

### Option 3: Create Hybrid Approach (Best of Both Worlds)

Support both legacy GET and new POST v0.54:

```javascript
async streamQuery(query, site) {
    // Check if server supports v0.54 (could be detected at init)
    if (this.serverSupportsV054) {
        return await this.streamQueryV054(query, site);
    } else {
        return await this.streamQueryLegacy(query, site);
    }
}

async streamQueryV054(query, site) {
    // Implementation from Option 2
}

async streamQueryLegacy(query, site) {
    // Current implementation (EventSource + GET)
}
```

## Recommendation

**Use Option 1** (Backend Backward Compatibility) for quickest fix:

1. Add legacy GET param conversion in `server.py`
2. Send both v0.54 and legacy response formats
3. `index.html` continues to work without changes
4. New clients can use pure v0.54

**Implementation**:

```python
# packages/network/nlweb_network/server.py

def convert_legacy_to_v054(params):
    """Convert legacy flat params to v0.54 nested format"""
    # Extract query text
    query_text = params.get('query', '')

    # Build v0.54 structure
    v054_request = {
        'query': {
            'text': query_text
        },
        'prefer': {
            'streaming': True,  # GET requests use streaming
            'response_format': 'conv_search'
        },
        'meta': {
            'api_version': '0.54'
        }
    }

    # Map legacy params to v0.54 structure
    if 'site' in params:
        v054_request['query']['site'] = params['site']
    if 'max_results' in params:
        v054_request['query']['num_results'] = int(params['max_results'])
    if 'mode' in params:
        v054_request['prefer']['mode'] = params['mode']

    return v054_request

async def ask_handler(request):
    query_params = dict(request.query)

    # For POST, merge JSON body
    if request.method == 'POST':
        try:
            body = await request.json()
            query_params = {**query_params, **body}
        except:
            pass

    # Detect format and convert if needed
    if 'query' in query_params and isinstance(query_params['query'], dict):
        # Already v0.54 format
        pass
    elif 'query' in query_params and isinstance(query_params['query'], str):
        # Legacy flat format - convert
        query_params = convert_legacy_to_v054(query_params)
    else:
        # Invalid format
        return web.json_response({
            '_meta': {'response_type': 'Failure', 'version': '0.54'},
            'error': {'code': 'INVALID_REQUEST', 'message': 'Missing query parameter'}
        }, status=400)

    # Extract streaming preference
    prefer = query_params.get('prefer', {})
    streaming = prefer.get('streaming', True) if isinstance(prefer, dict) else True

    # Route to appropriate interface
    if streaming:
        interface = HTTPSSEInterface()
    else:
        interface = HTTPJSONInterface()

    return await interface.handle_request(request, NLWebVectorDBRankingHandler)
```

## Testing After Fix

```bash
# Test legacy GET format (should work with Option 1)
curl "http://localhost:8000/ask?query=test&site=example.com"

# Test v0.54 POST format (should work)
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": {"text": "test"}, "prefer": {"streaming": false}, "meta": {"api_version": "0.54"}}'
```

## Summary

- ❌ **Current state**: index.html WILL NOT WORK with pure v0.54 backend
- ✅ **Option 1**: Add backward compat layer (15 minutes)
- ✅ **Option 2**: Update nlweb-chat.js fully (1-2 hours)
- ✅ **Option 3**: Hybrid approach (30 minutes)

**Recommended**: Implement Option 1 for immediate compatibility, then gradually migrate to Option 2.
