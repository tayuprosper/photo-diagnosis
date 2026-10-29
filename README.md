# Photo Diagnosis

Send a photo of a plant, a product or a piece of work. Get a diagnosis and what to do locally. It copes with poor phone photos.

Photos that are too dark, small or blurry are stopped on your computer, so they cost no API credits.

## Setup

You need Python 3.10 or newer and an Anthropic API key.

```
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install anthropic python-dotenv pillow fastapi uvicorn python-multipart
```

Create a file named `.env` with one line. Never commit it.

```
ANTHROPIC_API_KEY=your-key-here
```

## Run

From the command line. The note is optional.

```
python3 diagnose.py photo.jpg "optional note"
```

As an API. Keep `127.0.0.1`, because there is no login.

```
uvicorn app:app --host 127.0.0.1 --port 8000
```

Try it at http://127.0.0.1:8000/docs with `POST /diagnose`.

## Files

| File | Job |
|---|---|
| `diagnose.py` | The core function and command line output |
| `helpers.py` | Instructions, the answer form, retake tips |
| `quality.py` | Measures size, brightness and sharpness. No API call |
| `app.py` | The FastAPI endpoint |
| `degrade.py` | Makes bad copies of a photo, for testing |
