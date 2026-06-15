import os
import json
from typing import List, Optional

import requests
from dotenv import load_dotenv

load_dotenv()


class ChatClient:
    def __init__(self):
        self.api_token = self.load_api_token()
        self.api_url = self.load_api_url()
        self.models: List[str] = []

        if not self.api_token:
            raise ValueError("LM API token not found. Please set the LM_API_TOKEN environment variable.")
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


    def get_available_models(self, verbose: bool = False) -> None:
        """
        Get the list of available models from the LM, loads the associated data and print them.

        Args:
            verbose (bool): Whether to print the list of models. Defaults to False.

        Returns:
            None
        """
        response = requests.get(
            f"{self.api_url}/models",
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
        )

        response.raise_for_status()

        reponse_data = response.json()
        if "models" in reponse_data:
            self.models = reponse_data["models"]

        if verbose:
            print(json.dumps(reponse_data, indent=2))
        else:
            # just print the model names
            model_names = [model["display_name"] for model in self.models]
            print("Available models:")
            for model in model_names:
                print(model)


    def send_prompt(self, message: str, model: str) -> None:
        """
        Send a prompt to the LM API and print the response.

        Args:
            message (str): The prompt to send to the LM API.
            model (str): The name of the model to use for generating the response.
        Returns:
            None
        """
        response = requests.post(
            f"{self.api_url}/chat",
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "input": message
            }
        )
        print(json.dumps(response.json(), indent=2))
