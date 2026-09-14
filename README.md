# IRD Taxpayer Incentive Prize Checker

Extract coupon codes from payment screenshots using OCR and check them against official IRD winning lists.

## Features

- **Vercel Ready**: A lightweight FastAPI backend that easily deploys to Vercel's Serverless environment.
- **Client-Side OCR**: Automatic 12-digit code detection from screenshots using browser-based Tesseract.js (no backend overhead or rate limits).
- **Instant Validation**: Real-time cross-referencing with official IRD draw database.
- **Modern UI**: Clean HTML/JS frontend styled with TailwindCSS.

## Requirements

- Python 3.8+

## Quick Start (Local)

```bash
pip install -r requirements.txt
uvicorn index:app --reload
```

Open `http://127.0.0.1:8000` to upload images or input codes manually.

## Vercel Deployment

This project is now fully configured for deployment on [Vercel](https://vercel.com/):

1. Push this repository to GitHub.
2. Go to your Vercel Dashboard and click **Add New Project**.
3. Import the repository.
4. Leave the Framework Preset as **Other**.
5. Click **Deploy**.

Vercel will use the provided `vercel.json` and `index.py` to host the FastAPI application automatically.

## Project Structure

```text
.
├── index.py           # FastAPI application (Entrypoint)
├── templates/         # HTML/JS Frontend UI (TailwindCSS & Tesseract.js)
├── main.py            # Command line application
├── ird_api.py         # IRD API client
├── vercel.json        # Vercel deployment configuration
└── requirements.txt   # Python package dependencies
```

## Configuration

Optional environment variables for the backend:

```env
API_TIMEOUT=10
API_URL=https://prize.ird.gov.np/api/v1/public/winners
CACHE_TTL=3600
```

## License

Distributed as-is for IRD prize verification.
