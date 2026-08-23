import os
import gradio as gr
from backend.api.main import app

# Ensure database and vector index exist on cold start
if not os.path.exists("parcelpilot.db"):
    from backend.db.seed import seed_all
    seed_all()

if not os.path.exists("chroma_db"):
    from backend.rag.indexer import index_all_documents
    index_all_documents()

# Mount FastAPI app into Gradio (port 7860 is default on HF Spaces)
app_gradio = gr.mount_gradio_app(app, gr.Blocks(title="ParcelPilot AI"), path="/")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
