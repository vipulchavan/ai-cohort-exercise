import httpx
import os
from db.db import create_conversation, list_conversations, create_chat_message, list_messages_in_conversation, update_tokens_usage, get_conversation_summary, update_conversation_summary


conversation_history = []
total_tokens_used = 0

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
url = "https://api.openai.com/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json",
}

MAX_MESSAGES = 10  # Maximum number of messages to keep in the conversation history


def handle_response(response, prompt: str, conversation_id: int):
    global total_tokens_used

    if response.status_code != 200:
        raise Exception(f"Request failed with status_code: {response.status_code} and error: {response.text}")

    response_data = response.json()
    input_tokens = response_data["usage"]["prompt_tokens"]
    output_tokens = response_data["usage"]["completion_tokens"]
    total_tokens = response_data["usage"]["total_tokens"]
    print(f"Total Tokens used for this turn : {total_tokens}")
    total_tokens_used += total_tokens
    print(f"Total Tokens used so far : {total_tokens_used}")

    assistant_content = response_data["choices"][0]["message"]["content"]
    conversation_history.append({"role": "user", "content": prompt})
    conversation_history.append({"role": "assistant", "content": assistant_content})
    response = {
        "role": "assistant",
        "content": assistant_content,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "total_tokens_used": total_tokens_used,
    }
    return response, conversation_id


def call_llm(prompt: str, conversation_id: int):
    if conversation_id is None:
        # If no conversation_id is provided, start a new conversation
        new_conversation = create_conversation(title=prompt)
        conversation_id = new_conversation.id
    

    conversation_history = read_messages_after_compaction(conversation_id)
    conversation_summary = get_conversation_summary(conversation_id)
    
    summary_message = None
    if conversation_summary:
        summary_message = conversation_summary.summary_text   

    if len(conversation_history) > MAX_MESSAGES:
        compaction_result = compact_conversation(conversation_id)
        update_conversation_summary(conversation_id, compaction_result)

        
    
   data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "developer", "content": "summary_message"},
            *[{"role": message["role"], "content": message["content"]} for message in conversation_history],
            {"role": "user", "content": prompt}
            ],
    }
    client = httpx.Client()
    response = client.post(url, headers=headers, json=data)
    return handle_response(response, prompt, conversation_id)

def read_messages_after_compaction(conversation_id: int):
    conversation_summary = get_conversation_summary(conversation_id)
    if conversation_summary:
        last_message_id = conversation_summary.last_message_id
        messages = list_messages_in_conversation(conversation_id)
        # Filter messages to only include those after the last_message_id
        messages = [msg for msg in messages if msg.id > last_message_id]
    else:
        messages = list_messages_in_conversation(conversation_id)
    return messages

def compact_conversation(conversation_id: int):
    messages = list_messages_in_conversation(conversation_id)
    if not messages:
        return "No messages to summarize."
    
    # Create a summary of the conversation
    summary = 