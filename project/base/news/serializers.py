from rest_framework import serializers
from .models import Article
from .constants import VALID_CATEGORIES, VALID_LANGUAGES, VALID_COUNTRIES

class ArticleListSerializer(serializers.ModelSerializer):
    """Serializer for article list with preview"""
    content_preview = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = [
            'id', 'title', 'content_preview', 'url', 'category', 'source',
            'author', 'url_to_image', 'published_date'
        ]
    
    def get_content_preview(self, obj):
        """Return first 200 characters of content"""
        return obj.content[:200] + '...' if len(obj.content) > 200 else obj.content


class NewsFilterSerializer(serializers.Serializer):
    """Serializer for news filtering parameters"""
    search = serializers.CharField(
        required=False,
        max_length=500,
        help_text="Search in title and content"
    )
    category = serializers.CharField(
        required=False,
        max_length=100,
        help_text="Filter by category"
    )
    source = serializers.CharField(
        required=False,
        max_length=100,
        help_text="Filter by source"
    )
    author = serializers.CharField(
        required=False,
        max_length=100,
        help_text="Filter by author"
    )
    sort_by = serializers.ChoiceField(
        choices=['recent', 'oldest', 'title'],
        required=False,
        default='recent',
        help_text="Sort order: recent, oldest, or title"
    )
    user_language = serializers.ChoiceField(
        choices=[(lang, lang) for lang in VALID_LANGUAGES],
        required=False,
        help_text="Optional: preferred user language (ISO code) to bias results"
    )
    user_country_code = serializers.ChoiceField(
        choices=[(country, country) for country in VALID_COUNTRIES],
        required=False,
        help_text="Optional: preferred user country code to bias results"
    )
    date_from = serializers.DateTimeField(
        required=False,
        help_text="Filter articles from this date onwards (ISO 8601 format)"
    )
    date_to = serializers.DateTimeField(
        required=False,
        help_text="Filter articles up to this date (ISO 8601 format)"
    )

    def validate_category(self, value):
        """Validate category against valid categories"""
        if value not in VALID_CATEGORIES:
            raise serializers.ValidationError(f"Invalid category. Valid options are: {', '.join(VALID_CATEGORIES)}")
        return value
