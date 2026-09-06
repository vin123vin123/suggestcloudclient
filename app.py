import os
from flask import Flask, request, jsonify
from pymongo import MongoClient
import cloudinary
import cloudinary.uploader
import os
from flask import Flask, request, jsonify
from pymongo import MongoClient
import cloudinary
import cloudinary.uploader

app = Flask(__name__)

MONGO_URI = os.environ.get("MONGO_URI")
CLOUDINARY_ENV_URL = os.environ.get("CLOUDINARY_URL")

if not MONGO_URI or not CLOUDINARY_ENV_URL:
    print("❌ CRITICAL ERROR: Environment keys are completely missing from the Render dashboard configuration settings!")
else:
    # 🔧 FORCE EXPLICIT CLOUDINARY CONFIGURATION
    try:
        cloudinary.config(CLOUDINARY_ENV_URL=os.environ.get("CLOUDINARY_URL")
        print("☁️ Cloudinary configuration initialized successfully.")
    except Exception as e:
        print(f"❌ Cloudinary Configuration Error: {str(e)}")




# MongoDB Connection Pipeline Setup
try:
    # Adding a 5-second timeout avoids hanging server requests if the database connection drops.
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client['toy_db']
    toys_collection = db['toys']
    new_toy = {
            "name": 'name',
            "price": '0.0',
            "description": 'description',
            "image_url": 'image_url'
        }

        # STEP 4: Insert the record into your collection
    toys_collection.insert_one(new_toy)
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
@app.route('/add-toy', methods=['POST'])
def add_toy():
    name = request.form.get('name')
    price = request.form.get('price')
    description = request.form.get('description')
    image_file = request.files.get('image')

    # STEP 1: Check if Flask actually received the file from the webpage
    if not image_file or image_file.filename == '':
        print("❌ CRITICAL: No image file was submitted by the browser.")
        return jsonify({"error": "Please upload a valid image file."}), 400

    try:
        # STEP 2: Upload the image file directly to Cloudinary
        print(f"🚀 Uploading {image_file.filename} to Cloudinary...")
        upload_result = cloudinary.uploader.upload(image_file)
        image_url = upload_result.get('secure_url')

        # STEP 3: Construct the document structure for MongoDB
        new_toy = {
            "name": name,
            "price": float(price) if price else 0.0,
            "description": description,
            "image_url": image_url
        }

        # STEP 4: Insert the record into your collection
        result = toys_collection.insert_one(new_toy)
        new_toy['_id'] = str(result.inserted_id)

        print(f"✅ Successfully added toy with ID: {new_toy['_id']}")
        return jsonify({
            "message": "Toy successfully created!",
            "toy": new_toy
        }), 201

    except Exception as e:
        print(f"❌ Failed to add toy: {str(e)}")
        return jsonify({"error": f"Server processing failed: {str(e)}"}), 500

        
    
       
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
