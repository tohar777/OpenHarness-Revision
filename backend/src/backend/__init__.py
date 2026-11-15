
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from backend.intergration import sendRequest
import asyncio
app = Flask(__name__)
CORS(app)
@app.post("/api/sendrequest")
def send_request():
    data = request.get_json(silent=True) or {}
    prompt = data.get("prompt", "").strip()

    print("Received prompt:", prompt)

    if not prompt:
        return jsonify({"error": "Empty prompt"}), 400

    try:
        ai_response = asyncio.run(sendRequest(prompt))

        print("AI response:", ai_response)

        return jsonify({"response": ai_response}), 200

    except Exception:
        app.logger.exception("AI request failed")
        return jsonify({"error": "AI request failed"}), 500
    except requests.exceptions.HTTPError as error:
        response = error.response

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After", "unknown")

            try:
                details = response.json()
            except ValueError:
                details = response.text

            return {
                "error": "rate_limit",
                "message": "OpenRouter rate limit reached.",
                "retry_after": retry_after,
                "details": details
            }

        return {
            "error": "api_error",
            "message": str(error)
        }
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
