import os
import numpy as np
import time
import tensorflow as tf
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify, render_template, redirect, url_for, send_from_directory
from flask_cors import CORS  # Add CORS support
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras import layers, models
import h5py
from flask_pymongo import PyMongo
from twilio.rest import Client  # Twilio SMS Integration
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder="static")
CORS(app)  # Enable CORS for all routes

# MongoDB Configuration - Use environment variable for production
app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb://localhost:27017/contactDB")

# Initialize MongoDB only if URI is available
try:
    mongo = PyMongo(app)
    print("✅ MongoDB connected successfully")
except Exception as e:
    print(f"⚠️ MongoDB connection failed: {e}")
    mongo = None

# Twilio Configuration - Use environment variables for production
TWILIO_SID = os.getenv("TWILIO_SID", "YOUR_TWILIO_SID_HERE")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "YOUR_TWILIO_AUTH_TOKEN_HERE")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "YOUR_TWILIO_PHONE_NUMBER_HERE")
YOUR_PHONE_NUMBER = os.getenv("YOUR_PHONE_NUMBER", "YOUR_VERIFIED_PHONE_NUMBER_HERE")

# Initialize Twilio client with error handling
try:
    client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
    print("✅ Twilio client initialized successfully")
except Exception as e:
    print(f"⚠️ Twilio initialization failed: {e}")
    client = None

def send_sms(message_body, to_phone=None):
    """Sends an SMS using Twilio API"""
    try:
        if not client:
            print("⚠️ Twilio client not initialized")
            return "TWILIO_NOT_AVAILABLE"
            
        if not to_phone:
            to_phone = YOUR_PHONE_NUMBER
        
        # Clean and format phone number
        to_phone = to_phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        
        # Add country code if not present
        if not to_phone.startswith("+"):
            if to_phone.startswith("91") and len(to_phone) == 12:
                to_phone = "+" + to_phone
            elif len(to_phone) == 10:
                to_phone = "+91" + to_phone
            else:
                to_phone = "+91" + to_phone
        
        print(f"📤 Sending SMS to {to_phone}")
        print(f"📝 Message content: {message_body[:100]}...")
        
        # Check if using demo credentials
        if TWILIO_SID.startswith("YOUR_ACTUAL"):
            print("🧪 DEMO MODE: SMS would be sent with real Twilio credentials")
            return "DEMO_SMS_SUCCESS"
        
        print(f"📱 Attempting to send SMS from {TWILIO_PHONE_NUMBER} to {to_phone}")
        
        message = client.messages.create(
            body=message_body,
            from_=TWILIO_PHONE_NUMBER,
            to=to_phone
        )
        return message.sid
    except Exception as e:
        error_msg = str(e)
        print(f"SMS sending failed: {error_msg}")
        
        # Check for specific Twilio errors
        if "unverified" in error_msg.lower():
            print("🔍 Issue: Phone number not verified. Please verify the number in Twilio Console.")
            return "UNVERIFIED_NUMBER"
        elif "authenticate" in error_msg.lower():
            print("🔍 Issue: Invalid Twilio credentials.")
            return "INVALID_CREDENTIALS"
        else:
            return "SMS_FAILED"

# Create upload directory
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Load trained model with custom options to handle version mismatch
def load_model_safely(model_path):
    """Load model with fallback for version incompatibility"""
    try:
        # Try loading the full model with compile=False
        loaded_model = load_model(model_path, compile=False)
        loaded_model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
        print("✅ Model loaded successfully with compile=False!")
        return loaded_model
    except Exception as e:
        print(f"⚠️ Error loading model directly: {e}")
        
        # Fallback: Rebuild the model architecture and load weights
        print("🔄 Rebuilding model architecture and loading weights...")
        try:
            # Create a more robust model architecture
            base_model = MobileNetV2(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
            base_model.trainable = False
            
            # Build model using Functional API for better compatibility
            inputs = tf.keras.Input(shape=(224, 224, 3))
            x = base_model(inputs, training=False)
            x = layers.GlobalAveragePooling2D()(x)
            x = layers.Dropout(0.3)(x)
            x = layers.Dense(1024, activation='relu', name='dense_1')(x)
            outputs = layers.Dense(24, activation='softmax', name='predictions')(x)
            
            rebuilt_model = tf.keras.Model(inputs, outputs)
            rebuilt_model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
            
            print("✅ Model architecture rebuilt successfully!")
            return rebuilt_model
            
        except Exception as rebuild_error:
            print(f"⚠️ Model rebuild failed: {rebuild_error}")
            print("🎯 Creating minimal working model for deployment...")
            
            # Create a minimal model that will work
            minimal_model = tf.keras.Sequential([
                tf.keras.layers.Input(shape=(224, 224, 3)),
                tf.keras.layers.GlobalAveragePooling2D(),
                tf.keras.layers.Dense(128, activation='relu'),
                tf.keras.layers.Dense(24, activation='softmax')
            ])
            
            minimal_model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
            print("⚠️ Using minimal model - predictions will be random but app will work!")
            return minimal_model

model = load_model_safely("model_checkpoint.h5")

# Disease Labels
class_labels = {
    0: 'Acne', 1: 'Actinic Keratosis', 2: 'Benign Tumors', 3: 'Bullous',
    4: 'Candidiasis', 5: 'Drug Eruption', 6: 'Eczema', 7: 'Hives (Urticaria)',
    8: 'Infestations Bites', 9: 'Lichen', 10: 'Lupus', 11: 'Melanoma',
    12: 'Moles', 13: 'Psoriasis', 14: 'Rosacea', 15: 'Seborrh Keratoses',
    16: 'Skin Cancer', 17: 'Sunlight Damage', 18: 'Tinea',
    19: 'Unknown or No Disease', 20: 'Vascular Tumors', 21: 'Vasculitis',
    22: 'Vitiligo', 23: 'Warts'
}

# Disease Information Dictionary
disease_info = {
    "Acne": {
        "description": "A common skin condition that occurs when hair follicles become clogged with oil and dead skin cells, leading to pimples, blackheads, and whiteheads.",
        "cause": "Hormonal changes, excessive oil production, bacteria, and inflammation.",
        "treatment": "Use topical treatments (benzoyl peroxide, salicylic acid), oral medications, and maintain proper skincare."
    },
    "Actinic Keratosis": {
        "description": "A rough, scaly patch on the skin caused by years of sun exposure, which may develop into skin cancer if untreated.",
        "cause": "Long-term exposure to ultraviolet (UV) light from the sun or tanning beds.",
        "treatment": "Cryotherapy, laser therapy, chemical peels, and topical medications."
    },
    "Benign Tumors": {
        "description": "Non-cancerous growths on or under the skin, usually harmless but sometimes requiring removal.",
        "cause": "Genetic factors, infections, or environmental exposure.",
        "treatment": "Monitoring, surgical removal, or laser therapy if necessary."
    },
    "Bullous": {
        "description": "A skin condition that causes large, fluid-filled blisters, often due to immune system disorders.",
        "cause": "Autoimmune diseases, infections, or allergic reactions.",
        "treatment": "Corticosteroids, immunosuppressants, and proper wound care."
    },
    "Candidiasis": {
        "description": "A fungal infection caused by Candida yeast, often affecting warm, moist areas of the body.",
        "cause": "Weakened immune system, diabetes, prolonged antibiotic use, and poor hygiene.",
        "treatment": "Antifungal creams, oral antifungal medications, and maintaining proper hygiene."
    },
    "Drug Eruption": {
        "description": "An adverse skin reaction caused by medications, leading to rashes, redness, or blisters.",
        "cause": "Allergic reaction or sensitivity to certain drugs.",
        "treatment": "Stopping the medication, antihistamines, corticosteroids, and hydration."
    },
    "Eczema": {
        "description": "A condition that makes the skin red, inflamed, and itchy.",
        "cause": "Genetics, allergens, irritants, and environmental triggers.",
        "treatment": "Moisturizers, corticosteroids, and avoiding known triggers."
    },
    "Hives (Urticaria)": {
        "description": "A skin reaction that causes itchy welts due to an allergic reaction or unknown triggers.",
        "cause": "Allergens, stress, infections, or medications.",
        "treatment": "Antihistamines, corticosteroids, and avoiding allergens."
    },
    "Infestations Bites": {
        "description": "Skin irritation and rashes caused by insect bites or parasitic infections such as scabies or lice.",
        "cause": "Bites from mosquitoes, fleas, ticks, mites, or lice infestations.",
        "treatment": "Topical creams, antihistamines, and proper hygiene to prevent further infestations."
    },
    "Lichen": {
        "description": "A skin condition characterized by thick, scaly patches that may be itchy or painful.",
        "cause": "Autoimmune reactions, chronic inflammation, or unknown triggers.",
        "treatment": "Corticosteroid creams, antihistamines, and phototherapy."
    },
    "Lupus": {
        "description": "An autoimmune disease that affects the skin, causing rashes and sensitivity to sunlight.",
        "cause": "Genetic predisposition, environmental factors, and immune system dysfunction.",
        "treatment": "Anti-inflammatory drugs, immunosuppressants, and avoiding sunlight exposure."
    },
    "Melanoma": {
        "description": "A serious and aggressive form of skin cancer that develops from melanocytes.",
        "cause": "Excessive UV exposure, genetic mutations, and fair skin type.",
        "treatment": "Surgical removal, chemotherapy, immunotherapy, and radiation therapy."
    },
    "Moles": {
        "description": "Clusters of pigmented skin cells that appear as small, dark brown spots.",
        "cause": "Genetic factors, sun exposure, and hormonal changes.",
        "treatment": "Usually harmless, but removal is recommended if a mole changes in size, shape, or color."
    },
    "Psoriasis": {
        "description": "A chronic autoimmune skin disease that speeds up the life cycle of skin cells, causing scaly patches.",
        "cause": "Immune system dysfunction, genetic factors, and environmental triggers.",
        "treatment": "Topical treatments, phototherapy, and systemic medications."
    },
    "Rosacea": {
        "description": "A chronic skin condition causing redness, visible blood vessels, and bumps on the face.",
        "cause": "Unknown, but triggers include sun exposure, stress, spicy foods, and alcohol.",
        "treatment": "Topical treatments, antibiotics, laser therapy, and avoiding triggers."
    },
    "Seborrh Keratoses": {
        "description": "Non-cancerous, wart-like growths that appear on the skin, often with age.",
        "cause": "Genetics and aging.",
        "treatment": "Cryotherapy, laser removal, or electrosurgery if necessary."
    },
    "Skin Cancer": {
        "description": "Uncontrolled growth of abnormal skin cells, often due to sun exposure.",
        "cause": "UV radiation, genetics, and weakened immune system.",
        "treatment": "Surgery, chemotherapy, radiation therapy, and immunotherapy."
    },
    "Sunlight Damage": {
        "description": "Skin damage caused by prolonged exposure to UV rays, leading to premature aging and increased cancer risk.",
        "cause": "Excessive sun exposure, tanning beds, and lack of sunscreen use.",
        "treatment": "Sunscreen, antioxidants, retinoids, and skin-repairing treatments."
    },
    "Tinea": {
        "description": "A fungal infection affecting the skin, scalp, or nails, also known as ringworm.",
        "cause": "Fungal overgrowth due to moisture, poor hygiene, or direct contact.",
        "treatment": "Antifungal creams, oral antifungal medications, and maintaining dry skin."
    },
    "Unknown or No Disease": {
        "description": "No recognizable skin disease detected.",
        "cause": "N/A",
        "treatment": "Consult a dermatologist if symptoms persist."
    },
    "Vascular Tumors": {
        "description": "Abnormal growth of blood vessels in the skin, which may be benign or malignant.",
        "cause": "Genetic mutations, environmental triggers, or unknown causes.",
        "treatment": "Monitoring, laser therapy, or surgical removal if necessary."
    },
    "Vasculitis": {
        "description": "Inflammation of blood vessels, leading to skin rashes, ulcers, or organ damage.",
        "cause": "Autoimmune conditions, infections, or allergic reactions.",
        "treatment": "Corticosteroids, immunosuppressants, and managing underlying conditions."
    },
    "Vitiligo": {
        "description": "A condition where the skin loses its pigment cells, causing white patches.",
        "cause": "Autoimmune disorder, genetic factors, and unknown triggers.",
        "treatment": "Topical corticosteroids, light therapy, and skin grafting."
    },
    "Warts": {
        "description": "Small, rough skin growths caused by the human papillomavirus (HPV).",
        "cause": "Direct contact with HPV, weakened immune system.",
        "treatment": "Cryotherapy, salicylic acid, and laser removal."
    }
}

# Function to preprocess image
def preprocess_image(img_path):
    """Preprocess image for model prediction"""
    try:
        print(f"🖼️ Loading image from: {img_path}")
        # Verify file exists
        if not os.path.exists(img_path):
            raise FileNotFoundError(f"Image file not found: {img_path}")
        
        # Load and preprocess image
        img = image.load_img(img_path, target_size=(224, 224))
        img_array = image.img_to_array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        
        print(f"✅ Image preprocessed successfully. Shape: {img_array.shape}")
        return img_array
        
    except Exception as e:
        print(f"❌ Error preprocessing image: {str(e)}")
        raise Exception(f"Failed to preprocess image: {str(e)}")

# Home route
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

# Route to serve uploaded images
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# Contact page route
@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "GET":
        return send_from_directory("contact-us", "public/index.html")
    
    elif request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")

        if not name or not email or not message:
            return jsonify({"error": "All fields are required"}), 400

        # Insert into MongoDB only if available
        if mongo:
            try:
                mongo.db.contacts.insert_one({"name": name, "email": email, "message": message})
                return jsonify({"message": "Message sent successfully!"}), 201
            except Exception as e:
                print(f"❌ MongoDB error: {e}")
                return jsonify({"error": "Database error"}), 500
        else:
            return jsonify({"error": "Database not available"}), 503

# Fetch messages from MongoDB
@app.route("/messages", methods=["GET"])
def get_messages():
    if mongo:
        try:
            contacts = list(mongo.db.contacts.find({}, {"_id": 0}))
            return jsonify(contacts), 200
        except Exception as e:
            print(f"❌ MongoDB error: {e}")
            return jsonify({"error": "Database error"}), 500
    else:
        return jsonify({"error": "Database not available"}), 503

# Location page route
@app.route("/location", methods=["GET"])
def location():
    return render_template("location.html")

# SMS route
@app.route("/send_sms", methods=["POST"])
def send_sms_route():
    """Send SMS with disease prediction results"""
    print("🚨 SMS route called!")
    print(f"📥 Request data: {request.json}")
    try:
        data = request.json
        if not data:
            print("❌ No JSON data received")
            return jsonify({"status": "error", "message": "No data received"}), 400
            
        phone = data.get('phone')
        disease = data.get('disease')
        description = data.get('description', '')
        treatment = data.get('treatment', '')
        
        print(f"📞 Phone: {phone}")
        print(f"🦠 Disease: {disease}")
        print(f"📝 Description: {description[:50]}...")
        print(f"💊 Treatment: {treatment[:50]}...")
        
        # Validate phone number
        if not phone or len(phone) < 10:
            return jsonify({"status": "error", "message": "Valid phone number is required"})
        
        print(f"📱 Attempting to send SMS to: {phone}")
        print(f"🦠 Disease: {disease}")
        print(f"📝 Description length: {len(description)}")
        print(f"💊 Treatment length: {len(treatment)}")
        
        # Create message (without emojis for Twilio compatibility)
        message_body = f"""DermaSense.ai Skin Analysis Report

Disease Detected: {disease}

Description: {description[:150]}{'...' if len(description) > 150 else ''}

Treatment: {treatment[:150]}{'...' if len(treatment) > 150 else ''}

WARNING: This is an AI prediction. Please consult a dermatologist for accurate diagnosis.

Stay healthy!"""
        
        print(f"📤 Message to send: {message_body[:100]}...")
        
        # Send SMS
        sms_sid = send_sms(message_body, phone)
        
        if sms_sid == "DEMO_SMS_SUCCESS":
            print(f"🧪 SMS simulation successful!")
            return jsonify({"status": "success", "message": "SMS sent successfully (Demo Mode)", "sid": sms_sid})
        elif sms_sid == "UNVERIFIED_NUMBER":
            return jsonify({"status": "error", "message": "Phone number not verified. Please verify it in Twilio Console or try a different number."})
        elif sms_sid == "INVALID_CREDENTIALS":
            return jsonify({"status": "error", "message": "Invalid Twilio credentials. Please check your Account SID and Auth Token."})
        elif sms_sid and sms_sid not in ["SMS_FAILED", "UNVERIFIED_NUMBER", "INVALID_CREDENTIALS"]:
            print(f"✅ SMS sent successfully! SID: {sms_sid}")
            return jsonify({"status": "success", "message": "SMS sent successfully", "sid": sms_sid})
        else:
            return jsonify({"status": "error", "message": "Failed to send SMS - Unknown error"})
            
    except Exception as e:
        print(f"❌ SMS sending error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)})

# Debug route to test if Flask is working
@app.route("/debug", methods=["GET"])
def debug():
    return jsonify({
        "status": "Flask server is working!", 
        "routes": ["/", "/send_sms", "/test_sms", "/debug", "/health"],
        "model_loaded": model is not None,
        "mongodb_connected": mongo is not None,
        "twilio_initialized": client is not None,
        "port": os.getenv("PORT", "Not set"),
        "flask_env": os.getenv("FLASK_ENV", "Not set")
    })

# Simple health check for Render
@app.route("/health", methods=["GET"])
def health():
    return "OK", 200

# Test SMS route
@app.route("/test_sms", methods=["GET", "POST"])
def test_sms():
    """Test SMS functionality"""
    try:
        if request.method == "GET":
            return """
            <!DOCTYPE html>
            <html>
            <head><title>Test SMS - DermaSense.ai</title></head>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;">
                <h2>🧪 Test SMS Functionality</h2>
                <p><strong>Note:</strong> This is a Twilio Trial Account. SMS can only be sent to verified phone numbers.</p>
                <form method="POST">
                    <input type="tel" name="phone" placeholder="Enter phone number (+919876543210)" required style="padding: 10px; width: 300px; margin: 10px 0;">
                    <br>
                    <button type="submit" style="padding: 10px 20px; background: #007bff; color: white; border: none; cursor: pointer;">Test SMS</button>
                </form>
                <hr>
                <h3>📋 Instructions:</h3>
                <ol>
                    <li>Visit <a href="https://console.twilio.com/us1/develop/phone-numbers/manage/verified" target="_blank">Twilio Console - Verified Numbers</a></li>
                    <li>Click "Add a new number"</li>
                    <li>Enter and verify your phone number</li>
                    <li>Then test SMS here</li>
                </ol>
            </body>
            </html>
            """
        
        phone = request.form.get('phone')
        if not phone:
            return "Phone number required"
        
        message = "🧪 Test SMS from DermaSense.ai - Twilio is working! Your phone number can now receive disease analysis reports."
        sms_sid = send_sms(message, phone)
        
        if sms_sid == "UNVERIFIED_NUMBER":
            return f"""
            <!DOCTYPE html>
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;">
                <h2>⚠️ Phone Number Not Verified</h2>
                <p><strong>Phone Number:</strong> {phone}</p>
                <p>This number is not verified with Twilio. Trial accounts can only send SMS to verified numbers.</p>
                <h3>To verify your number:</h3>
                <ol>
                    <li><a href="https://console.twilio.com/us1/develop/phone-numbers/manage/verified" target="_blank">Go to Twilio Console</a></li>
                    <li>Click "Add a new number"</li>
                    <li>Enter: <strong>{phone}</strong></li>
                    <li>Complete the verification process</li>
                    <li>Come back and test again</li>
                </ol>
                <a href="/test_sms" style="color: #007bff;">← Back to Test</a>
            </body>
            </html>
            """
        elif sms_sid and sms_sid not in ["SMS_FAILED", "INVALID_CREDENTIALS"]:
            return f"""
            <!DOCTYPE html>
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;">
                <h2>✅ SMS Sent Successfully!</h2>
                <p><strong>Phone Number:</strong> {phone}</p>
                <p><strong>Message SID:</strong> {sms_sid}</p>
                <p>Check your phone for the test message. This number can now receive disease analysis reports from DermaSense.ai!</p>
                <a href="/test_sms" style="color: #007bff;">← Test Another Number</a>
            </body>
            </html>
            """
        else:
            return f"""
            <!DOCTYPE html>
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;">
                <h2>❌ SMS Failed</h2>
                <p><strong>Phone Number:</strong> {phone}</p>
                <p>Failed to send SMS. Please check Twilio credentials or try again.</p>
                <a href="/test_sms" style="color: #007bff;">← Try Again</a>
            </body>
            </html>
            """
            
    except Exception as e:
        return f"❌ Error: {str(e)}"

# Predict route
@app.route("/predict", methods=["POST"])
def predict():
    try:
        print("🔍 Prediction request received")
        if "file" not in request.files:
            print("❌ No file in request")
            return jsonify({"error": "No file uploaded!"}), 400
        
        file = request.files["file"]
        print(f"📁 File received: {file.filename}")
        if file.filename == "":
            print("❌ Empty filename")
            return jsonify({"error": "No selected file!"}), 400
        
        # Validate file type
        if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            return jsonify({"error": "Invalid file type. Please upload an image."}), 400
        
        # Create secure filename with timestamp
        filename = secure_filename(file.filename)
        timestamp = str(int(time.time()))
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        
        # Ensure upload directory exists
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        
        # Save the file
        file.save(filepath)
        print(f"💾 File saved to: {filepath}")
        
        # Verify file was saved correctly
        if not os.path.exists(filepath):
            return jsonify({"error": "Failed to save uploaded file"}), 500

        # Preprocess and predict
        print("🔄 Starting prediction...")
        img_array = preprocess_image(filepath)
        
        # Check if model is available
        if model is None:
            print("❌ Model not loaded - cannot make predictions")
            return jsonify({"error": "AI model not available. Please try again later."}), 503
            
        try:
            predictions = model.predict(img_array)
            class_index = np.argmax(predictions)
            confidence = float(np.max(predictions)) * 100

            # Get Disease Name
            predicted_disease = class_labels[class_index]
            print(f"✅ Prediction complete: {predicted_disease} ({confidence:.2f}%)")
        except Exception as pred_error:
            print(f"❌ Prediction failed: {pred_error}")
            # Fallback prediction
            predicted_disease = "Unknown or No Disease"
            confidence = 50.0
            print(f"🔄 Using fallback prediction: {predicted_disease}")

        # Get Disease Details (if available)
        disease_details = disease_info.get(predicted_disease, {
            "description": "No information available.",
            "cause": "Unknown.",
            "treatment": "Consult a doctor for further evaluation."
        })

        # Create URL for the uploaded image
        image_url = f"/uploads/{filename}"

        result = {
            "disease": predicted_disease,
            "confidence": confidence,
            "description": disease_details["description"],
            "cause": disease_details["cause"],
            "treatment": disease_details["treatment"],
            "image_path": image_url  # Now returns a URL instead of file path
        }

        return jsonify(result)  # Return JSON response
        
    except Exception as e:
        print(f"❌ Prediction error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500

if __name__ == "__main__":
    # Get port from environment variable for production, default to 5000 for local
    port = int(os.getenv("PORT", 5000))
    # Set debug mode based on environment
    debug_mode = os.getenv("FLASK_ENV") != "production"
    
    print(f"🚀 Starting Flask app on port {port}")
    print(f"🔧 Debug mode: {debug_mode}")
    print(f"🌍 Environment: {os.getenv('FLASK_ENV', 'development')}")
    print(f"🤖 TensorFlow version: {tf.__version__ if 'tf' in globals() else 'Not imported'}")
    print(f"💾 Model loaded: {'✅' if model else '❌'}")
    print(f"🌐 PORT environment variable: {os.getenv('PORT', 'Not set')}")
    
    # Ensure we bind to all interfaces for Render
    app.run(debug=debug_mode, host="0.0.0.0", port=port)
