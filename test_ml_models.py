"""
Test script for ML models
Run this to verify your models are working correctly.
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'maternity.settings')
django.setup()

from feetal_app.ml_service import predict_maternal_health, predict_preterm_delivery

def test_maternal_health_model():
    """Test maternal health prediction model."""
    print("\n" + "="*50)
    print("Testing Maternal Health Model")
    print("="*50)
    
    # Sample test data
    test_data = {
        'age': 28,
        'systolic_bp': 120,
        'diastolic_bp': 80,
        'bs': 95.5,
        'heart_rate': 72,
        'body_temp': 98.6
    }
    
    print(f"\nInput data: {test_data}")
    result = predict_maternal_health(test_data)
    
    if result.get('success'):
        print(f"✓ Prediction successful!")
        print(f"  Prediction: {result.get('prediction')}")
        print(f"  Risk Level: {result.get('risk_level')}")
        if result.get('prediction_proba'):
            print(f"  Probabilities: {result.get('prediction_proba')}")
    else:
        print(f"✗ Prediction failed: {result.get('error')}")
    
    return result.get('success', False)

def test_preterm_delivery_model():
    """Test preterm delivery prediction model."""
    print("\n" + "="*50)
    print("Testing Preterm Delivery CNN Model")
    print("="*50)
    
    # Sample test data
    test_data = {
        'gestational_age': 32,
        'maternal_age': 28,
        'bmi': 24.5,
        'previous_preterm': 0
    }
    
    print(f"\nInput data: {test_data}")
    result = predict_preterm_delivery(test_data)
    
    if result.get('success'):
        print(f"✓ Prediction successful!")
        print(f"  Probability: {result.get('probability')*100:.2f}%")
        print(f"  Risk Level: {result.get('risk_level')}")
        print(f"  Prediction: {result.get('prediction')}")
    else:
        print(f"✗ Prediction failed: {result.get('error')}")
    
    return result.get('success', False)

if __name__ == '__main__':
    print("\n" + "="*50)
    print("ML Models Test Script")
    print("="*50)
    
    # Test both models
    maternal_success = test_maternal_health_model()
    preterm_success = test_preterm_delivery_model()
    
    print("\n" + "="*50)
    print("Test Summary")
    print("="*50)
    print(f"Maternal Health Model: {'✓ PASSED' if maternal_success else '✗ FAILED'}")
    print(f"Preterm Delivery Model: {'✓ PASSED' if preterm_success else '✗ FAILED'}")
    
    if maternal_success and preterm_success:
        print("\n✓ All models are working correctly!")
    else:
        print("\n✗ Some models failed. Check the error messages above.")
