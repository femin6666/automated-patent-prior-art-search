import os
import sys
import pickle
import logging
from typing import Tuple, List, Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    from backend.app.core.database import SessionLocal, engine
    from backend.app.models.models import Patent
    from backend.ml.preprocessing import prepare_combined_text
except ImportError:
    from app.core.database import SessionLocal, engine
    from app.models.models import Patent
    from ml.preprocessing import prepare_combined_text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("patentlens.train_ml")

MODEL_SAVE_DIR = os.path.join(os.path.dirname(__file__), "saved_models")
MODEL_FILE_PATH = os.path.join(MODEL_SAVE_DIR, "tfidf_model.pkl")

class PatentMLTrainer:
    """Trainer pipeline for TF-IDF feature extraction & hybrid similarity scoring."""

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=5000,
            stop_words="english"
        )
        self.patent_ids: List[str] = []
        self.tfidf_matrix = None
        self.is_trained = False

    def train_on_postgres_dataset(self) -> bool:
        """Fetch all 1,000+ patent records from PostgreSQL and fit TF-IDF vectorizer."""
        db = SessionLocal()
        try:
            logger.info("Fetching patent dataset from PostgreSQL database...")
            patents = db.query(Patent).all()
            if not patents:
                logger.warning("No patents found in PostgreSQL database to train ML model.")
                return False

            logger.info(f"Loaded {len(patents)} patent records. Extracting textual features...")
            
            corpus = []
            self.patent_ids = []

            for p in patents:
                combined_text = prepare_combined_text(
                    title=p.title,
                    problem_statement="",
                    description=f"{p.abstract} {p.description or ''}"
                )
                corpus.append(combined_text)
                self.patent_ids.append(p.id)

            logger.info("Fitting TF-IDF Vectorizer on 1,000+ patent dataset...")
            self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
            self.is_trained = True

            os.makedirs(MODEL_SAVE_DIR, exist_ok=True)
            with open(MODEL_FILE_PATH, "wb") as f:
                pickle.dump({
                    "vectorizer": self.vectorizer,
                    "tfidf_matrix": self.tfidf_matrix,
                    "patent_ids": self.patent_ids
                }, f)

            logger.info(f"ML Model training complete! Saved model to {MODEL_FILE_PATH}")
            return True

        except Exception as e:
            logger.error(f"Error during ML model training: {e}")
            return False
        finally:
            db.close()

    def compute_tfidf_similarity(self, input_text: str) -> List[Tuple[str, float]]:
        """Compute TF-IDF cosine similarity scores against trained dataset matrix."""
        if not self.is_trained or self.tfidf_matrix is None:
            if os.path.exists(MODEL_FILE_PATH):
                self.load_trained_model()
            else:
                return []

        try:
            input_vec = self.vectorizer.transform([input_text])
            sim_scores = cosine_similarity(input_vec, self.tfidf_matrix)[0]
            
            results = []
            for idx, score in enumerate(sim_scores):
                results.append((self.patent_ids[idx], float(score)))
                
            return sorted(results, key=lambda x: x[1], reverse=True)
        except Exception as e:
            logger.error(f"Error computing TF-IDF similarity: {e}")
            return []

    def load_trained_model(self) -> bool:
        """Load pre-trained TF-IDF model artifacts from disk."""
        if not os.path.exists(MODEL_FILE_PATH):
            return False

        try:
            with open(MODEL_FILE_PATH, "rb") as f:
                data = pickle.load(f)
                self.vectorizer = data["vectorizer"]
                self.tfidf_matrix = data["tfidf_matrix"]
                self.patent_ids = data["patent_ids"]
                self.is_trained = True
                logger.info("Loaded trained ML TF-IDF model into memory.")
                return True
        except Exception as e:
            logger.error(f"Failed to load trained ML model: {e}")
            return False

ml_trainer = PatentMLTrainer()

if __name__ == "__main__":
    ml_trainer.train_on_postgres_dataset()
