from django.apps import AppConfig
from django.conf import settings

class NewsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'news'

    def ready(self):
        from .services.language_detect import model_loader
        # Preload the fastText model when the app is ready
        model_loader.get_model(model_path=settings.FASTTEXT_MODEL_PATH)