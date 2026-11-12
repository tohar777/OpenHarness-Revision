
from flask import Flask, jsonify, request
from flask_cors import CORS
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

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
