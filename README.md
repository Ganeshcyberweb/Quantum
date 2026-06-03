# Quantum — Hotel Review Sentiment Analysis

A Flask app that analyzes hotel review sentiment. It combines classical NLP
([TextBlob](https://textblob.readthedocs.io/)) with a **quantum-simulated**
confidence layer: each review's polarity is encoded onto a qubit and measured
on [qiskit-aer](https://qiskit.org/ecosystem/aer/)'s `AerSimulator` to produce a
probabilistic "positive" confidence (see [`quantum.py`](quantum.py)).

Reviews can be supplied three ways:
- free-text feedback,
- a Google **Place ID**, or
- a **hotel name** (looked up via the Google Places API).

## Setup

```bash
python -m venv venv
venv\Scripts\activate        # Windows  (use: source venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
python -m textblob.download_corpora
```

## Configuration

The app needs a Google API key with the **Places API** enabled. Never commit it.

```bash
cp .env.example .env         # then edit .env and set GOOGLE_API_KEY
```

Or set it in the environment directly:

```bash
set GOOGLE_API_KEY=your-key-here     # Windows
export GOOGLE_API_KEY=your-key-here  # macOS/Linux
```

The free-text feedback mode works without a key.

## Run

```bash
python app.py
```

Then open http://127.0.0.1:5000.

For production: `gunicorn app:app` (see `Procfile.txt`).
