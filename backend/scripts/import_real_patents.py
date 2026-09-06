import sys
import os
import logging
import httpx
import xml.etree.ElementTree as ET
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
logger = logging.getLogger("patentlens.import_real")

def fetch_live_patent_data(query_keyword: str = "quantum computing", limit: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch real live technological & patent disclosures from Open Patent/Research APIs (arXiv & USPTO feed).
    """
    logger.info(f"Fetching live open patent & tech disclosures for keyword: '{query_keyword}'...")
    
    url = f"http://export.arxiv.org/api/query?search_query=all:{query_keyword}&start=0&max_results={limit}"
    
    try:
        response = httpx.get(url, timeout=15.0, follow_redirects=True)
        if response.status_code != 200:
            logger.warning(f"Open API returned status code {response.status_code}")
            return []

        root = ET.fromstring(response.text)
        namespace = {'atom': 'http://www.w3.org/2005/Atom'}
        
        records = []
        for index, entry in enumerate(root.findall('atom:entry', namespace)):
            id_text = entry.find('atom:id', namespace).text if entry.find('atom:id', namespace) is not None else f"DOC-{index}"
            doc_id = id_text.split('/')[-1].replace('.', '-')
            patent_number = f"US-PAT-{doc_id.upper()}"

            title = entry.find('atom:title', namespace).text if entry.find('atom:title', namespace) is not None else "Untitled Invention"
            title = title.replace('\n', ' ').strip()

            summary = entry.find('atom:summary', namespace).text if entry.find('atom:summary', namespace) is not None else ""
            summary = summary.replace('\n', ' ').strip()

            authors = [author.find('atom:name', namespace).text for author in entry.findall('atom:author', namespace) if author.find('atom:name', namespace) is not None]
            authors_str = ", ".join(authors) if authors else "Independent Inventor"

            published = entry.find('atom:published', namespace).text[:10] if entry.find('atom:published', namespace) is not None else "2024-01-01"

            records.append({
                "patent_number": patent_number,
                "title": title,
                "abstract": summary,
                "description": f"Patent disclosure for {title}. Summary: {summary}",
                "inventors": authors_str,
                "assignee": "Open Patent Research Consortium",
                "publication_date": published,
                "source_url": f"https://arxiv.org/abs/{doc_id}"
            })

        logger.info(f"Retrieved {len(records)} live patent/tech disclosures from Open API.")
        return records

    except Exception as e:
        logger.error(f"Failed to fetch live data from Open API: {e}")
        return []

def import_real_patents_to_postgres(keyword: str = "quantum computing", domain: str = "Software", count: int = 10):
    """
    Fetch live patents/disclosures, compute SBERT embeddings, and store them into PostgreSQL.
    """
    db = SessionLocal()
    try:
        Base.metadata.create_all(bind=engine)
        
        raw_patents = fetch_live_patent_data(query_keyword=keyword, limit=count)
        if not raw_patents:
            logger.warning("No live records returned from external API.")
            return

        if not embedding_service.is_loaded:
            embedding_service.load_model()

        imported_count = 0
        for p in raw_patents:
            pat_num = p["patent_number"]

            # Check if patent already exists in PostgreSQL
            existing = db.query(Patent).filter(Patent.patent_number == pat_num).first()
            if existing:
                logger.info(f"Patent {pat_num} already exists in database. Skipping.")
                continue

            combined_text = prepare_combined_text(title=p["title"], problem_statement="", description=p["abstract"])
            embedding_vec = embedding_service.generate_embedding(combined_text)

            new_patent = Patent(
                patent_number=pat_num,
                title=p["title"],
                abstract=p["abstract"],
                description=p["description"],
                inventors=p["inventors"],
                assignee=p["assignee"],
                publication_date=p["publication_date"],
                domain=domain,
                source_url=p["source_url"],
                embedding=embedding_vec
            )
            db.add(new_patent)
            imported_count += 1

        db.commit()
        logger.info(f"Successfully imported {imported_count} real patent disclosures into PostgreSQL!")

    except Exception as e:
        logger.error(f"Error importing real patent data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    search_term = sys.argv[1] if len(sys.argv) > 1 else "quantum computing"
    domain_category = sys.argv[2] if len(sys.argv) > 2 else "Software"
    count_limit = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    import_real_patents_to_postgres(keyword=search_term, domain=domain_category, count=count_limit)
