import sys
import os
import json
import csv
import logging
from typing import List, Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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
logger = logging.getLogger("patentlens.import_custom")

def load_records_from_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Parse custom dataset from JSON, CSV, or JSONL file formats.
    """
    if not os.path.exists(file_path):
        logger.error(f"Dataset file not found at: {file_path}")
        return []

    ext = os.path.splitext(file_path)[1].lower()
    records = []

    try:
        if ext == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                content = json.load(f)
                records = content if isinstance(content, list) else content.get("patents", [content])
        elif ext == ".jsonl":
            with open(file_path, "r", encoding="utf-8") as f:
                records = [json.loads(line) for line in f if line.strip()]
        elif ext == ".csv":
            with open(file_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                records = list(reader)
        else:
            logger.error(f"Unsupported file extension: '{ext}'. Use .json, .csv, or .jsonl")
            return []

        logger.info(f"Loaded {len(records)} raw records from {file_path}")
        return records

    except Exception as e:
        logger.error(f"Failed to parse dataset file {file_path}: {e}")
        return []


def import_custom_dataset_to_postgres(file_path: str, default_domain: str = "Artificial Intelligence"):
    """
    Import 1000+ patent dataset into PostgreSQL with batch SBERT vector embedding generation.
    """
    records = load_records_from_file(file_path)
    if not records:
        logger.warning("No records to import.")
        return

    db = SessionLocal()
    try:
        Base.metadata.create_all(bind=engine)

        if not embedding_service.is_loaded:
            embedding_service.load_model()

        logger.info(f"Starting bulk vector embedding & import of {len(records)} patents into PostgreSQL...")

        imported_count = 0
        batch_size = 50

        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]
            
            for index, item in enumerate(batch):
                pat_num = item.get("publication_number") or item.get("patent_number") or item.get("patent_id") or item.get("id") or f"PAT-CUSTOM-{i + index + 1}"
                
                # Check for existing record in PostgreSQL
                existing = db.query(Patent).filter(Patent.patent_number == pat_num).first()
                if existing:
                    continue

                title = item.get("title") or item.get("patent_title") or "Custom Invention"
                abstract = item.get("abstract") or item.get("patent_abstract") or title
                description = item.get("patent_text") or item.get("description") or item.get("patent_description") or abstract
                inventors = item.get("inventors") or item.get("inventor") or "Custom Inventor"
                assignee = item.get("assignee") or item.get("organization") or "Custom Assignee"
                pub_date = str(item.get("publication_date") or item.get("date") or "2024-01-01")
                domain = item.get("domain") or default_domain
                source_url = item.get("source_url") or item.get("url") or f"https://patents.google.com/patent/{pat_num}/en"

                combined_text = prepare_combined_text(title=title, problem_statement="", description=abstract + " " + description[:300])
                embedding_vec = embedding_service.generate_embedding(combined_text)

                patent = Patent(
                    patent_number=pat_num,
                    title=title,
                    abstract=abstract,
                    description=description,
                    inventors=inventors,
                    assignee=assignee,
                    publication_date=pub_date,
                    domain=domain,
                    source_url=source_url,
                    embedding=embedding_vec
                )
                db.add(patent)
                imported_count += 1

            db.commit()
            logger.info(f"Progress: Processed {min(i + batch_size, len(records))}/{len(records)} records...")

        logger.info(f"Successfully imported {imported_count} dataset records into PostgreSQL database!")

    except Exception as e:
        logger.error(f"Error importing custom dataset: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m backend.scripts.import_custom_dataset <path_to_dataset_file> [default_domain]")
        print("Example: python -m backend.scripts.import_custom_dataset backend/data/my_1000_patents.json \"Artificial Intelligence\"")
        sys.exit(1)

    dataset_path = sys.argv[1]
    domain_arg = sys.argv[2] if len(sys.argv) > 2 else "Artificial Intelligence"
    import_custom_dataset_to_postgres(file_path=dataset_path, default_domain=domain_arg)
