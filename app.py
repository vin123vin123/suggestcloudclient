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
    
@app.route('/add-toy', methods=['POST'])
 
def add_toy():
    name = request.form.get('name')
    price = request.form.get('price')
    description = request.form.get('description')
    image_file = request.files.get('image')

    # STEP 1: Check if Flask actually received the file from the webpage
    if not image_file or image_file.filename == '':
        print("❌ CRITICAL: No image file was submitted by the browser.")
        return "Error: Please upload a valid image file.", 400

    print(f"📦 File detected: {image_file.filename} | Content-Type: {image_file.content_type}")
    print(f"🔑 Using CLOUDINARY_URL: {os.getenv('CLOUDINARY_URL')[:30]}...") # Mask secret for logs

    try:
        # STEP 2: Execute Cloudinary upload
        print("⏳ Uploading directly to Cloudinary...")
        upload_result = cloudinary.uploader.upload(image_file, folder="toys_website")
        image_url = upload_result.get('secure_url')
        print(f"✅ Cloudinary Success! Image URL: {image_url}")

        # STEP 3: Execute Database Save
        print("⏳ Connecting to MongoDB...")
        toy_data = {
            "name": name,
            "price": float(price) if price else 0.0,
            "description": description,
            "image_url": image_url
        }
        toys_collection.insert_one(toy_data)
        print("✅ Database Saved Successfully!")

    except Exception as e:
        # STEP 4: Capture any backend crash details explicitly
        print("\n💥 --- ERROR TRACEBACK ENCOUNTERED --- 💥")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Error Message Details: {str(e)}")
        print("💥 --------------------------------- 💥\n")
        return f"Application Error: {str(e)}", 500

            # Delete: return redirect(url_for('home'))
        # Replace with this:
        return jsonify({
            "status": "success",
            "message": "Toy updated successfully!",
            "image_url": secure_url
        }), 200



     
        
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
