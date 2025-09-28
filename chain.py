import hashlib, time
from dataclasses import dataclass, asdict
from typing import List, Dict, Any

@dataclass
class Block:
    index: int
    timestamp: float
    actor: str
    action: str        # "DEPOSIT" | "WITHDRAW" | "GENESIS"
    amount: float
    note: str
    prev_hash: str
    # crypto flavor:
    wallet_address: str   # may be "" for unsigned tx
    signed_message: str   # the exact message user signed (canonical)
    signature: str        # 0x... signature from wallet
    hash: str

def _hash_block(payload: Dict[str, Any]) -> str:
    # include wallet/signature so tampering is evident
    raw = (
        f"{payload['index']}|{payload['timestamp']}|{payload['actor']}|"
        f"{payload['action']}|{payload['amount']}|{payload['note']}|{payload['prev_hash']}|"
        f"{payload['wallet_address']}|{payload['signed_message']}|{payload['signature']}"
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def make_genesis() -> Block:
    base = {
        "index": 0,
        "timestamp": 0.0,
        "actor": "SYSTEM",
        "action": "GENESIS",
        "amount": 0.0,
        "note": "Ledger created",
        "prev_hash": "0"*64,
        "wallet_address": "",
        "signed_message": "",
        "signature": "",
    }
    return Block(**base, hash=_hash_block(base))

def canonical_message(pot_name: str, actor: str, action: str, amount: float, ts: float, prev_hash: str) -> str:
    # This is what MetaMask signs. Keep format stable!
    return f"POT:{pot_name}|ACTOR:{actor}|ACTION:{action}|AMOUNT:{amount:.2f}|TS:{int(ts)}|PREV:{prev_hash}"

def make_block(prev: Block, actor: str, action: str, amount: float, note: str,
               wallet_address: str, signed_message: str, signature: str) -> Block:
    idx = prev.index + 1
    payload = {
        "index": idx,
        "timestamp": time.time(),
        "actor": actor.strip() or "UNKNOWN",
        "action": action,
        "amount": round(float(amount), 2),
        "note": (note or "").strip(),
        "prev_hash": prev.hash,
        "wallet_address": wallet_address or "",
        "signed_message": signed_message or "",
        "signature": signature or "",
    }
    return Block(**payload, hash=_hash_block(payload))

def validate_chain(chain: List[Block]) -> bool:
    if not chain or chain[0].action != "GENESIS":
        return False
    for i in range(1, len(chain)):
        cur, prev = chain[i], chain[i-1]
        if cur.prev_hash != prev.hash:
            return False
        recomputed = _hash_block({
            "index": cur.index,
            "timestamp": cur.timestamp,
            "actor": cur.actor,
            "action": cur.action,
            "amount": cur.amount,
            "note": cur.note,
            "prev_hash": cur.prev_hash,
            "wallet_address": cur.wallet_address,
            "signed_message": cur.signed_message,
            "signature": cur.signature,
        })
        if recomputed != cur.hash:
            return False
    return True

def to_dicts(chain: List[Block]) -> List[Dict[str, Any]]:
    return [asdict(b) for b in chain]

def from_dicts(rows: List[Dict[str, Any]]) -> List[Block]:
    return [Block(**row) for row in rows]
