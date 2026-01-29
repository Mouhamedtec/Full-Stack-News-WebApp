import logging
import re

from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound

from django.db.models import Q

from .models import Article, Source
from .serializers import (
    ArticleListSerializer,
    NewsFilterSerializer
)
from .services.language_detect.detect import detect_language


logger = logging.getLogger(__name__)


class NewsRetrievalWithFiltersView(GenericAPIView):
    """
    Comprehensive news retrieval API with advanced filtering and search capabilities.

    Behavior notes:
    - The `search` query parameter performs full-text search against `title` and `content`.
    - Additionally, the `search` text is tokenized and used to derive keyword phrases (n-grams).
        These candidate phrases (longer phrases preferred) are matched against the stored
        `keywords` JSONField entries (which are stored as [keyword, score] pairs). Matching
        is performed as a case-insensitive substring search of the phrase inside the JSON
        representation of the keywords list, and candidate phrases are limited to avoid
        overly broad queries.
    - If a `search` term is provided, the language of the search term is automatically detected and used to filter results. The `user_language` parameter is only used if no `search` term is provided.

    Supports filtering by:
    - Category
    - Source
    - Author
    - Date range
    - User language
    - User country code
    - Full-text search (via `search`) — which also derives and matches keyword phrases
    - Pagination and sorting
    """
    queryset = Article.objects.all()
    serializer_class = ArticleListSerializer

    def get(self, request, *args, **kwargs):
        """
        Get all articles with optional filtering, sorting, and pagination.
        
        Query Parameters:
                - search: Search in title and content. Also used to derive keyword phrases (n-grams)
                    which will be matched against the article `keywords` JSONField. Phrases are
                    generated up to 4 words, longer phrases are preferred, and candidate phrases are
                    limited (default limit: 30) to prevent heavy queries. If a search term is provided, the language of the search term is automatically detected and used to filter results.
        - category: Filter by category
        - source: Filter by source
        - author: Filter by author
        - user_language: Filter by user language (only used if no search term is provided)
        - user_country_code: Filter by user country code (maps to sources in that country)
        - sort_by: Sort order (recent, oldest, title)
        - date_from: Filter from date (ISO 8601)
        - date_to: Filter to date (ISO 8601)
        
        Example: /api/news/?category=Technology&page=1&page_size=20
        """
        try:
            # Parse and validate filter parameters
            filter_serializer = NewsFilterSerializer(data=request.query_params)
            if not filter_serializer.is_valid():
                return Response(
                    {'errors': filter_serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            filters = filter_serializer.validated_data
            
            # Build queryset with filters (database operations)
            queryset = self._apply_filters(self.get_queryset(), filters)
            
            # Apply sorting
            queryset = self._apply_sorting(queryset, filters.get('sort_by', 'recent'))
            
            # Paginate results using DRF
            paginated_queryset = self.paginate_queryset(queryset)
            serializer = ArticleListSerializer(paginated_queryset, many=True)
            
            return self.get_paginated_response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error in news retrieval: {e}", exc_info=True)
            return Response(
                {'error': "Error retrieving news articles."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _apply_filters(self, queryset, filters):
        """Apply filters to queryset"""
        # Apply user-provided helpers first to reduce search scope
        if filters.get('user_language') and filters.get('search') is None:
            queryset = queryset.filter(language__iexact=filters['user_language'])

        # If no user_language provided, try to detect from search text
        if filters.get('search'):
            detected = detect_language(filters['search'])
            print("Detected language from search text:", detected)
            if detected:
                lang, _ = detected
                queryset = queryset.filter(language__iexact=lang)

        if filters.get('user_country_code'):
            # Try to map country code to known sources; Article.source is a string name
            country_code = filters['user_country_code']
            try:
                source_names = list(Source.objects.filter(country__iexact=country_code).values_list('name', flat=True))
                if source_names:
                    queryset = queryset.filter(source__in=source_names)
            except Exception:
                # If Source model lookup fails for any reason, skip country filtering
                pass

        # Search filter: use search text for full-text search and derive keywords
        if filters.get('search'):
            search_term = filters['search']
            queryset = queryset.filter(
                Q(title__icontains=search_term) | Q(content__icontains=search_term)
            )
            # Derive keyword phrases (n-grams) from the search string and prefer longer phrases
            kw_candidates = self._derive_keyword_phrases(search_term, max_ngram=4, max_phrases=30)
            if kw_candidates:
                q_obj = None
                for kw in kw_candidates:
                    # Search JSONField for the keyword text (case-insensitive)
                    cond = Q(keywords__icontains=kw)
                    q_obj = cond if q_obj is None else (q_obj | cond)
                if q_obj is not None:
                    queryset = queryset.filter(q_obj)
        
        # Category filter
        if filters.get('category'):
            queryset = queryset.filter(category__iexact=filters['category'])
        
        # Source filter
        if filters.get('source'):
            queryset = queryset.filter(source__iexact=filters['source'])
        
        # Author filter
        if filters.get('author'):
            queryset = queryset.filter(author__icontains=filters['author'])
        
        # Date range filters
        if filters.get('date_from'):
            queryset = queryset.filter(published_date__gte=filters['date_from'])
        
        if filters.get('date_to'):
            queryset = queryset.filter(published_date__lte=filters['date_to'])
        
        
        return queryset

    def _derive_keyword_phrases(self, text: str, max_ngram: int = 3, max_phrases: int = 50):
        """Derive candidate keyword phrases from `text`.

        - Tokenizes the text on whitespace/punctuation.
        - Generates n-grams up to `max_ngram`.
        - Returns phrases sorted by length (longer phrases first) and limited to `max_phrases`.
        """
        if not text:
            return []

        # Normalize whitespace and strip surrounding punctuation from tokens
        tokens = [t.strip("'\"()[]{}:;,.!?-/") for t in re.split(r'[\s,]+', text) if t.strip()] 
        if not tokens:
            return []

        n = min(max_ngram, len(tokens))
        phrases = set()

        # Generate n-grams (prefer longer n-grams)
        for size in range(n, 0, -1):
            for i in range(0, len(tokens) - size + 1):
                gram = " ".join(tokens[i : i + size]).strip()
                # skip very short tokens
                if len(gram) < 2:
                    continue
                phrases.add(gram)

        # Sort by number of words then by length, prefer longer/more specific phrases
        sorted_phrases = sorted(phrases, key=lambda p: (-len(p.split()), -len(p)))
        return sorted_phrases[:max_phrases]

    def _apply_sorting(self, queryset, sort_by):
        """Apply sorting to queryset"""
        if sort_by == 'oldest':
            return queryset.order_by('published_date')
        elif sort_by == 'title':
            return queryset.order_by('title')
        else:  # 'recent' is default
            return queryset.order_by('-published_date')
