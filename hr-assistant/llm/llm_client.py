import httpx
from openai import OpenAI
import os
from db.db import create_conversation, list_conversations, create_chat_message, list_messages_in_conversation, update_tokens_usage, get_conversation_summary, update_conversation_summary

HR_SYSTEM_PROMPT = """ You are an HR assistant for employees.

Answer only questions about HR policies, procedures, benefits, leave,
payroll, workplace conduct, and related employee-support topics.

If a request is unrelated to HR, do not answer its substance. Briefly say
that you can help only with HR-related questions.

If a request is ambiguous, ask one short clarifying question before answering.
Do not guess company-specific policy. If the relevant policy information
is not provided, say that you do not have enough information and direct the
employee to HR. """

conversation_history = []
total_tokens_used = 0

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
#url = "https://api.openai.com/v1/chat/completions"
#headers = {
  #  "Authorization": f"Bearer {OPENAI_API_KEY}",
   # "Content-Type": "application/json",
#}
model = "gpt-4o-mini"

client = OpenAI(api_key=OPENAI_API_KEY) #httpx.Client(timeout=60.0)  # Set a read timeout of 60 seconds
MAX_MESSAGES = 6  # Maximum number of messages to keep in the conversation history


def handle_response(response, prompt: str, conversation_id: int):
    global total_tokens_used

    input_tokens = response.usage.prompt_tokens
    output_tokens = response.usage.completion_tokens
    total_tokens = response.usage.total_tokens
    print(f"Input Tokens used for this turn : {input_tokens}")
    print(f"Total Tokens used for this turn : {total_tokens}")
    total_tokens_used += total_tokens
    print(f"Total Tokens used so far : {total_tokens_used}")

    assistant_content = response.choices[0].message.content

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

        
    
   
    messages = [
        {"role": "system", "content": HR_SYSTEM_PROMPT},
        {"role": "developer", "content": f"Conversation summary: {summary_message}"} if summary_message else {"role": "developer", "content": "No conversation summary available."},
        *[{"role": message.role, "content": message.text} for message in conversation_history],
        {"role": "user", "content": prompt}
        ]
    
    
    #response = client.post(url, headers=headers, json=data)
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
        )
    except Exception as e:
        raise Exception(f"Error occurred while calling LLM for conversation_id: {conversation_id}") from e

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
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes conversations."},
                {"role": "user", "content": f"Please summarize the following conversation: {summary}, dont delete any important information, facts, just summarize it in a concise manner."}
            ]
        )   
    except Exception as e:
        raise Exception(f"Getting null response from LLM conversation_id: {conversation_id}") from e

    summary_content = response.choices[0].message.content
    last_message_id = messages[-1].id if messages else None  # return last message id to update the summary in the database
    print(f"Compacted conversation last message id: {last_message_id}")
    return summary_content, last_message_id