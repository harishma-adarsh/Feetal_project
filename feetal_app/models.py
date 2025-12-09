from django.db import models
from django.contrib.auth.models import User


class Patient(models.Model):
    """Patient model to store user registration data."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    phone = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Patient"
        verbose_name_plural = "Patients"

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.user.email})"


class Doctor(models.Model):
    """Doctor model to store doctor registration data."""
    SPECIALIZATION_CHOICES = [
    ('obgyn', 'Obstetrics & Gynecology'),
    ('mfm', 'Maternal-Fetal Medicine'),
    ('radiology', 'Radiology'),
    ('pediatrics', 'Pediatrics'),
    ('prenatal_counselling', 'Prenatal Counselling'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    phone = models.CharField(max_length=20)
    specialization = models.CharField(max_length=50, choices=SPECIALIZATION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Doctor"
        verbose_name_plural = "Doctors"

    def __str__(self):
        return f"Dr. {self.user.get_full_name() or self.user.username} ({self.get_specialization_display()})"


class Appointment(models.Model):
    """Appointment model to store patient appointments with doctors."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    REASON_CHOICES = [
        ('routine-checkup', 'Routine Checkup'),
        ('prenatal-care', 'Prenatal Care'),
        ('ultrasound', 'Ultrasound Scan'),
        ('consultation', 'Medical Consultation'),
        ('follow-up', 'Follow-up Visit'),
        ('emergency', 'Emergency'),
        ('other', 'Other'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments', null=True, blank=True)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    
    # Patient information (for non-registered patients)
    patient_name = models.CharField(max_length=200)
    patient_email = models.EmailField()
    patient_phone = models.CharField(max_length=20)
    patient_age = models.IntegerField(null=True, blank=True)
    
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Appointment"
        verbose_name_plural = "Appointments"
        ordering = ['-appointment_date', '-appointment_time']

    def __str__(self):
        return f"{self.patient_name} - Dr. {self.doctor.user.get_full_name()} - {self.appointment_date} {self.appointment_time}"
    
class AnalysisReport(models.Model):
    patient_name = models.CharField(max_length=255)
    patient_email = models.EmailField(blank=True)
    combined_risk_level = models.CharField(max_length=50)
    pdf = models.FileField(upload_to="analysis_reports/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient_name} - {self.combined_risk_level} ({self.created_at.date()})"
from django.db import models

class MLReport(models.Model):
    patient_name = models.CharField(max_length=255)
    analysis_type = models.CharField(max_length=50)
    risk_level = models.CharField(max_length=20)
    confidence = models.IntegerField()
    findings = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient_name} - {self.analysis_type}"

class DoctorSchedule(models.Model):
    DAYS = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="schedule")
    day = models.CharField(max_length=20, choices=DAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        unique_together = ('doctor', 'day', 'start_time', 'end_time')
        ordering = ['day', 'start_time']

    def __str__(self):
        return f"{self.doctor.user.get_full_name() or self.doctor.user.username} - {self.day} {self.start_time}-{self.end_time}"
