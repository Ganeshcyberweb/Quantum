import os

import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request
from textblob import TextBlob

from quantum import quantum_sentiment

load_dotenv()

app = Flask(__name__)

# Read the Google API key from the environment (see .env.example).
API_KEY = os.environ.get("GOOGLE_API_KEY", "")

# Network timeout (seconds) for all outbound Google Places calls.
REQUEST_TIMEOUT = 10


def fetch_place_details(place_id):
    """Fetch a place's name + reviews. Returns (property_name, reviews, error)."""
    details_url = (
        "https://maps.googleapis.com/maps/api/place/details/json"
        f"?place_id={place_id}&fields=name,reviews&key={API_KEY}"
    )
    data = requests.get(details_url, timeout=REQUEST_TIMEOUT).json()

    if data.get("status") != "OK":
        return None, [], data.get("error_message", "Unable to fetch hotel details.")

    result = data["result"]
    return result.get("name", "Unknown"), result.get("reviews", []), None


@app.route("/health")
def health():
    """Lightweight liveness check (no qiskit import) for uptime pingers."""
    return {"status": "ok"}, 200


@app.route("/", methods=["GET", "POST"])
def home():
    sentiment = None
    text = None
    confidence = None
    reviews = []
    property_name = None
    positive = negative = neutral = 0
    avg_rating = None
    error = None

    if request.method == "POST":
        property_name_input = request.form.get("property_name", "").strip()
        place_id_input = request.form.get("place_id", "").strip()
        feedback = request.form.get("feedback", "").strip()

        google_reviews = []

        # 1) Custom feedback text -> quantum sentiment on the polarity.
        if feedback:
            text = feedback
            polarity = TextBlob(text).sentiment.polarity
            result = quantum_sentiment(polarity)
            sentiment = result["label"]
            confidence = round(result["p_positive"] * 100)
            return render_template(
                "index.html", sentiment=sentiment, text=text, confidence=confidence
            )

        # 2) A Places lookup requires a configured key.
        if (place_id_input or property_name_input) and not API_KEY:
            error = "Google API key not configured. Set GOOGLE_API_KEY (see .env.example)."
        elif place_id_input:
            try:
                property_name, google_reviews, error = fetch_place_details(place_id_input)
            except requests.RequestException:
                error = "Network error while contacting Google. Please try again."
        elif property_name_input:
            try:
                search_url = (
                    "https://maps.googleapis.com/maps/api/place/textsearch/json"
                    f"?query={property_name_input}&key={API_KEY}"
                )
                search_response = requests.get(search_url, timeout=REQUEST_TIMEOUT).json()

                if not search_response.get("results"):
                    error = "No results found for that hotel name."
                else:
                    place_id = search_response["results"][0]["place_id"]
                    property_name, google_reviews, error = fetch_place_details(place_id)
            except requests.RequestException:
                error = "Network error while contacting Google. Please try again."
        else:
            error = "Please enter a hotel name or place ID."

        # 3) Analyze any reviews we fetched.
        if not error and google_reviews:
            ratings = []
            for review in google_reviews:
                review_text = review.get("text", "")
                rating = review.get("rating", 0)

                if not review_text:
                    continue

                polarity = TextBlob(review_text).sentiment.polarity
                quantum = quantum_sentiment(polarity)

                # Star rating is a strong explicit signal; trust it when decisive
                # and fall back to the quantum-measured label otherwise.
                if rating >= 4:
                    sentiment_result = "Positive"
                elif rating <= 2:
                    sentiment_result = "Negative"
                else:
                    sentiment_result = quantum["label"]

                if sentiment_result == "Positive":
                    positive += 1
                elif sentiment_result == "Negative":
                    negative += 1
                else:
                    neutral += 1

                if rating:
                    ratings.append(rating)

                reviews.append({
                    "author": review.get("author_name", "Anonymous"),
                    "rating": rating,
                    "text": review_text,
                    "sentiment": sentiment_result,
                    "confidence": round(quantum["p_positive"] * 100),
                    "time": review.get("relative_time_description", "Recently"),
                })

            if ratings:
                avg_rating = round(sum(ratings) / len(ratings), 1)

    return render_template(
        "index.html",
        sentiment=sentiment,
        text=text,
        confidence=confidence,
        reviews=reviews,
        property_name=property_name,
        positive=positive,
        negative=negative,
        neutral=neutral,
        avg_rating=avg_rating,
        error=error,
    )


if __name__ == "__main__":
    app.run(debug=True)
