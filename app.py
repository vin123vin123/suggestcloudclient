import os
from flask import Flask, request, jsonify
from pymongo import MongoClient
import cloudinary
import cloudinary.uploader

app = Flask(__name__)

# --- SERVER SIDE RECOVERY TRAP ---
# Instead of failing silently with a 500 error, this provides a clear message if variables are missing.
MONGO_URI = os.environ.get("MONGO_URI")
CLOUDINARY_URL = os.environ.get("CLOUDINARY_URL")

if not MONGO_URI or not CLOUDINARY_URL:
    print("❌ CRITICAL ERROR: Environment keys are completely missing from the Render dashboard configuration settings!")

# MongoDB Connection Pipeline Setup
try:
    # Adding a 5-second timeout avoids hanging server requests if the database connection drops.
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client['toy_db']
    toys_collection = db['toys']
    # Trigger a fast query request to force link verification on startup
    client.server_info() 
except Exception as e:
    print(f"❌ Database Connection Crash: {str(e)}")

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        "status": "online", 
        "database_connected": MONGO_URI is not None,
        "cloudinary_connected": CLOUDINARY_URL is not None
    }), 200

@app.route('/api/toys', methods=['GET'])
def get_toys():
    try:
        all_toys = list(toys_collection.find({}))
        for toy in all_toys:
            toy['_id'] = str(toy['_id'])
        return jsonify(all_toys), 200
    except Exception as e:
        return jsonify({"error": f"Database retrieval error: {str(e)}"}), 500

@app.route('/api/toys/add', methods=['POST'])
def add_toy():
    name = request.form.get('name')
    price = request.form.get('price')
    image_file = request.files.get('image')

    if not name or not price or not image_file:
        return jsonify({"error": "Form parsing validation error: missing parameters"}), 400

    try:
        # 1. Cloudinary upload using the environment string
        upload_result = cloudinary.uploader.upload(image_file, folder="toys_website")
        image_url = upload_result.get('secure_url')

        # 2. Database record injection tracking block
        toy_data = {
            "name": name,
            "price": float(price),
            "image_url": image_url
        }
        toys_collection.insert_one(toy_data)
        return jsonify({"message": "Toy added successfully!", "toy": name}), 201

    except Exception as e:
        # Returning the actual exception helps debug why the 500 error occurred
        return jsonify({"error": f"Internal process failed during upload lifecycle: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
