from flask import Flask, request, render_template
import requests
from textblob import TextBlob

app = Flask(__name__)

API_KEY = "GOOGLE_API_KEY_REDACTED"  # Replace with your valid Google API key

@app.route("/", methods=["GET", "POST"])
def home():
    sentiment = None
    text = None
    reviews = []
    property_name = None
    positive = negative = neutral = 0
    error = None

    if request.method == "POST":
        property_name_input = request.form.get("property_name", "").strip()
        place_id_input = request.form.get("place_id", "").strip()
        feedback = request.form.get("feedback", "").strip()

        # If user enters custom feedback
        if feedback:
            text = feedback
            polarity = TextBlob(text).sentiment.polarity
            if polarity > 0.1:
                sentiment = "Positive"
            elif polarity < -0.1:
                sentiment = "Negative"
            else:
                sentiment = "Neutral"
            return render_template("index.html", sentiment=sentiment, text=text)

        # If Place ID is provided
        if place_id_input:
            details_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id_input}&fields=name,reviews&key={API_KEY}"
            response = requests.get(details_url)
            data = response.json()
            if data.get("status") != "OK":
                error = data.get("error_message", "Invalid Place ID or API Key issue.")
            else:
                property_name = data["result"].get("name", "Unknown")
                google_reviews = data["result"].get("reviews", [])
        elif property_name_input:
            # If hotel name is provided
            search_url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={property_name_input}&key={API_KEY}"
            search_response = requests.get(search_url).json()

            if not search_response.get("results"):
                error = "No results found for that hotel name."
            else:
                place_id = search_response["results"][0]["place_id"]
                details_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,reviews&key={API_KEY}"
                response = requests.get(details_url)
                data = response.json()

                if data.get("status") != "OK":
                    error = data.get("error_message", "Unable to fetch hotel details.")
                else:
                    property_name = data["result"].get("name", "Unknown")
                    google_reviews = data["result"].get("reviews", [])
        else:
            error = "Please enter a hotel name or place ID."

        # If we got reviews, analyze them
        if not error and google_reviews:
            for review in google_reviews:
                text = review.get("text", "")
                rating = review.get("rating", 0)

                if not text:
                    continue

                polarity = TextBlob(text).sentiment.polarity

                # Combine polarity + rating for better accuracy
                if rating >= 4:
                    sentiment_result = "Positive"
                elif rating <= 2:
                    sentiment_result = "Negative"
                else:
                    if polarity > 0.2:
                        sentiment_result = "Positive"
                    elif polarity < -0.2:
                        sentiment_result = "Negative"
                    else:
                        sentiment_result = "Neutral"

                # Count categories
                if sentiment_result == "Positive":
                    positive += 1
                elif sentiment_result == "Negative":
                    negative += 1
                else:
                    neutral += 1

                reviews.append({
                    "author": review.get("author_name", "Anonymous"),
                    "rating": rating,
                    "text": text,
                    "sentiment": sentiment_result,
                    "time": review.get("relative_time_description", "Recently")
                })

    return render_template(
        "index.html",
        sentiment=sentiment,
        text=text,
        reviews=reviews,
        property_name=property_name,
        positive=positive,
        negative=negative,
        neutral=neutral,
        error=error
    )


if __name__ == "__main__":
    app.run(debug=True)
