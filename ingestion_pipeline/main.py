from utils import IngestConfig
from ingest import ingest
import os

config = IngestConfig()
print(f"Base detected - Config path: {config.events_csv}")
print(f"Config exists: {os.path.exists(config.events_csv)}")
print(f"Chroma path: {config.chroma_path}")

ingest(config)