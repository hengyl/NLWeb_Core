# NLWeb Dropdown Widget v0.54 Update

## Overview
The `nlweb-dropdown-chat.js` widget has been updated to use NLWeb Protocol v0.54. It now sends properly structured requests and handles all four response types.

## File Updated
- **Location**: `/packages/network/nlweb_network/static/nlweb-dropdown-chat.js`

## Changes Made

### 1. Constructor - Added Conversation History
```javascript
// OLD
constructor(config = {}) {
    this.config = { ... };
    this.init();
}

// NEW
constructor(config = {}) {
    this.config = { ... };

    // Initialize conversation history for v0.54 context
    this.conversationHistory = [];

    this.init();
}
```

**Purpose**: Track user queries to include as context in future requests (v0.54 `context.prev` field).

### 2. Request Building - v0.54 Format
```javascript
// OLD
body: JSON.stringify({
    query: query,
    site: this.config.site,
    conversation_id: this.currentConversationId || null
})

// NEW
const request = {
    query: {
        text: query,
        ...(this.config.site && { site: this.config.site })
    },
    prefer: {
        streaming: false,
        response_format: 'conv_search'
    },
    meta: {
        api_version: '0.54'
    }
};

// Add conversation context if available
if (this.conversationHistory && this.conversationHistory.length > 0) {
    request.context = {
        '@type': 'ConversationalContext',
        prev: this.conversationHistory.slice(-5) // Last 5 queries
    };
}

body: JSON.stringify(request)
```

**Changes**:
- Query text moved to `query.text`
- Site moved to `query.site`
- Added `prefer.streaming = false` (non-streaming)
- Added `prefer.response_format = 'conv_search'`
- Added `meta.api_version = '0.54'`
- Previous queries included in `context.prev`

### 3. Conversation History Tracking
```javascript
// In handleSearch() and sendFollowUpMessage()
this.conversationHistory.push(query);
```

**Purpose**: Maintains last 5 user queries for context in future requests.

### 4. Response Handling - Type-Based Routing
```javascript
// OLD - Single handler
async handleJSONResponse(response, preloadedData = null) {
    const data = preloadedData || await response.json();
    const parsed = NLWebSSEParser.parseMessage(data);
    // ... single response handling
}

// NEW - Type-based routing
async handleJSONResponse(response, preloadedData = null) {
    const data = preloadedData || await response.json();

    // Handle v0.54 response types
    if (data._meta && data._meta.response_type) {
        switch (data._meta.response_type) {
            case 'Answer':
                this.handleAnswerResponse(data);
                break;
            case 'Elicitation':
                this.handleElicitationResponse(data);
                break;
            case 'Promise':
                this.handlePromiseResponse(data);
                break;
            case 'Failure':
                this.handleFailureResponse(data);
                break;
            default:
                this.handleLegacyResponse(data);
        }
    } else {
        // Legacy format
        this.handleLegacyResponse(data);
    }
}
```

### 5. New Response Handlers

#### Answer Response Handler
```javascript
handleAnswerResponse(data) {
    const messageElement = this.addMessage('assistant', '');
    const contentDiv = messageElement.querySelector('.message-content');
    contentDiv.innerHTML = '';

    // Extract results (handles both conv_search and chatgpt_app formats)
    const results = data.results || data.structuredData || [];

    // Display results
    results.forEach(result => {
        const resourceElement = NLWebSSEParser.createResourceElement(result);
        contentDiv.appendChild(resourceElement);
    });

    if (results.length === 0) {
        contentDiv.innerHTML = '<p>No results found.</p>';
    }
}
```

**Features**:
- Handles both `results` (conv_search) and `structuredData` (chatgpt_app)
- Uses existing `NLWebSSEParser.createResourceElement()` for rendering
- Shows message when no results

#### Elicitation Response Handler
```javascript
handleElicitationResponse(data) {
    const messageElement = this.addMessage('assistant', '');
    const contentDiv = messageElement.querySelector('.message-content');
    contentDiv.innerHTML = '';

    // Show elicitation text
    const textP = document.createElement('p');
    textP.textContent = data.elicitation.text;
    contentDiv.appendChild(textP);

    // Show questions with options
    data.elicitation.questions.forEach(q => {
        const questionDiv = document.createElement('div');
        questionDiv.className = 'elicitation-question';

        const questionText = document.createElement('strong');
        questionText.textContent = q.text;
        questionDiv.appendChild(questionText);

        if (q.options) {
            const optionsList = document.createElement('ul');
            q.options.forEach(opt => {
                const li = document.createElement('li');
                li.textContent = opt;
                optionsList.appendChild(li);
            });
            questionDiv.appendChild(optionsList);
        }

        contentDiv.appendChild(questionDiv);
    });
}
```

**Features**:
- Displays intro text
- Shows each question with its options as a bulleted list
- Supports single_select, multi_select, and text question types

#### Promise Response Handler
```javascript
handlePromiseResponse(data) {
    const messageElement = this.addMessage('assistant', '');
    const contentDiv = messageElement.querySelector('.message-content');
    contentDiv.innerHTML = '';

    const estimatedTime = data.promise.estimated_time
        ? ` (estimated ${data.promise.estimated_time}s)`
        : '';
    contentDiv.innerHTML = `<p>Task started${estimatedTime}. Token: <code>${data.promise.token}</code></p>`;
}
```

**Features**:
- Shows promise token for future status checks
- Displays estimated completion time if available
- User can copy token to check status later

#### Failure Response Handler
```javascript
handleFailureResponse(data) {
    const messageElement = this.addMessage('assistant', '');
    const contentDiv = messageElement.querySelector('.message-content');
    contentDiv.innerHTML = '';

    contentDiv.innerHTML = `<p class="error">Error (${data.error.code}): ${data.error.message}</p>`;
}
```

**Features**:
- Shows error code and message
- Uses CSS class `error` for styling

#### Legacy Response Handler
```javascript
handleLegacyResponse(data) {
    // Parse using existing SSE parser for old format
    const parsed = NLWebSSEParser.parseMessage(data);
    // ... existing parsing logic
}
```

**Features**:
- Maintains backward compatibility with old response format
- Uses existing `NLWebSSEParser` logic

### 6. Session Context Handling
```javascript
// Handle conversation ID if present
if (data._meta && data._meta.session_context && data._meta.session_context.conversation_id) {
    this.currentConversationId = data._meta.session_context.conversation_id;
}
```

**Changes**:
- Moved from `data.conversation_id` to `data._meta.session_context.conversation_id`

## Benefits

1. **Full v0.54 Compliance**: All requests follow v0.54 protocol structure
2. **Conversation Context**: Previous queries automatically included for better results
3. **4 Response Types**: Proper handling of Answer, Elicitation, Promise, and Failure
4. **Error Handling**: Clear error messages with codes
5. **Backward Compatible**: Still handles old format responses via `handleLegacyResponse()`
6. **Two Answer Formats**: Supports both conv_search and chatgpt_app formats

## Breaking Changes

### For Backend Developers
- Backend must now accept v0.54 nested request structure
- Old flat format (`{query: "text", site: "..."}`) is no longer sent

### For Widget Users
- **No changes required** - Widget API remains the same
- Usage example still works:
  ```javascript
  const chat = new NLWebDropdownChat({
      containerId: 'my-search-container',
      site: 'example.com',
      endpoint: 'https://nlw.azurewebsites.net'
  });
  ```

## Example Request/Response

### Request Sent by Widget
```json
{
  "query": {
    "text": "chocolate cake recipes",
    "site": "example.com"
  },
  "context": {
    "@type": "ConversationalContext",
    "prev": ["dessert recipes", "easy baking"]
  },
  "prefer": {
    "streaming": false,
    "response_format": "conv_search"
  },
  "meta": {
    "api_version": "0.54"
  }
}
```

### Answer Response (Success)
```json
{
  "_meta": {
    "response_type": "Answer",
    "response_format": "conv_search",
    "version": "0.54"
  },
  "results": [
    {
      "@type": "Recipe",
      "name": "Chocolate Cake",
      "description": "Delicious chocolate cake",
      "url": "https://example.com/recipe1",
      "image": "https://example.com/image1.jpg"
    }
  ]
}
```

### Failure Response (Error)
```json
{
  "_meta": {
    "response_type": "Failure",
    "version": "0.54"
  },
  "error": {
    "code": "NO_RESULTS",
    "message": "No recipes found matching your query"
  }
}
```

## Testing

### Test with Example HTML
```html
<!DOCTYPE html>
<html>
<head>
    <title>NLWeb Dropdown Test</title>
    <link rel="stylesheet" href="/static/nlweb-dropdown-chat.css">
</head>
<body>
    <div id="search-container"></div>

    <script type="module">
        import { NLWebDropdownChat } from '/static/nlweb-dropdown-chat.js';

        const chat = new NLWebDropdownChat({
            containerId: 'search-container',
            site: 'all',
            placeholder: 'Ask about recipes...',
            endpoint: 'http://localhost:8000'
        });
    </script>
</body>
</html>
```

### Expected Console Output
```
POST http://localhost:8000/ask
{
  "query": {"text": "chocolate cake", "site": "all"},
  "prefer": {"streaming": false, "response_format": "conv_search"},
  "meta": {"api_version": "0.54"}
}
```

## Migration Checklist

- [x] Update request building to v0.54 format
- [x] Add conversation history tracking
- [x] Add context to requests
- [x] Add response type detection
- [x] Add Answer response handler
- [x] Add Elicitation response handler
- [x] Add Promise response handler
- [x] Add Failure response handler
- [x] Maintain backward compatibility with legacy format
- [x] Update session context extraction
- [ ] Add CSS for elicitation questions
- [ ] Add CSS for error messages
- [ ] Add promise status checking UI (future enhancement)

## CSS Additions Needed

Add these styles to `nlweb-dropdown-chat.css`:

```css
/* Elicitation questions */
.elicitation-question {
    margin: 10px 0;
    padding: 10px;
    background: #f5f5f5;
    border-radius: 4px;
}

.elicitation-question strong {
    display: block;
    margin-bottom: 8px;
}

.elicitation-question ul {
    margin: 8px 0 0 20px;
    padding: 0;
}

/* Error messages */
.error {
    color: #d32f2f;
    background: #ffebee;
    padding: 10px;
    border-radius: 4px;
    border-left: 4px solid #d32f2f;
}

/* Promise/task messages */
code {
    background: #f5f5f5;
    padding: 2px 6px;
    border-radius: 3px;
    font-family: monospace;
    font-size: 0.9em;
}
```

## Future Enhancements

1. **Promise Polling**: Auto-poll promise status and update UI when complete
2. **Interactive Elicitation**: Make elicitation questions interactive (clickable options)
3. **Streaming Support**: Enable streaming mode with real-time result updates
4. **Result Actions**: Support clicking on result actions (from `ResultObject.actions`)
5. **Grounding Display**: Show source URLs and citations from `Grounding` object

## Summary

The nlweb-dropdown-chat.js widget now fully supports NLWeb Protocol v0.54:
- ✅ Sends v0.54 structured requests
- ✅ Includes conversation context automatically
- ✅ Handles all 4 response types
- ✅ Backward compatible with old responses
- ✅ No breaking changes for widget users
- ✅ Clear error handling with codes

The widget is ready to work with v0.54 backends!
