# Language Detection

Language detection is implemented in base/news/services/language_detect and is used in:
- NewsRetrievalWithFiltersView (when a search term is present)
- fetch_provider_articles management command

## Components
- helpers.clean_text: normalizes and sanitizes input text
- detect.detect_language: performs fastText prediction and thresholding
- model_loader.get_model: lazy, thread-safe model loading

## Text Cleaning (helpers.clean_text)
The input is:
- encoded/decoded as UTF-8
- lowercased
- stripped of URLs
- stripped of punctuation while keeping a wide Unicode range (Latin, Cyrillic, Arabic, CJK, etc.)

If cleaning fails, None is returned.

## Detection Flow (detect.detect_language)
1) Clean the text.
2) If empty, return (None, 0.0).
3) Repeat short texts (< 20 chars) three times to improve accuracy.
4) Load the fastText model and run predict().
5) Convert fastText label to a language code (strip __label__).
6) Apply a minimum confidence threshold (default 0.7).
   - If confidence is below threshold: return (None, confidence).
   - Otherwise return (language_code, confidence).

## Model Loading (model_loader.get_model)
- Uses a global singleton `_model` and a threading lock.
- Loads the model from the provided `model_path` once, then reuses it.
- The default model path used by detect_language is `lid.176.ftz`.

## fastText Dependency
fastText is imported in model_loader.py:
- If fastText is not installed, an ImportError is raised at import time.
- On Windows, the error message recommends installing fasttext-wheel.

## Usage Notes
- The API view calls detect_language(search) and filters by Article.language if a language is detected.
- The article ingestion command calls detect_language on a shortened snippet (first 100 chars) and defaults language to 'en' if detection fails.
