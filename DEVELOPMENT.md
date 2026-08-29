# Development Guide

## 🛠️ Local Development Setup

### Prerequisites
- Python 3.8+
- Git
- Virtual environment tool (venv, conda, etc.)

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/al7-ideale/IRD-Taxpayer-Incentive-Prize-Checker.git
cd IRD-Taxpayer-Incentive-Prize-Checker

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

---

## 🧪 Testing

### Run Unit Tests
```bash
pytest tests/ -v
```

### Run with Coverage
```bash
pytest tests/ --cov=. --cov-report=html
```

### Test Specific Module
```bash
pytest tests/test_ocr.py -v
pytest tests/test_ird_api.py -v
```

### Manual Testing

**Test OCR Extraction:**
```python
from ocr import extract_coupons_from_image
from pathlib import Path

# Test with sample image
coupons = extract_coupons_from_image("path/to/screenshot.png")
print(f"Extracted: {coupons}")
```

**Test API Fetching:**
```python
from ird_api import fetch_winners

try:
    winners = fetch_winners()
    print(f"Loaded {len(winners)} winners")
except Exception as e:
    print(f"Error: {e}")
```

**Test CLI Mode:**
```bash
# Place test images in screenshots/ directory
python main.py
```

**Test Streamlit App:**
```bash
streamlit run app.py
```

---

## 🐛 Debugging

### Enable Debug Logging
```python
# In app.py or main.py
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
```

### Test OCR with Image Preview
```python
from ocr import preprocess_and_downscale
from PIL import Image
import matplotlib.pyplot as plt

img = Image.open("test_image.png")
preprocessed = preprocess_and_downscale(img)

plt.imshow(preprocessed, cmap='gray')
plt.title("Preprocessed Image for OCR")
plt.show()
```

### Test API Response
```bash
# Check API connectivity
curl https://prize.ird.gov.np/api/v1/public/winners | head -c 500

# Pretty print response
curl https://prize.ird.gov.np/api/v1/public/winners | python -m json.tool | head -50
```

### Streamlit Debug Mode
```bash
streamlit run app.py --logger.level=debug
```

---

## 📝 Code Quality

### Format Code
```bash
# Using Black
black app.py ird_api.py ocr.py main.py

# Using autopep8
autopep8 --in-place --aggressive app.py ird_api.py ocr.py main.py
```

### Check Type Hints
```bash
# Using mypy
mypy app.py ird_api.py ocr.py main.py

# Using pyright
pyright app.py ird_api.py ocr.py main.py
```

### Lint Code
```bash
# Using flake8
flake8 app.py ird_api.py ocr.py main.py

# Using pylint
pylint app.py ird_api.py ocr.py main.py
```

### Check for Security Issues
```bash
bandit -r . -ll
```

---

## 📦 Creating Test Images

### With ImageMagick
```bash
# Create test image with coupon number
convert -size 400x600 xc:white \
  -pointsize 48 \
  -draw "text 50,300 '027538139157'" \
  test_coupon.png
```

### With Python PIL
```python
from PIL import Image, ImageDraw, ImageFont

img = Image.new('RGB', (400, 600), color='white')
draw = ImageDraw.Draw(img)
draw.text((50, 300), "027538139157", fill='black')
img.save('test_coupon.png')
```

---

## 🔄 Git Workflow

### Feature Development
```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes and commit
git add .
git commit -m "Add new feature"

# Push to remote
git push origin feature/new-feature

# Create pull request
# (on GitHub)
```

### Code Review Checklist
- [ ] Type hints are complete
- [ ] Docstrings are present
- [ ] No unused imports
- [ ] Tests pass
- [ ] Code is formatted
- [ ] No security issues
- [ ] Performance is acceptable

---

## 🚀 Release Process

### Version Bump
```bash
# Update version in files
# - app.py: PAGE_TITLE
# - setup.py: version (if exists)
# - README.md: changelog

# Create git tag
git tag v1.1.0
git push origin v1.1.0
```

### Create Release Notes
```markdown
# Version 1.1.0

## Features
- Added feature X
- Improved feature Y

## Bug Fixes
- Fixed issue #123

## Performance
- Optimized OCR processing

## Dependencies
- Updated easyocr to 1.7.0
```

---

## 📊 Performance Profiling

### Profile OCR Performance
```python
import cProfile
import pstats
from ocr import extract_coupons_from_image

profiler = cProfile.Profile()
profiler.enable()

# Run OCR
coupons = extract_coupons_from_image("test_image.png")

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

### Profile Memory Usage
```bash
# Install memory profiler
pip install memory-profiler

# Run with memory profiling
python -m memory_profiler main.py
```

---

## 🔍 Debugging Streamlit Issues

### Clear Cache
```bash
streamlit cache clear
```

### Run with Verbose Output
```bash
streamlit run app.py --logger.level=debug --client.logger.level=debug
```

### Check Streamlit Version
```bash
streamlit --version
```

### Reset Streamlit Config
```bash
rm -rf ~/.streamlit/
```

---

## 📚 Documentation

### Update Docstrings
Use Google-style docstrings:
```python
def extract_coupons_from_image(image_input: Union[Path, str, Image.Image, bytes]) -> List[str]:
    """
    Extracts 12-digit coupon codes from an image using OCR.
    
    Uses EasyOCR for text recognition and applies intelligent error
    correction for common OCR misreadings.
    
    Args:
        image_input: Image source - can be a file path, PIL Image, or raw bytes
        
    Returns:
        List of extracted 12-digit coupon codes, deduplicated and cleaned
        
    Raises:
        ValueError: If image input type is not supported
        IOError: If image file cannot be read or is corrupted
        
    Example:
        >>> coupons = extract_coupons_from_image("screenshot.png")
        >>> print(coupons)
        ['027538139157', '026954870201']
    """
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Before Submitting PR
- [ ] Code follows project style
- [ ] Tests pass
- [ ] Type hints are complete
- [ ] Docstrings are updated
- [ ] No console errors
- [ ] README updated if needed

---

## 🆘 Troubleshooting Development Issues

### Issue: "ModuleNotFoundError: No module named 'streamlit'"
```bash
# Ensure virtual environment is activated
source venv/bin/activate
# or on Windows: venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: "CUDA not available" (for GPU users)
```bash
# This is normal if CUDA isn't installed
# The app will use CPU instead (slower but works)

# To use GPU:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Issue: "Port 8501 already in use"
```bash
# Use different port
streamlit run app.py --server.port 8502
```

### Issue: "No such file or directory: 'screenshots'"
```bash
# Create the directory
mkdir screenshots

# Add test images
cp test_images/*.png screenshots/
```

---

## 📖 Additional Resources

- **Streamlit Docs:** https://docs.streamlit.io
- **EasyOCR Docs:** https://github.com/JaidedAI/EasyOCR
- **OpenCV Docs:** https://docs.opencv.org
- **Python Typing:** https://docs.python.org/3/library/typing.html

---

## 💬 Getting Help

- **Issues:** Open a GitHub issue
- **Discussions:** Start a discussion thread
- **Email:** Contact the maintainers

---

**Happy developing! 🚀**
