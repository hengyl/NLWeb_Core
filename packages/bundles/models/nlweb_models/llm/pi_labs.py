import asyncio
import httpx
import json

import time
import os


class PiLabsClient:
    """PiLabsClient accesses a Pi Labs scoring API.
    It lazily initializes the client it will use to make requests."""
    lock = asyncio.Lock()
    client: httpx.AsyncClient | None = None
    concurrency_limit = asyncio.Semaphore(5)

    @classmethod
    async def score(cls, query: str, answer: str) -> tuple[float, float]:
        async with cls.lock:
            if cls.client is None:
                cls.client = httpx.AsyncClient(
                    http2=True,
                    timeout=10.0,
                    limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
                )
        async with cls.concurrency_limit:
            start_time = time.perf_counter()
            resp = await cls.client.post(
                url="http://localhost:8000/invocations",
                json={
                    "llm_input": query,
                    "llm_output": answer,
                    "scoring_spec": [
                        {'question': 'Is this response relevant?'},
                        {'question': 'Is this response helpful?'}
                    ]
                }
            )
            resp.raise_for_status()

            time_taken = round(time.perf_counter() - start_time, 2)
            score = resp.json().get("total_score", 0) * 100
            return score, time_taken

async def pi_score_item(query, answer):
    return await PiLabsClient.score(query, answer)

async def pi_scoring_comparison(file):
    # Generate output filename
    base_name = file.rsplit('.', 1)[0] if '.' in file else file
    output_file = f"{base_name}_pi_eval.csv"

    with open(file, 'r') as f:
        lines = f.readlines()
        data = []
        for line in lines:
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    tasks = []
    async with asyncio.TaskGroup() as tg:
        for item in data:
            tasks.append(tg.create_task(process_item(item)))
        
    with open(output_file, 'a') as f:
        for task in tasks:
            score, pi_score, csv_line = task.result()
            if (score > 64 or pi_score > 30):
                print(csv_line)
            f.write(csv_line + '\n')

async def process_item(item):
    item_fields = {
        "url": item.get("url", ""),
        "name": item.get("name", ""),
        "site": item.get("site", ""),
        "siteUrl": item.get("site", ""),
        "score": item.get("ranking", {}).get("score", 0),
        "description": item.get("ranking", {}).get("description", ""),
        "schema_object": item.get("schema_object", {}),
        "query": item.get("query", "")
    }
    desc = json.dumps(item_fields["schema_object"])
    pi_score, time_taken = await pi_score_item(item['query'], desc)
    score = item_fields['score']
            
    item['ranking']['score'] = pi_score
    csv_line = f"O={score},P={pi_score},T={time_taken},Q={item_fields['query']},N={item_fields['name']}" #,D={item_fields['description']}"

    if (score > 64 or pi_score > 30):
        print(csv_line)
    return score, pi_score, csv_line
            
       

     

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 -m nlweb_models.llm.pi_labs <input_file.jsonl>")
        sys.exit(1)

    input_file = sys.argv[1]
    asyncio.run(pi_scoring_comparison(input_file))