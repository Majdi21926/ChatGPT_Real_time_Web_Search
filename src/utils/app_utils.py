from typing import Dict, List
import inspect
import json
from inspect import Parameter
from pydantic import create_model, BaseModel
from utils.web_search import WebSearch
import openai
from utils.load_config import LoadConfig

APPCFG = LoadConfig()
client = openai.OpenAI(api_key=APPCFG.api_key)
model_map = {
    "GPT-3.5": "gpt-3.5-turbo",
    "GPT-4": "gpt-4"
}

class Apputils:
    @staticmethod
    def jsonschema(f) -> Dict:
        """
        Generate a JSON schema for the input parameters of the given function.
        """
        kw = {
            n: (o.annotation if o.annotation != Parameter.empty else str, 
                ... if o.default == Parameter.empty else o.default)
            for n, o in inspect.signature(f).parameters.items()
        }
        model_config = {"arbitrary_types_allowed": True}
        s = create_model(f'Input for `{f.__name__}`', __config__=model_config, **kw).schema()
        return dict(name=f.__name__, description=f.__doc__, parameters=s)

    @staticmethod
    def wrap_functions() -> List:
        """
        Wrap web search functions and generate JSON schemas for each.
        """
        return [
            Apputils.jsonschema(WebSearch.retrieve_results),
            Apputils.jsonschema(WebSearch.search_text),
            Apputils.jsonschema(WebSearch.search_pdf),
            Apputils.jsonschema(WebSearch.get_instant),
            Apputils.jsonschema(WebSearch.search_image),
            Apputils.jsonschema(WebSearch.search_video),
            Apputils.jsonschema(WebSearch.search_news),
            Apputils.jsonschema(WebSearch.search_map),
            Apputils.jsonschema(WebSearch.give_suggestion),
            Apputils.jsonschema(WebSearch.user_proxy_for_text_web_search),
        ]

    @staticmethod
    def execute_json_function(response) -> List:
        """
        Execute a function based on the response from an OpenAI ChatCompletion API call.
        """
        try:
            tool_call = response.choices[0].message.tool_calls[0]
            func_name = tool_call.function.name
            func_args = json.loads(tool_call.function.arguments)
            print(f"Executing function: {func_name} with args: {func_args}")
        except (AttributeError, IndexError, json.JSONDecodeError) as e:
            print(f"Error parsing tool call: {str(e)}")
            return []

        try:
            if func_name == 'retrieve_results':
                result = WebSearch.retrieve_results(**func_args)
            elif func_name == 'search_text':
                result = WebSearch.search_text(**func_args)
            elif func_name == 'search_pdf':
                result = WebSearch.search_pdf(**func_args)
            elif func_name == 'search_image':
                result = WebSearch.search_image(**func_args)
            elif func_name == 'search_video':
                result = WebSearch.search_video(**func_args)
            elif func_name == 'search_news':
                result = WebSearch.search_news(**func_args)
            elif func_name == 'get_instant':
                result = WebSearch.get_instant(**func_args)
            elif func_name == 'search_map':
                result = WebSearch.search_map(**func_args)
            elif func_name == 'give_suggestion':
                result = WebSearch.give_suggestion(**func_args)
            elif func_name == 'user_proxy_for_text_web_search':
                result = WebSearch.user_proxy_for_text_web_search(**func_args)
            else:
                print(f"Unknown function: {func_name}")
                return []
            print(f"Function {func_name} result: {result}")
            return result
        except Exception as e:
            print(f"Error executing function {func_name}: {str(e)}")
            return []

    @staticmethod
    def ask_llm_function_caller(gpt_model: str, temperature: float, messages: List, function_json_list: List):
        """
        Generate a response from an OpenAI ChatCompletion API call with tool calls.
        """
        try:
            tools = [{"type": "function", "function": f} for f in function_json_list]
            response = client.chat.completions.create(
                model=gpt_model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=temperature
            )
            return response
        except Exception as e:
            print(f"Error in LLM function caller: {str(e)}")
            return None

    @staticmethod
    def ask_llm_chatbot(gpt_model: str, temperature: float, messages: List):
        """
        Generate a response from an OpenAI ChatCompletion API call without specific function calls.
        """
        try:
            response = client.chat.completions.create(
                model=gpt_model,
                messages=messages,
                temperature=temperature
            )
            return response
        except Exception as e:
            print(f"Error in LLM chatbot: {str(e)}")
            return None