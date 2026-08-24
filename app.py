import gradio as gr
from backend.api.main import app

# Mount FastAPI app into Gradio (port 7860 is default on HF Spaces)
app_gradio = gr.mount_gradio_app(app, gr.Blocks(title="ParcelPilot AI"), path="/")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
