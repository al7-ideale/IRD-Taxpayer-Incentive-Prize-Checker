# IRD Taxpayer Incentive Prize Checker

Extract coupon codes from payment screenshots using OCR and check them against official IRD winning lists.

## Features

- **Vercel Ready**: A lightweight FastAPI backend that easily deploys to Vercel's Serverless environment.
- **OCR Extraction**: Automatic 12-digit code detection from PNG, JPG, and WebP files using OCR.space.
- **Instant Validation**: Real-time cross-referencing with official IRD draw database.
- **Modern UI**: Clean HTML/JS frontend styled with TailwindCSS.

## Requirements

- Python 3.8+
- (Optional) OCR.space free API key (defaults to test key 'helloworld')

## Quick Start (Local)

```bash
pip install -r requirements.txt
uvicorn index:app --reload
```

Open `http://127.0.0.1:8000` to upload images or input codes manually.

## Vercel Deployment

This project is now fully configured for deployment on [Vercel](https://vercel.com/):

1. Push this repository to GitHub/GitLab/Bitbucket.
2. Go to your Vercel Dashboard and click **Add New Project**.
3. Import the repository.
4. Leave the Framework Preset as **Other**.
5. Set any environment variables if needed (e.g., `OCR_SPACE_API_KEY` for a dedicated OCR API key).
6. Click **Deploy**.

Vercel will use the provided `vercel.json` and `index.py` to host the FastAPI application automatically.

## Project Structure

```text
.
├── index.py           # FastAPI application (Entrypoint)
├── templates/         # HTML/JS Frontend UI (TailwindCSS)
├── main.py            # Command line application
├── ird_api.py         # IRD API client
├── ocr.py             # OCR.space integration & text extraction logic
├── vercel.json        # Vercel deployment configuration
└── requirements.txt   # Python package dependencies
```

## Configuration

Optional environment variables:

```env
API_TIMEOUT=10
API_URL=https://prize.ird.gov.np/api/v1/public/winners
OCR_SPACE_API_KEY=helloworld
CACHE_TTL=3600
```

## License

Distributed as-is for IRD prize verification.
