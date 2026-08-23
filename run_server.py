import os
import sys
import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.db.seed import seed_database
from backend.rag.ingest import ingest_documents

def bootstrap():
    print("==================================================")
    print("  ParcelPilot AI — Operations & Support Engine")
    print("==================================================")

    db_path = os.path.join(PROJECT_ROOT, "parcelpilot.db")
    if not os.path.exists(db_path):
        print("Seeding relational database from candidate pack...")
        seed_database()
    else:
        print(f"Database found at: {db_path}")

    chroma_path = os.path.join(PROJECT_ROOT, "chroma_db")
    if not os.path.exists(chroma_path) or len(os.listdir(chroma_path)) == 0:
        print("Ingesting PDF documents into ChromaDB vector store...")
        ingest_documents()
    else:
        print(f"Vector store found at: {chroma_path}")

    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    provider = os.environ.get("LLM_PROVIDER", "groq")

    # Ensure port is bindable or find open port
    import socket
    def is_port_bound(h, p):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind((h, p))
            s.close()
            return False
        except OSError:
            return True

    active_port = port
    if is_port_bound(host, active_port):
        for candidate in range(port + 1, port + 10):
            if not is_port_bound(host, candidate):
                active_port = candidate
                break

    print(f"\nStarting FastAPI Server & UI on http://{host}:{active_port} (Active LLM Provider: {provider}) ...")
    uvicorn.run("backend.api.main:app", host=host, port=active_port, reload=False)

if __name__ == "__main__":
    bootstrap()
