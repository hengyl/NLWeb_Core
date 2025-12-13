NLWeb Specification v0.54
1. Overview
NLWeb defines a standardized interface for natural language interactions with agents. It abstracts the complexity of agentic interactions—such as tool use, long-running tasks, and rich structured data—into a unified protocol.
The primary API/tool/skill provided by an NLWeb agent is ‘ask’, using which a caller can ask the agent for some information or to perform a task. Await is a helper API that enables asynchronous answers, which is useful for long running requests.
2. Underlying concepts
Transport Neutrality: NLWeb is designed to be transport-protocol agnostic. While this specification uses HTTP for its primary examples, the core JSON structures are almost identical whether transmitted via HTTP, WebSockets, JSON-RPC, or within agentic protocols like the Model Context Protocol (MCP). We describe the core JSON structures in the main document and provide examples with HTTP and MCP in the appendix.
Extensibility: Arguments passed to ‘ask’, responses, etc. all involve structured objects with schemas. Indeed much of specs like this one is to define these schemas. However, we would like extensibility and for that we need to be able to introduce new schemas without changing the core spec. The linked data community has solved this problem with the use of the ‘@context’ attribute in json-ld. This is in wide use on tens of billions of web pages. Since NLWeb uses json for pretty much everything, ‘@context’ is easily incorporated.
Context: A defining feature of LLMs is their ability to understand and use extended context. We expect many tools will themselves be AI powered. Tools should be able to send and receive context. Context also covers a very wide range of temporal granularities, from tokens identifying sessions to the last few queries to conversation histories to memory. We introduce contexts as first class objects. We represent contexts as json objects with an extensible set of attributes whose definitions can be referenced using the @context attribute. Context objects may appear as values of attributes, both in the request and in the response.

3. Ask Query Structure
The request object consists of four sections: query, context, prefer, and meta.
3.1 Query (Required)
Specifies the user’s current request and associated query parameters.
Attributes:
text (required): The natural language query string from the user


site (optional): An agent may have ‘sub corpora’ and allow a request to specify which corpora must be searched.


Additional filter attributes (optional): Any number of domain-specific filters such as:
itemType: the type of the item requested (e.g., Movie, Recipe, etc.)
location: Geographic constraint
price: Price range or constraint
These attributes, and their values, should use schema.org vocabulary or comparable schemas where possible.
Example:
	“query”: {
		“text”: “something protein rich that has cinnamon in it”,
		“site”: “pumpkins-r-us.com”,
		“location”: “Idaho”,
		“price”: “less than $20”
		}


3.2 Context (Optional)
Provides contextual information about the query to help the agent better understand and respond to the request. Context can be communicated using one or more attributes, as specified by the schema specified in the @context attribute. 
Attributes
@type: the type of Context, which determines the attributes and their semantics. The default is “ConversationalContext”. The following attributes are specified by ConversationalContext.
prev (optional): Array of previous queries in the conversation
text (optional): Free-form text paragraph describing the broader context
memory (optional): Persistent information about the user’s preferences, constraints, or characteristics

Example
“context”: {
	“prev”: [“breakfast muffins”, “high fiber snacks”],
	“text”: “User has been looking at different options in the context of planning a party”,
	“memory”: “vegetarian, has a sweet tooth”
}
The ability to reference external schemas via the @context mechanism enables future extensibility. For instance, in a more advanced setting, documents could contain context shared by multiple agents, and a reference to that document could be passed within the context.

3.3 Prefer (Optional)
Specifies expectations and requirements for how the response should be formatted and delivered. The design pattern we try to follow is that of HTTP content negotiation.
Attributes (all optional)
streaming: Boolean indicating whether streaming response is desired (true or false)
response_format: Indicates the preferred response format (e.g., chatgpt_app)
mode: Response mode such as list, summarize, etc.
accept-language: Language code for the response (e.g., en), aligning with Accept-Language HTTP header.
user-agent: Type of client making the request (mobile, desktop, etc.), aligning with a conceptual User-Agent HTTP header.
Example
“prefer”: {
	“streaming”: false,
	“response_format”: “chatgpt_app”,
	“mode”: “list”,
	“accept-language”: “en”,
	“user-agent”: “Copilot/1.0.0”
}
3.3.1 response_format
We expect a wide range of clients to call NLWeb agents — from chatbots to site search interfaces to data analytics tools. Different output structures may be suitable for different clients. We expect NLWeb agents may support multiple output formats. A client may specify the formats it can accept and leave it to the NLWeb agent to choose the best.
3.3.2 mode
The mode parameter can be used to specify the preferred level of AI processing on the results. The ‘list’ mode provides a list of results. ‘Summarize’ mode add a summary of the results. The extensibility mechanism can be used to introduce new types.

3.4 Meta (Optional)
Contains metadata about the request itself, requested version number of the protocol, tracking information, etc.
Attributes
api_version (optional): API version number being used
session_context (optional): Context object for capture state about the session (loosely the analog of http cookies).
Example
“meta”: {
	“version”: “0.54”,
	“session_context”: {
		“conversation_id”: “conv_98765”,
		“state_token”: “encrypted_blob_xyz”
	}
}


4. Response Structure
Though NLWeb agents may support multiple response types, the response should always be a json object with a field for metadata (meta or _meta) and one or more types of fields (e.g., content, structured_data) carrying the content.
_meta (required): Metadata about the response.
response_type (required) : Answer | Elicitation | Promise | Failure
response_format (optional): The response format of the answer
version (required): API version number
session_context (optional): context object which can include attribute value pairs that need to be included in future calls to the NLWeb Agent.
Response format specific fields such as:
openai/outputTemplate (string): For ChatGPT Apps SDK - URI of the widget template
openai/widgetAccessible (boolean): For ChatGPT Apps SDK - whether widget can make tool calls
Other protocol-specific metadata as needed

4.1 Response Content
The result structure will be a function of the response_type. We go through the result structures for answer, elicitation, promise and failure.
4.1.1 Answer
Though we expect to allow different structures for the content, as specified by the ‘response_format’ in the request, we expect most answers to be an array of json objects, each encoding some semi-structured information. In some cases, as with ChatGPT apps, we might see the structured and unstructured portions broken out into separate sections.
We specify two result structures here, one aligned with the output structure expected of chatGPT apps and another that is more suited for conversational search.
Conversational Search result structure
Conversational search (for websites, applications, etc.) is a use case for NLWeb. In this case, the attribute “results” contains an array of typed semi-structured json objects. Each object contains
@type (string, recommended): Specifies the object’s type (e.g., Restaurant, Movie, Product, Recipe). The use of schema.org types is recommended where applicable, although any defined schema is permissible.
Type-specific fields: Includes attributes such as url, name, title, description, image, price, ingredients, and other fields relevant to the object’s type.
grounding (object, optional): Contains data establishing provenance, such as source URLs, citations, or references to schema objects.
actions (array, optional): Lists the executable actions associated with the item. Each action is represented as a JSON object detailing its URL, description, and the specific parameters for this action invocation. They may be MCP or A2A actions. 

Example
“results”: [
	    {
	       “@type”: “Recipe”,
	       “name”: “Pumpkin spice with coconut”,
                   “description”: “....”,
	       “Ingredients”: …
	       “cookingTime”: …
       “actions”: [{<action for adding ingredients to shopping cart>}, …]
     },
     {
        “@type”: “Restaurant”,
        “title”: “Idaho pumpkin place”,
         “Address”: …..
         …
      }
]
ChatGPT app result structure
   This structure is in conformance with the structure specified for chatGPT apps. The main differences are that the top level attribute is called “structuredData” (as opposed to “results”) and there is an additional attribute “content”, with has text provided for consumption by an LLM.
content: used for natural language descriptions of the result, meant for consumption by the chatbot. An array of json objects with the attributes:
“Type” with the value “text”
“Text” with a natural language description of the result


structuredData: An array of json objects with semi-structured data, meant for consumption by a client that understands this structure. Follows the same structure as ‘results’ in the case of Conversational Search result structure.



4.1.2 Promise
If the NLWeb agent is unable to immediately respond with an answer, it may return a promise (which is loosely modeled after the promise in javascript or async in python).
Example
{
      “response_type”: “promise”,
      “promise”: {
            “token”: “promise_xyz”,
            “estimated_time”: 120,}
}
The ‘await’ api/tool can be used to check on a promise.

4.1.3 Elicitation
Sometimes, the agent requires more information before answering. In such cases, the response_type should be “elicitation”. The “elicitation” attribute of the response contains the information being requested.
Example: User makes a vague request for dinner
Request:

{
  "query": {
    "text": "I need something for dinner"
  },
  "meta": {
    "version": "0.54"
  }
}

Response:

{
  "_meta": {
    "response_type": "elicitation",
    "version": "0.54"
  },
  "elicitation": {
    "text": "I'd love to help you find a great dinner recipe! To provide the best recommendations, could you tell me:",
    "questions": [
      {
        "id": "dietary_restrictions",
        "text": "Do you have any dietary restrictions or preferences (vegetarian, vegan, gluten-free, etc.)?",
        "type": "multi_select",
        "options": ["vegetarian", "vegan", "gluten-free", "dairy-free", "none"]
      },
      {
        "id": "protein_type",
        "text": "What type of protein would you like?",
        "type": "single_select",
        "options": ["chicken", "beef", "fish", "pork", "tofu", "beans", "no preference"]
      },
      {
        "id": "cooking_time",
        "text": "How much time do you have for cooking?",
        "type": "single_select",
        "options": ["under 20 minutes", "20-40 minutes", "40-60 minutes", "over an hour"]
      }
    ]
  }
}

4.1.4 Failure
  "_meta": {
	“response_type”: “failure”
                }
   “error”: {
	      “code”: “NO_RESULTS”,
	      “message”: “Ran out of tokens.”
	    }


4.2 Await
Check the status of or cancel a task using a promise_token.
Exampole:
{
	“promise_token”: “promise_xyz789”,
	“action”: “checkin”, // or “cancel”
	“meta”: {
		“version”: “0.54”,
		“request_id”: “req_def456”
	}
}
Response: Returns a standard NLWeb Response. If the task is still running, it returns another promise. If complete, it returns an answer.

7. Actions
 Each result object can include a set of actions relevant to the action. This structure aligns with standard tool definition formats
Example:
“actions”:
         {@context: “http://schema.org/”, 
 “@type”: “AddToCartAction”, 
            “name”: “add_ingredients”, 
             “description”: “Add recipe ingredients for XYZ to your shopping cart”, 
              “protocol”: “HTTP”,
             “method”: “POST”, 
   “endpoint”: “https://api.recipes.example.com/cart/add”, 
             “params”:  <ingredients specific to the recipe>
          }
8. Binding: HTTP Transport
This section defines how NLWeb maps to standard HTTP 1.1/2.0.
8.1 Endpoints
POST /ask


POST /await
8.2 Headers
 The prefer argument to ask is used to specify preferences for the streaming, structure of output, etc. (as opposed to http headers).

8.4 Streaming
Server-Sent Events (SSE) are supported via Accept: text/event-stream.
Events must eventually deliver the full JSON structure.


One of the events must contain the meta block to ensure the client captures the context state for the next turn.

