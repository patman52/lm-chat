# lm-chat

Basic Chat Interface Wrapper for LM Studio or a similar LM server using a user-friendly chat form. The form is served via Uvicorn with a FastAPI backend.

## Quickstart

This wrapper is currently set up to interface with an LM Studio server, either run on localhost or over a local network.

### Install LM Studio

If a local LM Studio server is already set up, you can skip this section.

On the machine you plan to host your LMs from, download an install [LM Studio](https://lmstudio.ai/).

Please take a moment to familiarize yourself with their [documentation](https://lmstudio.ai/docs/developer) before proceeding. You must first download and install the models you would like to use. Also, if running on a local network, it is advisable to create API keys for authentication.

### Install the Wrapper

Clone this repo, create a .venv and install the dependencies `pip install -r requirements`

### Connect the Wrapper

Create a .env file in the same report as `main.py`.

Add the variable `LM_API_URL=<hostname:port>/api/v1`, updating the host name / IP and port to the adress where your LM Studio server is running.

If using authentication, add another variable `LM_API_TOKEN=<insert your API token here>` and update with your API token.

### Run the Wrapper

Activate your .venv and run the command: `python main.py` to run the Uvicorn server.

By default, the server will bind to "127.0.0.1:8000". To specify a different host or port use the `--host` or `--port` optional args when running the command:

`python main.py --host 127.0.0.1 --port 8080`

Note that while the uvicorn server can be hosted to 0.0.0.0 for use on a local network server, the FastAPI app currently does not support any authetication.

### Chat History

This app uses a local sqlite database to save chat messages and history. This database will be created automatically the first time the app is ran.
