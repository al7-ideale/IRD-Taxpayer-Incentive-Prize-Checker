import io
import re
import warnings
from pathlib import Path
from typing import Union, List

import cv2
import easyocr
import numpy as np
from PIL import Image
import streamlit as st

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


@st.cache_resource
def get_ocr_reader():
    """Initializes and caches the EasyOCR reader instance."""
    with st.spinner("Loading OCR model (first run only, please wait)..."):
        return easyocr.Reader(["en"], gpu=False, verbose=False)


def normalize_ocr_digits(text: str) -> str:
    """
    Fixes common OCR character misreadings where digits are read as letters.
    
    Args:
        text: Raw OCR text containing potential misreadings
        
    Returns:
        Text with common OCR errors corrected
    """
    return "".join(OCR_CHAR_MAP.get(char, char) for char in text)


def is_similar(code1: str, code2: str, max_diff: int = 2) -> bool:
    """
    Detects near-duplicate codes caused by single-digit OCR misreads.
    
    Args:
        code1: First coupon code
        code2: Second coupon code
        max_diff: Maximum number of differing digits to consider similar
        
    Returns:
        True if codes are similar (potential duplicates)
    """
    if len(code1) != len(code2):
        return False
    diff_count = sum(1 for a, b in zip(code1, code2) if a != b)
    return 0 < diff_count <= max_diff


def deduplicate_near_matches(coupons: List[str]) -> List[str]:
    """
    Collapses near-duplicate OCR readings into the most accurate candidate.
    Prioritizes codes starting with "0" as they are more reliable.
    
    Args:
        coupons: List of coupon codes potentially containing duplicates
        
    Returns:
        Deduplicated list of coupon codes
    """
    clean_coupons: List[str] = []
    
    for coupon in coupons:
        duplicate = False
        for i, existing in enumerate(clean_coupons):
            if is_similar(coupon, existing):
                # Prefer codes starting with "0" (more reliable OCR)
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
) -> np.ndarray:
    """
    Converts image to grayscale and downscales to prevent memory issues.
    Downscaling prevents Out-Of-Memory errors on Streamlit Cloud.
    
    Args:
        image_input: Image as file path, PIL Image, or bytes
        max_dim: Maximum dimension to downscale to
        
    Returns:
        Grayscale numpy array ready for OCR
        
    Raises:
        ValueError: If image input type is unsupported
        IOError: If image file cannot be read
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

        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
    
    except IOError as e:
        raise IOError(f"Failed to read image: {str(e)}")
    except Exception as e:
        raise Exception(f"Error preprocessing image: {str(e)}")


def extract_coupons_from_image(image_input: Union[Path, str, Image.Image, bytes]) -> List[str]:
    """
    Uses EasyOCR on downscaled images to safely extract 12-digit coupon codes.
    
    Args:
        image_input: Image as file path, PIL Image, or bytes
        
    Returns:
        List of extracted and deduplicated 12-digit coupon codes
    """
    try:
        reader = get_ocr_reader()
        processed_img = preprocess_and_downscale(image_input)
        results = reader.readtext(processed_img, detail=0)
    except Exception as e:
        st.error(f"OCR processing failed: {str(e)}")
        return []

    found_coupons: List[str] = []

    for item in results:
        if not isinstance(item, str):
            continue
            
        # Method 1: Direct regex match for 12-digit patterns
        matches = re.findall(COUPON_PATTERN, item)
        found_coupons.extend(matches)

        # Method 2: Check individual words for potential OCR-garbled coupons
        words = item.split()
        for word in words:
            # Remove special characters but keep digits and letters
            cleaned_word = re.sub(r"[^\w]", "", word)
            
            # Only process if it looks like a 12-character code
            if len(cleaned_word) == COUPON_LENGTH:
                # Normalize common OCR misreadings
                normalized = normalize_ocr_digits(cleaned_word)
                
                # Only add if result is all digits
                if normalized.isdigit():
                    found_coupons.append(normalized)

    # Remove exact duplicates while preserving order
    unique_matches = list(dict.fromkeys(found_coupons))
    
    # Handle near-duplicates caused by single-digit OCR errors
    return deduplicate_near_matches(unique_matches)


def extract_coupons_from_directory(directory: Path) -> List[str]:
    """
    Recursively extracts coupons from all image files in a directory.
    
    Args:
        directory: Path to directory containing image files
        
    Returns:
        Deduplicated list of all extracted coupon codes
    """
    if not isinstance(directory, Path):
        directory = Path(directory)
    
    if not directory.exists():
        raise ValueError(f"Directory does not exist: {directory}")
    
    if not directory.is_dir():
        raise ValueError(f"Path is not a directory: {directory}")
    
    all_coupons: List[str] = []
    
    # Recursively find all image files
    image_files = [
        f for f in directory.rglob('*')
        if f.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
    ]
    
    for image_file in image_files:
        try:
            coupons = extract_coupons_from_image(image_file)
            all_coupons.extend(coupons)
        except Exception as e:
            print(f"⚠️  Error processing {image_file.name}: {str(e)}")
            continue
    
    # Deduplicate across all files
    return list(dict.fromkeys(all_coupons))
