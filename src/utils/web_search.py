# https://pypi.org/project/duckduckgo-search/
# pip install -U duckduckgo_search

from duckduckgo_search import DDGS
from typing import List, Optional
import time

class WebSearch:
    @staticmethod
    def retrieve_results(query: str, max_results: Optional[int] = 5) -> List:
        """
        Retrieve search results from duckduckgo.com with rate limit handling.
        """
        try:
            with DDGS(timeout=30) as ddgs:
                results = [
                    {
                        "title": r.get("title", "Untitled"),
                        "url": r.get("href", ""),
                        "description": r.get("body", "No description")
                    }
                    for r in ddgs.text(query, max_results=max_results)
                    if r.get("href", "")
                ]
                print(f"retrieve_results for '{query}': {results}")
                return results
        except Exception as e:
            if "Ratelimit" in str(e):
                print(f"Rate limit hit for '{query}'. Retrying after delay...")
                time.sleep(5)
                return WebSearch.retrieve_results(query, max_results)
            print(f"Error in retrieve_results for '{query}': {str(e)}")
            return []

    @staticmethod
    def search_text(query: str, max_results: Optional[int] = 5) -> List:
        """
        Search for text on duckduckgo.com with rate limit handling.
        """
        try:
            with DDGS(timeout=30) as ddgs:
                results = [
                    {
                        "title": r.get("title", "Untitled"),
                        "url": r.get("href", ""),
                        "description": r.get("body", "No description")
                    }
                    for r in ddgs.text(query, region='wt-wt', safesearch='off', timelimit='y', max_results=max_results)
                    if r.get("href", "")
                ]
                print(f"search_text for '{query}': {results}")
                return results
        except Exception as e:
            if "Ratelimit" in str(e):
                print(f"Rate limit hit for '{query}'. Retrying after delay...")
                time.sleep(5)
                return WebSearch.search_text(query, max_results)
            print(f"Error in search_text for '{query}': {str(e)}")
            return []

    @staticmethod
    def search_pdf(query: str, max_results: Optional[int] = 5) -> List:
        """
        Search for PDF files on duckduckgo.com with rate limit handling.
        """
        try:
            with DDGS(timeout=30) as ddgs:
                results = [
                    {
                        "title": r.get("title", "Untitled"),
                        "url": r.get("href", ""),
                        "description": r.get("body", "No description")
                    }
                    for r in ddgs.text(
                        f"{query} filetype:pdf site:*.edu | site:*.org | site:*.gov | site:*.io -inurl:(signup | login)",
                        region='wt-wt', safesearch='off', timelimit='y', max_results=max_results
                    )
                    if r.get("href", "").lower().endswith(".pdf")
                ]
                print(f"search_pdf for '{query}': {results}")
                return results
        except Exception as e:
            if "Ratelimit" in str(e):
                print(f"Rate limit hit for '{query}'. Retrying after delay...")
                time.sleep(5)
                return WebSearch.search_pdf(query, max_results)
            print(f"Error in search_pdf for '{query}': {str(e)}")
            return []

    @staticmethod
    def get_instant(query: str) -> List:
        """
        Retrieve instant answers from DuckDuckGo.com with rate limit handling.
        """
        try:
            with DDGS(timeout=30) as ddgs:
                results = [
                    {
                        "title": r.get("text", "Untitled"),
                        "url": r.get("url", ""),
                        "description": r.get("text", "No description")
                    }
                    for r in ddgs.answers(query)
                    if r.get("url", "")
                ]
                print(f"get_instant for '{query}': {results}")
                return results
        except Exception as e:
            if "Ratelimit" in str(e):
                print(f"Rate limit hit for '{query}'. Retrying after delay...")
                time.sleep(5)
                return WebSearch.get_instant(query)
            print(f"Error in get_instant for '{query}': {str(e)}")
            return []

    @staticmethod
    def search_image(keywords: str, max_results: Optional[int] = 5) -> List:
        """
        Search for images on DuckDuckGo.com with rate limit handling.
        """
        try:
            with DDGS(timeout=30) as ddgs:
                results = [
                    {
                        "title": r.get("title", "Untitled"),
                        "url": r.get("image", ""),
                        "description": r.get("source", "No description")
                    }
                    for r in ddgs.images(
                        keywords, region="us-en", safesearch="on", max_results=max_results
                    )
                    if r.get("image", "")
                ]
                print(f"search_image for '{keywords}': {results}")
                return results
        except Exception as e:
            if "Ratelimit" in str(e):
                print(f"Rate limit hit for '{keywords}'. Retrying after delay...")
                time.sleep(5)
                return WebSearch.search_image(keywords, max_results)
            print(f"Error in search_image for '{keywords}': {str(e)}")
            return []

    @staticmethod
    def search_video(keywords: str, max_results: Optional[int] = 5) -> List:
        """
        Search for videos on DuckDuckGo.com with rate limit handling.
        """
        try:
            with DDGS(timeout=30) as ddgs:
                results = [
                    {
                        "title": r.get("title", "Untitled"),
                        "url": r.get("content", ""),
                        "description": r.get("description", "No description"),
                        "duration": r.get("duration", "N/A"),
                        "uploader": r.get("uploader", "Unknown")
                    }
                    for r in ddgs.videos(
                        f"{keywords} site:youtube.com | site:vimeo.com -inurl:(signup | login)",
                        region="wt-wt", safesearch="off", timelimit="y", resolution="high", duration="medium", max_results=max_results
                    )
                    if r.get("content", "") and ("youtube.com" in r.get("content", "").lower() or "vimeo.com" in r.get("content", "").lower())
                ]
                print(f"search_video for '{keywords}': {results}")
                return results
        except Exception as e:
            if "Ratelimit" in str(e):
                print(f"Rate limit hit for '{keywords}'. Retrying after delay...")
                time.sleep(5)
                return WebSearch.search_video(keywords, max_results)
            print(f"Error in search_video for '{keywords}': {str(e)}")
            return []

    @staticmethod
    def search_news(keywords: str, max_results: Optional[int] = 5) -> List:
        """
        Search for news articles on DuckDuckGo.com with rate limit handling.
        """
        try:
            with DDGS(timeout=30) as ddgs:
                results = [
                    {
                        "title": r.get("title", "Untitled"),
                        "url": r.get("url", ""),
                        "description": r.get("description", "No description"),
                        "source": r.get("source", "Unknown")
                    }
                    for r in ddgs.news(
                        keywords, region="wt-wt", safesearch="off", timelimit="m", max_results=max_results
                    )
                    if r.get("url", "")
                ]
                print(f"search_news for '{keywords}': {results}")
                return results
        except Exception as e:
            if "Ratelimit" in str(e):
                print(f"Rate limit hit for '{keywords}'. Retrying after delay...")
                time.sleep(5)
                return WebSearch.search_news(keywords, max_results)
            print(f"Error in search_news for '{keywords}': {str(e)}")
            return []

    @staticmethod
    def search_map(query: str, place: str = "Ottawa", max_results: Optional[int] = 5) -> List:
        """
        Search for maps on DuckDuckGo.com with rate limit handling.
        """
        try:
            with DDGS(timeout=30) as ddgs:
                results = [
                    {
                        "title": r.get("title", "Untitled"),
                        "url": r.get("url", ""),
                        "description": r.get("address", "No description")
                    }
                    for r in ddgs.maps(query, place=place, max_results=max_results)
                    if r.get("url", "")
                ]
                print(f"search_map for '{query}': {results}")
                return results
        except Exception as e:
            if "Ratelimit" in str(e):
                print(f"Rate limit hit for '{query}'. Retrying after delay...")
                time.sleep(5)
                return WebSearch.search_map(query, place, max_results)
            print(f"Error in search_map for '{query}': {str(e)}")
            return []

    @staticmethod
    def give_suggestion(query: str) -> List:
        """
        Retrieve search suggestions from DuckDuckGo.com with rate limit handling.
        """
        try:
            with DDGS(timeout=30) as ddgs:
                results = [
                    {
                        "title": r.get("text", "Untitled"),
                        "url": "",
                        "description": r.get("text", "No description")
                    }
                    for r in ddgs.suggestions(query)
                ]
                print(f"give_suggestion for '{query}': {results}")
                return results
        except Exception as e:
            if "Ratelimit" in str(e):
                print(f"Rate limit hit for '{query}'. Retrying after delay...")
                time.sleep(5)
                return WebSearch.give_suggestion(query)
            print(f"Error in give_suggestion for '{query}': {str(e)}")
            return []

    @staticmethod
    def user_proxy_for_text_web_search(query: str, timeout: Optional[int] = 20, max_results: Optional[int] = 5) -> List:
        """
        Search for text on DuckDuckGo.com using a user-defined proxy with rate limit handling.
        """
        try:
            with DDGS(proxies="socks5://localhost:9150", timeout=timeout) as ddgs:
                results = [
                    {
                        "title": r.get("title", "Untitled"),
                        "url": r.get("href", ""),
                        "description": r.get("body", "No description")
                    }
                    for r in ddgs.text(query, max_results=max_results)
                    if r.get("href", "")
                ]
                print(f"user_proxy_for_text_web_search for '{query}': {results}")
                return results
        except Exception as e:
            if "Ratelimit" in str(e):
                print(f"Rate limit hit for '{query}'. Retrying after delay...")
                time.sleep(5)
                return WebSearch.user_proxy_for_text_web_search(query, timeout, max_results)
            print(f"Error in user_proxy_for_text_web_search for '{query}': {str(e)}")
            return []