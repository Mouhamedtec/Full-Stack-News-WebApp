import logging
from typing import Tuple, Optional
from .helpers import clean_text
from .model_loader import get_model

def detect_language(text: str, min_confidence: float = 0.7, model_path: str = "lid.176.ftz"):
    """
    Detect the language of the given text using fastText.
    Explanation:
    - Clean the text to remove noise.
    - Repeat short texts to improve detection accuracy.
    - Check against a minimum confidence threshold to filter uncertain detections.
    Returns a tuple of (language_code, confidence) or None, 0.0 if detection fails.
    """
    try:
        # Clean the text before detection from special characters and links
        text = clean_text(text)
        if not text:
            return None, 0.0

        # Repeat short texts to improve detection accuracy
        if len(text) < 20:
            text = " ".join([text] * 3)

        model = get_model(model_path)
        labels, probabilities = model.predict(text)
        language = labels[0].replace("__label__", "")
        confidence = probabilities[0]

        # Check against minimum confidence threshold
        if confidence < min_confidence:
            return None, confidence

        return language, confidence
    except Exception as e:
        logging.error(f"Language detection failed: {e}")
        return None, 0.0
