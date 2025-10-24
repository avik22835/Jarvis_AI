# apps/debugger/web_searcher.py
"""
Search StackOverflow and web for solutions
"""
import requests
from typing import List, Dict


class WebSearcher:
    """Search external sources for debugging help"""
    
    def search_stackoverflow(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search StackOverflow API
        
        Returns list of:
            {
                'title': str,
                'link': str,
                'score': int,
                'answer_count': int,
                'excerpt': str
            }
        """
        try:
            # StackOverflow API search
            url = "https://api.stackexchange.com/2.3/search/advanced"
            params = {
                'order': 'desc',
                'sort': 'relevance',
                'q': query,
                'accepted': 'True',  # Only questions with accepted answers
                'site': 'stackoverflow',
                'pagesize': top_k,
                'filter': 'withbody'  # Include question body
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for item in data.get('items', []):
                results.append({
                    'title': item.get('title', ''),
                    'link': item.get('link', ''),
                    'score': item.get('score', 0),
                    'answer_count': item.get('answer_count', 0),
                    'excerpt': item.get('body', '')[:300],  # First 300 chars
                    'tags': item.get('tags', []),
                    'source': 'stackoverflow'
                })
            
            print(f"✅ Found {len(results)} StackOverflow results")
            return results
            
        except Exception as e:
            print(f"⚠️ StackOverflow search failed: {e}")
            return []
    
    def search_web(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Search web using DuckDuckGo (no API key needed)
        
        Returns list of:
            {
                'title': str,
                'link': str,
                'snippet': str
            }
        """
        try:
            from duckduckgo_search import DDGS
            
            results = []
            with DDGS() as ddgs:
                for i, result in enumerate(ddgs.text(query, max_results=top_k)):
                    results.append({
                        'title': result.get('title', ''),
                        'link': result.get('href', ''),
                        'snippet': result.get('body', ''),
                        'source': 'web'
                    })
            
            print(f"✅ Found {len(results)} web results")
            return results
            
        except Exception as e:
            print(f"⚠️ Web search failed: {e}")
            # Fallback: return empty (or try another search engine)
            return []

