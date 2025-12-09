from django.contrib import admin
from .models import Patient, Doctor, Appointment


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'phone')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'phone', 'created_at')
    list_filter = ('specialization', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'phone', 'specialization')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient_name', 'doctor', 'appointment_date', 'appointment_time', 'status', 'reason', 'created_at')
    list_filter = ('status', 'reason', 'appointment_date', 'created_at')
    search_fields = ('patient_name', 'patient_email', 'patient_phone', 'doctor__user__username', 'doctor__user__email')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'appointment_date'
