import logging
import gradio as gr
from rag_system.rag_engine import answer_question

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

def format_sources(sources):
    if not sources:
        return ""
    
    md = "### Sources\n\n"
    md += "| # | EventID | Location | Severity | Category | Timestamp |\n"
    md += "|---|---------|----------|----------|----------|----------|\n"
    
    for i, src in enumerate(sources, 1):
        md += (
            f"| {i} | {src.get('EventID', 'N/A')} | "
            f"{src.get('Location', 'N/A')} | "
            f"{src.get('Severity', 'N/A')} | "
            f"{src.get('Category', 'N/A')} | "
            f"{src.get('Timestamp', 'N/A')} |\n"
        )
    
    return md

def chatbot_response(message, history):
    if not message.strip():
        return "Please enter a question."
    
    try:
        answer, sources = answer_question(message, history=history, top_k=10)
        response = f"{answer}\n\n---\n\n{format_sources(sources)}" if sources else answer
        return response
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.exception("Error handling chatbot request: %s", error_details)
        return f"Error: {str(e)}\n\nPlease try again or contact support."

css_hide_footer = "footer {display:none !important;} .footer {display:none !important;}"
with gr.Blocks(title="Security Events RAG Chatbot") as demo:
    gr.HTML(f"<style>{css_hide_footer}</style>")
    
    gr.Markdown(
        """
        # 🔐 Security Events RAG Chatbot
        
        Ask questions about security events in natural language.
        
        **Example queries:**
        - "What happened in Building B?"
        - "Show me all critical events"
        - "Any unauthorized entries in the server room?"
        - "Fire alarms in the last week?"
        """
    )
    
    chatbot_interface = gr.ChatInterface(
        fn=chatbot_response,
        chatbot=gr.Chatbot(height=500, label="Chat History"),
        textbox=gr.Textbox(
            placeholder="Ask about security events...",
            container=False,
            scale=7
        ),
        title=None,
        description=None,
        examples=[
            "What happened in Building B?",
            "Show me all critical events",
            "Any fire alarms today?",
            "Unauthorized entries in the server room",
            "Camera issues in Building C"
        ],
        cache_examples=False,
    )
    
if __name__ == "__main__":
    demo.launch(share=False)