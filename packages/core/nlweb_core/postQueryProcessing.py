# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""
Post-query processing for NLWeb handlers.
Handles summarization and other post-ranking tasks.

WARNING: This code is under development and may undergo changes in future releases.
Backwards compatibility is not guaranteed at this time.
"""

import asyncio
from nlweb_core.llm import ask_llm
from nlweb_core.utils import fill_prompt_variables


class PostQueryProcessing:
    """Post-processing after ranking is complete."""

    SUMMARIZE_RESULTS_PROMPT = ["""Summarize the following search results in 2-3 sentences, highlighting the key information that answers the user's question: {request.query}

Results:
{results}""",
        {"summary": "A 2-3 sentence summary of the results"}
    ]

    def __init__(self, handler):
        self.handler = handler

    async def do(self):
        """Execute post-query processing based on mode."""
        if not self.handler.connection_alive_event.is_set():
            return

        # Check if summarize mode is enabled
        if 'summarize' in self.handler.modes:
            await self.summarize_results()

    async def summarize_results(self):
        """Generate and send a summary of the top results."""
        # Get top 3 results for summarization
        results = getattr(self.handler, 'final_ranked_answers', [])
        if not results:
            return

        top_results = results[:3]

        # Build results text for prompt
        results_text = []
        for i, result in enumerate(top_results, 1):
            name = result.get('name', 'Unknown')
            description = result.get('description', '')
            results_text.append(f"{i}. {name}: {description}")

        # Prepare prompt variables
        prompt_vars = {
            "request.query": self.handler.query.text,
            "results": "\n".join(results_text)
        }

        prompt_str, schema = self.SUMMARIZE_RESULTS_PROMPT
        prompt = fill_prompt_variables(prompt_str, {}, prompt_vars)

        # Call LLM for summarization
        response = await ask_llm(prompt, schema, level='high', timeout=20)

        if response and 'summary' in response:
            # Send summary as a v0.54 result
            summary_result = {
                '@type': 'Summary',
                'text': response['summary']
            }
            await self.handler.send_results([summary_result])
