import os
from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader

# 1. Load environment configurations immediately at runtime
load_dotenv()

app = Flask(__name__)

# 2. Cloudinary Setup - Automatically detects CLOUDINARY_URL environment key
cloudinary.config(secure=True)

# 3. MongoDB Setup
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client['toy_store']
toys_collection = db['toys']

@app.route('/')
def home():
    try:
        # Fetch all toys from MongoDB to display on the storefront
        all_toys = list(toys_collection.find({}, {'_id': 0}))
    except Exception as e:
        print(f"❌ Database error reading inventory: {e}")
        all_toys = []
    
    return render_template('index.html', toys=all_toys)

@app.route('/add-toy', methods=['POST'])
def add_toy():
    name = request.form.get('name')
    price = request.form.get('price')
    description = request.form.get('description')
    image_file = request.files.get('image')

    # Guard clause: Verify if the form submission included a valid file payload
    if not image_file or image_file.filename == '':
        print("❌ CRITICAL: No image file was submitted by the browser.")
        return "Error: Please upload a valid image file.", 400

    try:
        print("⏳ Step 1: Uploading file directly to Cloudinary CDN...")
        upload_result = cloudinary.uploader.upload(image_file, folder="toys_website")
        image_url = upload_result.get('secure_url')
        print(f"✅ Cloudinary upload complete! Link: {image_url}")

        print("⏳ Step 2: Persisting toy metadata to MongoDB Atlas...")
        toy_data = {
            "name": name,
            "price": float(price) if price else 0.0,
            "description": description,
            "image_url": image_url
        }
        toys_collection.insert_one(toy_data)
        print("✅ Database Saved Successfully!")

    except Exception as e:
        print("\n💥 --- ERROR TRACEBACK ENCOUNTERED --- 💥")
        print(f"Exception Type: {type(e).__name__}")
        print(f"Error Message Details: {str(e)}")
        print("💥 --------------------------------- 💥\n")
        return f"Application Error: {str(e)}", 500

    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
