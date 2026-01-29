from django.urls import path
from .views import (
    NewsRetrievalWithFiltersView
)

app_name = 'news'

urlpatterns = [
    path('', NewsRetrievalWithFiltersView.as_view(), name='news-retrieval-with-filters'),
]
