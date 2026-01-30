import re
import logging

def clean_text(text):
    """
    Clean the input text by removing URLs and unwanted characters.
    Explanation:
    - Encode and decode to UTF-8 to handle any encoding issues.
    - Convert to lowercase for uniformity.
    - Remove URLs to avoid noise in language detection.
    - Use an expanded Unicode range to retain characters from multiple languages/scripts.
    Returns cleaned text or None if an error occurs.
    """

    try:
        text = text.encode('utf-8', 'ignore').decode('utf-8')
    except Exception as e:
        logging.error(f"Text encoding error: {e}")
        return None
    
    try:
        text = text.lower()
        text = re.sub(r"http\S+", "", text)
        # Expanded Unicode ranges: Latin, Latin Extended, Arabic, Cyrillic, CJK, Devanagari, Greek, Hebrew, Thai, etc.
        text = re.sub(r"[^\w\s\u00C0-\u024F\u0600-\u06FF\u0400-\u04FF\u4E00-\u9FFF\u3040-\u30FF\u0900-\u097F\u0370-\u03FF\u0590-\u05FF\u0E00-\u0E7F]", "", text)
        return text.strip()
    except Exception as e:
        logging.error(f"Text cleaning error: {e}")
        return None
