import re
import unicodedata
from html import unescape
import pandas as pd
import hashlib
from dataclasses import dataclass
import os

@dataclass
class IngestConfig:
    chroma_path: str = None
    events_csv: str = None
    event_types_csv: str = None
    collection_name: str = "security_events_open_source"
    embedding_model: str = "all-MiniLM-L6-v2"
    batch_size: int = 50
    
    def __post_init__(self):
        base_dir = os.getenv('APP_BASE_DIR')
        
        if base_dir is None:
            current_file = os.path.abspath(__file__)
            
            if current_file.startswith('/app/'):
                base_dir = '/app'
            else:
                base_dir = os.path.dirname(os.path.dirname(current_file))
        
        if self.chroma_path is None:
            self.chroma_path = os.path.join(base_dir, "chroma_db")
        if self.events_csv is None:
            self.events_csv = os.path.join(base_dir, "data", "events_octopus.csv")
        if self.event_types_csv is None:
            self.event_types_csv = os.path.join(base_dir, "data", "event_types_octopus.csv")

def clean_text(text: str) -> str:
    if pd.isna(text):
        return ""
    
    text = str(text)
    text = re.sub(r"<[^>]+>", "", text)        
    text = unescape(text)                       
    text = unicodedata.normalize("NFKC", text) 
    text = text.lower()                         
    text = re.sub(r"[^a-zA-Z0-9\s\u00C0-\u017F]", " ", text) 
    text = re.sub(r"\s+", " ", text).strip()   
    
    return text

def parse_timestamp(ts):
    try:
        return pd.to_datetime(ts, dayfirst=True)
    except Exception:
        try:
            return pd.to_datetime(ts)
        except Exception:
            return pd.NaT

def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()