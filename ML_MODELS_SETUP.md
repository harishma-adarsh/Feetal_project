# ML Models Integration Setup Guide

## Overview
This project now supports two machine learning models for maternal health predictions:
1. **Maternal Health Model** (`model_maternal_health_v2.pkl`) - Predicts overall maternal health risk
2. **Preterm Delivery CNN Model** (`preterm_delivery_cnn.h5`) - Predicts preterm delivery risk

## Setup Instructions

### Step 1: Place Model Files
Copy your model files to the `ml_models` directory:
```
maternity/feetal_app/ml_models/model_maternal_health_v2.pkl
maternity/feetal_app/ml_models/preterm_delivery_cnn.h5
```

### Step 2: Install Dependencies
```bash
cd maternity
pip install -r requirements.txt
```

Required packages:
- numpy>=1.24.0
- scikit-learn>=1.3.0
- tensorflow>=2.13.0
- Pillow>=10.0.0
- pandas>=2.0.0

### Step 3: Configure Model Inputs (if needed)
Edit `maternity/feetal_app/ml_service.py` to match your model's expected input format:
- Adjust feature extraction in `predict_maternal_health()`
- Adjust feature extraction in `predict_preterm_delivery()`
- Update input shape for CNN model if different

### Step 4: Test the Integration
1. Start the Django server: `python manage.py runserver`
2. Navigate to the patient portal
3. Use the "AI Health Predictions" section to test predictions

## API Endpoints

### Maternal Health Prediction
**POST** `/api/predict/maternal-health/`

**Request Body:**
```json
{
    "age": 28,
    "systolic_bp": 120,
    "diastolic_bp": 80,
    "bs": 95.5,
    "heart_rate": 72,
    "body_temp": 98.6
}
```

**Response:**
```json
{
    "success": true,
    "prediction": 0,
    "risk_level": "Low Risk",
    "prediction_proba": [0.85, 0.10, 0.05],
    "message": "Risk assessment: Low Risk"
}
```

### Preterm Delivery Prediction
**POST** `/api/predict/preterm-delivery/`

**Request Body:**
```json
{
    "gestational_age": 32,
    "maternal_age": 28,
    "bmi": 24.5,
    "previous_preterm": 0
}
```

**Response:**
```json
{
    "success": true,
    "probability": 0.15,
    "risk_level": "Low Risk",
    "prediction": "Low Risk",
    "message": "Preterm delivery risk: Low Risk (15.00%)"
}
```

## Features

### Patient Portal
- **Maternal Health Assessment Form**: Enter health metrics to get risk assessment
- **Preterm Delivery Risk Form**: Enter pregnancy data to get preterm delivery probability
- Real-time predictions with visual risk indicators
- Results displayed with confidence scores

### Model Loading
- Models are loaded lazily (on first use)
- Cached in memory for performance
- Error handling for missing model files

## Customization

### Adjusting Input Features
If your models require different input features, update:
1. `ml_service.py` - Feature extraction functions
2. `views.py` - API validation for required fields
3. `patient-portal.html` - Form fields
4. `patient-portal.js` - Form data collection

### Model Output Interpretation
Customize risk level interpretation in:
- `_interpret_maternal_health_risk()` function
- `_interpret_preterm_risk()` function

## Troubleshooting

### Model Not Loading
- Check file paths in `ml_models/` directory
- Verify file permissions
- Check Django logs for error messages

### Prediction Errors
- Verify input data format matches model expectations
- Check model file integrity
- Review `ml_service.py` for feature extraction logic

### TensorFlow/Keras Issues
- Ensure TensorFlow version is compatible with your `.h5` model
- Check if model was saved with same TensorFlow version

## Notes
- Models are loaded once and cached for performance
- Adjust feature extraction based on your actual model requirements
- The CNN model input shape may need adjustment based on your model architecture

