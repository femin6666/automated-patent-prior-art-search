import sys
import os
import json
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session

try:
    from backend.app.core.database import SessionLocal, engine, Base
    from backend.app.models.models import Patent
    from backend.ml.embedding_service import embedding_service
    from backend.ml.preprocessing import prepare_combined_text
except ImportError:
    from app.core.database import SessionLocal, engine, Base
    from app.models.models import Patent
    from ml.embedding_service import embedding_service
    from ml.preprocessing import prepare_combined_text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("patentlens.seed")

def seed_patents_if_needed(db: Session = None):
    """Seed sample patent dataset and generate SBERT embeddings if database is empty."""
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        Base.metadata.create_all(bind=engine)

        # Seed Demo User if missing
        try:
            from backend.app.models.models import User
            from backend.app.core.security import hash_password
        except ImportError:
            from app.models.models import User
            from app.core.security import hash_password

        demo_user = db.query(User).filter(User.email == "inventor@startup.com").first()
        if not demo_user:
            demo_user = User(
                name="Demo Inventor",
                email="inventor@startup.com",
                password_hash=hash_password("password123"),
                is_verified=True
            )
            db.add(demo_user)
            db.commit()
            logger.info("Demo user 'inventor@startup.com' created successfully.")
        
        existing_count = db.query(Patent).count()
        if existing_count >= 100:
            logger.info(f"Database already seeded with {existing_count} patents. Skipping seeding.")
            return

        json_path = os.path.join(os.path.dirname(__file__), "..", "data", "sample_patents.json")
        if not os.path.exists(json_path):
            logger.error(f"Sample patent data file not found at {json_path}")
            return

        with open(json_path, "r", encoding="utf-8") as f:
            patents_data = json.load(f)

        logger.info(f"Seeding {len(patents_data)} patents into database & computing SBERT embeddings...")
        
        if not embedding_service.is_loaded:
            embedding_service.load_model()

        added = 0
        for item in patents_data:
            existing = db.query(Patent).filter(Patent.patent_number == item["patent_number"]).first()
            if existing:
                continue

            combined_text = prepare_combined_text(
                title=item["title"],
                problem_statement="",
                description=item["abstract"] + " " + item["description"]
            )
            
            embedding_vec = embedding_service.generate_embedding(combined_text)

            patent = Patent(
                id=item["id"],
                patent_number=item["patent_number"],
                title=item["title"],
                abstract=item["abstract"],
                description=item["description"],
                inventors=item["inventors"],
                assignee=item["assignee"],
                publication_date=item["publication_date"],
                domain=item["domain"],
                source_url=item.get("source_url"),
                embedding=embedding_vec
            )
            db.add(patent)
            added += 1

        db.commit()
        logger.info(f"Successfully seeded {added} patent documents with 384-d SBERT embeddings.")

    except Exception as e:
        logger.error(f"Error during patent database seeding: {e}")
        db.rollback()
    finally:
        if close_session:
            db.close()

if __name__ == "__main__":
    seed_patents_if_needed()
