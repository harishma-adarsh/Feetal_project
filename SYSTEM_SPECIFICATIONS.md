# 3. SYSTEM SPECIFICATIONS

## 3.1 HARDWARE SPECIFICATION

| Component | Minimum Requirement |
| :--- | :--- |
| **Processor** | Intel Core i3 or above |
| **System Bus** | 32-bit or 64-bit |
| **RAM** | 4 GB or above |
| **HDD / SSD** | 500 GB or above |
| **Monitor** | 14" LCD or above |
| **Keyboard** | 108 Keys |
| **Mouse** | Any Optical Mouse |

---

## 3.2 SOFTWARE SPECIFICATION

| Component | Specification |
| :--- | :--- |
| **Operating System** | Windows 10 / 11 (64-bit) |
| **Front End** | HTML5, CSS3, JavaScript (Django Templates) |
| **Back End** | Python (Django Framework) |
| **Database** | SQLite / MySQL Server |
| **AI / ML Library** | TensorFlow, Keras, Scikit-learn |
| **IDE** | Visual Studio Code / PyCharm |
| **Python Version** | 3.10 or above |

---

> [!NOTE]
> This specification is tailored for the **Feetal (FetoScope)** project, ensuring optimal performance for running machine learning models and processing medical reports.

---

## 3.3 DATABASE DESIGN (TABLES)

The following tables represent the core data structure of the **Feetal** system.

### 3.3.1 USER PROFILE TABLES

| Table Name | Columns | Description |
| :--- | :--- | :--- |
| **Patient** | `user_id` (FK), `phone`, `created_at`, `updated_at` | Stores detailed patient registration information. |
| **Doctor** | `user_id` (FK), `phone`, `specialization`, `created_at`, `updated_at` | Stores professional details of registered doctors. |

### 3.3.2 APPOINTMENT & SCHEDULE TABLES

| Table Name | Columns | Description |
| :--- | :--- | :--- |
| **Appointment** | `patient_id` (FK), `doctor_id` (FK), `patient_name`, `patient_email`, `patient_phone`, `patient_age`, `appointment_date`, `appointment_time`, `reason`, `notes`, `status` | Manages appointments between patients and doctors. |
| **DoctorSchedule**| `doctor_id` (FK), `day`, `start_time`, `end_time` | Manages availability slots for doctors. |

### 3.3.3 ANALYSIS & REPORT TABLES

| Table Name | Columns | Description |
| :--- | :--- | :--- |
| **AnalysisReport** | `patient_name`, `patient_email`, `combined_risk_level`, `pdf` (File), `created_at` | Stores generated PDF reports for patient analysis. |
| **MLReport** | `patient_name`, `analysis_type`, `risk_level`, `confidence`, `findings`, `created_at` | Stores metadata and results of machine learning predictions. |

### 3.3.4 ENTITY RELATIONSHIP DIAGRAM (ERD)

```mermaid
erDiagram
    USER ||--|| Patient : "has profile"
    USER ||--|| Doctor : "has profile"
    Patient ||--o{ Appointment : "books"
    Doctor ||--o{ Appointment : "attends"
    Doctor ||--o{ DoctorSchedule : "manages"

    Patient {
        ForeignKey user_id
        String phone
        DateTime created_at
    }

    Doctor {
        ForeignKey user_id
        String phone
        String specialization
        DateTime created_at
    }

    Appointment {
        ForeignKey patient_id
        ForeignKey doctor_id
        String patient_name
        Date appointment_date
        Time appointment_time
        String status
    }

    DoctorSchedule {
        ForeignKey doctor_id
        String day
        Time start_time
        Time end_time
    }

    AnalysisReport {
        String patient_name
        String risk_level
        File pdf
        DateTime created_at
    }

    MLReport {
        String patient_name
        String risk_level
        Int confidence
        DateTime created_at
    }
```

![Entity Relationship Diagram (ERD)](file:///C:/Users/haris/.gemini/antigravity/brain/848e4473-9ab1-419a-9c48-f6d96631eddc/feetal_erd_diagram_1772610065570.png)

---

## 3.4 DATA FLOW DIAGRAM (DFD)

The following diagrams illustrate the movement of data through the Feetal (FetoScope) system, from user input to AI-driven analysis and report generation.

### 3.4.1 LEVEL 0 DFD (CONTEXT DIAGRAM)
The Context Diagram shows the system boundary and its interactions with external entities.

```mermaid
graph LR
    %% External Entities
    P[Patient]
    D[Doctor]
    A[Admin]

    %% Main System Process
    S((FEETAL SYSTEM))

    %% Data Flows
    P -- "Personal Info, Health Metrics (BP, Heart Rate, BS)" --> S
    P -- "Pregnancy History (Gestational Age, Previous Preterm)" --> S
    S -- "Appointment Notifications" --> P

    D -- "Consultation Availability, Doctor Profile" --> S
    S -- "Patient Risk Analytics, Appointment Schedule" --> D
    S -- "PDF Analysis Reports" --> D

    A -- "User Credentials, System Config" --> S
    S -- "User Activity Logs, System Analytics" --> A
```

![Level 0 DFD](file:///C:/Users/haris/.gemini/antigravity/brain/848e4473-9ab1-419a-9c48-f6d96631eddc/feetal_dfd_level_0_v4_final_1772611061810.png)

### 3.4.2 LEVEL 1 DFD
The Level 1 DFD decomposes the system into functional processes and identifies data stores.

```mermaid
graph TD
    %% External Entities
    Patient((Patient))
    Doctor((Doctor))

    %% Processes
    P1[1.0 User Management & Auth]
    P2[2.0 Health Data Processing]
    P3[3.0 Risk Prediction Engine]
    P4[4.0 Appointment Management]
    P5[5.0 Report & Analytics Generation]

    %% Data Stores
    D1[(User Profiles DB)]
    D2[(Medical Records DB)]
    D3[(Appointment & Schedule DB)]
    D4[(ML Prediction Cache)]

    %% Logic Flows for Process 1.0
    Patient -- "Registration/Login Data" --> P1
    Doctor -- "Login Credentials" --> P1
    P1 <--> D1
    P1 -- "User Context" --> P2

    %% Logic Flows for Process 2.0
    Patient -- "Input Vitals (BP, BS, BMI)" --> P2
    P2 -- "Formatted Medical Data" --> D2
    P2 -- "Raw Features" --> P3

    %% Logic Flows for Process 3.0
    P3 -- "Invoke Maternal Health model" --> D4
    P3 -- "Invoke Preterm model" --> D4
    D4 -- "Prediction Results" --> P5

    %% Logic Flows for Process 4.0
    Patient -- "Book Appointment" --> P4
    Doctor -- "Set Availability" --> P4
    P4 <--> D3
    P4 -- "Status Alerts" --> Patient

    %% Logic Flows for Process 5.0
    D2 -- "Retrieve History" --> P5
    P5 -- "Export PDF Report" --> Doctor
    P5 -- "Patient Statistics" --> Doctor
```

![Level 1 DFD](file:///C:/Users/haris/.gemini/antigravity/brain/848e4473-9ab1-419a-9c48-f6d96631eddc/feetal_dfd_level_1_v2_1772610419896.png)

---

### 3.4.3 STEP-BY-STEP DATA FLOW PROCESS

The following steps define the complete operational flow of data within the Feetal system:

1.  **Stage 1: User Onboarding**
    *   **Patient/Doctor** provides registration details to **Process 1.0**.
    *   Data is validated and stored in **D1 (User Profiles DB)**.

2.  **Stage 2: Health Data Collection**
    *   **Patient** enters vitals (BP, Heart Rate, BS) and pregnancy history (Gestational Age, BMI) via the portal.
    *   **Process 2.0** normalizes this data and stores it in **D2 (Medical Records DB)**.

3.  **Stage 3: AI Inference & Analysis**
    *   **Process 3.0** retrieves raw features from Process 2.0.
    *   The system invokes the **Maternal Health** and **Preterm Delivery** ML models.
    *   Predictions and confidence scores are cached in **D4 (ML Prediction Cache)**.

4.  **Stage 4: Communication & Alerting**
    *   **Process 4.0** checks for appointment availability in **D3**.
    *   System sends an **Appointment Notification** (SMS/Email/In-app) to the **Patient**.
    *   *Note: No risk data is included in this user-facing notification.*

5.  **Stage 5: Report Synthesis (Doctor-Only)**
    *   **Process 5.0** aggregates patient medical history from **D2** and ML results from **D4**.
    *   A comprehensive **PDF Analysis Report** is generated.

6.  **Stage 6: Clinical Delivery**
    *   The **PDF Report** and visualized **Risk Statistics** are transmitted to the **Doctor's Dashboard**.
    *   Doctor reviews the findings for clinical consultation.

---

### 3.4.4 STEP-BY-STEP SEQUENCE DIAGRAM

The following sequence diagram provides a detailed, step-by-step visualization of how data interacts between entities, processes, and data stores throughout the entire system lifecycle.

```mermaid
sequenceDiagram
    autonumber
    actor P as Patient
    participant S as Feetal System (AI)
    participant DB as System Database
    actor D as Doctor

    Note over P, D: Stage 1: Onboarding
    P->>S: Submit Registration Details
    S->>DB: Store User Profile (D1)
    
    Note over P, D: Stage 2: Data Collection
    P->>S: Input Vitals & Pregnancy History
    S->>DB: Store Medical Records (D2)
    
    Note over P, D: Stage 3: AI Analysis
    S->>S: Process Risk Models (Maternal & Preterm)
    S->>DB: Cache Prediction Results (D4)
    
    Note over P, D: Stage 4: Patient Notification
    DB->>S: Trigger Appointment Status
    S->>P: Send Appointment Notification (ONLY)
    
    Note over P, D: Stage 5 & 6: Clinical Delivery
    DB->>S: Aggregate History (D2) & Predictions (D4)
    S->>S: Generate PDF Report
    S->>D: Transmit PDF Report & Risk Statistics
    D->>D: Review Findings for Consultation
```

---
