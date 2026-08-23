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

# Create top-level demo object for Hugging Face Spaces supervisor
with gr.Blocks(title="ParcelPilot AI — Operations & Support Intelligence", fill_height=True) as demo:
    gr.HTML("""
    <style>
        .gradio-container { max-width: 100% !important; padding: 0 !important; }
        footer { display: none !important; }
    </style>
    <iframe src="/" style="width: 100%; height: 96vh; border: none; border-radius: 8px;"></iframe>
    """)

# Mount Gradio sub-route onto the FastAPI application
app = gr.mount_gradio_app(app, demo, path="/gradio")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
