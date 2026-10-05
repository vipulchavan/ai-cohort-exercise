from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn
from llm.llm_client import call_llm
from db.db import create_conversation, list_conversations, create_chat_message, list_messages_in_conversation, update_tokens_usage

app = FastAPI()
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class ChatRequest(BaseModel):
    user_input: str
    conversation_id: int | None = None


@app.get("/")
def chat_page():
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/greet")
def greet(name: str="World"):
    return {"message": f"Hello, {name}!"}

@app.get("/chat")
def chat_with_hr_assistant(user_input: str):
    response = call_llm(user_input)
    return response


@app.post("/chat")
def chat_with_hr_assistant_post(user_input: str, conversation_id: int | None = None):
    
    response =  call_llm(user_input, conversation_id)
    print(f"LLM response: {response}")
    create_chat_message(conversation_id=response["conversation_id"], text=user_input, role="user", tokens_spent=response["input_tokens"])
    create_chat_message(conversation_id=response["conversation_id"], text=response["content"], role="assistant", tokens_spent=response["output_tokens"])
    
    update_tokens_usage(response["conversation_id"], response["total_tokens"])
    return {"response" : response}

if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000)