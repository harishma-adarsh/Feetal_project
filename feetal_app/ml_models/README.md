# ML Models Directory

Place your machine learning model files here:

1. **model_maternal_health_v2.pkl** - Maternal health prediction model
2. **preterm_delivery_cnn.h5** - Preterm delivery prediction CNN model

## Setup Instructions

1. Copy your model files to this directory:
   ```
   maternity/feetal_app/ml_models/model_maternal_health_v2.pkl
   maternity/feetal_app/ml_models/preterm_delivery_cnn.h5
   ```

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. The models will be automatically loaded when first used.

## Model Input Requirements

### Maternal Health Model (model_maternal_health_v2.pkl)
Expected input fields:
- `age`: Patient age (integer)
- `systolic_bp`: Systolic blood pressure (integer)
- `diastolic_bp`: Diastolic blood pressure (integer)
- `bs`: Blood sugar level (float)
- `heart_rate`: Heart rate (integer)
- `body_temp`: Body temperature (float, optional)

### Preterm Delivery CNN Model (preterm_delivery_cnn.h5)
Expected input fields:
- `gestational_age`: Gestational age in weeks (integer)
- `maternal_age`: Maternal age (integer)
- `bmi`: Body Mass Index (float, optional)
- `previous_preterm`: Previous preterm delivery (0 or 1, optional)

**Note:** Adjust the input fields in `ml_service.py` based on your actual model requirements.

