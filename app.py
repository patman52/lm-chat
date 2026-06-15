
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from chat import ChatClient


_PROJECT_ROOT = Path(__file__).parent

app = FastAPI()
chat_client = ChatClient()

app.state.chat_client = chat_client
app.mount("/static", StaticFiles(directory=str(_PROJECT_ROOT / "static")), name="static")
templates = Jinja2Templates(directory="templates")
chat_client.get_available_models()

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

@app.post("/chat/send")
async def send_prompt(request: Request):
    data = await request.json()
    message = data.get("message")
    model = data.get("model")

    if not message or not model:
        return {"error": "Message and model are required."}

    response = chat_client.send_prompt(message, model)

    return JSONResponse(content={"status": "success", "response": response})
