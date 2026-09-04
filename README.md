# IRD Taxpayer Incentive Prize Checker

Extract coupon codes from payment screenshots using OCR and check them against official IRD winning lists.

## Features

- **OCR Extraction**: Automatic 12-digit code detection from PNG, JPG, and WebP files
- **Instant Validation**: Real-time cross-referencing with official IRD draw database
- **Dual Interface**: Modern Streamlit web dashboard and command-line tool
- **Privacy First**: Client-side image processing; only coupon codes are sent to the API

## Requirements

- Python 3.8+
- System packages: `ffmpeg`, `libsm6`, `libxext6`, `libjpeg-dev`, `libpng-dev`, `libopencv-dev`

## Quick Start

### Web App (Streamlit)

```bash
pip install -r requirements.txt
streamlit run app.py

```

Open `http://localhost:8501` to upload images or input codes manually.

### CLI

```bash
pip install -r requirements.txt
python main.py

```

Place screenshots inside the `screenshots/` directory before running.

## Project Structure

```text
.
├── app.py           # Streamlit web application
├── main.py          # Command line application
├── ird_api.py       # IRD API client
├── ocr.py           # OCR engine & text extraction logic
├── packages.txt     # System level dependencies
└── requirements.txt # Python package dependencies

```

## Configuration

Optional environment variables (`.env`):

```env
API_TIMEOUT=10
API_URL=[https://prize.ird.gov.np/api/v1/public/winners](https://prize.ird.gov.np/api/v1/public/winners)
OCR_GPU=false
MAX_IMAGE_DIMENSION=1280
CACHE_TTL=3600

```

## Docker Deployment

```bash
docker build -t ird-checker .
docker run -p 8501:8501 ird-checker

```

## License

Distributed as-is for IRD prize verification.
