# 🤖 lm-chat

> A user-friendly chat interface wrapper for LM Studio powered by FastAPI and Uvicorn.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 📖 Overview

**lm-chat** provides a clean, intuitive chat interface for interacting with local large language models. It wraps around LM Studio's API (or any compatible server) to deliver a seamless conversational experience with persistent chat history stored in SQLite.

### ✨ Features

- 🎨 **Clean Chat Interface** - User-friendly form-based UI
- 💾 **Persistent History** - All conversations saved locally via SQLite
- 🚀 **Fast & Lightweight** - Built on FastAPI + Uvicorn for optimal performanc
- 📱 **Local Network Ready** - Access from multiple devices on your network

---

## 🚀 Quickstart Guide

### Prerequisites

1. **LM Studio 0.3.6 or newer Installed** - Download from [lmstudio.ai](https://lmstudio.ai/)
2. **Python 3.8+** - With pip package manager
3. **Models Loaded** - Ensure you have at least one model downloaded in LM Studio

---

## 📦 Installation & Setup

### Step 1: Configure LM Studio Server

If you haven't already set up the LM Studio server on the machine you intend to run your LMs:

1. Download and install LM Studio
2. Install your model(s) you would like to use and configure a server through the app.
   Open LM Studio and navigate to the **Server** tab
3. Start the local server (default port: `1234`)
4. _(Optional)_ Create an API key for authentication via Settings → API Keys

> 📚 For detailed setup instructions, see the [LM Studio Developer Documentation](https://lmstudio.ai/docs/developer)

LM Chat uses two endpoints on the LM Studio Server:

1. `GET /api/v1/models` for accessing the list of installed models
2. `POST /api/v1/chat` for posting a new chat prompt.

---

### Step 2: Install the Wrapper

```bash
# Clone the repository
git clone <repository-url>
cd lm-chat

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

### Step 3: Configure Environment Variables

Create a `.env` file in the project root (same directory as `main.py`):

```env
# LM Studio server address and port
LM_API_URL=http://localhost:1234

# Optional: API token for authentication
LM_API_TOKEN=your-api-token-here
```

**Example configurations:**

| Scenario                  | LM_API_URL                  |
| ------------------------- | --------------------------- |
| Localhost (default)       | `http://localhost:1234/`    |
| Same machine, custom port | `http://127.0.0.1:8080/`    |
| Network access            | `http://192.168.1.100:1234` |

---

### Step 4: Run the Server

```bash
# Default run (binds to 127.0.0.1:8000)
python main.py

# Custom host and port
python main.py --host 0.0.0.0 --port 8080
```

**Access the interface:** Open your browser at `http://localhost:8000` (or your configured address).

---

## ⚙️ Configuration Options

### Command-Line Arguments

| Argument | Default     | Description             |
| -------- | ----------- | ----------------------- |
| `--host` | `127.0.0.1` | Host to bind the server |
| `--port` | `8000`      | Port to listen on       |

### Environment Variables

| Variable       | Required | Default | Description                        |
| -------------- | -------- | ------- | ---------------------------------- |
| `LM_API_URL`   | ✅ Yes   | —       | Full URL to LM Studio API endpoint |
| `LM_API_TOKEN` | ❌ No    | —       | Bearer token for authentication    |

---

## 🗄️ Chat History & Database

All chat messages are automatically saved to a local SQLite database:

- **Database File:** `lm_chat.db` (created in project root on first run)
- **Automatic Creation:** The database is created and initialized on first launch
- **Persistence:** All conversations persist across sessions

### Resetting Chat History

To start fresh, simply delete the database file:

```bash
rm lm_chat.db  # Or delete via your OS file manager
```

---

## 🔧 Troubleshooting

| Issue                                | Solution                                                             |
| ------------------------------------ | -------------------------------------------------------------------- |
| **Connection refused**               | Verify LM Studio server is running and `LM_API_URL` is correct       |
| **Authentication failed**            | Ensure `LM_API_TOKEN` matches a valid API key in LM Studio           |
| **Cannot access from other devices** | Use `--host 0.0.0.0` to bind to all network interfaces               |
| **Port already in use**              | Change port with `--port <new-port>` or stop the conflicting service |

---

## ⚠️ Security Note

> The FastAPI application currently does not implement authentication for the chat interface itself. When binding to `0.0.0.0` for network access, ensure you're on a trusted local network or add external authentication (e.g., reverse proxy with auth).

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. For the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🔗 Links

- **LM Studio:** [https://lmstudio.ai](https://lmstudio.ai)
- **FastAPI Docs:** [https://fastapi.tiangolo.com](https://fastapi.tiangolo.com)
- **Uvicorn Docs:** [https://uvicorn.dev/](https://uvicorn.dev/)

---
