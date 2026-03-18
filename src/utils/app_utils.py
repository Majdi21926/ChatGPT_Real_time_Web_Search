from typing import Dict, List
import inspect
import json
from inspect import Parameter
from pydantic import create_model, BaseModel
from utils.web_search import WebSearch, TavilySearch
import openai
from utils.load_config import LoadConfig

APPCFG = LoadConfig()

# Set of function names that Tavily can handle
_TAVILY_SUPPORTED = {'retrieve_results', 'search_text'}
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
    def _dispatch_search(func_name: str, func_args: dict, provider: str) -> List:
        """
        Dispatch a search call to the appropriate provider.
        For functions not supported by Tavily, always use DuckDuckGo.
        """
        use_tavily = provider == 'tavily' and func_name in _TAVILY_SUPPORTED

        if use_tavily:
            func = getattr(TavilySearch, func_name, None)
            if func:
                return func(**func_args)

        # DuckDuckGo dispatch
        ddgs_funcs = {
            'retrieve_results': WebSearch.retrieve_results,
            'search_text': WebSearch.search_text,
            'search_pdf': WebSearch.search_pdf,
            'search_image': WebSearch.search_image,
            'search_video': WebSearch.search_video,
            'search_news': WebSearch.search_news,
            'get_instant': WebSearch.get_instant,
            'search_map': WebSearch.search_map,
            'give_suggestion': WebSearch.give_suggestion,
            'user_proxy_for_text_web_search': WebSearch.user_proxy_for_text_web_search,
        }
        func = ddgs_funcs.get(func_name)
        if func:
            return func(**func_args)

        print(f"Unknown function: {func_name}")
        return []

    @staticmethod
    def execute_json_function(response) -> List:
        """
        Execute a function based on the response from an OpenAI ChatCompletion API call.
        Routes to Tavily or DuckDuckGo based on the configured search_provider.
        Falls back to Tavily on DuckDuckGo rate-limit errors for supported functions.
        """
        try:
            tool_call = response.choices[0].message.tool_calls[0]
            func_name = tool_call.function.name
            func_args = json.loads(tool_call.function.arguments)
            print(f"Executing function: {func_name} with args: {func_args}")
        except (AttributeError, IndexError, json.JSONDecodeError) as e:
            print(f"Error parsing tool call: {str(e)}")
            return []

        provider = APPCFG.search_provider
        try:
            result = Apputils._dispatch_search(func_name, func_args, provider)
            print(f"Function {func_name} result: {result}")
            return result
        except Exception as e:
            # Fallback to Tavily on DuckDuckGo rate-limit if provider is duckduckgo
            if "Ratelimit" in str(e) and provider == 'duckduckgo' and func_name in _TAVILY_SUPPORTED and APPCFG.tavily_api_key:
                print(f"DuckDuckGo rate limit hit for {func_name}. Falling back to Tavily...")
                try:
                    fallback_func = getattr(TavilySearch, func_name)
                    result = fallback_func(**func_args)
                    print(f"Tavily fallback result for {func_name}: {result}")
                    return result
                except Exception as tavily_err:
                    print(f"Tavily fallback also failed: {str(tavily_err)}")
                    return []
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