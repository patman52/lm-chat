import argparse

import uvicorn

from app import app


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Run the LM Chat application.")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address to bind the server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    args = parser.parse_args()

    uvicorn.run(app, host=args.host, port=args.port)
