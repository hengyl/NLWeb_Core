#!/usr/bin/env python3
"""
Standalone test script to debug LLM summarization issue.
"""

import asyncio
import os
import json
from openai import AsyncAzureOpenAI

async def test_azure_openai():
    """Test Azure OpenAI completion directly."""

    # Load from environment
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "https://yoastoai.openai.azure.com/")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    api_version = "2024-02-15-preview"
    model = "gpt-4.1"

    print(f"Endpoint: {endpoint}")
    print(f"API Key: {api_key[:10]}..." if api_key else "API Key: None")
    print(f"API Version: {api_version}")
    print(f"Model: {model}")
    print()

    # Create client
    client = AsyncAzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
        timeout=30.0
    )

    print("Client created successfully")

    # The prompt and schema from the logs
    prompt = """Summarize the following search results in 2-3 sentences, highlighting the key information that answers the user's question: Are there movies about AI that might be suitable for a pre-teen who might get easily scared? could you make some recommendations?

Results:
1. The Iron Giant: A young boy befriends a giant robot from outer space that a paranoid government agent wants to destroy.
2. The Invisible Boy: A ten-year-old boy and Robby the Robot team up to prevent a Super Computer from controlling the Earth from a satellite.
3. Robotbror: In the near future, all children have their own robot assistants. Eleven-year-old Alberte receives Konrad, the most lifelike robot ever seen, for her birthday, and she quickly begins to feel a real connection with him."""

    schema = {"summary": "A 2-3 sentence summary of the results"}
    system_prompt = f"Provide a response that matches this JSON schema: {json.dumps(schema)}"

    print(f"System Prompt: {system_prompt}")
    print(f"User Prompt: {prompt[:100]}...")
    print()

    try:
        print("Calling Azure OpenAI...")
        response = await asyncio.wait_for(
            client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=512,
                temperature=0.7,
                top_p=0.1,
                stream=False,
                presence_penalty=0.0,
                frequency_penalty=0.0,
                model=model
            ),
            timeout=20.0
        )

        print("Response received!")
        print(f"Response object: {response}")
        print()

        if response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content
            print(f"Content: {content}")

            # Try to parse as JSON
            try:
                parsed = json.loads(content)
                print(f"Parsed JSON: {parsed}")
                if 'summary' in parsed:
                    print(f"\nSUMMARY: {parsed['summary']}")
                else:
                    print("\nNo 'summary' key in response")
            except json.JSONDecodeError as e:
                print(f"Failed to parse as JSON: {e}")
                print("Trying to extract JSON from content...")
                # Try to find JSON in content
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    try:
                        parsed = json.loads(json_match.group())
                        print(f"Extracted JSON: {parsed}")
                    except:
                        print("Could not extract valid JSON")
        else:
            print("No choices in response")

    except asyncio.TimeoutError:
        print("ERROR: Request timed out")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    # Also try to load from set_keys.sh if it exists
    import subprocess
    try:
        result = subprocess.run(
            ['bash', '-c', 'source set_keys.sh && env'],
            capture_output=True,
            text=True,
            cwd='/Users/rvguha/code/NLWeb_Core'
        )
        for line in result.stdout.split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                if key.startswith('AZURE_'):
                    os.environ[key] = value
    except Exception as e:
        print(f"Could not load set_keys.sh: {e}")

    asyncio.run(test_azure_openai())
