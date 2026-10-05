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

client = httpx.Client(timeout=60.0)  # Set a read timeout of 60 seconds
MAX_MESSAGES = 6  # Maximum number of messages to keep in the conversation history


def handle_response(response, prompt: str, conversation_id: int):
    global total_tokens_used

    if response.status_code != 200:
        raise Exception(f"Request failed with status_code: {response.status_code} and error: {response.text}")

    response_data = response.json()
    input_tokens = response_data["usage"]["prompt_tokens"]
    output_tokens = response_data["usage"]["completion_tokens"]
    total_tokens = response_data["usage"]["total_tokens"]
    print(f"Input Tokens used for this turn : {input_tokens}")
    print(f"Total Tokens used for this turn : {total_tokens}")
    total_tokens_used += total_tokens
    print(f"Total Tokens used so far : {total_tokens_used}")

    assistant_content = response_data["choices"][0]["message"]["content"]
    
    response = {
        "role": "assistant",
        "content": assistant_content,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "total_tokens_used": total_tokens_used,
        "conversation_id": conversation_id
    }
    return response


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

    print(f"length of conversation history: {len(conversation_history)}")
    if len(conversation_history) > MAX_MESSAGES:
        compaction_result, last_message_id = compact_conversation(conversation_id)
        print(f"Compaction result: {compaction_result} and last message id: {last_message_id}")
        update_conversation_summary(conversation_id, compaction_result, last_message_id)

        
    
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "developer", "content": "summary_message"},
            *[{"role": message.role, "content": message.text} for message in conversation_history],
            {"role": "user", "content": prompt}
            ],
    }
    
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
    summary = " ".join([msg.text for msg in messages])

    # call the LLM to summarize the conversation
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that summarizes conversations."},
            {"role": "user", "content": f"Please summarize the following conversation: {summary}, dont delete any important information, facts, just summarize it in a concise manner."}
        ],
    }
    response = client.post(url, headers=headers, json=data)
    if response.status_code != 200:
        raise Exception(f"Request failed with status_code: {response.status_code} and error: {response.text}")
    response_data = response.json()
    summary_content = response_data["choices"][0]["message"]["content"] 
    last_message_id = messages[-1].id if messages else None  # return last message id to update the summary in the database
    print(f"Compacted conversation last message id: {last_message_id}")
    return summary_content, last_message_id