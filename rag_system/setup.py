from sentence_transformers import SentenceTransformer
from openai import OpenAI
from chromadb import PersistentClient
import os
import dotenv
base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, "../chroma_db")

dotenv.load_dotenv()

client_llm = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

client = PersistentClient(db_path)
collection = client.get_collection("security_events_open_source")

embedder = SentenceTransformer("all-MiniLM-L6-v2")