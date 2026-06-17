"""

main.py

This module defines the entry point for the LM Chat application.

The main function includes the following steps:
- Parse command-line arguments for host and port.
- Set up logging configuration.
- Start the Uvicorn server with the specified host and port.

Author: P Tunis
"""

import argparse
import logging
import os

from dotenv import load_dotenv
load_dotenv()

# set up logging configuration to local log folder with timestamped log files
os.makedirs("logs", exist_ok=True)
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
log_file = os.path.join("logs", f"lm_chat.log")

logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]

)
logger = logging.getLogger(__name__)

import uvicorn

from app import app


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Run the LM Chat application.")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address to bind the server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    args = parser.parse_args()

    logger.info(f"Starting LM Chat application on {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)
