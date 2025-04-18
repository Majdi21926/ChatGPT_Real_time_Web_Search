from web_search import WebSearch

# Test search_news
try:
    results = WebSearch.search_news(keywords="Tesla", max_results=5)
    print("Search results:", results)
except Exception as e:
    print(f"Error: {str(e)}")