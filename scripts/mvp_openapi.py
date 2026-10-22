"""Generate the frontend contract from the actual application routes."""
import json
import sys
import tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.app import create_app

with tempfile.TemporaryDirectory() as directory:
    schema=create_app(Path(directory)).openapi()
target=Path(__file__).resolve().parents[1]/'frontend/openapi.json'
target.write_text(json.dumps(schema,indent=2)+'\n')
