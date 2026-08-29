import requests
from typing import Dict, Any

API_URL = "https://prize.ird.gov.np/api/v1/public/winners"
API_TIMEOUT_SECONDS = 10


def fetch_winners(timeout: int = API_TIMEOUT_SECONDS) -> Dict[str, Dict[str, Any]]:
    """
    Fetches public winners from IRD API and formats them indexed by coupon number.
    
    Args:
        timeout: Request timeout in seconds
        
    Returns:
        Dictionary mapping coupon numbers to winner information
        
    Raises:
        TimeoutError: If API request times out
        RuntimeError: If API returns an error or unexpected format
        ValueError: If API response is malformed
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Application/1.0"
    }
    
    try:
        response = requests.get(API_URL, headers=headers, timeout=timeout)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise TimeoutError(
            f"IRD API request timed out after {timeout} seconds. "
            "Please check your internet connection and try again."
        )
    except requests.exceptions.HTTPError as e:
        error_msg = f"IRD API returned HTTP {response.status_code}"
        try:
            error_details = response.text[:200]
            if error_details:
                error_msg += f": {error_details}"
        except Exception:
            pass
        raise RuntimeError(error_msg)
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Failed to connect to IRD API. Please check your internet connection."
        )
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Unexpected error connecting to IRD API: {str(e)}")

    try:
        data = response.json()
    except ValueError as e:
        raise ValueError(f"IRD API returned invalid JSON: {str(e)}")

    # Validate response structure
    if not isinstance(data, dict):
        raise ValueError("IRD API response is not a dictionary")
    
    if "draws" not in data:
        raise ValueError("IRD API response missing 'draws' key")
    
    if not isinstance(data["draws"], list):
        raise ValueError("IRD API 'draws' field is not a list")

    winners: Dict[str, Dict[str, Any]] = {}

    for draw in data.get("draws", []):
        if not isinstance(draw, dict):
            continue
            
        category = draw.get("category_title_en", "Unknown")
        draw_title = draw.get("title_en", "Unknown")
        claim_deadline = draw.get("claim_deadline")

        for winner in draw.get("winners", []):
            if not isinstance(winner, dict):
                continue
                
            coupon = winner.get("prize_coupon_number")
            
            # Skip if coupon is missing or not a string
            if not coupon or not isinstance(coupon, str):
                continue
            
            # Ensure coupon is 12 digits
            coupon = coupon.strip()
            if not coupon.isdigit() or len(coupon) != 12:
                continue
            
            winners[coupon] = {
                "category": category,
                "rank": winner.get("winner_rank"),
                "draw": draw_title,
                "claim_deadline": claim_deadline,
            }

    return winners
