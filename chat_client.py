"""
chat_client.py

This module defines the ChatClient class, which provides methods for interacting with the LM API.

The ChatClient class includes the following methods:
- load_api_token: Loads the LM API token from the environment variable.
- load_api_url: Loads the LM API URL from the environment variable.
- model_names: A property that returns the list of available model display names.
- get_available_models: Retrieves the list of available models from the LM API and loads the associated
    data.
- send_prompt: Sends a prompt to the LM API and returns the response.

Author: P Tunis
"""

import os
import json
import logging
from typing import List, Optional

import requests

logger = logging.getLogger(__name__)

ENDPOINTS = {
    "models": "/api/v1/models",
    "chat": "/api/v1/chat"
}


class ChatClient:
    def __init__(self):
        self.api_token = self.load_api_token()
        self.api_url = self.load_api_url()
        self._models: List[str] = []

        if not self.api_token:
            logger.warning("LM API token not found. Please set the LM_API_TOKEN environment variable if using authentication.")
        if not self.api_url:
            raise ValueError("LM API URL not found. Please set the LM_API_URL environment variable.")

    @staticmethod
    def load_api_token() -> Optional[str]:
        """
        Load the LM API token from the environment variable.

        Returns:
            Optional[str]: The LM API token if available, otherwise None.
        """
        return os.environ.get("LM_API_TOKEN")

    @staticmethod
    def load_api_url() -> Optional[str]:
        """
        Load the LM API URL from the environment variable.

        Returns:
            Optional[str]: The LM API URL if available, otherwise None.
        """
        return os.environ.get("LM_API_URL")


    @property
    def model_names(self) -> List[str]:
        """
        Get the list of available models.

        Returns:
            List[str]: The list of available models.
        """
        return [model["display_name"] for model in self._models]

    def test_connection(self) -> bool:
        """
        Test available endpoints to ensure the LM API is reachable and the API token is valid.
        Returns:
            bool: True if the connection is successful, False otherwise.
        """
        
        try:
            self.get_available_models()
            logger.info("Successfully connected to LM API and retrieved available models.")
            return True
        except requests.RequestException as e:
            logger.error(f"Error connecting to LM API: {e}")
            return False
        except Exception:
            logger.exception(f"Unknown error connecting to LM API")
            return False
    

    def get_available_models(self, verbose: bool = False) -> None:
        """
        Get the list of available models from the LM and loads the associated data.

        Args:
            verbose (bool): Whether to print the list of models. Defaults to False.

        Returns:
            None
        """
        response = requests.get(
            f"{self.api_url}{ENDPOINTS['models']}",
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
        )

        response.raise_for_status()

        response_data = response.json()
        if "models" in response_data:
            self._models = response_data["models"]

        if verbose:
            logger.info(json.dumps(response_data, indent=2))

    def _get_model_key_by_name(self, model_name: str) -> Optional[str]:
        """
        Get the model key by its display name.

        Args:
            model_name (str): The display name of the model.

        Returns:
            Optional[str]: The model key if found, otherwise None.
        """
        for model in self._models:
            if model["display_name"] == model_name:
                return model["key"]
        return None

    def send_prompt(self, message: str, model_name: str) -> str:
        """
        Send a prompt to the LM API and print the response.

        Args:
            message (str): The prompt to send to the LM API.
            model_name (str): The name of the model to use for generating the response.
        Returns:
            str: The response from the LM API.
        """
        model_key = self._get_model_key_by_name(model_name)
        if not model_key:
            raise ValueError(f"Model '{model_name}' not found.")

        headers = {
            "Content-Type": "application/json"
        }

        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"

        try:
            response = requests.post(
                f"{self.api_url}{ENDPOINTS['chat']}",
                headers=headers,
                json={
                    "model": model_key,
                    "input": message
                }
            )
            response.raise_for_status()
            response_data = response.json()

            return response_data.get("output", "")
        except requests.RequestException as e:
            logger.exception(f"Error sending prompt to LM API: {e}")
            raise
        
