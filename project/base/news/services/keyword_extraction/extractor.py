
import logging
from typing import List, Tuple, Optional
from .exceptions import KeywordExtractionError

try:
    import yake
except ImportError:
    raise ImportError("The 'yake' library is required. Install it with 'pip install yake'.")

logger = logging.getLogger(__name__)

class KeywordExtractorService:
    """Service for extracting keywords from text using YAKE.
    Args:
        language (str): Language code for the text (default: 'en').
        ngram_size (int): Size of the n-grams to consider (default: 3).
        dedup_lim (float): Deduplication limit (default: 0.7).
        dedup_func (str): Deduplication function to use (default: 'seqm').
        window_size (int): Size of the context window (default: 2).
        top (int): Number of top keywords to extract (default: 15).
        features (Optional[list]): Additional features for YAKE (default: None).
    Raises:
        KeywordExtractionError: If initialization fails.
    """
    def __init__(
        self,
        language: str = "en",
        ngram_size: int = 3,
        dedup_lim: float = 0.7,
        dedup_func: str = "seqm",
        window_size: int = 2,
        top: int = 15,
        features: Optional[list] = None,
    ):
        self.language = language
        self.ngram_size = ngram_size
        self.dedup_lim = dedup_lim
        self.dedup_func = dedup_func
        self.window_size = window_size
        self.top = top
        self.features = features
        try:
            self.extractor = yake.KeywordExtractor(
                lan=self.language,
                n=self.ngram_size,
                dedupLim=self.dedup_lim,
                dedupFunc=self.dedup_func,
                windowsSize=self.window_size,
                top=self.top,
                features=self.features,
            )
        except Exception as e:
            logger.error(f"Failed to initialize YAKE extractor: {e}")
            raise KeywordExtractionError("Failed to initialize keyword extractor.")

    def extract_keywords(self, text: str) -> List[Tuple[str, float]]:
        """Extract keywords from the given text.
        Args:
            text (str): The input text from which to extract keywords.
        Returns:
            List[Tuple[str, float]]: A list of tuples containing keywords and their scores.
        Raises:
            KeywordExtractionError: If extraction fails.
        """

        if not isinstance(text, str) or not text.strip():
            logger.warning("Input text is empty or not a string.")
            return []
        try:
            keywords = self.extractor.extract_keywords(text)
            return keywords
        except Exception as e:
            logger.error(f"Keyword extraction failed: {e}")
            keywords = self.extract_unique_long_words(text)
            if keywords:
                return [(kw, 0.0) for kw in keywords]

        raise KeywordExtractionError("Keyword extraction failed.")
    
    def extract_unique_long_words(self, text: str, min_length: int = 5, max_keywords: int = 10) -> List[str]:
        """Extract unique long words from the text as fallback keywords.
        Args:
            text (str): The input text.
            min_length (int): Minimum length of words to consider (default: 5).
            max_keywords (int): Maximum number of keywords to return (default: 10).
        
        Returns:
            List[str]: A list of unique long words.
        """
        words = set(word for word in text.split() if len(word) >= min_length)
        return list(words)[:max_keywords]