# NLWeb Protocol v0.54 Implementation Design

## Overview
This document describes the changes needed to align the current NLWeb implementation with the NLWeb Protocol Specification v0.54. All code will be updated to use v0.54 format exclusively - no backward compatibility is needed.

## Current State Analysis

### Current Request Structure
The current implementation uses a flat parameter structure:
```python
{
    "query": "some text",
    "site": "example.com",
    "prev": ["previous query"],
    "context": "some context",
    "streaming": true,
    "num_results": 50
}
```

### Current Response Structure
```python
{
    "_meta": {
        "version": "0.5",
        ...
    },
    "content": [
        {"type": "text", "text": "..."},
        {"type": "resource", "resource": {"data": {...}}}
    ]
}
```

## Target State (v0.54 Compliant)

### Request Structure
```json
{
    "query": {
        "text": "something protein rich that has cinnamon in it",
        "site": "pumpkins-r-us.com",
        "itemType": "Recipe",
        "location": "Idaho",
        "price": "less than $20"
    },
    "context": {
        "@type": "ConversationalContext",
        "prev": ["breakfast muffins", "high fiber snacks"],
        "text": "User has been looking at different options...",
        "memory": "vegetarian, has a sweet tooth"
    },
    "prefer": {
        "streaming": false,
        "response_format": "chatgpt_app",
        "mode": "list",
        "accept-language": "en",
        "user-agent": "Copilot/1.0.0"
    },
    "meta": {
        "api_version": "0.54",
        "session_context": {
            "conversation_id": "conv_98765",
            "state_token": "encrypted_blob_xyz"
        }
    }
}
```

### Response Structure (Answer)
```json
{
    "_meta": {
        "response_type": "Answer",
        "response_format": "conversational_search",
        "version": "0.54",
        "session_context": {...}
    },
    "results": [
        {
            "@type": "Recipe",
            "name": "Pumpkin spice with coconut",
            "description": "...",
            "ingredients": [...],
            "cookingTime": "...",
            "grounding": {
                "source_urls": ["https://..."],
                "citations": [...]
            },
            "actions": [
                {
                    "@context": "http://schema.org/",
                    "@type": "AddToCartAction",
                    "name": "add_ingredients",
                    "description": "Add recipe ingredients to cart",
                    "protocol": "HTTP",
                    "method": "POST",
                    "endpoint": "https://api.recipes.example.com/cart/add",
                    "params": {...}
                }
            ]
        }
    ]
}
```

### Response Structure (Elicitation)
```json
{
    "_meta": {
        "response_type": "Elicitation",
        "version": "0.54"
    },
    "elicitation": {
        "text": "I'd love to help you find a great dinner recipe!...",
        "questions": [
            {
                "id": "dietary_restrictions",
                "text": "Do you have any dietary restrictions?",
                "type": "multi_select",
                "options": ["vegetarian", "vegan", "gluten-free", ...]
            }
        ]
    }
}
```

### Response Structure (Promise)
```json
{
    "_meta": {
        "response_type": "Promise",
        "version": "0.54"
    },
    "promise": {
        "token": "promise_xyz",
        "estimated_time": 120
    }
}
```

### Response Structure (Failure)
```json
{
    "_meta": {
        "response_type": "Failure",
        "version": "0.54"
    },
    "error": {
        "code": "NO_RESULTS",
        "message": "Ran out of tokens."
    }
}
```

## Changes Required

### 1. Protocol Models (`packages/core/nlweb_core/protocol/models.py`)

**Changes:**
- Replace existing models with v0.54 compliant models
- Add new models: `Query`, `Context`, `Prefer`, `SessionContext`, `Meta`
- Update `AskRequest` to use nested structure with query/context/prefer/meta
- Update `AskResponseMeta` to include `response_type` (required), `response_format`, `version`, `session_context`
- Add response models: `AnswerResponse`, `PromiseResponse`, `ElicitationResponse`, `FailureResponse`
- Add models for result objects: `ResultObject`, `Grounding`, `Action`
- Add models for elicitation: `Elicitation`, `Question`
- Add models for promises: `Promise`
- Add models for errors: `Error`
- Add `AwaitRequest` for await API
- Remove legacy models that are no longer needed

**Key changes:**
- `Query.text` is required, all other query fields are optional
- `Query` allows arbitrary extra fields via `extra='allow'` for custom filters
- `Context.@type` defaults to "ConversationalContext"
- `Context.memory` is `List[str]` (list of strings)
- `Prefer` uses hyphenated field names (accept-language, user-agent) via aliases
- `Prefer.response_format` defaults to "chatgpt_app"
- Response types: Answer, Elicitation, Promise, Failure
- `ResultObject` allows extra fields via `extra='allow'` for type-specific attributes

### 2. HTTP JSON Interface (`packages/network/nlweb_network/interfaces/http_json.py`)

**Changes:**
- Update `parse_request()` to validate v0.54 nested format
- Reject non-v0.54 requests with clear error messages
- Pass full v0.54 structure to handlers
- Update `build_json_response()` to construct v0.54 compliant responses
- Build appropriate response structure based on response_type

**Parsing logic:**
```python
async def parse_request(self, request: web.Request) -> Dict[str, Any]:
    # Get query parameters from URL
    query_params = dict(request.query)

    # For POST, merge JSON body (body takes precedence)
    if request.method == 'POST':
        body = await request.json()
        query_params = {**query_params, **body}

    # Validate v0.54 structure
    if 'query' not in query_params or not isinstance(query_params['query'], dict):
        raise ValueError("Invalid request: missing 'query' object. Expected v0.54 format.")

    if 'text' not in query_params['query']:
        raise ValueError("Invalid request: missing 'query.text' field")

    return query_params
```

**Response building logic:**
```python
def build_json_response(self, responses: list) -> Dict[str, Any]:
    # Collect _meta and content
    meta = None
    results = []
    elicitation = None
    promise = None
    error = None

    for response in responses:
        if '_meta' in response:
            meta = response['_meta']
        if 'results' in response:
            results.extend(response['results'])
        if 'elicitation' in response:
            elicitation = response['elicitation']
        if 'promise' in response:
            promise = response['promise']
        if 'error' in response:
            error = response['error']

    # Ensure required meta fields
    if not meta:
        meta = {'response_type': 'Answer', 'version': '0.54'}
    if 'response_type' not in meta:
        meta['response_type'] = 'Answer'
    if 'version' not in meta:
        meta['version'] = '0.54'

    # Build response based on response_type
    response_type = meta['response_type']

    if response_type == 'Answer':
        return {'_meta': meta, 'results': results}
    elif response_type == 'Elicitation':
        return {'_meta': meta, 'elicitation': elicitation}
    elif response_type == 'Promise':
        return {'_meta': meta, 'promise': promise}
    elif response_type == 'Failure':
        return {'_meta': meta, 'error': error}
    else:
        raise ValueError(f"Unknown response_type: {response_type}")
```

### 3. Base NLWeb Handler (`packages/core/nlweb_core/baseNLWeb.py`)

**Changes:**
- Update `__init__()` to extract query from v0.54 structure
- Update `set_meta_attribute()` to ensure v0.54 required fields
- Update `send_meta()` to ensure response_type and version are set
- Add `send_results()` method for sending v0.54 compliant results
- Remove `send_answer()` (replaced by `send_results()`)
- Add helper methods: `send_elicitation()`, `send_promise()`, `send_failure()`
- Update `decontextualizeQuery()` to extract context from v0.54 structure

**Key changes:**
```python
def __init__(self, query_params, output_method):
    self.output_method = output_method
    self.query_params = query_params

    # Extract query text from v0.54 format
    query_obj = query_params.get('query', {})
    if isinstance(query_obj, dict):
        self.query = query_obj.get('text', '')
    else:
        raise ValueError("Invalid request: 'query' must be an object with 'text' field")

    self.query_params["raw_query"] = self.query
    self.return_value = None
    self._meta = {
        'version': '0.54',
        'response_type': 'Answer'
    }

async def send_results(self, results: list):
    """Send v0.54 compliant results array."""
    if self.output_method:
        await self.output_method({"results": results})

async def send_elicitation(self, text: str, questions: list):
    """Send an elicitation response."""
    self._meta['response_type'] = 'Elicitation'
    await self.send_meta()
    if self.output_method:
        await self.output_method({
            "elicitation": {
                "text": text,
                "questions": questions
            }
        })

async def send_promise(self, token: str, estimated_time: int = None):
    """Send a promise response."""
    self._meta['response_type'] = 'Promise'
    await self.send_meta()
    if self.output_method:
        promise = {"token": token}
        if estimated_time is not None:
            promise["estimated_time"] = estimated_time
        await self.output_method({"promise": promise})

async def send_failure(self, code: str, message: str):
    """Send a failure response."""
    self._meta['response_type'] = 'Failure'
    await self.send_meta()
    if self.output_method:
        await self.output_method({
            "error": {
                "code": code,
                "message": message
            }
        })

async def decontextualizeQuery(self):
    # Extract context from v0.54 structure
    context_obj = self.query_params.get('context', {})
    prev_queries = context_obj.get('prev', []) if isinstance(context_obj, dict) else []
    context_text = context_obj.get('text') if isinstance(context_obj, dict) else None

    # ... rest of decontextualization logic
```

### 4. HTTP SSE Interface (`packages/network/nlweb_network/interfaces/http_sse.py`)

**Changes:**
- Update `parse_request()` same as HTTP JSON interface
- Update `send_response()` to handle v0.54 response structure
- Ensure SSE events deliver full JSON structure
- Ensure meta block is sent in one of the events

### 5. Server (`packages/network/nlweb_network/server.py`)

**Changes:**
- Update `ask_handler()` to extract streaming from `prefer.streaming`
- Add `/await` endpoint for promise handling
- Update error handling to return v0.54 Failure responses

**Streaming detection:**
```python
async def ask_handler(request):
    # Get query parameters
    query_params = dict(request.query)

    # For POST, check JSON body too
    if request.method == 'POST':
        body = await request.json()
        query_params = {**query_params, **body}

    # Extract streaming from prefer section (default: true)
    prefer = query_params.get('prefer', {})
    streaming = prefer.get('streaming', True) if isinstance(prefer, dict) else True

    # Route to appropriate interface
    if streaming:
        interface = HTTPSSEInterface()
    else:
        interface = HTTPJSONInterface()

    return await interface.handle_request(request, NLWebVectorDBRankingHandler)
```

**New endpoint:**
```python
async def await_handler(request):
    """
    Handle /await requests for promise checking.

    Expected body:
    {
        "promise_token": "promise_xyz789",
        "action": "checkin",  // or "cancel"
        "meta": {...}
    }

    Returns:
    - JSON response with promise status or final answer
    """
    try:
        body = await request.json()

        # Validate required fields
        if 'promise_token' not in body:
            return web.json_response({
                '_meta': {'response_type': 'Failure', 'version': '0.54'},
                'error': {'code': 'MISSING_FIELD', 'message': 'Missing required field: promise_token'}
            }, status=400)

        if 'action' not in body or body['action'] not in ['checkin', 'cancel']:
            return web.json_response({
                '_meta': {'response_type': 'Failure', 'version': '0.54'},
                'error': {'code': 'INVALID_ACTION', 'message': 'Action must be "checkin" or "cancel"'}
            }, status=400)

        # TODO: Implement promise tracking/checking logic
        # For now, return a placeholder
        return web.json_response({
            '_meta': {'response_type': 'Promise', 'version': '0.54'},
            'promise': {'token': body['promise_token'], 'estimated_time': 60}
        })

    except Exception as e:
        return web.json_response({
            '_meta': {'response_type': 'Failure', 'version': '0.54'},
            'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}
        }, status=500)
```

### 6. Error Handling

**Changes:**
- All error responses must use v0.54 Failure structure
- Update all exception handlers in interfaces to return proper Failure responses
- Use appropriate error codes (e.g., MISSING_FIELD, INVALID_REQUEST, NO_RESULTS, INTERNAL_ERROR)

**Example:**
```python
except ValueError as e:
    return web.json_response({
        '_meta': {'response_type': 'Failure', 'version': '0.54'},
        'error': {'code': 'INVALID_REQUEST', 'message': str(e)}
    }, status=400)
except Exception as e:
    return web.json_response({
        '_meta': {'response_type': 'Failure', 'version': '0.54'},
        'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}
    }, status=500)
```

## No Backward Compatibility

**Decision**: No backward compatibility needed. All code will be updated to use v0.54 format exclusively.

This simplifies the implementation:
- No request format detection needed
- No translation layer needed
- All requests must be v0.54 compliant
- All responses will be v0.54 compliant
- Internal handler logic uses v0.54 structure directly

## Testing Considerations

1. Test v0.54 request parsing with all optional fields
2. Test v0.54 request validation (missing required fields)
3. Test v0.54 response generation for all response types (Answer, Elicitation, Promise, Failure)
4. Test streaming with v0.54 format
5. Test non-streaming with v0.54 format
6. Test MCP and A2A interfaces with v0.54
7. Test await endpoint
8. Test that old flat format requests are rejected with clear error messages

## Implementation Order

1. **First**: Update `protocol/models.py` with v0.54 models
2. **Second**: Update `baseNLWeb.py` with v0.54 helper methods and request parsing
3. **Third**: Update `http_json.py` interface with request validation and response building
4. **Fourth**: Update `http_sse.py` interface similarly
5. **Fifth**: Update `server.py` with streaming detection and /await endpoint
6. **Sixth**: Update error handling throughout
7. **Seventh**: Test with example requests

## Open Questions & Answers

1. **How should we handle custom query filters beyond site/itemType/location/price?**
   - **Answer**: Allow arbitrary fields in Query object via Pydantic's `extra='allow'`. Only `query.text` is required. All other fields (including `site`, `itemType`, `location`, `price`) are optional and extensible.

2. **Should `Context.memory` be a string or list?**
   - **Answer**: List of strings (`List[str]`)

3. **For ChatGPT app format, should we support both conversational_search and chatgpt_app response formats?**
   - **Answer**: Yes, support both formats based on `prefer.response_format`:
     - `chatgpt_app`: ChatGPT Apps format with `content` + `structuredData` (this is the **default**)
     - `conv_search`: Conversational Search format with `results` array

4. **Should we version the API endpoint (e.g., /v1/ask vs /ask)?**
   - **Answer**: Correct - keep `/ask`. The `meta.api_version` field handles versioning.

## Summary

This design provides a clean v0.54 implementation with no backward compatibility. The key strategy is to:
- Replace all request parsing with v0.54 structure validation
- Update internal handler logic to work directly with v0.54 structure
- Replace all response building with v0.54 compliant formats
- Add v0.54 response methods to base handler (send_results, send_elicitation, send_promise, send_failure)
- Update all concrete handlers to use new methods
- Reject any non-v0.54 requests with clear error messages
