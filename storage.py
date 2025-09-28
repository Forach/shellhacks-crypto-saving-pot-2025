import os, pandas as pd
from typing import List, Dict, Any

DATA_DIR = "data"
CSV_PATH = os.path.join(DATA_DIR, "ledger.csv")

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)

def save_chain(rows: List[Dict[str, Any]]):
    ensure_data_dir()
    pd.DataFrame(rows).to_csv(CSV_PATH, index=False)

def load_chain() -> List[Dict[str, Any]]:
    ensure_data_dir()
    if not os.path.exists(CSV_PATH):
        return []
    df = pd.read_csv(CSV_PATH)
    # types
    if "index" in df: df["index"] = df["index"].astype(int)
    if "timestamp" in df: df["timestamp"] = df["timestamp"].astype(float)
    if "amount" in df: df["amount"] = df["amount"].astype(float)
    for col in ["actor","action","note","prev_hash","wallet_address","signed_message","signature","hash"]:
        if col in df: df[col] = df[col].fillna("").astype(str)
    return df.to_dict(orient="records")
