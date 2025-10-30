# Render Deployment Guide for Skin Disease Detection App

This guide will help you deploy your Flask-based skin disease detection application to Render.

## Prerequisites

1. A Render account (sign up at [render.com](https://render.com))
2. A GitHub repository with your project code
3. MongoDB Atlas account for database (recommended for production)
4. Twilio account for SMS functionality (optional)

## Step 1: Prepare Your Repository

Ensure your repository contains the following files:
- `app.py` (main Flask application)
- `requirements.txt` (Python dependencies)
- `render.yaml` (Render service configuration)
- `model_checkpoint.h5` (your trained ML model)
- `static/` and `templates/` folders
- All other project files

## Step 2: Set up MongoDB Atlas (Recommended)

1. Go to [MongoDB Atlas](https://cloud.mongodb.com/)
2. Create a free cluster
3. Create a database user with read/write permissions
4. Whitelist all IPs (0.0.0.0/0) or configure specific IPs
5. Get your connection string (should look like):
   ```
   mongodb+srv://username:password@cluster.mongodb.net/databasename?retryWrites=true&w=majority
   ```

## Step 3: Deploy to Render

### Option 1: Using Blueprint (Recommended)

1. **Fork/Push your code to GitHub**
   - Ensure all files are committed and pushed to your GitHub repository

2. **Create New Blueprint on Render**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New" → "Blueprint"
   - Connect your GitHub repository
   - Select the repository containing your skin disease detection app

3. **Render will automatically detect your `render.yaml` file and set up the service**

### Option 2: Manual Web Service Creation

1. **Create New Web Service**
   - Go to Render Dashboard
   - Click "New" → "Web Service"
   - Connect your GitHub repository

2. **Configure Service Settings**
   - **Name**: `skin-disease-detection` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT app:app`
   - **Plan**: Free (or paid plan for better performance)

## Step 4: Configure Environment Variables

In your Render service settings, add the following environment variables:

### Required Variables:
```
FLASK_ENV=production
PORT=10000
PYTHON_VERSION=3.9.18
```

### MongoDB Configuration:
```
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/databasename?retryWrites=true&w=majority
```

### Twilio SMS Configuration (Optional):
```
TWILIO_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number
YOUR_PHONE_NUMBER=your_verified_phone_number
```

## Step 5: Deploy and Test

1. **Trigger Deployment**
   - Render will automatically deploy when you push to your repository
   - Or manually trigger deployment from the Render dashboard

2. **Monitor Deployment**
   - Check the deployment logs in Render dashboard
   - Look for any errors and resolve them

3. **Test Your Application**
   - Once deployed, Render will provide you with a URL
   - Test all functionalities:
     - Image upload and prediction
     - SMS functionality (if configured)
     - Contact form (if MongoDB is configured)

## Common Issues and Solutions

### 1. Large Model File Issues
If your `model_checkpoint.h5` file is too large (>100MB):
- Use Git LFS (Large File Storage)
- Or host the model file externally and download it during deployment

### 2. Memory Issues
- The free plan has limited memory
- Consider upgrading to a paid plan
- Optimize your model size if possible

### 3. MongoDB Connection Issues
- Ensure your connection string is correct
- Check that IP addresses are whitelisted in MongoDB Atlas
- Verify database user permissions

### 4. Static Files Not Loading
- Ensure your static files are in the correct directory structure
- Check that Flask is configured to serve static files correctly

### 5. Twilio SMS Not Working
- Verify your Twilio credentials
- Ensure phone numbers are verified in Twilio console
- Check that you have sufficient Twilio credit

## Production Optimizations

1. **Use a Paid Plan**: For better performance and no sleep mode
2. **Enable Persistent Disks**: For file uploads storage
3. **Set up Custom Domain**: For professional appearance
4. **Enable HTTPS**: Usually enabled by default on Render
5. **Monitor Performance**: Use Render's monitoring tools

## Security Considerations

1. **Never commit sensitive data**: Use environment variables for all secrets
2. **Regular Updates**: Keep dependencies updated
3. **Input Validation**: Ensure proper file upload validation
4. **Rate Limiting**: Consider implementing rate limiting for API endpoints

## Post-Deployment

1. **Test thoroughly**: Test all features in production environment
2. **Monitor logs**: Regularly check application logs for issues
3. **Set up monitoring**: Consider using external monitoring services
4. **Backup data**: Regular backups of your MongoDB data

## Support and Troubleshooting

If you encounter issues:
1. Check Render deployment logs
2. Review environment variables configuration
3. Test MongoDB connection separately
4. Verify Twilio credentials and phone number verification
5. Contact Render support for platform-specific issues

## Useful Commands for Local Testing

Before deploying, test locally with production-like settings:

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables locally
export FLASK_ENV=production
export MONGO_URI=your_mongodb_uri
export TWILIO_SID=your_twilio_sid

# Run with gunicorn (production server)
gunicorn --bind 0.0.0.0:5000 app:app
```

## Next Steps

1. Set up continuous deployment
2. Configure custom domain
3. Set up monitoring and alerting
4. Plan for scaling if needed
5. Regular security updates

Your skin disease detection app should now be successfully deployed on Render!