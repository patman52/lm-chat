
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

    # Handle new chat creation logic here
    return JSONResponse(content={"status": "success", "chat_id": chat.id})


@app.post("/chat/new-message")
async def new_message(request: Request):
    data = await request.json()

    chat_id = data.get("chat_id")
    sender = data.get("sender")
    message = data.get("message")

    app.state.db.create_chat_message(chat_id, sender, message)

    # Handle new message logic here (e.g., save to database)
    return JSONResponse(content={"status": "success", "chat_id": chat_id, "sender": sender, "message": message})


@app.post("/chat/send")
async def send_prompt(request: Request):
    data = await request.json()
    message = data.get("message")
    model = data.get("model")

    if not message or not model:
        return {"error": "Message and model are required."}

    response = chat_client.send_prompt(message, model)

    return JSONResponse(content={"status": "success", "response": response})

