import io
import re
import warnings
from pathlib import Path
from typing import Union, List
import base64

import requests
from PIL import Image

warnings.filterwarnings("ignore")

# =============================================================================
# Constants
# =============================================================================
SUPPORTED_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp'}
COUPON_PATTERN = r"\b\d{12}\b"
COUPON_LENGTH = 12
MAX_IMAGE_DIMENSION = 1280

# Character map for fixing common OCR misreadings
OCR_CHAR_MAP = {
    "O": "0",
    "o": "0",
    "I": "1",
    "l": "1",
    "|": "1",
    "Z": "2",
    "S": "5",
    "s": "5",
    "B": "8",
}

# Free API key for OCR.space - user can override via environment variable if needed
OCR_SPACE_API_KEY = "helloworld"


def normalize_ocr_digits(text: str) -> str:
    """Fixes common OCR character misreadings where digits are read as letters."""
    return "".join(OCR_CHAR_MAP.get(char, char) for char in text)


def is_similar(code1: str, code2: str, max_diff: int = 2) -> bool:
    """Detects near-duplicate codes caused by single-digit OCR misreads."""
    if len(code1) != len(code2):
        return False
    diff_count = sum(1 for a, b in zip(code1, code2) if a != b)
    return 0 < diff_count <= max_diff


def deduplicate_near_matches(coupons: List[str]) -> List[str]:
    """
    Collapses near-duplicate OCR readings into the most accurate candidate.
    Prioritizes codes starting with "0" as they are more reliable.
    """
    clean_coupons: List[str] = []
    
    for coupon in coupons:
        duplicate = False
        for i, existing in enumerate(clean_coupons):
            if is_similar(coupon, existing):
                if coupon.startswith("0") and not existing.startswith("0"):
                    clean_coupons[i] = coupon
                duplicate = True
                break
        
        if not duplicate:
            clean_coupons.append(coupon)
    
    return clean_coupons


def preprocess_and_downscale(
    image_input: Union[Path, str, Image.Image, bytes],
    max_dim: int = MAX_IMAGE_DIMENSION
) -> bytes:
    """
    Downscales image to prevent memory/payload issues and returns as JPEG bytes.
    """
    try:
        if isinstance(image_input, (str, Path)):
            img = Image.open(image_input).convert("RGB")
        elif isinstance(image_input, bytes):
            img = Image.open(io.BytesIO(image_input)).convert("RGB")
        elif isinstance(image_input, Image.Image):
            img = image_input.convert("RGB")
        else:
            raise ValueError(
                f"Unsupported image input type: {type(image_input).__name__}. "
                "Expected Path, str, Image.Image, or bytes."
            )

        width, height = img.size
        if max(width, height) > max_dim:
            if width > height:
                new_w, new_h = max_dim, int(height * (max_dim / width))
            else:
                new_h, new_w = max_dim, int(width * (max_dim / height))
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        # Convert back to bytes for API payload
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=85)
        return img_byte_arr.getvalue()
    
    except IOError as e:
        raise IOError(f"Failed to read image: {str(e)}")
    except Exception as e:
        raise Exception(f"Error preprocessing image: {str(e)}")


def _call_ocr_space_api(image_bytes: bytes) -> str:
    """Calls the OCR.space API and returns the parsed text."""
    b64_image = base64.b64encode(image_bytes).decode('utf-8')
    payload = {
        'base64Image': f'data:image/jpeg;base64,{b64_image}',
        'apikey': OCR_SPACE_API_KEY,
        'language': 'eng',
        'isOverlayRequired': False
    }
    
    try:
        response = requests.post(
            'https://api.ocr.space/parse/image',
            data=payload,
            timeout=15
        )
        response.raise_for_status()
        result = response.json()
        
        if result.get('IsErroredOnProcessing'):
            print(f"OCR API Error: {result.get('ErrorMessage')}")
            return ""
            
        parsed_results = result.get('ParsedResults', [])
        if not parsed_results:
            return ""
            
        return parsed_results[0].get('ParsedText', '')
    except Exception as e:
        print(f"OCR Request failed: {e}")
        return ""


def extract_coupons_from_image(image_input: Union[Path, str, Image.Image, bytes]) -> List[str]:
    """
    Uses OCR.space API on downscaled images to safely extract 12-digit coupon codes.
    """
    try:
        processed_img_bytes = preprocess_and_downscale(image_input)
        raw_text = _call_ocr_space_api(processed_img_bytes)
    except Exception as e:
        print(f"OCR processing failed: {str(e)}")
        return []

    found_coupons: List[str] = []

    # Method 1: Direct regex match for 12-digit patterns
    matches = re.findall(COUPON_PATTERN, raw_text)
    found_coupons.extend(matches)

    # Method 2: Check individual words for potential OCR-garbled coupons
    words = raw_text.split()
    for word in words:
        cleaned_word = re.sub(r"[^\w]", "", word)
        if len(cleaned_word) == COUPON_LENGTH:
            normalized = normalize_ocr_digits(cleaned_word)
            if normalized.isdigit():
                found_coupons.append(normalized)

    unique_matches = list(dict.fromkeys(found_coupons))
    return deduplicate_near_matches(unique_matches)


def extract_coupons_from_directory(directory: Path) -> List[str]:
    """Recursively extracts coupons from all image files in a directory."""
    if not isinstance(directory, Path):
        directory = Path(directory)
    
    if not directory.exists() or not directory.is_dir():
        raise ValueError(f"Invalid directory: {directory}")
    
    all_coupons: List[str] = []
    image_files = [f for f in directory.rglob('*') if f.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS]
    
    for image_file in image_files:
        try:
            coupons = extract_coupons_from_image(image_file)
            all_coupons.extend(coupons)
        except Exception as e:
            print(f"⚠️  Error processing {image_file.name}: {str(e)}")
            continue
    
    return list(dict.fromkeys(all_coupons))
