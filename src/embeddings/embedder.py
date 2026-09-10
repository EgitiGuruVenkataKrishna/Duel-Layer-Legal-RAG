from typing import List
from sentence_transformers import SentenceTransformer
from src.config import EMBEDDING_MODEL_NAME

class Embedder:
    """
    Abstracted embedding interface. Currently uses local sentence-transformers.
    Designed to easily swap for an API (like Sarvam/Gemini) later.
    """
    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        # We load the model lazily or at initialization
        self.model_name = model_name
        self._model = None
        
    @property
    def model(self):
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Embeds a list of strings and returns a list of vectors.
        """
        if not texts:
            return []
            
        # sentence-transformers outputs a numpy array, we convert to list of floats for Chroma
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()

# Singleton-like instance for easy import
default_embedder = Embedder()
