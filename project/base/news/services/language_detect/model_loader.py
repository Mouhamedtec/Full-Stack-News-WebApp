import logging
import threading

try:
    import fasttext
except ImportError:
    raise ImportError("The 'fasttext' library is required. Install it with 'pip install fasttext' if you are using windows use 'pip install fasttext-wheel'.")

_model = None
_model_lock = threading.Lock()

def get_model(model_path: str = "lid.176.ftz"):
    """
    Lazily load and return the fastText model. Thread-safe.
    Explanation:
    - Use a global variable to store the model instance.
    - Use a threading lock to ensure only one thread loads the model at a time.
    - Load the model from the specified path if not already loaded.
    Returns the loaded fastText model.
    """
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                try:
                    _model = fasttext.load_model(model_path)
                except Exception as e:
                    logging.error(f"Failed to load fastText model: {e}")
                    raise
    return _model
