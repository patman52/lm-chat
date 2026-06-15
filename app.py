
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from chat import ChatClient

app = FastAPI()
chat_client = ChatClient()
app.state.chat_client = chat_client


@app.get("/")
def redirect_to_chat():
    return RedirectResponse(url="/chat")

@app.get("/chat")
def chat():
    return {"message": "Hello, World!"}

@app.get("/models")
def get_models():
    chat_client.get_available_models(verbose=False)
    return {"models": chat_client.models}
