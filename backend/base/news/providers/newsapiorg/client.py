from newsapi import NewsApiClient
from newsapi.const import categories

class NewsApiOrgProvider:
    def __init__(self, api_key: str):
        self.client = NewsApiClient(api_key=api_key)
        self.categories = categories
    
    def get_top_headlines(self, country: str = 'us', category: str = None, q: str = None, page_size: int = 20):
        response = self.client.get_top_headlines(
            country=country,
            category=category,
            q=q,
            page_size=page_size
        )
        articles = response.get("articles", []) if isinstance(response, dict) else []
        return articles

    def get_everything(self, q: str, from_param: str = None, to: str = None, language: str = 'en', sort_by: str = 'relevancy', page_size: int = 20):
        return self.client.get_everything(
            q=q,
            from_param=from_param,
            to=to,
            language=language,
            sort_by=sort_by,
            page_size=page_size
        )
    
    def get_sources(self, category: str = None, language: str = None, country: str = None):
        response = self.client.get_sources(
            category=category,
            language=language,
            country=country
        )
        sources = response.get("sources", []) if isinstance(response, dict) else []

        # Skip early return if no sources
        if not sources:
            return []

        # Filter out sources with empty critical fields
        filtered_sources = []
        for source in sources:
            has_empty_value = [v for v in source.values() if v == "" or v is None]
            if not has_empty_value:
                filtered_sources.append(source)

        return filtered_sources

