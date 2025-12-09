"""
ML Service module for loading and using maternal health & preterm delivery models.
Supports numeric form input + medical report files (TXT/PDF/DOCX) with OCR extraction.
"""
import os
import logging
import re
from django.conf import settings

try:
    import numpy as np
except ImportError:
    np = None
    logging.warning("NumPy not installed. ML prediction disabled.")

# OCR dependencies
import pdfplumber
from docx import Document

logger = logging.getLogger(__name__)

# Lazy-loaded model instances
_maternal_health_model = None
_preterm_delivery_model = None


# ------------------------- MODEL LOADING -------------------------
def get_model_path(filename):
    return os.path.join(settings.BASE_DIR, "feetal_app", "ml_models", filename)


def load_maternal_health_model():
    """Load the maternal health prediction model"""
    global _maternal_health_model
    if _maternal_health_model is None:
        try:
            import joblib
            _maternal_health_model = joblib.load(get_model_path("model_maternal_health_v2.pkl"))
            logger.info("Maternal health model loaded successfully")
        except Exception as e:
            logger.error(f"Maternal model load error: {str(e)}")
            _maternal_health_model = None
    return _maternal_health_model


def load_preterm_delivery_model():
    """Load the preterm delivery CNN model"""
    global _preterm_delivery_model
    if _preterm_delivery_model is None:
        try:
            from tensorflow import keras
            _preterm_delivery_model = keras.models.load_model(get_model_path("preterm_delivery_cnn.h5"))
            logger.info("Preterm delivery CNN model loaded successfully")
        except Exception as e:
            logger.error(f"Preterm model load error: {str(e)}")
            _preterm_delivery_model = None
    return _preterm_delivery_model


# ------------------------- MEDICAL REPORT OCR EXTRACTOR -------------------------
def extract_medical_values(file):
    """Extract structured numeric values from TXT / PDF / DOCX reports."""
    text = ""

    # TXT or CSV
    if file.name.lower().endswith((".txt", ".csv")):
        # Reset file pointer to beginning in case it was read before
        if hasattr(file, 'seek'):
            file.seek(0)
        text = file.read().decode("utf-8", errors="ignore")
        # Reset again after reading
        if hasattr(file, 'seek'):
            file.seek(0)
        
        # Check if it's CSV/Excel format (has headers and comma/tab separated)
        import csv
        import io
        if ',' in text or '\t' in text:
            # Try to parse as CSV
            try:
                file.seek(0)
                csv_text = file.read().decode("utf-8", errors="ignore")
                file.seek(0)
                csv_reader = csv.DictReader(io.StringIO(csv_text))
                rows = list(csv_reader)
                if rows:
                    # Use the first row of data
                    row = rows[0]
                    print(f"[INFO] Detected CSV/Excel format. Columns: {list(row.keys())}")
                    
                    # Map column names (handle variations and case)
                    extracted_csv = {}
                    for key, value in row.items():
                        key_lower = key.lower().strip()
                        try:
                            val = float(value) if value else 0
                        except (ValueError, TypeError):
                            continue
                            
                        # Map various column name formats
                        if 'age' in key_lower:
                            extracted_csv["age"] = val
                        elif 'systolic' in key_lower or 'sbp' in key_lower:
                            extracted_csv["systolic_bp"] = val
                        elif 'diastolic' in key_lower or 'dbp' in key_lower or 'diastolicbi' in key_lower:
                            extracted_csv["diastolic_bp"] = val
                        elif key_lower in ['bs', 'blood sugar', 'glucose', 'bloodsugar']:
                            # Check if value is in mmol/L (typically 4-25) vs mg/dL (typically 70-500)
                            if val < 30:  # Likely mmol/L, convert to mg/dL
                                val = val * 18.0182  # Convert mmol/L to mg/dL
                                print(f"[INFO] Converted BS from {row[key]} mmol/L to {val:.1f} mg/dL")
                            extracted_csv["bs"] = val
                        elif 'heart' in key_lower and 'rate' in key_lower or 'hr' in key_lower or 'pulse' in key_lower:
                            extracted_csv["heart_rate"] = val
                        elif 'temp' in key_lower or 'temperature' in key_lower or 'bodytemp' in key_lower:
                            extracted_csv["body_temp"] = val
                    
                    if extracted_csv:
                        print(f"[INFO] Extracted from CSV: {extracted_csv}")
                        return extracted_csv
            except Exception as e:
                print(f"[WARNING] CSV parsing failed, falling back to text extraction: {e}")
                # Fall back to text extraction
                pass

    # PDF
    elif file.name.lower().endswith(".pdf"):
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

    # DOCX
    elif file.name.lower().endswith(".docx"):
        doc = Document(file)
        text = "\n".join([p.text for p in doc.paragraphs])

    # Unsupported DOC
    else:
        return None

    # Value extractor using regex - try multiple patterns for each value
    def extract(pattern, default=0, patterns=None):
        if patterns:
            # Try multiple patterns
            for pat in patterns:
                match = re.search(pat, text, re.IGNORECASE)
                if match:
                    try:
                        return float(match.group(1))
                    except (ValueError, IndexError):
                        continue
        else:
            # Single pattern
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except (ValueError, IndexError):
                    pass
        return default

    extracted = {
        # Age - try multiple formats
        "age": extract(None, 0, [
            r"Age[:= ]+(\d+)",
            r"Age\s+is\s+(\d+)",
            r"(\d+)\s+years?\s+old",
            r"Age\s*:?\s*(\d+)",
        ]),
        # Systolic BP - try multiple formats including combined BP format
        "systolic_bp": extract(None, 0, [
            r"Systolic[:= ]+(\d+)",
            r"Systolic\s+BP[:= ]+(\d+)",
            r"SBP[:= ]+(\d+)",
            r"Systolic\s*:?\s*(\d+)",
            r"BP[:= ]+(\d+)[/ ]+(\d+)",  # BP: 120/80 - capture first number
            r"Blood\s+Pressure[:= ]+(\d+)[/ ]+(\d+)",  # Blood Pressure: 120/80
            r"(\d+)[/ ]+(\d+)\s*mmHg",  # 120/80 mmHg
        ]),
        # Diastolic BP - try multiple formats including combined BP format
        "diastolic_bp": extract(None, 0, [
            r"Diastolic[:= ]+(\d+)",
            r"Diastolic\s+BP[:= ]+(\d+)",
            r"DBP[:= ]+(\d+)",
            r"Diastolic\s*:?\s*(\d+)",
            r"BP[:= ]+\d+[/ ]+(\d+)",  # BP: 120/80 - capture second number
            r"Blood\s+Pressure[:= ]+\d+[/ ]+(\d+)",  # Blood Pressure: 120/80
            r"\d+[/ ]+(\d+)\s*mmHg",  # 120/80 mmHg
        ]),
        # Blood Sugar - try multiple formats
        "bs": extract(None, 0, [
            r"Blood.?Sugar[:= ]+(\d+\.?\d*)",
            r"BS[:= ]+(\d+\.?\d*)",
            r"Glucose[:= ]+(\d+\.?\d*)",
            r"Blood\s+Sugar\s*:?\s*(\d+\.?\d*)",
            r"BS\s*:?\s*(\d+\.?\d*)",
            r"Fasting\s+Glucose[:= ]+(\d+\.?\d*)",
            r"Random\s+Glucose[:= ]+(\d+\.?\d*)",
        ]),
        # Heart Rate - try multiple formats
        "heart_rate": extract(None, 0, [
            r"(?:Heart.?Rate|Pulse|HR)[:= ]+(\d+)",
            r"Heart\s+Rate[:= ]+(\d+)",
            r"Pulse[:= ]+(\d+)",
            r"HR[:= ]+(\d+)",
        ]),
        # Body Temperature - try multiple formats
        "body_temp": extract(None, 0, [
            r"(?:Temperature|Temp|Body\s+Temp)[:= ]+(\d+\.?\d*)",
            r"Temp[:= ]+(\d+\.?\d*)",
            r"Temperature[:= ]+(\d+\.?\d*)",
        ]),
    }

    # Debug: print extracted values and sample text
    import os
    print(f"[DEBUG] Sample text (first 500 chars): {text[:500]}")
    print(f"[DEBUG] Initial extracted values: {extracted}")
    
    # Post-processing: Fix common extraction issues and convert units
    
    # 0. Convert Blood Sugar from mmol/L to mg/dL if needed (Excel/CSV format often uses mmol/L)
    bs_value = extracted.get("bs", 0)
    if bs_value > 0 and bs_value < 30:  # Likely in mmol/L (range 4-25), convert to mg/dL
        # Formula: mg/dL = mmol/L × 18.0182
        # Example: 15 mmol/L = 270.27 mg/dL (high risk!)
        bs_mgdl = bs_value * 18.0182
        print(f"[INFO] Converted BS from {bs_value} mmol/L to {bs_mgdl:.1f} mg/dL")
        extracted["bs"] = bs_mgdl
    
    # 1. Check for BP in "120/80" format (most common)
    if extracted.get("systolic_bp", 0) == 0 or extracted.get("diastolic_bp", 0) == 0:
        print(f"[INFO] BP values missing or incomplete. Searching for combined BP format...")
        bp_patterns = [
            r"BP[:= ]+(\d+)[/ ]+(\d+)",  # BP: 120/80
            r"Blood\s+Pressure[:= ]+(\d+)[/ ]+(\d+)",  # Blood Pressure: 120/80
            r"(\d+)[/ ]+(\d+)\s*mmHg",  # 120/80 mmHg
            r"(\d+)\s*/\s*(\d+)\s*BP",  # 120 / 80 BP
        ]
        for pattern in bp_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    sys_val = float(match.group(1))
                    dia_val = float(match.group(2))
                    # Validate reasonable BP values (typically 90-200 for systolic, 50-120 for diastolic)
                    if 80 <= sys_val <= 250 and 40 <= dia_val <= 150:
                        print(f"[INFO] Found BP in format '{match.group(0)}': SBP={sys_val}, DBP={dia_val}")
                        extracted["systolic_bp"] = sys_val
                        extracted["diastolic_bp"] = dia_val
                        break
                except (ValueError, IndexError):
                    continue
    
    # 2. Validate and fix Blood Sugar (should be 70-300+ typically)
    if extracted.get("bs", 0) < 50:
        print(f"[WARNING] Blood Sugar value ({extracted.get('bs', 0)}) seems unusually low. Re-searching...")
        # Try alternative patterns that might have been missed
        bs_patterns = [
            r"Blood\s+Sugar[:= ]+(\d+\.?\d*)",
            r"Glucose[:= ]+(\d+\.?\d*)",
            r"BS[:= ]+(\d+\.?\d*)",
            r"Fasting\s+Glucose[:= ]+(\d+\.?\d*)",
            r"Random\s+Glucose[:= ]+(\d+\.?\d*)",
            r"Blood\s+Glucose[:= ]+(\d+\.?\d*)",
        ]
        for pattern in bs_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    bs_val = float(match.group(1))
                    # Only use if it's a reasonable value (50-500)
                    if 50 <= bs_val <= 500:
                        print(f"[INFO] Found better BS value: {bs_val} from pattern '{match.group(0)}'")
                        extracted["bs"] = bs_val
                        break
                except (ValueError, IndexError):
                    continue
            if extracted.get("bs", 0) >= 50:
                break
    
    # 3. Validate Body Temperature (should be 95-105°F typically)
    if extracted.get("body_temp", 0) < 90 or extracted.get("body_temp", 0) > 110:
        print(f"[WARNING] Body Temperature value ({extracted.get('body_temp', 0)}) seems unusual. Re-searching...")
        temp_patterns = [
            r"Temperature[:= ]+(\d+\.?\d*)",
            r"Temp[:= ]+(\d+\.?\d*)",
            r"Body\s+Temp[:= ]+(\d+\.?\d*)",
            r"(\d+\.?\d*)\s*°?\s*F",  # 98.6 F or 98.6°F
            r"(\d+\.?\d*)\s*°?\s*Fahrenheit",
        ]
        for pattern in temp_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    temp_val = float(match.group(1))
                    # Only use if it's a reasonable value (90-110°F)
                    if 90 <= temp_val <= 110:
                        print(f"[INFO] Found better Temp value: {temp_val} from pattern '{match.group(0)}'")
                        extracted["body_temp"] = temp_val
                        break
                except (ValueError, IndexError):
                    continue
            if 90 <= extracted.get("body_temp", 0) <= 110:
                break
    
    print(f"[DEBUG] Final extracted values after validation: {extracted}")

    return extracted


# ------------------------- MATERNAL HEALTH PREDICTION -------------------------
def predict_maternal_health(data):
    """Predict maternal health risk based on structured values."""
    if np is None:
        return {"success": False, "error": "NumPy not installed"}

    model = load_maternal_health_model()
    if model is None:
        return {"success": False, "error": "Maternal model missing"}

    try:
        # Get values with defaults
        age = data.get("age", 0)
        systolic_bp = data.get("systolic_bp", 0)
        diastolic_bp = data.get("diastolic_bp", 0)
        bs = data.get("bs", 0)
        heart_rate = data.get("heart_rate", 0)
        body_temp = data.get("body_temp", 98.6)  # Default to normal temp if missing
        
        # Log input values for debugging
        import os
        print(f"[DEBUG] ML Model Input - Age: {age}, SBP: {systolic_bp}, DBP: {diastolic_bp}, BS: {bs}, HR: {heart_rate}, Temp: {body_temp}")
        
        features = np.array([
            age,
            systolic_bp,
            diastolic_bp,
            bs,
            heart_rate,
            body_temp,
        ]).reshape(1, -1)

        # Get prediction probabilities
        proba_array = model.predict_proba(features)[0]
        proba_class_0 = float(proba_array[0])  # Probability of class 0
        proba_class_1 = float(proba_array[1])  # Probability of class 1
        
        # Log both probabilities for debugging
        print(f"[DEBUG] ML Model Probabilities - Class 0: {proba_class_0:.4f} ({proba_class_0*100:.2f}%), Class 1: {proba_class_1:.4f} ({proba_class_1*100:.2f}%)")
        
        # Determine which class represents high risk based on input values
        # High-risk indicators: SBP >= 140, DBP >= 90, BS >= 200, HR >= 100
        # Use stricter criteria to avoid false positives
        has_high_risk_values = (
            systolic_bp >= 140 or 
            diastolic_bp >= 90 or 
            bs >= 200 or 
            heart_rate >= 100
        )
        
        # Also check if values are clearly normal (to avoid false Medium Risk)
        has_normal_values = (
            systolic_bp > 0 and systolic_bp < 140 and
            diastolic_bp > 0 and diastolic_bp < 90 and
            bs > 0 and bs < 200 and
            heart_rate > 0 and heart_rate < 100
        )
        
        # Strategy: If high-risk values are present, use the HIGHER probability class
        # This handles cases where the model might be inverted (class 0 = high risk)
        if has_high_risk_values:
            # With high-risk inputs, the high-risk class should have higher probability
            if proba_class_0 > proba_class_1:
                proba = proba_class_0
                print(f"[INFO] High-risk values detected. Using Class 0 ({proba:.4f}) - appears to be high-risk class.")
            else:
                proba = proba_class_1
                print(f"[INFO] High-risk values detected. Using Class 1 ({proba:.4f}) - appears to be high-risk class.")
        else:
            # For normal values, use class 1 (assuming standard: class 0 = low, class 1 = high)
            # But if class 0 is higher, it might be the high-risk class
            proba = max(proba_class_0, proba_class_1)
            if proba == proba_class_0:
                print(f"[INFO] Using Class 0 ({proba:.4f}) - higher probability.")
            else:
                print(f"[INFO] Using Class 1 ({proba:.4f}) - higher probability.")
        
        # Use adjusted thresholds if high-risk values are present
        risk = _interpret_maternal_health_risk(proba, has_high_risk_values=has_high_risk_values)
        
        # Additional upgrade: If high-risk values are very severe, upgrade risk level
        # BUT: Don't upgrade if values are clearly normal
        if has_high_risk_values:
            severe_indicators = 0
            if systolic_bp >= 160: severe_indicators += 1
            if diastolic_bp >= 100: severe_indicators += 1
            if bs >= 250: severe_indicators += 1
            if heart_rate >= 120: severe_indicators += 1
            
            # If multiple severe indicators, upgrade to High Risk
            if severe_indicators >= 2 and risk != "High Risk":
                print(f"[INFO] Multiple severe indicators ({severe_indicators}) detected. Upgrading risk to High Risk.")
                risk = "High Risk"
            elif severe_indicators >= 1 and risk == "Low Risk":
                print(f"[INFO] Severe indicator detected. Upgrading risk to Medium Risk.")
                risk = "Medium Risk"
            elif risk == "Medium Risk" and (systolic_bp >= 160 or diastolic_bp >= 100 or bs >= 250):
                print(f"[INFO] Severe high-risk values detected. Upgrading Medium Risk to High Risk.")
                risk = "High Risk"
        elif has_normal_values and risk == "Medium Risk":
            # If values are clearly normal but model says Medium Risk, downgrade to Low Risk
            # This prevents false Medium Risk when values are actually normal
            print(f"[INFO] Normal values detected but model predicted Medium Risk. Downgrading to Low Risk.")
            print(f"[INFO] Values: SBP={systolic_bp}, DBP={diastolic_bp}, BS={bs}, HR={heart_rate}")
            risk = "Low Risk"
        
        # Log prediction for debugging
        print(f"[DEBUG] ML Model Output - Final Probability: {proba:.4f} ({proba*100:.2f}%), Risk Level: {risk}")
        
        # Final validation: if high-risk values but low risk output, force re-evaluation
        if has_high_risk_values and risk == "Low Risk" and proba < 0.50:
            # Try the other class
            proba_alt = proba_class_0 if proba == proba_class_1 else proba_class_1
            print(f"[WARNING] High-risk values but Low Risk output. Trying alternative class: {proba_alt:.4f}")
            if proba_alt > proba:
                proba = proba_alt
                # Use adjusted thresholds if high-risk values are present
                risk = _interpret_maternal_health_risk(proba, has_high_risk_values=has_high_risk_values)
                print(f"[INFO] Corrected - Using probability: {proba:.4f}, Risk Level: {risk}")
            else:
                print(f"[WARNING] High-risk values (SBP: {systolic_bp}, DBP: {diastolic_bp}, BS: {bs}, HR: {heart_rate}) but model predicts Low Risk. Model may need retraining or threshold adjustment.")

        return {
            "success": True,
            "prediction_proba": proba,  # Use this key for consistency with views
            "probability": proba,  # Also include for backward compatibility
            "risk_level": risk,
            "prediction": f"Maternal health risk: {risk} (Probability: {proba:.2%})",
        }

    except Exception as e:
        logger.error(f"Maternal prediction error: {str(e)}")
        return {"success": False, "error": str(e)}


# ------------------------- PRETERM DELIVERY PREDICTION -------------------------
def predict_preterm_delivery(data):
    """Predict preterm delivery using ultrasound image."""
    if np is None:
        return {"success": False, "error": "NumPy not installed"}

    model = load_preterm_delivery_model()
    if model is None:
        return {"success": False, "error": "Preterm model missing"}

    try:
        from PIL import Image
        import io

        if "image_file" in data:
            img = Image.open(data["image_file"])
        elif "image_data" in data:
            import base64
            img_bytes = base64.b64decode(data["image_data"])
            img = Image.open(io.BytesIO(img_bytes))
        else:
            return {"success": False, "error": "Image is required"}

        img = img.convert("RGB").resize((224, 224))
        img_array = np.expand_dims(np.array(img) / 255.0, axis=0)

        prediction = model.predict(img_array, verbose=0)
        probability = float(prediction[0][0])
        probability = max(0.0, min(1.0, probability))
        risk = _interpret_preterm_risk(probability)

        return {
            "success": True,
            "probability": probability,
            "risk_level": risk,
            "prediction": f"Preterm delivery risk: {risk}",
        }

    except Exception as e:
        logger.error(f"Preterm prediction error: {str(e)}")
        return {"success": False, "error": str(e)}


# ------------------------- RISK INTERPRETATION THRESHOLDS -------------------------
def _interpret_maternal_health_risk(p, has_high_risk_values=False):
    """
    Interpret maternal health risk from probability.
    If high-risk values are present, use lower thresholds.
    For normal values, use stricter thresholds to avoid false Medium Risk.
    """
    if has_high_risk_values:
        # With high-risk values present, use more sensitive thresholds
        if p >= 0.60: return "High Risk"  # Lowered from 0.80
        if p >= 0.35: return "Medium Risk"  # Lowered from 0.50
        return "Low Risk"
    else:
        # Standard thresholds for normal values - stricter to avoid false positives
        if p >= 0.80: return "High Risk"
        if p >= 0.60: return "Medium Risk"  # Raised from 0.50 to avoid false Medium Risk
        return "Low Risk"


def _interpret_preterm_risk(p):
    if p >= 0.70: return "High Risk"
    if p >= 0.40: return "Medium Risk"
    return "Low Risk"


#OLD CODE
# """
# ML Service module for loading and using maternal health & preterm delivery models.
# """
# import os
# from django.conf import settings
# import logging

# try:
#     import numpy as np
# except ImportError:
#     np = None
#     logging.warning("NumPy is not installed. ML predictions will not work.")

# logger = logging.getLogger(__name__)

# # Lazy-loaded model instances
# _maternal_health_model = None
# _preterm_delivery_model = None


# # ------------------------- MODEL LOADING UTILS -------------------------
# def get_model_path(filename):
#     return os.path.join(settings.BASE_DIR, 'feetal_app', 'ml_models', filename)


# def load_maternal_health_model():
#     """Load the maternal health ML model"""
#     global _maternal_health_model
#     if _maternal_health_model is None:
#         try:
#             import joblib
#             model_path = get_model_path('model_maternal_health_v2.pkl')
#             _maternal_health_model = joblib.load(model_path)
#             logger.info("Maternal health model loaded")
#         except Exception as e:
#             logger.error(f"Maternal model load error: {str(e)}")
#             _maternal_health_model = None
#     return _maternal_health_model


# def load_preterm_delivery_model():
#     """Load preterm delivery CNN model"""
#     global _preterm_delivery_model
#     if _preterm_delivery_model is None:
#         try:
#             from tensorflow import keras
#             model_path = get_model_path('preterm_delivery_cnn.h5')
#             _preterm_delivery_model = keras.models.load_model(model_path)
#             logger.info("Preterm delivery CNN loaded")
#         except Exception as e:
#             logger.error(f"Preterm model load error: {str(e)}")
#             _preterm_delivery_model = None
#     return _preterm_delivery_model


# # ------------------------- PREDICT MATERNAL HEALTH -------------------------
# def predict_maternal_health(data):
#     """
#     Predict maternal health risk based on structured medical values.
#     data must include: age, systolic_bp, diastolic_bp, bs, heart_rate, body_temp
#     """
#     if np is None:
#         return {'success': False, 'error': 'NumPy not installed'}

#     model = load_maternal_health_model()
#     if model is None:
#         return {'success': False, 'error': 'Maternal health model missing'}

#     try:
#         features = np.array([
#             data.get('age', 0),
#             data.get('systolic_bp', 0),
#             data.get('diastolic_bp', 0),
#             data.get('bs', 0),
#             data.get('heart_rate', 0),
#             data.get('body_temp', 0),
#         ]).reshape(1, -1)

#         # Extract probability of "Risk class"
#         proba = model.predict_proba(features)[0][1]  # probability of high risk
#         proba = float(proba)  # ensure JSON convertible
#         risk_level = _interpret_maternal_health_risk(proba)

#         return {
#             'success': True,
#             'prediction': f"Maternal health risk: {risk_level}",
#             'prediction_proba': proba,
#             'risk_level': risk_level
#         }

#     except Exception as e:
#         logger.error(f"Maternal prediction error: {str(e)}")
#         return {'success': False, 'error': str(e)}


# # ------------------------- PREDICT PRETERM DELIVERY -------------------------
# def predict_preterm_delivery(data):
#     """
#     Predict preterm delivery using ultrasound image.
#     data must include `image_file` or `image_data`
#     """
#     if np is None:
#         return {'success': False, 'error': 'NumPy not installed'}

#     model = load_preterm_delivery_model()
#     if model is None:
#         return {'success': False, 'error': 'Preterm model missing'}

#     try:
#         from PIL import Image
#         import io

#         # Load image
#         if 'image_file' in data:
#             img = Image.open(data['image_file'])
#         elif 'image_data' in data:
#             import base64
#             img_bytes = base64.b64decode(data['image_data'])
#             img = Image.open(io.BytesIO(img_bytes))
#         else:
#             return {'success': False, 'error': 'Image is required'}

#         img = img.convert('RGB').resize((224, 224))
#         img_array = np.expand_dims(np.array(img) / 255.0, axis=0)

#         prediction = model.predict(img_array, verbose=0)
#         probability = float(prediction[0][0])
#         probability = max(0.0, min(1.0, probability))
#         risk_level = _interpret_preterm_risk(probability)

#         return {
#             'success': True,
#             'probability': probability,
#             'risk_level': risk_level,
#             'prediction': f"Preterm delivery risk: {risk_level}",
#         }

#     except Exception as e:
#         logger.error(f"Preterm prediction error: {str(e)}")
#         return {'success': False, 'error': str(e)}


# # ------------------------- RISK INTERPRETATION -------------------------
# def _interpret_maternal_health_risk(probability):
#     """Convert probability → human readable risk (improved thresholding)"""
#     if probability >= 0.80:
#         return "High Risk"
#     elif probability >= 0.50:
#         return "Medium Risk"
#     else:
#         return "Low Risk"


# def _interpret_preterm_risk(probability):
#     """Convert probability → risk"""
#     if probability >= 0.70:
#         return "High Risk"
#     elif probability >= 0.40:
#         return "Medium Risk"
#     else:
#         return "Low Risk"
