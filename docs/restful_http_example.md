# NLWeb Protocol RESTful HTTP Examples - Cooking Recipes

This document provides the same examples as `http_example.md` but using RESTful HTTP conventions where preferences are expressed as HTTP headers and session context as cookies.

## 1. Simple Recipe Search

### Request
```http
POST /ask HTTP/1.1
Host: api.recipes.example.com
Content-Type: application/json
Accept: application/json
X-API-Version: 0.54

{
  "query": {
    "text": "healthy breakfast recipes with eggs",
    "site": "breakfast-central.com"
  }
}
```

### Response
```http
HTTP/1.1 200 OK
Content-Type: application/json
X-API-Version: 0.54
X-Processing-Time-Ms: 145

{
  "_meta": {
    "response_type": "answer",
    "version": "0.54",
    "processing_time_ms": 145
  },
  "results": [
    {
      "@type": "Recipe",
      "@context": "https://schema.org",
      "name": "Veggie-Packed Scrambled Eggs",
      "description": "Nutritious scrambled eggs loaded with colorful vegetables",
      "url": "https://recipes.example.com/veggie-scrambled-eggs",
      "image": "https://cdn.recipes.example.com/images/veggie-eggs-425.jpg",
      "cookTime": "PT15M",
      "prepTime": "PT10M",
      "recipeYield": "2 servings",
      "nutrition": {
        "@type": "NutritionInformation",
        "calories": "220 calories",
        "proteinContent": "18g",
        "fatContent": "12g",
        "carbohydrateContent": "8g"
      },
      "recipeIngredient": [
        "4 large eggs",
        "1/2 cup diced bell peppers",
        "1/4 cup chopped spinach",
        "2 tbsp milk",
        "Salt and pepper to taste"
      ],
      "grounding": {
        "source": "user-submitted",
        "author": "Chef Maria",
        "datePublished": "2024-01-15"
      },
      "actions": [
        {
          "@type": "SaveAction",
          "name": "save_recipe",
          "description": "Save this recipe to your cookbook",
          "endpoint": "https://api.recipes.example.com/user/saved",
          "method": "POST"
        }
      ]
    },
    {
      "@type": "Recipe",
      "@context": "https://schema.org",
      "name": "Protein-Rich Egg White Omelette",
      "description": "Low-calorie, high-protein breakfast option",
      "url": "https://recipes.example.com/egg-white-omelette",
      "image": "https://cdn.recipes.example.com/images/white-omelette-425.jpg",
      "cookTime": "PT10M",
      "prepTime": "PT5M",
      "recipeYield": "1 serving",
      "nutrition": {
        "@type": "NutritionInformation",
        "calories": "150 calories",
        "proteinContent": "20g",
        "fatContent": "3g",
        "carbohydrateContent": "5g"
      },
      "recipeIngredient": [
        "4 egg whites",
        "1/4 cup mushrooms, sliced",
        "1/4 cup tomatoes, diced",
        "1 oz reduced-fat cheese",
        "Cooking spray"
      ]
    }
  ]
}
```

## 2. Contextual Search with Preferences

### Request
```http
POST /ask HTTP/1.1
Host: api.recipes.example.com
Content-Type: application/json
Accept: application/json
Accept-Language: en-US
User-Agent: RecipeBot/2.0
X-API-Version: 0.54
X-Response-Format: conversational_search
X-Response-Mode: summarize
X-Streaming: false
Cookie: conversation_id=conv_98765; diet=vegetarian; skill_level=intermediate

{
  "query": {
    "text": "something protein rich that has cinnamon in it",
    "site": "healthy-meals.com",
    "itemType": "Recipe"
  },
  "context": {
    "@type": "ConversationalContext",
    "prev": ["healthy breakfast recipes", "high fiber snacks"],
    "text": "User is meal prepping for the week and prefers make-ahead options",
    "memory": "vegetarian, allergic to nuts, prefers whole foods"
  }
}
```

### Response
```http
HTTP/1.1 200 OK
Content-Type: application/json
X-API-Version: 0.54
Set-Cookie: conversation_id=conv_98765; Path=/; HttpOnly; Secure; SameSite=Strict
Set-Cookie: state_token=encrypted_blob_xyz123; Path=/; HttpOnly; Secure; SameSite=Strict

{
  "_meta": {
    "response_type": "answer",
    "version": "0.54",
    "session_context": {
      "conversation_id": "conv_98765",
      "state_token": "encrypted_blob_xyz123"
    },
    "summary": "Found 3 protein-rich recipes with cinnamon that align with your vegetarian diet and meal prep goals"
  },
  "results": [
    {
      "@type": "Recipe",
      "@context": "https://schema.org",
      "name": "Cinnamon Protein Overnight Oats",
      "description": "High-protein overnight oats with Greek yogurt and cinnamon, perfect for meal prep",
      "url": "https://recipes.example.com/cinnamon-protein-oats",
      "image": "https://cdn.recipes.example.com/images/cinnamon-oats-425.jpg",
      "cookTime": "PT0M",
      "prepTime": "PT10M",
      "totalTime": "PT8H10M",
      "recipeYield": "5 servings",
      "suitableForDiet": ["https://schema.org/VegetarianDiet", "https://schema.org/HighProteinDiet"],
      "nutrition": {
        "@type": "NutritionInformation",
        "calories": "320 calories",
        "proteinContent": "22g",
        "fiberContent": "8g",
        "sugarContent": "12g"
      },
      "recipeIngredient": [
        "2.5 cups rolled oats",
        "2.5 cups milk (dairy or plant-based)",
        "1.25 cups Greek yogurt",
        "5 tbsp chia seeds",
        "2.5 tbsp maple syrup",
        "2.5 tsp ground cinnamon",
        "Pinch of salt"
      ],
      "recipeInstructions": [
        {
          "@type": "HowToStep",
          "text": "Mix all ingredients in a large bowl"
        },
        {
          "@type": "HowToStep",
          "text": "Divide into 5 mason jars"
        },
        {
          "@type": "HowToStep",
          "text": "Refrigerate overnight or up to 5 days"
        }
      ],
      "keywords": ["meal-prep", "make-ahead", "high-protein", "vegetarian"],
      "grounding": {
        "source": "nutritionist-verified",
        "rating": 4.8,
        "reviewCount": 234
      }
    },
    {
      "@type": "Recipe",
      "@context": "https://schema.org",
      "name": "Cinnamon Chickpea Protein Pancakes",
      "description": "Flourless pancakes made with chickpea flour, packed with plant protein",
      "url": "https://recipes.example.com/chickpea-cinnamon-pancakes",
      "image": "https://cdn.recipes.example.com/images/chickpea-pancakes-425.jpg",
      "cookTime": "PT15M",
      "prepTime": "PT5M",
      "recipeYield": "2 servings",
      "nutrition": {
        "@type": "NutritionInformation",
        "calories": "280 calories",
        "proteinContent": "18g",
        "fiberContent": "6g"
      },
      "recipeIngredient": [
        "1 cup chickpea flour",
        "1 cup water",
        "2 tsp ground cinnamon",
        "1 tbsp maple syrup",
        "1 tsp baking powder",
        "Pinch of salt"
      ]
    },
    {
      "@type": "Recipe",
      "@context": "https://schema.org",
      "name": "Quinoa Cinnamon Breakfast Bowl",
      "description": "Warm quinoa breakfast bowl with cinnamon and protein-rich toppings",
      "url": "https://recipes.example.com/quinoa-cinnamon-bowl",
      "image": "https://cdn.recipes.example.com/images/quinoa-bowl-425.jpg",
      "cookTime": "PT20M",
      "prepTime": "PT5M",
      "recipeYield": "4 servings",
      "nutrition": {
        "@type": "NutritionInformation",
        "calories": "340 calories",
        "proteinContent": "19g",
        "fiberContent": "7g"
      },
      "recipeIngredient": [
        "1 cup quinoa",
        "2 cups almond milk",
        "2 tsp cinnamon",
        "4 tbsp almond butter (nut-free alternative: sunflower seed butter)",
        "2 tbsp hemp seeds",
        "Fresh berries for topping"
      ],
      "recipeInstructions": [
        {
          "@type": "HowToStep",
          "text": "Cook quinoa in almond milk with cinnamon"
        },
        {
          "@type": "HowToStep",
          "text": "Divide into meal prep containers"
        },
        {
          "@type": "HowToStep",
          "text": "Top with seeds and berries when serving"
        }
      ],
      "keywords": ["meal-prep", "gluten-free", "high-protein", "vegetarian"]
    }
  ]
}
```

## 3. Request Requiring Clarification (Elicitation)

### Request
```http
POST /ask HTTP/1.1
Host: api.recipes.example.com
Content-Type: application/json
Accept: application/json
X-API-Version: 0.54

{
  "query": {
    "text": "pasta recipe"
  }
}
```

### Response
```http
HTTP/1.1 200 OK
Content-Type: application/json
X-API-Version: 0.54

{
  "_meta": {
    "response_type": "elicitation",
    "version": "0.54"
  },
  "elicitation": {
    "text": "I can help you find the perfect pasta recipe! To give you the best recommendations, could you tell me more about what you're looking for? For example, what type of sauce do you prefer (tomato, cream, pesto, oil-based)? Do you have any dietary restrictions? How much time do you have for cooking?"
  }
}
```

## 4. Long-Running Request with Promise

### Initial Request
```http
POST /ask HTTP/1.1
Host: api.recipes.example.com
Content-Type: application/json
Accept: application/json
X-API-Version: 0.54
Cookie: conversation_id=conv_meal_plan_789

{
  "query": {
    "text": "analyze my meal history and create a personalized weekly meal plan with shopping list",
    "personalized": true
  },
  "context": {
    "@type": "PersonalizationContext",
    "user_id": "user_123",
    "preferences_profile": "health_conscious_vegetarian"
  }
}
```

### Initial Response (Promise)
```http
HTTP/1.1 202 Accepted
Content-Type: application/json
X-API-Version: 0.54
Set-Cookie: conversation_id=conv_meal_plan_789; Path=/; HttpOnly; Secure; SameSite=Strict

{
  "_meta": {
    "response_type": "promise",
    "version": "0.54",
    "session_context": {
      "conversation_id": "conv_meal_plan_789"
    }
  },
  "promise": {
    "token": "promise_mealplan_xyz789",
    "estimated_time": 30,
    "message": "Analyzing your meal history and preferences to create a personalized plan...",
    "progress": 0.1
  }
}
```

### Check Promise Status
```http
POST /await HTTP/1.1
Host: api.recipes.example.com
Content-Type: application/json
X-API-Version: 0.54
Cookie: conversation_id=conv_meal_plan_789

{
  "promise_token": "promise_mealplan_xyz789",
  "action": "checkin"
}
```

### Promise Status Response (Still Processing)
```http
HTTP/1.1 202 Accepted
Content-Type: application/json
X-API-Version: 0.54

{
  "_meta": {
    "response_type": "promise",
    "version": "0.54"
  },
  "promise": {
    "token": "promise_mealplan_xyz789",
    "estimated_time": 15,
    "message": "Creating shopping list based on meal plan...",
    "progress": 0.65
  }
}
```

### Final Promise Resolution
```http
HTTP/1.1 200 OK
Content-Type: application/json
X-API-Version: 0.54
Set-Cookie: conversation_id=conv_meal_plan_789; Path=/; HttpOnly; Secure; SameSite=Strict
Set-Cookie: meal_plan_id=plan_20240118_123; Path=/; HttpOnly; Secure; SameSite=Strict

{
  "_meta": {
    "response_type": "answer",
    "version": "0.54",
    "session_context": {
      "conversation_id": "conv_meal_plan_789",
      "meal_plan_id": "plan_20240118_123"
    }
  },
  "results": [
    {
      "@type": "MealPlan",
      "@context": ["https://schema.org", "https://recipes.example.com/schemas/mealplan"],
      "name": "Your Personalized Weekly Meal Plan",
      "startDate": "2024-01-22",
      "endDate": "2024-01-28",
      "totalNutrition": {
        "averageDailyCalories": 2100,
        "averageDailyProtein": "75g",
        "weeklyFiberTotal": "210g"
      },
      "meals": [
        {
          "day": "Monday",
          "breakfast": {
            "@type": "Recipe",
            "name": "Cinnamon Protein Overnight Oats",
            "url": "https://recipes.example.com/cinnamon-protein-oats"
          },
          "lunch": {
            "@type": "Recipe",
            "name": "Mediterranean Quinoa Bowl",
            "url": "https://recipes.example.com/med-quinoa-bowl"
          },
          "dinner": {
            "@type": "Recipe",
            "name": "Lentil Bolognese Pasta",
            "url": "https://recipes.example.com/lentil-bolognese"
          }
        }
      ],
      "shoppingList": {
        "@type": "ShoppingList",
        "name": "Week of Jan 22 Shopping List",
        "items": [
          {
            "category": "Produce",
            "items": ["5 lbs mixed vegetables", "2 lbs fresh fruit", "Fresh herbs bundle"]
          },
          {
            "category": "Proteins",
            "items": ["2 lbs dried lentils", "1 lb chickpeas", "Greek yogurt (32 oz)"]
          },
          {
            "category": "Grains",
            "items": ["Quinoa (2 lbs)", "Rolled oats (1 lb)", "Whole wheat pasta (1 lb)"]
          }
        ],
        "estimatedCost": "$85-95"
      },
      "actions": [
        {
          "@type": "DownloadAction",
          "name": "download_pdf",
          "description": "Download meal plan as PDF",
          "endpoint": "https://api.recipes.example.com/mealplan/plan_20240118_123/pdf",
          "method": "GET"
        },
        {
          "@type": "ShareAction",
          "name": "share_plan",
          "description": "Share meal plan with family",
          "endpoint": "https://api.recipes.example.com/mealplan/plan_20240118_123/share",
          "method": "POST"
        }
      ]
    }
  ]
}
```

## 5. Streaming Response (Server-Sent Events)

### Request with Streaming Preference
```http
POST /ask HTTP/1.1
Host: api.recipes.example.com
Content-Type: application/json
Accept: text/event-stream
X-API-Version: 0.54
X-Response-Format: conversational_search
X-Response-Mode: detailed
X-Streaming: true

{
  "query": {
    "text": "give me a detailed tutorial on making homemade pasta from scratch"
  }
}
```

### Streaming Response (SSE)
```http
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
X-API-Version: 0.54

event: start
data: {"_meta": {"response_type": "answer", "version": "0.54", "streaming": true}}

event: result
data: {"index": 0, "item": {"@type": "Recipe", "name": "Classic Homemade Pasta Dough", "description": "Traditional Italian pasta dough recipe"}}

event: content
data: {"type": "text", "text": "Making pasta from scratch is easier than you think! Let's start with the basic dough..."}

event: result
data: {"index": 1, "item": {"@type": "HowToSection", "name": "Step 1: Preparing the Dough", "description": "Create a well with flour and add eggs", "image": "https://cdn.recipes.example.com/pasta-well.jpg"}}

event: content
data: {"type": "instruction", "step": 1, "text": "On a clean surface, pour 2 cups of 00 flour and create a well in the center..."}

event: result
data: {"index": 2, "item": {"@type": "HowToSection", "name": "Step 2: Kneading", "description": "Knead for 10 minutes until smooth", "video": "https://videos.recipes.example.com/kneading-technique.mp4"}}

event: content
data: {"type": "instruction", "step": 2, "text": "Begin kneading by folding the dough over itself and pushing with the heel of your hand..."}

event: result
data: {"index": 3, "item": {"@type": "HowToTip", "text": "The dough should be smooth and elastic when properly kneaded. It should spring back when poked."}}

event: complete
data: {"_meta": {"response_type": "answer", "version": "0.54", "session_context": {"conversation_id": "conv_pasta_tutorial_456"}, "total_items": 4, "processing_time_ms": 234}}

event: end
data: {"message": "Tutorial complete"}
```

## 6. Error Response

### Request with Invalid Parameters
```http
POST /ask HTTP/1.1
Host: api.recipes.example.com
Content-Type: application/json
Accept: application/json
X-API-Version: 0.54

{
  "query": {
    "text": "recipes with",
    "max_cooking_time": "invalid_number"
  }
}
```

### Error Response
```http
HTTP/1.1 400 Bad Request
Content-Type: application/json
X-API-Version: 0.54

{
  "_meta": {
    "response_type": "failure",
    "version": "0.54",
    "timestamp": "2024-01-18T15:30:45Z"
  },
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "The parameter 'max_cooking_time' must be a valid duration in ISO 8601 format (e.g., 'PT30M' for 30 minutes)",
    "details": {
      "parameter": "max_cooking_time",
      "provided_value": "invalid_number",
      "expected_format": "ISO 8601 Duration"
    }
  }
}
```

## 7. ChatGPT App Response Format

### Request with ChatGPT App Format Preference
```http
POST /ask HTTP/1.1
Host: api.recipes.example.com
Content-Type: application/json
Accept: application/json
X-API-Version: 0.54
X-Response-Format: chatgpt_app

{
  "query": {
    "text": "quick lunch ideas with avocado"
  }
}
```

### ChatGPT App Format Response
```http
HTTP/1.1 200 OK
Content-Type: application/json
X-API-Version: 0.54
X-OpenAI-Output-Template: https://templates.recipes.example.com/recipe-card
X-OpenAI-Widget-Accessible: true

{
  "_meta": {
    "response_type": "answer",
    "version": "0.54",
    "openai/outputTemplate": "https://templates.recipes.example.com/recipe-card",
    "openai/widgetAccessible": true
  },
  "content": [
    {
      "type": "text",
      "text": "Here are some delicious and quick lunch ideas featuring avocado:"
    },
    {
      "type": "text",
      "text": "1. **Avocado Toast Supreme**: Whole grain bread topped with mashed avocado, cherry tomatoes, and a poached egg. Ready in 10 minutes!"
    },
    {
      "type": "text",
      "text": "2. **California Avocado Wrap**: Tortilla filled with avocado, turkey, lettuce, and ranch dressing. Perfect for on-the-go!"
    },
    {
      "type": "text",
      "text": "3. **Avocado Chickpea Salad**: Creamy mashed avocado mixed with chickpeas, lemon, and herbs. Great as a sandwich filling or with crackers."
    }
  ],
  "structuredData": [
    {
      "@type": "Recipe",
      "name": "Avocado Toast Supreme",
      "cookTime": "PT10M",
      "calories": 320,
      "image": "https://cdn.recipes.example.com/avocado-toast.jpg",
      "difficulty": "Easy"
    },
    {
      "@type": "Recipe",
      "name": "California Avocado Wrap",
      "cookTime": "PT5M",
      "calories": 380,
      "image": "https://cdn.recipes.example.com/avocado-wrap.jpg",
      "difficulty": "Easy"
    },
    {
      "@type": "Recipe",
      "name": "Avocado Chickpea Salad",
      "cookTime": "PT15M",
      "calories": 290,
      "image": "https://cdn.recipes.example.com/chickpea-salad.jpg",
      "difficulty": "Easy"
    }
  ]
}
```

## Notes on RESTful HTTP Implementation

### Header Mappings

The following mappings are used to convert between the JSON `prefer` object and HTTP headers:

| JSON Field | HTTP Header | Notes |
|------------|-------------|-------|
| `prefer.streaming` | `X-Streaming` | Boolean value as string |
| `prefer.response_format` | `X-Response-Format` | Format identifier |
| `prefer.mode` | `X-Response-Mode` | Processing mode |
| `prefer.accept-language` | `Accept-Language` | Standard HTTP header |
| `prefer.user-agent` | `User-Agent` | Standard HTTP header |
| `meta.version` | `X-API-Version` | API version |

### Cookie Mappings

Session context fields are mapped to HTTP cookies:

| Session Context Field | Cookie Name | Cookie Attributes |
|----------------------|-------------|-------------------|
| `conversation_id` | `conversation_id` | HttpOnly, Secure, SameSite=Strict |
| `state_token` | `state_token` | HttpOnly, Secure, SameSite=Strict |
| Custom fields | Same as field name | HttpOnly, Secure, SameSite=Strict |

### Additional Response Headers

Some metadata can also be returned as response headers for easier client processing:

| Metadata Field | Response Header |
|---------------|-----------------|
| `processing_time_ms` | `X-Processing-Time-Ms` |
| `openai/outputTemplate` | `X-OpenAI-Output-Template` |
| `openai/widgetAccessible` | `X-OpenAI-Widget-Accessible` |

### Benefits of RESTful Approach

1. **Standard HTTP Semantics**: Leverages existing HTTP headers and cookies
2. **Cleaner Request Bodies**: Preferences and session state separated from business logic
3. **Better Caching**: Standard HTTP caching headers can be used
4. **Simpler Clients**: No need to manage session tokens in request body
5. **Security**: Cookies can use standard security attributes (HttpOnly, Secure, SameSite)