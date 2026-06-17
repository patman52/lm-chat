"""
app.py

This module defines the FastAPI application for the LM Chat application. 
It sets up the API endpoints for handling chat interactions, including creating new chats, sending messages, and retrieving chat history.

Author: P Tunis
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from chat_client import ChatClient
from db import db


_PROJECT_ROOT = Path(__file__).parent

chat_client = ChatClient()

def get_models():
    chat_client.get_available_models()

def init_db():
    db.create_schema()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    get_models()
    yield

app = FastAPI(lifespan=lifespan)

app.state.chat_client = chat_client
app.state.db = db
app.mount("/static", StaticFiles(directory=str(_PROJECT_ROOT / "static")), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/")
def redirect_to_chat():
    return RedirectResponse(url="/chat")


@app.get("/chat", response_class=HTMLResponse)
def chat(request: Request):

    context = {
        "request": request,
        "model_names": chat_client.model_names
    }

    return templates.TemplateResponse(request, "base.html", context)


@app.get("/chat/{chat_id}")
def get_chat_history(request: Request, chat_id: int):
    chat_messages = app.state.db.get_chat_messages(chat_id)
    # todo add file context to the messages data if it exists for each message in the chat history, so that it can be displayed in the UI along with the sender and message content
    messages_data = [{"sender": msg.sender, "message": msg.message} for msg in chat_messages]
    return JSONResponse(content={"status": "success", "messages": messages_data})


@app.get("/chats")
def get_chats(request: Request, title_query: str = None, max_results: int = 25):
    chats = app.state.db.get_multiple_chats(title_query, max_results)
    return JSONResponse(content={
        "status": "success",
        "chats": [{"title": chat.title, "id": chat.id} for chat in chats]
    })


@app.post("/chat/new")
async def new_chat(request: Request):
    data = await request.json()
    chat_title = data.get("title", "New Chat")
    chat = app.state.db.create_chat(chat_title)

    return JSONResponse(content={"status": "success", "chat_id": chat.id})


@app.post("/chat/new-message")
async def new_message(request: Request):
    data = await request.json()

    chat_id = data.get("chat_id")
    sender = data.get("sender")
    message = data.get("message")
    file_context = data.get("file_context")  # Optional field for file attachment content

    app.state.db.create_chat_message(chat_id, sender, message, file_context)

    return JSONResponse(content={"status": "success", "chat_id": chat_id, "sender": sender, "message": message})


@app.post("/chat/send")
async def send_prompt(request: Request):
    data = await request.json()
    message = data.get("message")
    model = data.get("model")
    file_context = data.get("file_context")  # Optional field for file attachment content

    if (not message and not file_context) or not model:
        return {"error": "Message, file context, and model are required."}

    # combine the message and file context into a single prompt for the chat client
    if file_context is not None:
        if message:
            prompt = f"{message}\n\nFile Context:\n{file_context}"
        else:
            prompt = f"File Context:\n{file_context}"
    else:
        prompt = message

    response = chat_client.send_prompt(prompt, model)

    return JSONResponse(content={"status": "success", "response": response})


@app.delete("/chat/{chat_id}")
async def delete_chat(request: Request, chat_id: int):
    app.state.db.delete_chat(chat_id)
    return JSONResponse(content={"status": "success", "chat_id": chat_id})
