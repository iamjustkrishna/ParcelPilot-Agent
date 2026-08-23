import os
import gradio as gr
from backend.api.main import app

# Ensure database and vector index exist on cold start
if not os.path.exists("parcelpilot.db"):
    from backend.db.seed import seed_database
    seed_database()

if not os.path.exists("chroma_db"):
    from backend.rag.ingest import ingest_documents
    ingest_documents()

# Mount FastAPI app into Gradio (port 7860 is default on HF Spaces)
app_gradio = gr.mount_gradio_app(app, gr.Blocks(title="ParcelPilot AI"), path="/")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
