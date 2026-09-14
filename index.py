from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pathlib import Path
from dateutil import parser as date_parser
import gc

from ird_api import fetch_winners
from ocr import extract_coupons_from_image, MAX_IMAGE_DIMENSION

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


@app.post("/api/check")
async def check_prizes(
    manual_input: str = Form(""),
    images: list[UploadFile] = File([])
):
    winning_dict = get_winners()
    if winning_dict is None:
        raise HTTPException(status_code=500, detail="Cannot process: IRD winners data is unavailable.")

    ocr_coupons = []
    
    # Process uploaded images
    for image in images:
        if not image.filename:
            continue
            
        try:
            image_bytes = await image.read()
            if len(image_bytes) > 0:
                extracted = extract_coupons_from_image(image_bytes)
                ocr_coupons.extend(extracted)
        except Exception as exc:
            print(f"Error reading {image.filename}: {exc}")
        finally:
            gc.collect()
            
    # Process manual inputs
    manual_coupons = []
    if manual_input.strip():
        raw_tokens = manual_input.replace(",", " ").split()
        for token in raw_tokens:
            clean_token = "".join(filter(str.isdigit, token))
            if len(clean_token) == MAX_COUPON_LENGTH:
                manual_coupons.append(clean_token)

    # Deduplicate across all sources
    all_coupons = list(dict.fromkeys(ocr_coupons + manual_coupons))
    
    results = []
    winners_count = 0

    for coupon in all_coupons:
        if coupon in winning_dict:
            info = winning_dict[coupon]
            raw_deadline = info.get("claim_deadline")
            
            formatted_deadline = "N/A"
            if raw_deadline:
                try:
                    dt = date_parser.parse(raw_deadline)
                    formatted_deadline = dt.strftime("%d %b %Y, %I:%M %p")
                except (ValueError, TypeError):
                    formatted_deadline = str(raw_deadline)

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
        "ocr_scanned": len(ocr_coupons),
        "results": results
    })

