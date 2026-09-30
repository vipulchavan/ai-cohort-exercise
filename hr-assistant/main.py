from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn
from llm.llm_client import call_llm

app = FastAPI()
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class ChatRequest(BaseModel):
    user_input: str


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
def chat_with_hr_assistant_post(request: ChatRequest):
    return call_llm(request.user_input)

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)