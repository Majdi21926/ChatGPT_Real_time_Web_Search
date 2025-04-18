import yaml
import os
from pyprojroot import here

class LoadConfig:
    """
    A class for loading configuration settings, including OpenAI credentials.
    """
    def __init__(self) -> None:
        """
        Initializes the LoadConfig instance by loading configuration from a YAML file.
        """
        with open(here("configs/app_config.yml")) as file:
            config = yaml.safe_load(file)

        self.gpt_model = config['gpt_model']
        self.temperature = config['temperature']
        self.llm_system_role = config['llm_system_role']
        self.llm_function_caller_system_role = config['llm_function_caller_system_role']
        
        # Charger la clé API depuis le fichier YAML
        self.api_key = config['openai']['api_key']
        self.api_version = config['openai']['api_version']

        # Charger la clé API dans la configuration d'OpenAI
        self.load_openai_credentials()
    
    def load_openai_credentials(self):
        """
        Loads OpenAI API credentials and sets them in the OpenAI library.
        """
        import openai
        openai.api_key = self.api_key
        openai.api_version = self.api_version
        if openai.api_key is None:
            raise ValueError("OpenAI API key not found in the config.")
