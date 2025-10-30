# 🩺 AI Skin Disease Detection App

A powerful AI-powered web application for skin disease detection using machine learning, built with Flask, TensorFlow, and integrated with SMS notifications via Twilio.

## 🌟 Features

- **AI-Powered Detection**: Uses TensorFlow/Keras with MobileNetV2 for accurate skin disease classification
- **24 Disease Types**: Detects Acne, Melanoma, Eczema, Psoriasis, and 20+ other skin conditions
- **SMS Notifications**: Instant SMS reports via Twilio integration
- **Contact Form**: MongoDB-powered contact system
- **Responsive Design**: Mobile-friendly interface with Three.js animations
- **Cloud Ready**: Optimized for Render deployment

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- MongoDB (local or MongoDB Atlas)
- Twilio account (optional, for SMS features)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/vaibhavwaliaa/Skin-Disease-Detection-App.git
   cd Skin-Disease-Detection-App
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your actual credentials
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

Visit `http://localhost:5000` to access the application.

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Flask Configuration
FLASK_ENV=development
PORT=5000

# MongoDB (Optional)
MONGO_URI=mongodb://localhost:27017/contactDB

# Twilio SMS (Optional)
TWILIO_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number
YOUR_PHONE_NUMBER=your_verified_phone_number
```

## 🏥 Supported Skin Conditions

The AI model can detect 24 different skin conditions:

- Acne
- Actinic Keratosis  
- Benign Tumors
- Bullous
- Candidiasis
- Drug Eruption
- Eczema
- Hives (Urticaria)
- Infestations Bites
- Lichen
- Lupus
- Melanoma
- Moles
- Psoriasis
- Rosacea
- Seborrheic Keratoses
- Skin Cancer
- Sunlight Damage
- Tinea
- Unknown/No Disease
- Vascular Tumors
- Vasculitis
- Vitiligo
- Warts

## ☁️ Cloud Deployment

This app is optimized for deployment on [Render](https://render.com/).

### Deploy to Render

1. **Fork this repository**
2. **Connect to Render**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Create new "Web Service"
   - Connect your GitHub repository

3. **Configure Environment Variables**
   - Add all required environment variables in Render dashboard
   - See `RENDER_DEPLOYMENT.md` for detailed instructions

4. **Deploy**
   - Render will automatically build and deploy your app
   - Use the provided URL to access your live application

For detailed deployment instructions, see [`RENDER_DEPLOYMENT.md`](RENDER_DEPLOYMENT.md).

## 📁 Project Structure

```
├── app.py                 # Main Flask application
├── model.py              # Model training script
├── model_checkpoint.h5   # Pre-trained AI model
├── requirements.txt      # Python dependencies
├── runtime.txt          # Python version for deployment
├── render.yaml          # Render deployment configuration
├── static/              # Static files (CSS, images, uploads)
├── templates/           # HTML templates
├── contact-us/          # Contact form functionality
└── derma-auth/          # Authentication system
```

## 🛠️ Development

### Running Tests
```bash
python -m pytest tests/
```

### Training New Model
```bash
python model.py
```

### API Endpoints

- `GET /` - Main application interface
- `POST /predict` - Image prediction endpoint
- `POST /send_sms` - SMS notification endpoint
- `GET /contact` - Contact form
- `GET /location` - Dermatologist locator

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## ⚠️ Disclaimer

This application is for educational and research purposes only. AI predictions should not replace professional medical diagnosis. Always consult with qualified healthcare providers for medical advice.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Vaibhav Walia**
- GitHub: [@vaibhavwaliaa](https://github.com/vaibhavwaliaa)

## 🙏 Acknowledgments

- TensorFlow team for the excellent ML framework
- MobileNetV2 architecture for efficient image classification
- Render for reliable cloud hosting
- Twilio for SMS integration

---

⭐ **Star this repo if you found it helpful!**