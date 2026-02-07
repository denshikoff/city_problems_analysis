from fastapi import FastAPI
from typing import List, Dict, Any
import pandas as pd

from main import process_items  # твоя логика

app = FastAPI()

@app.post("/process")
def process_endpoint(items: List[Dict[str, Any]]):
    return process_items(items)
