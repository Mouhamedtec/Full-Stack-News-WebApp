from django.db import models
from django.core.validators import URLValidator

class Article(models.Model):
    """
    News Article model for storing articles from various providers.
    """

    # Core article fields
    title = models.CharField(max_length=500, db_index=True)
    content = models.TextField()
    description = models.TextField()
    url = models.URLField(unique=True, max_length=2000, validators=[URLValidator()], db_index=True)

    # Article metadata
    category = models.CharField(max_length=100, default="general", db_index=True)
    source = models.CharField(max_length=200, db_index=True)
    author = models.CharField(max_length=200, blank=True, null=True)
    url_to_image = models.URLField(max_length=2000, blank=True, null=True)

    # Processing fields
    published_date = models.DateTimeField(db_index=True)
    fetched_date = models.DateTimeField(auto_now_add=True)

    # NLP/Extraction fields
    keywords = models.JSONField(default=list, blank=True)
    language = models.CharField(max_length=10, default="en", db_index=True)

    # Metadata
    is_featured = models.BooleanField(default=False, db_index=True)
    is_archived = models.BooleanField(default=False, db_index=True)

    def __str__(self):
        return self.title[:50] + "..."
    
    class Meta:
        ordering = ['-published_date']
        verbose_name = "Article"
        verbose_name_plural = "Articles"

        indexes = [
            models.Index(fields=['title', 'published_date']),
            models.Index(fields=['source', 'published_date']),
            models.Index(fields=['category', 'published_date']),
            models.Index(fields=['language', 'published_date']),
            models.Index(fields=['is_featured', 'published_date']),
            models.Index(fields=['is_archived', 'published_date'])
        ]
        
        # prevent duplicate articles from the same source
        unique_together = [('url', 'source')]


class Source(models.Model):
    """
    News Source model for storing information about news sources.
    """

    name = models.CharField(max_length=200, unique=True, db_index=True)
    url = models.URLField(max_length=2000, validators=[URLValidator()], db_index=True)
    category = models.CharField(max_length=100, default="general", db_index=True)
    language = models.CharField(max_length=10, default="en", db_index=True)
    country = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']
        verbose_name = "Source"
        verbose_name_plural = "Sources"

        indexes = [
            models.Index(fields=['country']),
            models.Index(fields=['category', 'language', 'country']),
            models.Index(fields=['language', 'country']),
        ]