from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel
from typing import List

from ird_api import fetch_winners

app = FastAPI(title="IRD Prize Winner Checker")

# Use absolute path for templates
BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = BASE_DIR / "templates" / "index.html"

# Constants
MAX_COUPON_LENGTH = 12
CACHE_TTL_SECONDS = 3600

# Simple memory cache for winners
_winners_cache = {"data": None, "timestamp": 0}


def get_winners():
    """Fetches winners data with a basic in-memory cache."""
    import time
    now = time.time()
    
    if _winners_cache["data"] and (now - _winners_cache["timestamp"] < CACHE_TTL_SECONDS):
        return _winners_cache["data"]
        
    try:
        winners = fetch_winners()
        _winners_cache["data"] = winners
        _winners_cache["timestamp"] = now
        return winners
    except Exception as e:
        print(f"Failed to fetch winners: {e}")
        return None


@app.get("/", response_class=HTMLResponse)
async def read_root():
    return HTMLResponse(content=TEMPLATE_PATH.read_text(encoding="utf-8"))


class CheckRequest(BaseModel):
    coupons: List[str]


@app.post("/api/check")
async def check_prizes(req: CheckRequest):
    """
    Receives a list of parsed coupons from the frontend, checks them against the IRD database.
    """
    # 1. Get the current winning draw dictionary
    winning_dict = get_winners()
    
    if not winning_dict:
        raise HTTPException(status_code=500, detail="Cannot process: IRD winners data is unavailable.")

    # Deduplicate coupons
    all_coupons = list(dict.fromkeys(req.coupons))
    
    results = []
    winners_count = 0
    
    # Check each unique coupon against the winning dictionary
    for coupon in all_coupons:
        if coupon in winning_dict:
            info = winning_dict[coupon]
            
            # Extract and format the claim deadline
            deadline_str = info.get("claim_deadline", "N/A")
            formatted_deadline = deadline_str
            if deadline_str != "N/A" and "T" in deadline_str:
                date_part = deadline_str.split("T")[0]
                try:
                    dt = datetime.strptime(date_part, "%Y-%m-%d")
                    formatted_deadline = dt.strftime("%B %d, %Y")
                except Exception:
                    pass
            
            results.append({
                "Result": "WINNER",
                "Coupon Code": coupon,
                "Prize Rank": str(info.get("rank", "N/A")),
                "Draw Title": info.get("draw", info.get("category", "N/A")),
                "Claim Deadline": formatted_deadline,
            })
            winners_count += 1
        else:
            results.append({
                "Result": "No Prize Won",
                "Coupon Code": coupon,
                "Prize Rank": "—",
                "Draw Title": "—",
                "Claim Deadline": "—",
            })

    return JSONResponse({
        "total_checked": len(all_coupons),
        "winners_count": winners_count,
        "results": results
    })
