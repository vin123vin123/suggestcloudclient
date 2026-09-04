import os
from flask import Flask, request, jsonify
from pymongo import MongoClient
import cloudinary
import cloudinary.uploader

app = Flask(__name__)
app = Flask(__name__)

# 🟢 ADD THIS ROOT PATH SO THE MAIN HOMEPAGE WORKS
@app.route('/', methods=['GET'])
def homepage_status():
    return jsonify({
        "status": "online",
        "message": "Toy Store Backend API is working perfectly!"
    }), 200

# Your existing routes remain below this line...
@app.route('/api/toys', methods=['GET'])
def get_toys():
    # ... rest of your code


# Cloudinary automatically configures itself when CLOUDINARY_URL environment variable is set
# MongoDB Setup
MONGO_URI = os.getenv("MONGO_URI")
try:
    client = MongoClient(MONGO_URI)
    db = client['toy_db']
    toys_collection = db['toys']
except Exception as e:
    print(f"Database Connection Error: {e}")

# Endpoint for your Tkinter client to get all toys
@app.route('/api/toys', methods=['GET'])
def get_toys():
    try:
        all_toys = list(toys_collection.find({}))
        for toy in all_toys:
            toy['_id'] = str(toy['_id'])  # Convert MongoDB ID to string for JSON stability
        return jsonify(all_toys), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint for your Tkinter client to upload and add a toy
@app.route('/api/toys/add', methods=['POST'])
def add_toy():
    name = request.form.get('name')
    price = request.form.get('price')
    image_file = request.files.get('image')

    if not name or not price or not image_file:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # 1. Upload stream directly to Cloudinary
        upload_result = cloudinary.uploader.upload(image_file, folder="toys_website")
        image_url = upload_result.get('secure_url')

        # 2. Save product tracking inside your MongoDB cluster
        toy_data = {
            "name": name,
            "price": float(price),
            "image_url": image_url
        }
        toys_collection.insert_one(toy_data)
        return jsonify({"message": "Toy synchronized successfully!", "toy": name}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':


    # Local fallback runner

    app.run(host='0.0.0.0', port=5000) 