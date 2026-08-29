import sys
import logging
from pathlib import Path

from ird_api import fetch_winners
from ocr import extract_coupons_from_directory

# =============================================================================
# Configuration
# =============================================================================
SCREENSHOTS_DIR = Path("screenshots")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# Functions
# =============================================================================

def get_manual_coupons() -> list[str]:
    """
    Prompts user for manual/missed coupon entries.
    
    Returns:
        List of manually entered 12-digit coupon codes
    """
    print("\n" + "=" * 50)
    print("MANUAL / MISSED COUPON ENTRY")
    print("=" * 50)
    print("Enter coupons (12 digits each) separated by spaces or commas.")
    print("Include coupons from IRD cash bill registration or missed screenshots.")
    print("Press ENTER without typing anything to skip.")

    user_input = input("\n> ").strip()
    if not user_input:
        return []

    raw_tokens = user_input.replace(",", " ").split()
    valid_coupons = []

    for token in raw_tokens:
        clean_token = "".join(filter(str.isdigit, token))
        if len(clean_token) == 12:
            valid_coupons.append(clean_token)
        else:
            print(f"⚠️  Skipped invalid coupon length: '{token}' (Must be 12 digits)")

    return valid_coupons


def display_results(all_coupons: list[str], winning_dict: dict) -> int:
    """
    Displays results of coupon verification.
    
    Args:
        all_coupons: List of coupon codes to check
        winning_dict: Dictionary of winning coupons from IRD API
        
    Returns:
        Number of winners found
    """
    print("\n" + "=" * 50)
    print("CHECK RESULTS")
    print("=" * 50)

    winners_found = 0
    
    for coupon in all_coupons:
        if coupon in winning_dict:
            prize_info = winning_dict[coupon]
            rank = prize_info.get("rank", "N/A")
            category = prize_info.get("category", "N/A")
            draw = prize_info.get("draw", "N/A")
            deadline = prize_info.get("claim_deadline", "N/A")
            
            print(
                f"🎉 WINNER FOUND: {coupon} | "
                f"Rank: {rank} | Category: {category} | Draw: {draw} | "
                f"Deadline: {deadline}"
            )
            winners_found += 1
        else:
            print(f"❌ NOT A WINNER: {coupon}")

    print("\n" + "=" * 50)
    print(f"Total Checked: {len(all_coupons)} | Winners Found: {winners_found}")
    print("=" * 50)
    
    return winners_found


def main() -> None:
    """Main entry point for the IRD Prize Checker CLI application."""
    
    # 1. Setup screenshots directory
    if not SCREENSHOTS_DIR.exists():
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created '{SCREENSHOTS_DIR}' directory. Place your screenshots there.")
        logger.info(f"Created screenshots directory at {SCREENSHOTS_DIR.absolute()}")
    
    # 2. OCR Extraction
    print("\n📸 Reading screenshots...")
    try:
        ocr_coupons = extract_coupons_from_directory(SCREENSHOTS_DIR)
        logger.info(f"Extracted {len(ocr_coupons)} unique coupon(s) via OCR")
        print(f"✅ Extracted {len(ocr_coupons)} unique coupon(s) via OCR.")
    except Exception as e:
        logger.error(f"Error during OCR extraction: {str(e)}")
        print(f"❌ Error reading screenshots: {str(e)}")
        sys.exit(1)

    # 3. Manual / Cash Payment Entry Prompt
    print("\n📝 Manual coupon entry...")
    manual_coupons = get_manual_coupons()
    logger.info(f"User entered {len(manual_coupons)} manual coupon(s)")
    if manual_coupons:
        print(f"✅ Entered {len(manual_coupons)} manual coupon(s).")

    # 4. Aggregate & Deduplicate
    all_coupons = list(dict.fromkeys(ocr_coupons + manual_coupons))

    if not all_coupons:
        print("\n⚠️  No coupons found or entered. Exiting.")
        logger.warning("No coupons found. Exiting.")
        sys.exit(0)

    print(f"\n✅ Total unique coupons to check: {len(all_coupons)}")
    logger.info(f"Total unique coupons to check: {len(all_coupons)}")

    # 5. Fetch IRD Winners
    print("\n🔄 Fetching winning records from IRD...")
    try:
        winning_dict = fetch_winners()
        logger.info(f"Loaded {len(winning_dict)} winning coupons from IRD API")
        print(f"✅ Loaded {len(winning_dict)} current winning coupons.")
    except TimeoutError as e:
        logger.error(f"API timeout: {str(e)}")
        print(f"❌ {str(e)}")
        sys.exit(1)
    except RuntimeError as e:
        logger.error(f"API error: {str(e)}")
        print(f"❌ {str(e)}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Invalid API response: {str(e)}")
        print(f"❌ {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error fetching winners: {str(e)}")
        print(f"❌ Failed to fetch winners from IRD API: {str(e)}")
        sys.exit(1)

    # 6. Check Results and Display
    winners_found = display_results(all_coupons, winning_dict)
    
    # 7. Log final summary
    logger.info(
        f"Verification complete. Total checked: {len(all_coupons)}, "
        f"Winners found: {winners_found}"
    )
    
    # Exit with appropriate code
    sys.exit(0 if winners_found > 0 else 1)


if __name__ == "__main__":
    main()
