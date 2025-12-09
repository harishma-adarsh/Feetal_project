from django.urls import path

from . import views

app_name = 'feetal_app'

urlpatterns = [
    path('', views.index, name='index'),
    path('patient/register/', views.patient_register, name='patient_register'),
    path('patient/login/', views.patient_login, name='patient_login'),
    # path('api/doctor/register/', views.doctor_register, name='doctor_register'),
    path('patient-portal/', views.patient_portal, name='patient_portal'),
    path('patient-dashboard/', views.patient_portal),
    path('patient-portal.html', views.patient_portal),
    path('dashboard/login/', views.dashboard_login, name='dashboard_login'),
    path('dashboard/login.html', views.dashboard_login),
    path('dashboard/doctor/', views.dashboard_doctor, name='dashboard_doctor'),
    path('dashboard/doctor-dashboard.html', views.dashboard_doctor),
    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),
    path('dashboard/admin-dashboard.html', views.dashboard_admin),
    path('dashboard/admin/add-doctor/', views.admin_add_doctor, name='admin_add_doctor'),
    path('dashboard/admin/users/<int:user_id>/edit/', views.admin_user_edit, name='admin_user_edit'),
    path('dashboard/admin/users/<int:user_id>/delete/', views.admin_user_delete, name='admin_user_delete'),
    path('dashboard/admin/doctors/<int:doctor_id>/edit/', views.admin_doctor_edit, name='admin_doctor_edit'),
    path('dashboard/admin/doctors/<int:doctor_id>/toggle-active/', views.admin_doctor_toggle_active, name='admin_doctor_toggle_active'),
    path('dashboard/admin/doctors/<int:doctor_id>/schedule/', views.admin_doctor_schedule, name='admin_doctor_schedule'),
    path('dashboard/admin/patients/<int:patient_id>/view/', views.admin_patient_view, name='admin_patient_view'),
    path('dashboard/admin/patients/<int:patient_id>/delete/', views.admin_patient_delete, name='admin_patient_delete'),
    path('api/doctors/', views.get_doctors, name='get_doctors'),
    path('api/appointments/book/', views.book_appointment, name='book_appointment'),
    path('api/appointments/<int:appointment_id>/update-status/', views.admin_update_appointment_status, name='admin_update_appointment_status'),
    path('api/predict/maternal-health/', views.predict_maternal_health_api, name='predict_maternal_health'),
    path('api/predict/preterm-delivery/', views.predict_preterm_delivery_api, name='predict_preterm_delivery'),
    path("api/predict/combined-analysis/", views.combined_analysis_api, name="combined_analysis_api"),
    path("api/save-combined-report/", views.save_combined_report, name="save_combined_report"),

    path('dashboard/admin/reports/', views.admin_reports, name='admin_reports'),
    path('dashboard/admin/reports/download/<int:report_id>/', views.download_report, name='download_report'),
    path('reports/download/<int:report_id>/', views.download_report, name='download_analysis_report'),


    path('patient/appointments/', views.patient_appointments, name='patient_appointments'),
    path('doctor/appointments/', views.doctor_appointments, name='doctor_appointments'),
    path('logout/', views.user_logout, name='user_logout'),
    
    # Forgot Password URLs
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('forgot-password/done/', views.forgot_password_done, name='forgot_password_done'),
    path('reset-password/<uidb64>/<token>/', views.reset_password_confirm, name='reset_password_confirm'),

]