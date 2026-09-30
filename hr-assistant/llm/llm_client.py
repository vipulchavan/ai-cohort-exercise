import httpx
import os

conversation_history = []
total_tokens_used = 0


def handle_response(response, prompt: str):
    global total_tokens_used

    if response.status_code != 200:
        raise Exception(f"Request failed with status_code: {response.status_code} and error: {response.text}")

    response_data = response.json()
    total_tokens = response_data["usage"]["total_tokens"]
    print(f"Total Tokens used for this turn : {total_tokens}")
    total_tokens_used += total_tokens
    print(f"Total Tokens used so far : {total_tokens_used}")

    assistant_content = response_data["choices"][0]["message"]["content"]
    conversation_history.append({"role": "user", "content": prompt})
    conversation_history.append({"role": "assistant", "content": assistant_content})
    return {
        "role": "assistant",
        "content": assistant_content,
        "total_tokens": total_tokens,
        "total_tokens_used": total_tokens_used,
    }


def call_llm(prompt: str):
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            *conversation_history,
            {"role": "user", "content": prompt}
            ],
    }
    client = httpx.Client()
    response = client.post(url, headers=headers, json=data)
    return handle_response(response, prompt)