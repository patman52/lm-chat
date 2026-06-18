"""
app.py

This module defines the FastAPI application for the LM Chat application. 
It sets up the API endpoints for handling chat interactions, including creating new chats, sending messages, and retrieving chat history.

Author: P Tunis
"""

import json
import logging
import os
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import requests

try:
    import tiktoken
except ImportError:
    tiktoken = None

from chat_client import ChatClient
from db import db


_PROJECT_ROOT = Path(__file__).parent

MAX_FILE_CONTEXT_TOKENS = int(os.environ.get("LM_CHAT_MAX_FILE_CONTEXT_TOKENS", os.environ.get("LM_CHAT_MAX_FILE_CONTEXT_CHARS", "20000")))
TRUNCATION_NOTICE_TEMPLATE = "\n[Content truncated; {omitted_tokens} tokens omitted to keep the prompt within the file context budget.]"

chat_client = ChatClient()


@lru_cache(maxsize=1)
def _get_token_encoder():
    if tiktoken is None:
        return None

    try:
        return tiktoken.get_encoding("cl100k_base")
    except Exception:
        logger.exception("Failed to initialize the token encoder.")
        return None


def _count_tokens(text: str) -> int:
    encoder = _get_token_encoder()
    if encoder is None:
        return len(text.split())

    return len(encoder.encode(text))


def _truncate_file_content(file_name: str, content: str, budget_remaining: int) -> tuple[Optional[str], int, Optional[str]]:
    encoder = _get_token_encoder()
    header = f"File: {file_name}\nContent: "

    if budget_remaining <= 0:
        return None, 0, f"Skipped file '{file_name}' because the file context budget was exhausted."

    header_tokens = _count_tokens(header)
    if header_tokens >= budget_remaining:
        return None, 0, f"Skipped file '{file_name}' because there was no room left for file metadata."

    if encoder is None:
        content_tokens = content.split()
        if header_tokens + len(content_tokens) <= budget_remaining:
            entry = f"{header}{content}"
            return entry, header_tokens + len(content_tokens), None

        content_budget = max(0, budget_remaining - header_tokens - _count_tokens(TRUNCATION_NOTICE_TEMPLATE.format(omitted_tokens=0)))
        kept_tokens = content_tokens[:content_budget]
        kept_content = " ".join(kept_tokens)
        omitted_tokens = len(content_tokens) - len(kept_tokens)
        entry = f"{header}{kept_content}{TRUNCATION_NOTICE_TEMPLATE.format(omitted_tokens=omitted_tokens)}"
        return entry, _count_tokens(entry), f"Truncated file '{file_name}' by {omitted_tokens} token(s)."

    content_tokens = encoder.encode(content)
    full_entry = f"{header}{content}"
    if _count_tokens(full_entry) <= budget_remaining:
        return full_entry, _count_tokens(full_entry), None

    low = 0
    high = len(content_tokens)
    best_entry = None
    best_tokens = 0
    best_kept_tokens = 0

    while low <= high:
        mid = (low + high) // 2
        kept_content = encoder.decode(content_tokens[:mid])
        omitted_tokens = len(content_tokens) - mid
        candidate_entry = f"{header}{kept_content}{TRUNCATION_NOTICE_TEMPLATE.format(omitted_tokens=omitted_tokens)}"
        candidate_tokens = _count_tokens(candidate_entry)

        if candidate_tokens <= budget_remaining:
            best_entry = candidate_entry
            best_tokens = candidate_tokens
            best_kept_tokens = mid
            low = mid + 1
        else:
            high = mid - 1

    if best_entry is None:
        return None, 0, f"Skipped file '{file_name}' because there was no remaining file context budget."

    omitted_tokens = len(content_tokens) - best_kept_tokens
    return best_entry, best_tokens, f"Truncated file '{file_name}' by {omitted_tokens} token(s)."

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

if not app.state.chat_client.test_connection():
    raise ConnectionError("Unable to connect to the LM API. Please check the API URL and token.")

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
    messages_data = [{"sender": msg.sender, "message": msg.message, "file_context": msg.file_context} for msg in chat_messages]
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


def _prepare_prompt(chat_id: int) -> tuple[str, Optional[dict]]:
    """
    Prepare the prompt for the LM API by combining the chat history and file context.

    Args:
        chat_id (int): The ID of the chat for which to prepare the prompt.
    """    
    chat_messages = app.state.db.get_chat_messages(chat_id, get_file_content=True)
    prompt_parts = []
    file_context_tokens = 0
    truncation_details = []
    file_budget_exhausted = False

    for msg in chat_messages:
        prompt_parts.append(f"{msg.sender}: {msg.message}")
        if msg.file_context and not file_budget_exhausted:
            for file_index, file_entry in enumerate(msg.file_context):
                if file_context_tokens >= MAX_FILE_CONTEXT_TOKENS:
                    remaining_files = len(msg.file_context) - file_index
                    truncation_details.append(
                        f"Skipped {remaining_files} file attachment(s) after reaching the file context budget of {MAX_FILE_CONTEXT_TOKENS} tokens."
                    )
                    file_budget_exhausted = True
                    break

                file_name = file_entry.get("file_name") or "Untitled file"
                content = file_entry.get("content") or ""
                remaining_budget = MAX_FILE_CONTEXT_TOKENS - file_context_tokens
                file_context_entry, used_tokens, truncation_detail = _truncate_file_content(file_name, content, remaining_budget)

                if file_context_entry is None:
                    if truncation_detail:
                        truncation_details.append(truncation_detail)
                    file_context_tokens = MAX_FILE_CONTEXT_TOKENS
                    file_budget_exhausted = True
                    break

                prompt_parts.append(file_context_entry)
                file_context_tokens += used_tokens
                if truncation_detail:
                    truncation_details.append(truncation_detail)

    prompt = "\n".join(prompt_parts)
    prompt_truncation = None
    if truncation_details:
        prompt_truncation = {
            "max_file_context_tokens": MAX_FILE_CONTEXT_TOKENS,
            "details": truncation_details,
        }

    return prompt, prompt_truncation

@app.post("/chat/send")
async def send_prompt(request: Request):
    data = await request.json()
    model = data.get("model")
    chat_id = data.get("chat_id")

    logger.info(f"Received request to send prompt to model '{model}' for chat ID {chat_id}")

    if not model:
        return JSONResponse(content={"status": "error", "message": "Model is required."}, status_code=400)
    
    if not chat_id:
        return JSONResponse(content={"status": "error", "message": "Chat ID is required."}, status_code=400)

    prompt, prompt_truncation = _prepare_prompt(chat_id)

    try:
        response = chat_client.send_prompt(prompt, model)
    except requests.RequestException as exc:
        lm_response = getattr(exc, "response", None)
        error_message = "The LM API rejected the prompt. Try reducing the number or size of uploaded files."

        if lm_response is not None:
            logger.error(
                "LM API error while sending prompt for chat ID %s: %s %s",
                chat_id,
                lm_response.status_code,
                lm_response.text,
            )
        else:
            logger.exception("LM API request failed while sending prompt for chat ID %s", chat_id)

        error_payload = {
            "status": "error",
            "message": error_message,
            "prompt_truncation": prompt_truncation,
        }

        if lm_response is not None:
            error_payload["lm_api_status_code"] = lm_response.status_code

        return JSONResponse(content=error_payload, status_code=502)

    return JSONResponse(content={"status": "success", "response": response, "prompt_truncation": prompt_truncation})


@app.delete("/chat/{chat_id}")
async def delete_chat(request: Request, chat_id: int):
    app.state.db.delete_chat(chat_id)
    return JSONResponse(content={"status": "success", "chat_id": chat_id})
