# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""
Post-query processing for NLWeb handlers.
Handles map detection, summarization, and other post-ranking tasks.

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

        # Always check for map opportunities
        await self.check_and_send_map_message()

        # Check if summarize mode is enabled
        if 'summarize' in self.handler.modes:
            await self.summarize_results()

    async def check_and_send_map_message(self):
        """Check if at least half of the results have addresses and send a map message if so."""
        try:
            # Get the final ranked answers
            results = getattr(self.handler, 'final_ranked_answers', [])
            if not results:
                return

            # Count results with addresses and collect map data
            results_with_addresses = []

            for result in results:
                # Try to extract address from various schema.org formats
                address = self._extract_address(result)

                if address:
                    results_with_addresses.append({
                        'title': result.get('name', 'Unnamed'),
                        'address': str(address)
                    })

            # Check if at least half have addresses
            total_results = len(results)
            results_with_addr_count = len(results_with_addresses)

            if results_with_addr_count >= total_results / 2 and results_with_addr_count > 0:
                # Send the map message as a v0.54 result
                map_result = {
                    '@type': 'LocationMap',
                    'locations': results_with_addresses
                }
                await self.handler.send_results([map_result])

        except Exception as e:
            # Don't fail the whole post-processing if map generation fails
            pass

    def _extract_address(self, result):
        """Extract address from a result object."""
        # Check various possible locations for address data
        address = None

        # Check top-level address fields
        for field in ['address', 'location', 'streetAddress', 'postalAddress']:
            if field in result:
                address = result[field]
                break

        if not address:
            return None

        # If address is a string with embedded dict, clean it
        if isinstance(address, str) and "{" in address:
            address = address.split(", {")[0]

        # If address is a dict, convert to string
        elif isinstance(address, dict):
            address_parts = []
            for field in ['streetAddress', 'addressLocality', 'addressRegion', 'postalCode']:
                if field in address:
                    value = address[field]
                    if not isinstance(value, dict):
                        address_parts.append(str(value))

            # Handle country separately
            if 'addressCountry' in address:
                country = address['addressCountry']
                if isinstance(country, dict) and 'name' in country:
                    address_parts.append(country['name'])
                elif isinstance(country, str) and not country.startswith('{'):
                    address_parts.append(country)

            if address_parts:
                address = ', '.join(address_parts)
            else:
                address = None

        return address

    async def summarize_results(self):
        """Generate and send a summary of the top results."""
        try:
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

        except Exception as e:
            # Don't fail if summarization fails
            pass
