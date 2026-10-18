![cover Logo](images/webchatbot.jpg)
# 🔍 GPT Function Calling with Real-Time Web Search

This project demonstrates how to extend the capabilities of GPT models beyond their knowledge cut-off date by integrating **real-time web search** using **function calling**. The system uses the OpenAI API with `streamlit` as the interface and `duckduckgo_search` for fetching up-to-date information from the web.

## 🚀 Features

- **Function Calling** with OpenAI's GPT models
- **Real-time Web Search** powered by DuckDuckGo
- **Streamlit-based Interface** for interactive conversations
- Modular codebase with support for **custom tool integration**

## 📦 Requirements

All required packages are listed in `requirements.txt`. Here's a summary:

- duckduckgo_search==8.0.1
- openai==1.75.0
- Pillow
- pydantic==2.11.3
- pyprojroot==0.3.0
- python-dotenv==1.1.0
- PyYAML==6.0.2
- streamlit==1.44.1
- streamlit-chat==0.1.1


You can install everything with:

```bash
pip install -r requirements.txt
```

### ▶️ Getting Started


1. Clone the repository:
```bash
https://github.com/Majdi21926/ChatGPT_Real_time_Web_Search.git
cd ChatGPT_Real_time_Web_Search
```
2. Add your OpenAI API key in a .env file:
```bash
OPENAI_API_KEY=your_api_key_here
```
3. Run the app with Streamlit:
```bash
streamlit run src/app.py
```
## 🧠 How It Works
- A user's query is parsed by the GPT model.
- The model chooses whether a function (e.g., web search) should be called.
- If needed, the DuckDuckGo web search tool is called with the relevant query.
- GPT gets the real-time search result and integrates it into its response.

### Optional Parallel web search

To use [Parallel Search MCP](https://docs.parallel.ai/integrations/mcp/search-mcp)
for general web searches, install the requirements above and set this in
`configs/app_config.yml` before starting the app:

```yaml
search_provider: parallel
```

Parallel provides free anonymous web search, powered by Fast mode, with no
Parallel account or API key. Search titles, source URLs and excerpts are passed
to the chatbot for its answer. The app still requires its OpenAI configuration.
The MCP client requires Python 3.10 or later.

This setting selects the provider for `retrieve_results` and `search_text`.
DuckDuckGo remains the default when the setting is absent or `duckduckgo`.
Specialized tools (PDFs, images, videos, news, instant answers, suggestions and
proxy searches) continue to use DuckDuckGo. Parallel text search is general web
search; it does not apply DuckDuckGo's region, safe-search or past-year filters.
`max_results` limits the returned results to 1–20 (default 5); the service may
return fewer. Requests have a 30-second total timeout. Service errors, including
anonymous quota exhaustion, use the app's existing empty-result handling and
never switch providers automatically. To switch back, set `search_provider` to
`duckduckgo`.

## 📁 Project Structure
```bash
.
├── src/
│   ├── app.py          # Main Streamlit app
│   ├── WebSearch.py    # Web search function class
│   ├── Apputils.py     # Utility functions and wrappers
│   └── ...
├── requirements.txt
└── .env                # Environment variables (not committed)
```
### Built with ❤️ using OpenAI, Streamlit & DuckDuckGo.




