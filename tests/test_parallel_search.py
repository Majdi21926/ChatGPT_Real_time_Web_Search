"""Exercise provider selection and the real MCP transport with scripted responses."""
import asyncio
import importlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import anyio
import httpx
from mcp.types import CallToolResult, TextContent
import yaml

from utils import load_config, parallel_search
from utils.parallel_search import ParallelSearch, _results


RESULTS = {"results": [{"title": "Python documentation", "url": "https://docs.python.org/3/",
                         "excerpts": ["The Python language reference."]}]}
REAL_HTTP_CLIENT = httpx.AsyncClient
TOOLS = {"tools": [{"name": "web_search", "inputSchema": {
    "type": "object", "properties": {"objective": {"type": "string"},
    "search_queries": {"type": "array", "items": {"type": "string"}}},
    "required": ["objective", "search_queries"]}}]}


def tool_response(name="search_text", arguments=None):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(tool_calls=[
        SimpleNamespace(function=SimpleNamespace(name=name, arguments=json.dumps(
            arguments or {"query": "Python language documentation", "max_results": 2})))
    ]))])


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.config_path = Path(self.temp.name) / "app_config.yml"
        self.config = yaml.safe_load(Path("configs/app_config.yml").read_text())
        self.config["openai"]["api_key"] = "test-placeholder"
        self.save_config()
        self.here = patch.object(load_config, "here", return_value=self.config_path)
        self.here.start()
        self.addCleanup(self.here.stop)
        self.app = importlib.import_module("utils.app_utils")
        self.selection = patch.object(self.app.APPCFG, "search_provider", "duckduckgo")
        self.selection.start()
        self.addCleanup(self.selection.stop)
        self.requests = []
        self.clients = []

    def save_config(self):
        self.config_path.write_text(yaml.safe_dump(self.config))

    def transport(self, payload=None, error=None):
        async def respond(request):
            body = json.loads(request.content)
            self.requests.append((request, body))
            if body["method"] == "notifications/initialized":
                return httpx.Response(202)
            if body["method"] == "initialize":
                result = {"protocolVersion": body["params"]["protocolVersion"],
                          "capabilities": {"tools": {}},
                          "serverInfo": {"name": "scripted-search", "version": "1"}}
            elif body["method"] == "tools/list":
                result = TOOLS
            else:
                self.assertEqual(body["method"], "tools/call")
                if error:
                    raise error
                result = {"content": [{"type": "text", "text": json.dumps(payload or RESULTS)}]}
            return httpx.Response(200, json={"jsonrpc": "2.0", "id": body["id"], "result": result})

        def client(**kwargs):
            http_client = REAL_HTTP_CLIENT(transport=httpx.MockTransport(respond), **kwargs)
            self.clients.append(http_client)
            return http_client
        return patch.object(parallel_search.httpx, "AsyncClient", side_effect=client)

    def assert_requests(self):
        self.assertCountEqual([b["method"] for _, b in self.requests],
                              ["initialize", "notifications/initialized", "tools/list", "tools/call"])
        for request, _ in self.requests:
            self.assertEqual(str(request.url), parallel_search.MCP_URL)
            self.assertEqual(request.headers["User-Agent"], parallel_search.USER_AGENT)
            self.assertNotIn("Authorization", request.headers)
        call = next(body for _, body in self.requests if body["method"] == "tools/call")
        self.assertEqual(call["params"], {
            "name": "web_search", "arguments": {"objective": "Python language documentation",
                                                   "search_queries": ["Python language documentation"]}})
        self.assertTrue(all(client.is_closed for client in self.clients))

    def test_config_defaults_saved_choices_and_invalid_selection(self):
        del self.config["search_provider"]
        self.save_config()
        self.assertEqual(load_config.LoadConfig().search_provider, "duckduckgo")
        for value in ("duckduckgo", "parallel"):
            self.config["search_provider"] = value
            self.save_config()
            self.assertEqual(load_config.LoadConfig().search_provider, value)
        self.config["search_provider"] = "unknown"
        self.save_config()
        with self.assertRaisesRegex(ValueError, "search_provider"):
            load_config.LoadConfig()

    def test_default_and_explicit_duckduckgo_do_not_connect_to_mcp(self):
        with patch.object(self.app.WebSearch, "search_text", return_value=[{"url": "https://example.org"}]) as ddg, \
             patch.object(ParallelSearch, "search_text") as parallel:
            self.assertEqual(self.app.Apputils.execute_json_function(tool_response()), [{"url": "https://example.org"}])
            ddg.assert_called_once()
            parallel.assert_not_called()

    def test_parallel_schema_dispatch_and_specialized_tools(self):
        self.app.APPCFG.search_provider = "parallel"
        schemas = {s["name"]: s for s in self.app.Apputils.wrap_functions()}
        self.assertIn("Parallel", schemas["search_text"]["description"])
        self.assertIn("search_image", schemas)
        with self.transport(), patch.dict("os.environ", {"PARALLEL_API_KEY": "unused"}):
            results = self.app.Apputils.execute_json_function(tool_response())
        self.assertEqual(results, [{"title": "Python documentation", "url": "https://docs.python.org/3/",
                                    "description": "The Python language reference."}])
        self.assert_requests()
        with patch.object(self.app.WebSearch, "search_image", return_value=["image"]) as images:
            self.assertEqual(self.app.Apputils.execute_json_function(
                tool_response("search_image", {"keywords": "Python"})), ["image"])
            images.assert_called_once_with(keywords="Python")

    def test_errors_do_not_fall_back(self):
        self.app.APPCFG.search_provider = "parallel"
        with self.transport(error=httpx.ReadTimeout("scripted timeout")), \
             patch.object(self.app.WebSearch, "search_text") as ddg:
            self.assertEqual(self.app.Apputils.execute_json_function(tool_response()), [])
            ddg.assert_not_called()
        self.assertTrue(all(client.is_closed for client in self.clients))

    def test_unknown_tool_does_not_search(self):
        with patch.object(ParallelSearch, "search_text") as search:
            self.assertEqual(self.app.Apputils.execute_json_function(tool_response("disabled_tool")), [])
            search.assert_not_called()

    def test_streamlit_consumes_search_urls_and_excerpts(self):
        from streamlit.testing.v1 import AppTest
        from openai.types.chat import ChatCompletion
        self.config["search_provider"] = "parallel"
        self.save_config()
        self.app.APPCFG.search_provider = load_config.LoadConfig().search_provider
        first = ChatCompletion(id="first", created=0, model="gpt-3.5-turbo", object="chat.completion",
            choices=[{"index": 0, "finish_reason": "tool_calls", "message": {"role": "assistant", "content": None,
                "tool_calls": [{"id": "call1", "type": "function", "function": {"name": "search_text",
                    "arguments": json.dumps({"query": "Python language documentation", "max_results": 2})}}]}}])
        second = ChatCompletion(id="second", created=0, model="gpt-3.5-turbo", object="chat.completion",
            choices=[{"index": 0, "finish_reason": "stop", "message": {"role": "assistant",
                "content": "See https://docs.python.org/3/ for Python documentation."}}])
        scripted = Mock(side_effect=[first, second])
        with self.transport(), patch.object(self.app.client.chat.completions, "create", scripted):
            app = AppTest.from_file("src/app.py").run(timeout=15)
            self.assertEqual(len(app.exception), 0)
            app.text_area[0].input("Find Python language documentation")
            app.button[-1].click().run(timeout=15)
            self.assertEqual(len(app.exception), 0)
        self.assertEqual(scripted.call_count, 2)
        prompt = scripted.call_args_list[1].kwargs["messages"][1]["content"]
        for value in ("Python documentation", "https://docs.python.org/3/", "The Python language reference."):
            self.assertIn(value, prompt)
        self.assertIn("https://docs.python.org/3/", app.session_state["generated"][0])
        self.assert_requests()


class ResponseTests(unittest.TestCase):
    def test_structured_content_url_filtering_and_limits(self):
        payload = {"results": [
            {"url": "javascript:alert(1)"}, {"url": "https://[invalid"},
            {"url": "https://example.org/a", "excerpts": ["one", 2, "two"]},
            {"url": "https://example.org/b", "title": "Second"}]}
        result = _results(CallToolResult(content=[], structuredContent=payload), 1)
        self.assertEqual(result, [{"title": "Untitled", "url": "https://example.org/a", "description": "one\ntwo"}])

    def test_tool_errors_and_malformed_payload(self):
        for response, error in [
            (CallToolResult(content=[], isError=True), RuntimeError),
            (CallToolResult(content=[TextContent(type="text", text="not json")]), ValueError),
            (CallToolResult(content=[], structuredContent={"other": []}), ValueError)]:
            with self.assertRaises(error):
                _results(response, 5)

    def test_invalid_arguments_do_not_connect(self):
        with patch.object(parallel_search.httpx, "AsyncClient") as client:
            for query, count in [("", 5), ("query", 0), ("query", True), ("query", 21)]:
                with self.assertRaises(ValueError):
                    ParallelSearch.retrieve_results(query, count)
            client.assert_not_called()

    def test_total_timeout_and_cancellation_close_transport(self):
        async def scenario(cancel):
            called = asyncio.Event()
            clients = []
            async def respond(request):
                body = json.loads(request.content)
                if body["method"] == "notifications/initialized":
                    return httpx.Response(202)
                if body["method"] == "initialize":
                    return httpx.Response(200, json={"jsonrpc": "2.0", "id": body["id"], "result": {
                        "protocolVersion": body["params"]["protocolVersion"], "capabilities": {"tools": {}},
                        "serverInfo": {"name": "scripted", "version": "1"}}})
                if body["method"] == "tools/list":
                    return httpx.Response(200, json={"jsonrpc": "2.0", "id": body["id"], "result": TOOLS})
                called.set()
                await anyio.sleep_forever()
            def client(**kwargs):
                c = REAL_HTTP_CLIENT(transport=httpx.MockTransport(respond), **kwargs)
                clients.append(c)
                return c
            with patch.object(parallel_search.httpx, "AsyncClient", side_effect=client), \
                 patch.object(parallel_search, "SEARCH_TIMEOUT", 5 if cancel else .05):
                task = asyncio.create_task(ParallelSearch._search("query", 5))
                if cancel:
                    await called.wait()
                    task.cancel()
                with self.assertRaises(asyncio.CancelledError if cancel else TimeoutError):
                    await task
            self.assertTrue(all(c.is_closed for c in clients))
        asyncio.run(scenario(False))
        asyncio.run(scenario(True))


if __name__ == "__main__":
    unittest.main()
