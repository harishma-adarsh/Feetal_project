from datetime import timedelta, date, time
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
import io
import json
import traceback
import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import JsonResponse, HttpResponse, Http404, FileResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_time
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.urls import reverse

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from .forms import (
    DoctorRegistrationForm,
    PatientRegistrationForm,
    AdminUserUpdateForm,
    DoctorAdminForm,
)
from .models import Doctor, Patient, Appointment, AnalysisReport, MLReport,DoctorSchedule
from .ml_service import (
    predict_maternal_health,
    predict_preterm_delivery,
    extract_medical_values,
)

from django.contrib.auth.models import User     # <-- ADD THIS
from .models import Doctor            


# ============================================================================
# Public / Auth
# ============================================================================

@ensure_csrf_cookie
def index(request):
    """Render the public landing page."""
    return render(request, "index.html")


@require_http_methods(["POST"])
def patient_login(request):
    try:
        data = json.loads(request.body)
        user = authenticate(request, username=data.get("email"), password=data.get("password"))

        if user:
            login(request, user)

            # 🔥 Fetch phone safely even if patient existed earlier
            phone = ""
            try:
                phone = user.patient_profile.phone
            except:
                pass

            return JsonResponse({
                "success": True,
                "message": f"Welcome back, {user.get_full_name() or user.email}!",
                "user": {
                    "name": user.get_full_name() or user.email,
                    "email": user.email,
                    "phone": phone,
                },
                "redirect_url": reverse("feetal_app:patient_portal"),
            })

        return JsonResponse({"success": False, "message": "Invalid email or password"}, status=401)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)



@require_http_methods(["POST"])
def patient_register(request):
    try:
        data = json.loads(request.body)
        form = PatientRegistrationForm({
            "name": data.get("name"),
            "email": data.get("email"),
            "phone": data.get("phone"),
            "password": data.get("password"),
        })

        if form.is_valid():
            user = form.save()

            # 🔥 ALWAYS create/update patient profile
            patient, created = Patient.objects.get_or_create(user=user)
            patient.phone = data.get("phone")
            patient.save()

            login(request, user)

            return JsonResponse({
                "success": True,
                "message": f"Account created successfully! Welcome, {user.get_full_name() or user.email}!",
                "user": {
                    "name": user.get_full_name() or user.email,
                    "email": user.email,
                    "phone": patient.phone,
                }
            })
        else:
            return JsonResponse({
                "success": False,
                "message": next(iter(form.errors.values()))[0]
            }, status=400)

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)




# @require_http_methods(["POST"])
# def doctor_register(request):
#     """Handle doctor registration via AJAX."""
#     try:
#         data = json.loads(request.body)
#         form = DoctorRegistrationForm(
#             {
#                 "name": data.get("name"),
#                 "email": data.get("email"),
#                 "phone": data.get("phone"),
#                 "specialization": data.get("specialization"),
#                 "password": data.get("password"),
#                 "password2": data.get("password2"),
#             }
#         )

#         if form.is_valid():
#             user = form.save()
#             # Verify doctor profile was created
#             try:
#                 user.doctor_profile
#                 login(request, user)
#                 return JsonResponse(
#                     {
#                         "success": True,
#                         "message": f'Doctor account created successfully! Welcome, Dr. {user.get_full_name() or user.email}!',
#                         "user": {
#                             "name": user.get_full_name() or user.email,
#                             "email": user.email,
#                             "type": "doctor",
#                         },
#                         "redirect_url": "/dashboard/doctor/",
#                     }
#                 )
#             except Doctor.DoesNotExist:
#                 # Doctor profile not created, delete user and return error
#                 user.delete()
#                 return JsonResponse(
#                     {
#                         "success": False,
#                         "message": "Failed to create doctor profile. Please try again.",
#                     },
#                     status=500,
#                 )
#         else:
#             errors = {}
#             for field, error_list in form.errors.items():
#                 errors[field] = error_list[0] if error_list else "Invalid input"
#             error_message = (
#                 "Registration failed: " + "; ".join(errors.values())
#                 if errors
#                 else "Registration failed"
#             )
#             return JsonResponse(
#                 {
#                     "success": False,
#                     "message": error_message,
#                     "errors": errors,
#                 },
#                 status=400,
#             )
#     except Exception as e:
#         error_msg = str(e)
#         if settings.DEBUG:
#             error_msg += f"\n{traceback.format_exc()}"
#         return JsonResponse(
#             {"success": False, "message": f"Registration error: {error_msg}"},
#             status=500,
#         )
# admin add doctor

@require_http_methods(["POST"])
@login_required
def admin_add_doctor(request):
    data = json.loads(request.body)

    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")
    specialization = data.get("specialization")
    password = data.get("password")

    if User.objects.filter(email=email).exists():
        return JsonResponse({"success": False, "message": "Email already exists"}, status=400)

    user = User.objects.create_user(
        username=email,
        email=email,
        password=password,
        first_name=name
    )
    user.is_staff = True   # doctor can login to dashboard
    user.save()

    Doctor.objects.create(
        user=user,
        phone=phone,
        specialization=specialization
    )

    return JsonResponse({"success": True, "message": "Doctor created successfully"})

@require_http_methods(["POST"])
@login_required
def admin_add_patient(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"})

    data = json.loads(request.body)
    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")
    password = data.get("password")

    if User.objects.filter(email=email).exists():
        return JsonResponse({"success": False, "message": "Email already registered"})

    user = User.objects.create_user(username=email, email=email, password=password, first_name=name)
    patient = Patient.objects.create(user=user, phone=phone)

    return JsonResponse({"success": True})
@require_http_methods(["POST"])
@login_required
@csrf_exempt
def admin_add_appointment(request):
    if request.method == "POST":
        data = json.loads(request.body)

        patient = Patient.objects.get(id=data["patient_id"])
        doctor = Doctor.objects.get(id=data["doctor_id"])

        Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            patient_name=patient.user.get_full_name(),
            patient_email=patient.user.email,
            patient_phone=patient.phone,
            appointment_date=data["date"],
            appointment_time=data["time"],
            reason=data["reason"],
            notes=data.get("notes", "")
        )

        return JsonResponse({"success": True})

    return JsonResponse({"success": False, "message": "Invalid request method"})

    
@login_required
def admin_doctor_schedule(request, doctor_id):
    if not request.user.is_superuser:
        messages.error(request, "Only the designated admin can view doctor schedules.")
        return redirect("feetal_app:index")

    doctor = Doctor.objects.get(id=doctor_id)

    # Days mapping MUST match template keys
    days = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
    schedule = {day: [] for day in days}

    slots = DoctorSchedule.objects.filter(doctor=doctor)
    for slot in slots:
        schedule[slot.day].append(slot)

    return render(request, "dashboard/admin_doctor_schedule.html", {
        "doctor": doctor,
        "schedule": schedule
    })

@csrf_exempt
@login_required
def admin_add_schedule_slot(request):
    if request.method != "POST":
        return JsonResponse({"success": False})

    data = json.loads(request.body)
    doctor_id = data["doctor_id"]
    day = data["day"]
    start_time = data["start"]
    end_time = data["end"]

    # Prevent duplicates
    if DoctorSchedule.objects.filter(doctor_id=doctor_id, day=day, start_time=start_time, end_time=end_time).exists():
        return JsonResponse({"success": False, "message": "Time slot already exists"})

    DoctorSchedule.objects.create(
        doctor_id=doctor_id, day=day,
        start_time=start_time, end_time=end_time
    )
    return JsonResponse({"success": True})


@csrf_exempt
@login_required
def admin_remove_schedule_slot(request):
    data = json.loads(request.body)
    DoctorSchedule.objects.filter(id=data["slot_id"]).delete()
    return JsonResponse({"success": True})
def patient_portal(request):
    """Authenticated portal shell (mock auth handled client-side for now)."""
    return render(request, "patient-portal.html")


def dashboard_login(request):
    """Staff (doctor/admin) login screen."""
    if request.method == "POST":
        identifier = request.POST.get("identifier")
        password = request.POST.get("password")
        role = request.POST.get("role")

        if not role:
            messages.error(
                request, "Please select whether you are logging in as Doctor or Admin."
            )
            return redirect("feetal_app:dashboard_login")

        if identifier and password:
            username = identifier.strip()
            User = get_user_model()
            # allow login via email
            if "@" in identifier:
                try:
                    username = User.objects.get(
                        email__iexact=identifier.strip()
                    ).username
                except User.DoesNotExist:
                    username = identifier.strip()

            user = authenticate(request, username=username, password=password)
            if user is not None:
                if role == "admin":
                    if user.is_superuser:
                        login(request, user)
                        messages.success(
                            request,
                            f'Welcome back, {user.get_full_name() or user.username}!',
                        )
                        return redirect("feetal_app:dashboard_admin")
                    else:
                        messages.error(
                            request,
                            "Admin access is restricted to the designated superuser.",
                        )
                        return redirect("feetal_app:dashboard_login")
                elif role == "doctor":
                    try:
                        user.doctor_profile
                        login(request, user)
                        messages.success(
                            request,
                            f'Welcome back, Dr. {user.get_full_name() or user.username}!',
                        )
                        return redirect("feetal_app:dashboard_doctor")
                    except Doctor.DoesNotExist:
                        messages.error(
                            request,
                            "Doctor access is restricted to registered doctor accounts.",
                        )
                        return redirect("feetal_app:dashboard_login")
                else:
                    messages.error(request, "Invalid role selection.")
                    return redirect("feetal_app:dashboard_login")
            else:
                messages.error(request, "Invalid email or password.")
        else:
            messages.error(request, "Please fill in all fields.")

    return render(request, "dashboard/login.html")


def user_logout(request):
    """Logout user and redirect to home."""
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect("feetal_app:index")


# ============================================================================
# Forgot / Reset Password
# ============================================================================

def forgot_password(request):
    """Forgot password email sender for patients (and any user by email)."""
    if request.method == "POST":
        email = request.POST.get("email")

        if not email:
            messages.error(request, "Please enter your email address.")
            return redirect("feetal_app:forgot_password")

        User = get_user_model()
        try:
            user = User.objects.get(email=email)

            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            reset_link = request.build_absolute_uri(
                reverse(
                    "feetal_app:reset_password_confirm",
                    kwargs={"uidb64": uid, "token": token},
                )
            )

            subject = "FetoScope AI - Password Reset Request"
            message = f"""Hello {user.get_full_name() or user.username},

You requested a password reset for your FetoScope AI account.

Click the link below to reset your password:
{reset_link}

This link will expire in 24 hours.

If you did not request this password reset, please ignore this email.

Best regards,
FetoScope AI Team
"""
            from_email = (
                settings.DEFAULT_FROM_EMAIL if hasattr(settings, "DEFAULT_FROM_EMAIL") else None
            ) or "noreply@fetoscope.ai"

            send_mail(subject, message, from_email, [email], fail_silently=False)

            messages.success(request, "Password reset link has been sent to your email.")
            return redirect("feetal_app:forgot_password_done")

        except User.DoesNotExist:
            messages.error(request, "No account found with this email address.")
            return redirect("feetal_app:forgot_password")

    return render(request, "forgot-password.html")


def forgot_password_done(request):
    """Password reset email sent confirmation page."""
    return render(request, "forgot-password-done.html")


def reset_password_confirm(request, uidb64, token):
    """Password reset confirmation page."""
    User = get_user_model()

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    # Token valid?
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            password = request.POST.get("password")
            password_confirm = request.POST.get("password_confirm")

            if not password or not password_confirm:
                messages.error(request, "Please fill in all fields.")
            elif password != password_confirm:
                messages.error(request, "Passwords do not match.")
            elif len(password) < 8:
                messages.error(
                    request, "Password must be at least 8 characters long."
                )
            else:
                user.set_password(password)
                user.save()
                messages.success(
                    request,
                    "Your password has been reset successfully. You can now login.",
                )
                return redirect("feetal_app:index")

        # GET request or POST with errors
        return render(request, "reset-password.html", {"valid": True})

    # Invalid or expired link
    messages.error(request, "Invalid or expired password reset link.")
    return render(request, "reset-password.html", {"valid": False})


# ============================================================================
# Doctor & Admin Dashboards
# ============================================================================

def dashboard_doctor(request):
    """Doctor dashboard screen."""
    if not request.user.is_authenticated:
        messages.warning(request, "Please log in to access the doctor dashboard.")
        return redirect("feetal_app:dashboard_login")

    try:
        doctor_profile = request.user.doctor_profile
    except Doctor.DoesNotExist:
        if request.user.is_superuser:
            return redirect("feetal_app:dashboard_admin")
        messages.warning(
            request, "Access denied. This dashboard is for doctors only."
        )
        return redirect("feetal_app:index")

    today = timezone.now().date()
    today_appointments = (
        Appointment.objects.filter(
            doctor=doctor_profile,
            appointment_date=today,
        )
        .exclude(status="cancelled")
        .order_by("appointment_time")
    )

    upcoming_appointments = (
        Appointment.objects.filter(
            doctor=doctor_profile,
            appointment_date__gte=today,
        )
        .exclude(status="cancelled")
        .order_by("appointment_date", "appointment_time")[:20]
    )

    total_appointments = Appointment.objects.filter(doctor=doctor_profile).count()
    pending_appointments = Appointment.objects.filter(
        doctor=doctor_profile, status="pending"
    ).count()

    recent_reports = AnalysisReport.objects.order_by("-created_at")[:10]
    total_patients = Patient.objects.count()

    unique_patients = (
        Appointment.objects.filter(doctor=doctor_profile)
        .values("patient_email")
        .distinct()
        .count()
    )

    completed_appointments = Appointment.objects.filter(
        doctor=doctor_profile, status="completed"
    ).count()

    from datetime import datetime
    current_month_start = datetime.now().replace(day=1).date()
    this_month_appointments = Appointment.objects.filter(
        doctor=doctor_profile, appointment_date__gte=current_month_start
    ).count()

    all_patients = Patient.objects.select_related("user").order_by("-created_at")[:20]

    all_appointments = (
        Appointment.objects.filter(doctor=doctor_profile)
        .exclude(status="cancelled")
        .order_by("-appointment_date", "-appointment_time")[:50]
    )

    context = {
        "doctor": doctor_profile,
        "user": request.user,
        "today": today,
        "today_appointments": today_appointments,
        "upcoming_appointments": upcoming_appointments,
        "all_appointments": all_appointments,
        "total_appointments": total_appointments,
        "pending_appointments": pending_appointments,
        "completed_appointments": completed_appointments,
        "this_month_appointments": this_month_appointments,
        "total_patients": total_patients,
        "unique_patients": unique_patients,
        "all_patients": all_patients,
        "recent_reports": recent_reports,
    }
    return render(request, "dashboard/doctor-dashboard.html", context)


def dashboard_admin(request):
    """Admin dashboard screen."""
    if not request.user.is_authenticated:
        messages.warning(request, "Please log in to access the admin dashboard.")
        return redirect("feetal_app:dashboard_login")

    if not request.user.is_superuser:
        messages.error(
            request, "Admin dashboard is restricted to the designated superuser."
        )
        return redirect("feetal_app:index")

    User = get_user_model()
    total_users = User.objects.count()
    doctor_count = Doctor.objects.count()
    patient_count = Patient.objects.count()
    week_start = timezone.now() - timedelta(days=7)
    new_users_week = User.objects.filter(date_joined__gte=week_start).count()

    recent_users_raw = User.objects.order_by("-date_joined")[:5]
    user_rows = []
    for user in recent_users_raw:
        if user.is_superuser:
            role = "Admin"
        elif hasattr(user, "doctor_profile"):
            role = "Doctor"
        elif hasattr(user, "patient_profile"):
            role = "Patient"
        else:
            role = "User"
        user_rows.append(
            {
                "id": user.pk,
                "name": user.get_full_name() or user.username,
                "email": user.email,
                "role": role,
                "status": "Active" if user.is_active else "Inactive",
                "status_class": "status-active"
                if user.is_active
                else "status-inactive",
                "last_login": user.last_login,
                "is_superuser": user.is_superuser,
            }
        )

    doctor_rows = [
        {
            "id": doc.pk,
            "name": doc.user.get_full_name() or doc.user.username,
            "specialization": doc.get_specialization_display(),
            "phone": doc.phone,
            "created_at": doc.created_at,
            "is_active": doc.user.is_active,
            "status_text": "Active" if doc.user.is_active else "Inactive",
            "status_class": "status-active"
            if doc.user.is_active
            else "status-inactive",
        }
        for doc in Doctor.objects.select_related("user").order_by("-created_at")[:5]
    ]

    patient_rows = [
        {
            "id": patient.pk,
            "name": patient.user.get_full_name() or patient.user.username,
            "email": patient.user.email,
            "phone": patient.phone,
            "created_at": patient.created_at,
            "status_text": "Active" if patient.user.is_active else "Inactive",
            "status_class": "status-active"
            if patient.user.is_active
            else "status-inactive",
            "is_active": patient.user.is_active,
        }
        for patient in Patient.objects.select_related("user").order_by(
            "-created_at"
        )[:5]
    ]

    today = timezone.now().date()
    total_appointments = Appointment.objects.count()
    pending_appointments = Appointment.objects.filter(status="pending").count()
    confirmed_appointments = Appointment.objects.filter(status="confirmed").count()
    today_appointments_count = Appointment.objects.filter(
        appointment_date=today
    ).count()

    appointment_rows = []
    for appointment in Appointment.objects.select_related(
        "doctor__user", "patient__user"
    ).order_by("-appointment_date", "-appointment_time")[:20]:
        appointment_rows.append(
            {
                "id": appointment.pk,
                "patient_name": appointment.patient_name,
                "patient_email": appointment.patient_email,
                "doctor_name": f"Dr. {appointment.doctor.user.get_full_name() or appointment.doctor.user.username}",
                "appointment_date": appointment.appointment_date,
                "appointment_time": appointment.appointment_time,
                "reason": appointment.get_reason_display(),
                "status": appointment.status,
                "status_display": appointment.get_status_display(),
                "status_class": f"status-{appointment.status}"
                if appointment.status
                in ["pending", "confirmed", "cancelled", "completed"]
                else "status-active",
                "created_at": appointment.created_at,
            }
        )

    context = {
        "user": request.user,
        "total_users": total_users,
        "doctor_count": doctor_count,
        "patient_count": patient_count,
        "new_users_week": new_users_week,
        "user_rows": user_rows,
        "doctor_rows": doctor_rows,
        "patient_rows": patient_rows,
        "appointment_rows": appointment_rows,
        "total_appointments": total_appointments,
        "pending_appointments": pending_appointments,
        "confirmed_appointments": confirmed_appointments,
        "today_appointments_count": today_appointments_count,
    }
    return render(request, "dashboard/admin-dashboard.html", context)


@login_required
def admin_reports(request):
    """
    Admin-only page listing all AI combined analysis reports.
    URL example: /dashboard/admin/reports/
    """
    if not request.user.is_superuser:
        messages.error(request, "Admin reports are restricted to the superuser.")
        return redirect("feetal_app:index")

    reports = AnalysisReport.objects.order_by("-created_at")
    return render(request, "dashboard/admin-reports.html", {"reports": reports})


@login_required
def admin_user_edit(request, user_id):
    """Allow the superuser to edit a user profile."""
    if not request.user.is_superuser:
        messages.error(request, "Only the designated admin can edit users.")
        return redirect("feetal_app:index")

    User = get_user_model()
    target_user = User.objects.filter(pk=user_id).first()
    if not target_user:
        messages.error(request, "User not found.")
        return redirect("feetal_app:dashboard_admin")

    if target_user.is_superuser and target_user != request.user:
        messages.error(
            request, "You cannot edit another superuser via this panel."
        )
        return redirect("feetal_app:dashboard_admin")

    if request.method == "POST":
        form = AdminUserUpdateForm(request.POST, instance=target_user)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"{target_user.get_full_name() or target_user.username} updated successfully.",
            )
            return redirect("feetal_app:dashboard_admin")
    else:
        form = AdminUserUpdateForm(instance=target_user)

    return render(
        request,
        "dashboard/admin_user_form.html",
        {
            "form": form,
            "target_user": target_user,
        },
    )


@login_required
def admin_user_delete(request, user_id):
    """Allow the superuser to delete a user."""
    if not request.user.is_superuser:
        messages.error(request, "Only the designated admin can delete users.")
        return redirect("feetal_app:index")

    User = get_user_model()
    target_user = User.objects.filter(pk=user_id).first()
    if not target_user:
        messages.error(request, "User not found.")
        return redirect("feetal_app:dashboard_admin")

    if target_user == request.user:
        messages.error(
            request, "You cannot delete your own account from this panel."
        )
        return redirect("feetal_app:dashboard_admin")

    if target_user.is_superuser:
        messages.error(request, "Cannot delete the superuser account.")
        return redirect("feetal_app:dashboard_admin")

    if request.method == "POST":
        target_user.delete()
        messages.success(request, "User deleted successfully.")
        return redirect("feetal_app:dashboard_admin")

    return render(
        request,
        "dashboard/admin_user_confirm_delete.html",
        {
            "target_user": target_user,
        },
    )


@login_required
def admin_doctor_edit(request, doctor_id):
    if not request.user.is_superuser:
        messages.error(request, "Only the designated admin can edit doctors.")
        return redirect("feetal_app:index")

    doctor = Doctor.objects.select_related("user").filter(pk=doctor_id).first()
    if not doctor:
        messages.error(request, "Doctor not found.")
        return redirect("feetal_app:dashboard_admin")

    if request.method == "POST":
        form = DoctorAdminForm(request.POST, instance=doctor)
        if form.is_valid():
            form.save()
            messages.success(request, "Doctor profile updated.")
            return redirect("feetal_app:dashboard_admin")
    else:
        form = DoctorAdminForm(instance=doctor)

    return render(
        request,
        "dashboard/admin_doctor_form.html",
        {
            "form": form,
            "doctor": doctor,
        },
    )


@login_required
def admin_doctor_toggle_active(request, doctor_id):
    if not request.user.is_superuser:
        messages.error(
            request, "Only the designated admin can change doctor status."
        )
        return redirect("feetal_app:index")

    doctor = Doctor.objects.select_related("user").filter(pk=doctor_id).first()
    if not doctor:
        messages.error(request, "Doctor not found.")
        return redirect("feetal_app:dashboard_admin")

    if request.method == "POST":
        doctor.user.is_active = not doctor.user.is_active
        doctor.user.save()
        status = "activated" if doctor.user.is_active else "deactivated"
        messages.success(request, f"Doctor {status}.")

    return redirect("feetal_app:dashboard_admin")


# @login_required
# def admin_doctor_schedule(request, doctor_id):
#     if not request.user.is_superuser:
#         messages.error(
#             request, "Only the designated admin can view doctor schedules."
#         )
#         return redirect("feetal_app:index")

#     doctor = Doctor.objects.select_related("user").filter(pk=doctor_id).first()
#     if not doctor:
#         messages.error(request, "Doctor not found.")
#         return redirect("feetal_app:dashboard_admin")

#     return render(
#         request,
#         "dashboard/admin_doctor_schedule.html",
#         {
#             "doctor": doctor,
#         },
#     )


@login_required
def admin_patient_view(request, patient_id):
    if not request.user.is_superuser:
        messages.error(
            request, "Only the designated admin can view patients."
        )
        return redirect("feetal_app:index")

    patient = Patient.objects.select_related("user").filter(pk=patient_id).first()
    if not patient:
        messages.error(request, "Patient not found.")
        return redirect("feetal_app:dashboard_admin")

    return render(
        request, "dashboard/admin_patient_view.html", {"patient": patient}
    )


@login_required
def admin_patient_delete(request, patient_id):
    if not request.user.is_superuser:
        messages.error(
            request, "Only the designated admin can delete patients."
        )
        return redirect("feetal_app:index")

    patient = Patient.objects.select_related("user").filter(pk=patient_id).first()
    if not patient:
        messages.error(request, "Patient not found.")
        return redirect("feetal_app:dashboard_admin")

    if request.method == "POST":
        user = patient.user
        patient.delete()
        user.delete()
        messages.success(request, "Patient deleted successfully.")
        return redirect("feetal_app:dashboard_admin")

    return render(
        request,
        "dashboard/admin_patient_confirm_delete.html",
        {
            "patient": patient,
        },
    )


# ============================================================================
# Appointments
# ============================================================================

@ensure_csrf_cookie
def get_doctors(request):
    """Get list of active doctors, optionally filtered by specialization."""
    try:
        specialization = request.GET.get("specialization", "")
        doctors = Doctor.objects.filter(user__is_active=True).select_related("user")

        if specialization:
            doctors = doctors.filter(specialization=specialization)

        doctors_list = [
            {
                "id": doc.id,
                "name": f"Dr. {doc.user.get_full_name() or doc.user.username}",
                "specialization": doc.get_specialization_display(),
                "specialization_code": doc.specialization,
            }
            for doc in doctors
        ]

        return JsonResponse({"success": True, "doctors": doctors_list})
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@require_http_methods(["POST"])
@ensure_csrf_cookie
def book_appointment(request):
    """Handle appointment booking via AJAX."""
    try:
        data = json.loads(request.body)

        doctor_id = data.get("doctor")
        patient_name = data.get("patientName", "").strip()
        patient_email = data.get("patientEmail", "").strip()
        patient_phone = data.get("patientPhone", "").strip()
        patient_age = data.get("patientAge")
        appointment_date = data.get("date")
        appointment_time = data.get("time")
        reason = data.get("reason")
        notes = data.get("notes", "").strip()

        try:
            doctor_id = int(doctor_id) if doctor_id else None
        except (ValueError, TypeError):
            return JsonResponse(
                {"success": False, "message": "Invalid doctor selection."},
                status=400,
            )

        if not all(
            [
                doctor_id,
                patient_name,
                patient_email,
                patient_phone,
                appointment_date,
                appointment_time,
                reason,
            ]
        ):
            return JsonResponse(
                {
                    "success": False,
                    "message": "Please fill in all required fields.",
                },
                status=400,
            )

        try:
            parsed_date = parse_date(appointment_date)
            if not parsed_date:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Invalid date format. Please use YYYY-MM-DD format.",
                    },
                    status=400,
                )

            parsed_time = parse_time(appointment_time)
            if not parsed_time:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Invalid time format. Please use HH:MM format.",
                    },
                    status=400,
                )
        except (ValueError, TypeError) as e:
            return JsonResponse(
                {
                    "success": False,
                    "message": f"Invalid date or time format: {str(e)}",
                },
                status=400,
            )

        try:
            doctor = Doctor.objects.get(pk=doctor_id)
        except (Doctor.DoesNotExist, ValueError):
            return JsonResponse(
                {"success": False, "message": "Selected doctor not found."},
                status=404,
            )

        patient = None
        if request.user.is_authenticated:
            try:
                patient = request.user.patient_profile
            except Patient.DoesNotExist:
                patient = None

        patient_age_int = None
        if patient_age:
            try:
                patient_age_int = int(patient_age)
                if patient_age_int < 1 or patient_age_int > 120:
                    return JsonResponse(
                        {
                            "success": False,
                            "message": "Age must be between 1 and 120.",
                        },
                        status=400,
                    )
            except (ValueError, TypeError):
                return JsonResponse(
                    {"success": False, "message": "Invalid age value."}, status=400
                )

        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            patient_name=patient_name,
            patient_email=patient_email,
            patient_phone=patient_phone,
            patient_age=patient_age_int,
            appointment_date=parsed_date,
            appointment_time=parsed_time,
            reason=reason,
            notes=notes,
            status="pending",
        )

        return JsonResponse(
            {
                "success": True,
                "message": "Appointment booked successfully! You will receive a confirmation email shortly.",
                "appointment_id": appointment.id,
                "appointment": {
                    "id": appointment.id,
                    "doctor": f"Dr. {appointment.doctor.user.get_full_name() or appointment.doctor.user.username}",
                    "date": appointment.appointment_date.strftime("%Y-%m-%d"),
                    "time": appointment.appointment_time.strftime("%H:%M"),
                    "status": appointment.get_status_display(),
                },
            }
        )
    except Exception as e:
        if settings.DEBUG:
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
        else:
            error_msg = (
                "An error occurred while booking the appointment. Please try again."
            )
        return JsonResponse(
            {"success": False, "message": error_msg},
            status=500,
        )


@login_required
def patient_appointments(request):
    """View appointments for logged-in patient."""
    try:
        patient = request.user.patient_profile
        appointments = Appointment.objects.filter(patient=patient).order_by(
            "-appointment_date", "-appointment_time"
        )
    except Patient.DoesNotExist:
        appointments = Appointment.objects.none()

    context = {
        "appointments": appointments,
        "user": request.user,
    }
    return render(request, "dashboard/patient-appointments.html", context)


@login_required
def doctor_appointments(request):
    """View appointments for logged-in doctor."""
    try:
        doctor = request.user.doctor_profile
        appointments = Appointment.objects.filter(doctor=doctor).order_by(
            "-appointment_date", "-appointment_time"
        )
    except Doctor.DoesNotExist:
        messages.error(request, "Access denied. This page is for doctors only.")
        return redirect("feetal_app:index")

    context = {
        "appointments": appointments,
        "doctor": doctor,
        "user": request.user,
    }
    return render(request, "dashboard/doctor-appointments.html", context)


@login_required
@require_http_methods(["POST"])
def admin_update_appointment_status(request, appointment_id):
    """Update appointment status (admin only)."""
    if not request.user.is_superuser:
        return JsonResponse(
            {"success": False, "message": "Access denied. Admin only."}, status=403
        )

    try:
        appointment = Appointment.objects.get(pk=appointment_id)
        new_status = request.POST.get("status")

        if new_status not in ["pending", "confirmed", "cancelled", "completed"]:
            return JsonResponse(
                {"success": False, "message": "Invalid status."}, status=400
            )

        appointment.status = new_status
        appointment.save()

        return JsonResponse(
            {
                "success": True,
                "message": f"Appointment status updated to {appointment.get_status_display()}.",
                "status": appointment.status,
                "status_display": appointment.get_status_display(),
            }
        )
    except Appointment.DoesNotExist:
        return JsonResponse(
            {"success": False, "message": "Appointment not found."}, status=404
        )
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


# ============================================================================
# ML APIs: Maternal Health & Preterm Delivery
# ============================================================================

@require_http_methods(["POST"])
@ensure_csrf_cookie
def predict_maternal_health_api(request):
    """
    API endpoint for maternal health prediction.
    Used by the "AI Health Predictions" card (numeric form on patient portal).
    """
    try:
        data = json.loads(request.body)

        required_fields = ["age", "systolic_bp", "diastolic_bp", "bs", "heart_rate"]
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            return JsonResponse(
                {
                    "success": False,
                    "message": f'Missing required fields: {", ".join(missing_fields)}',
                },
                status=400,
            )

        result = predict_maternal_health(data)

        if result.get("success"):
            return JsonResponse(
                {
                    "success": True,
                    "prediction": result.get("prediction"),
                    "risk_level": result.get("risk_level"),
                    "prediction_proba": result.get("prediction_proba"),
                    "message": f'Risk assessment: {result.get("risk_level")}',
                }
            )
        else:
            return JsonResponse(
                {
                    "success": False,
                    "message": result.get("error", "Prediction failed"),
                },
                status=500,
            )

    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "message": "Invalid JSON data"}, status=400
        )
    except Exception as e:
        if settings.DEBUG:
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
        else:
            error_msg = "An error occurred during prediction."
        return JsonResponse({"success": False, "message": error_msg}, status=500)


@require_http_methods(["POST"])
@ensure_csrf_cookie
def predict_preterm_delivery_api(request):
    """API endpoint for preterm delivery prediction (image-based)."""
    try:
        if request.FILES:
            image_file = request.FILES.get("image")
            if not image_file:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Image file is required. Please upload an image file.",
                    },
                    status=400,
                )
            data = {"image_file": image_file}
        else:
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Invalid JSON data or missing image file",
                    },
                    status=400,
                )

            if "image_data" not in data and "image_file" not in data:
                return JsonResponse(
                    {
                        "success": False,
                        "message": "Image data required. Please provide image_file (upload) or image_data (base64) in the request.",
                    },
                    status=400,
                )

        result = predict_preterm_delivery(data)

        if result.get("success"):
            return JsonResponse(
                {
                    "success": True,
                    "probability": result.get("probability"),
                    "risk_level": result.get("risk_level"),
                    "prediction": result.get("prediction"),
                    "message": f'Preterm delivery risk: {result.get("risk_level")} ({result.get("probability")*100:.2f}%)',
                }
            )
        else:
            return JsonResponse(
                {
                    "success": False,
                    "message": result.get("error", "Prediction failed"),
                },
                status=500,
            )

    except Exception as e:
        if settings.DEBUG:
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
        else:
            error_msg = "An error occurred during prediction."
        return JsonResponse({"success": False, "message": error_msg}, status=500)


# ============================================================================
# COMBINED ANALYSIS → PDF → ADMIN
# ============================================================================

def _build_combined_pdf(
    patient_name,
    patient_email,
    preterm_result,
    maternal_result,
    combined_result,
):
    """
    Hospital-theme PDF: Blue + White minimal clinical report
    """
    from reportlab.platypus import SimpleDocTemplate, KeepTogether
    from reportlab.lib.pagesizes import A4

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50,
    )

    elements = []
    styles = getSampleStyleSheet()

    # >>> Correct date & time (local timezone)
    generated_at = timezone.localtime()

    from reportlab.platypus import Paragraph, Table, TableStyle, Spacer
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.units import inch

    hospital_blue = colors.HexColor("#0052CC")
    text_black = colors.HexColor("#1A1A1A")
    text_gray = colors.HexColor("#6B7280")

    # ---------------- HEADER ----------------
    header = Table(
        [
            [Paragraph("<b><font size=24 color='white'>FetoScope AI</font></b>",
                       ParagraphStyle(name="header", alignment=TA_CENTER))]
        ],
        colWidths=[7 * inch],
    )
    header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), hospital_blue),
        ("TOPPADDING", (0, 0), (-1, -1), 18),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 18),
    ]))
    elements.append(header)
    elements.append(Spacer(1, 20))

    # ---------------- PATIENT INFO ----------------
    elements.append(Paragraph("<b>Patient Information</b>",
                              ParagraphStyle(name="sec", fontSize=13, textColor=hospital_blue)))
    elements.append(Spacer(1, 5))

    patient_table = Table([
        ["Name:", patient_name],
        ["Email:", patient_email],
        ["Report Date:", generated_at.strftime("%B %d, %Y | %I:%M %p")],
    ], colWidths=[1.7 * inch, 4.8 * inch])

    patient_table.setStyle(TableStyle([
        ("TEXTCOLOR", (0, 0), (-1, -1), text_black),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(patient_table)
    elements.append(Spacer(1, 20))

    # ---------------- OVERALL RISK ----------------
    risk = combined_result.get("risk_level")
    conf = combined_result.get("confidence")

    risk_color = {
        "High Risk": "#D90429",
        "Medium Risk": "#FF8800",
        "Low Risk": "#0BA82E",
    }.get(risk, "#000000")

    elements.append(Paragraph(
        "<b>Overall Risk Assessment</b>",
        ParagraphStyle(name="sec_title", fontSize=13, textColor=hospital_blue)
    ))
    elements.append(Spacer(1, 12))

    risk_section = KeepTogether([
        Paragraph(
            f"<b><font size=34 color='{risk_color}'>{risk}</font></b>",
            ParagraphStyle(name="risk_big", alignment=TA_CENTER, leading=38)
        ),
        Spacer(1, 14),
        Paragraph(
            f"<b><font size=14 color='{text_black}'>Confidence Level: {conf}%</font></b>",
            ParagraphStyle(name="risk_conf", alignment=TA_CENTER)
        )
    ])

    elements.append(risk_section)
    elements.append(Spacer(1, 60))  # spacing before next section

    # ---------------- DETAILED ANALYSIS ----------------
    elements.append(Paragraph(
        "<b>Detailed Analysis</b>",
        ParagraphStyle(name="sec2", fontSize=13, textColor=hospital_blue)
    ))
    elements.append(Spacer(1, 10))

    pre_r = preterm_result.get("risk_level")
    pre_p = round(preterm_result.get("probability", 0) * 100, 2)
    mat_r = maternal_result.get("risk_level")
    mat_p = round(maternal_result.get("prediction_proba", 0) * 100, 2)

    def risk_color_hex(r):
        return {
            "High Risk": "#D90429",
            "Medium Risk": "#FF8800",
            "Low Risk": "#0BA82E",
        }.get(r, "#000000")

    def risk_paragraph(title, risk, prob):
        return [
            Paragraph(title, ParagraphStyle(name="cell_title", fontSize=11, textColor=text_black)),
            Paragraph(f"<b><font color='{risk_color_hex(risk)}'>{risk}</font></b>",
                    ParagraphStyle(name="cell_risk", fontSize=11, alignment=TA_CENTER)),
            Paragraph(f"{prob}%", ParagraphStyle(name="cell_prob", fontSize=11, alignment=TA_CENTER)),
        ]

    analysis_table = Table(
        [
            [
                Paragraph("<b><font size=12 color='white'>Analysis Type</font></b>",
                        ParagraphStyle(name="hdr", alignment=TA_CENTER)),
                Paragraph("<b><font size=12 color='white'>Risk Level</font></b>",
                        ParagraphStyle(name="hdr", alignment=TA_CENTER)),
                Paragraph("<b><font size=12 color='white'>Probability</font></b>",
                        ParagraphStyle(name="hdr", alignment=TA_CENTER)),
            ],
            risk_paragraph("Preterm Delivery (Image-based)", pre_r, pre_p),
            risk_paragraph("Maternal Health (Reports-based)", mat_r, mat_p),
        ],
        colWidths=[3.7 * inch, 1.9 * inch, 1.1 * inch]
    )

    analysis_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), hospital_blue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    elements.append(analysis_table)
    elements.append(Spacer(1, 35))

    # ---------------- FOOTER ----------------
    elements.append(Paragraph(
        f"Generated automatically by FetoScope AI · {generated_at.strftime('%B %d, %Y %I:%M %p')}",
        ParagraphStyle(name="foot", fontSize=9, textColor=text_gray, alignment=TA_CENTER)
    ))

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf




@require_http_methods(["POST"])
@ensure_csrf_cookie
def combined_analysis_api(request):
    """
    Combined analysis API:
    - Accepts scanning images & medical reports (TXT/PDF/DOC/DOCX)
    - Runs both ML models
    - Generates a PDF report
    - Saves it to AnalysisReport for admin
    """
    try:
        if not request.FILES:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Please upload scanning and medical report files.",
                },
                status=400,
            )

        scanning_files = request.FILES.getlist("scanning_files")
        medical_files = request.FILES.getlist("medical_files")

        if not scanning_files or not medical_files:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Upload at least one scanning file and one medical report.",
                },
                status=400,
            )

        # Preterm analysis (image-based)
        preterm_input = {"image_file": scanning_files[0]}
        preterm_result = predict_preterm_delivery(preterm_input)
        if not preterm_result.get("success"):
            return JsonResponse(
                {
                    "success": False,
                    "message": preterm_result.get(
                        "error", "Preterm analysis failed."
                    ),
                },
                status=500,
            )

        # Maternal analysis (reports-based)
        extracted = {}
        for f in medical_files:
            vals = extract_medical_values(f)
            if vals:
                for k, v in vals.items():
                    if v is not None and v != "":
                        extracted[k] = v

        if not extracted:
            return JsonResponse(
                {
                    "success": False,
                    "message": "Could not detect medical values in reports. Please ensure Age, BP, Sugar, etc. are present in text.",
                },
                status=400,
            )

        maternal_result = predict_maternal_health(extracted)
        if not maternal_result.get("success"):
            return JsonResponse(
                {
                    "success": False,
                    "message": maternal_result.get(
                        "error", "Maternal analysis failed."
                    ),
                },
                status=500,
            )

        # Combine risk logic
        def risk_to_score(r):
            if r == "High Risk":
                return 3
            if r == "Medium Risk":
                return 2
            return 1

        preterm_risk = preterm_result.get("risk_level")
        maternal_risk = maternal_result.get("risk_level")

        scores = [risk_to_score(preterm_risk), risk_to_score(maternal_risk)]
        max_score = max(scores)

        if max_score == 3:
            combined_risk = "High Risk"
        elif max_score == 2:
            combined_risk = "Medium Risk"
        else:
            combined_risk = "Low Risk"

        pt_conf = preterm_result.get("probability", 0) * 100
        mh_conf = maternal_result.get("prediction_proba", 0) * 100
        combined_confidence = int(round((pt_conf + mh_conf) / 2))

        combined_result = {
            "risk_level": combined_risk,
            "confidence": combined_confidence,
        }

        # Build PDF & save
        if request.user.is_authenticated and hasattr(request.user, "patient_profile"):
            patient_name = (
                request.user.get_full_name() or request.user.username or "Patient"
            )
            patient_email = request.user.email
        else:
            patient_name = request.POST.get("patient_name", "Unknown Patient")
            patient_email = request.POST.get("patient_email", "")

        pdf_bytes = _build_combined_pdf(
            patient_name,
            patient_email,
            preterm_result,
            maternal_result,
            combined_result,
        )

        file_name = f"combined_report_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        report = AnalysisReport.objects.create(
            patient_name=patient_name,
            patient_email=patient_email,
            combined_risk_level=combined_risk,
        )

        try:
            report.pdf.save(file_name, ContentFile(pdf_bytes))
            report.save()
        except Exception:
            report.save()

        return JsonResponse(
            {
                "success": True,
                "message": "Your reports were analyzed successfully and forwarded to our medical team. They will review and contact you.",
            }
        )

    except Exception as e:
        if settings.DEBUG:
            error_msg = f"{e}\n{traceback.format_exc()}"
        else:
            error_msg = "An error occurred while running combined analysis."
        return JsonResponse({"success": False, "message": error_msg}, status=500)


@login_required
def download_report(request, report_id):
    """Download report PDF - handles both MLReport and AnalysisReport"""
    # Try AnalysisReport first (newer reports with PDF files)
    try:
        report = AnalysisReport.objects.get(id=report_id)
        if report.pdf and report.pdf.name:
            if default_storage.exists(report.pdf.name):
                file = default_storage.open(report.pdf.name, "rb")
                response = FileResponse(
                    file,
                    content_type="application/pdf",
                    filename=os.path.basename(report.pdf.name),
                )
                response[
                    "Content-Disposition"
                ] = f'attachment; filename="{os.path.basename(report.pdf.name)}"'
                return response
            else:
                try:
                    file_path = report.pdf.path
                    if os.path.exists(file_path):
                        return FileResponse(
                            open(file_path, "rb"),
                            content_type="application/pdf",
                            filename=os.path.basename(report.pdf.name),
                        )
                except (ValueError, AttributeError):
                    pass

                base_dir = settings.BASE_DIR
                alternative_paths = [
                    os.path.join(base_dir, report.pdf.name),
                    os.path.join(base_dir, "media", report.pdf.name),
                ]

                for alt_path in alternative_paths:
                    normalized_path = os.path.normpath(alt_path)
                    if os.path.exists(normalized_path):
                        return FileResponse(
                            open(normalized_path, "rb"),
                            content_type="application/pdf",
                            filename=os.path.basename(report.pdf.name),
                        )

                # Fallback: regenerate a simple PDF summary
                buffer = io.BytesIO()
                p = canvas.Canvas(buffer, pagesize=A4)
                p.setFont("Helvetica-Bold", 16)
                p.drawString(100, 800, "FetoScope AI Analysis Report")
                p.setFont("Helvetica", 12)
                p.drawString(50, 760, f"Patient: {report.patient_name}")
                p.drawString(
                    50, 740, f"Email: {report.patient_email or 'N/A'}"
                )
                p.drawString(
                    50, 720, f"Risk Level: {report.combined_risk_level}"
                )
                p.drawString(
                    50,
                    700,
                    f"Generated: {report.created_at.strftime('%Y-%m-%d %H:%M')}",
                )
                p.drawString(
                    50,
                    680,
                    "Note: Original PDF file was not found. This is a regenerated summary.",
                )
                p.showPage()
                p.save()

                buffer.seek(0)
                pdf_data = buffer.read()
                buffer.close()

                response = HttpResponse(pdf_data, content_type="application/pdf")
                response[
                    "Content-Disposition"
                ] = f'attachment; filename="report_{report_id}_regenerated.pdf"'
                return response
    except AnalysisReport.DoesNotExist:
        pass

    # Fallback to MLReport (older reports, generate PDF on the fly)
    try:
        report = MLReport.objects.get(id=report_id)
        response = HttpResponse(content_type="application/pdf")
        response[
            "Content-Disposition"
        ] = f"attachment; filename=report_{report_id}.pdf"

        p = canvas.Canvas(response, pagesize=A4)
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, 800, "Feetal Health Analysis Report")

        p.setFont("Helvetica", 12)
        p.drawString(50, 760, f"Patient: {report.patient_name}")
        p.drawString(50, 740, f"Report Type: {report.analysis_type}")
        p.drawString(50, 720, f"Risk Level: {report.risk_level}")
        p.drawString(50, 700, f"Confidence: {report.confidence}%")
        p.drawString(
            50, 680, f"Created: {report.created_at.strftime('%d-%m-%Y %H:%M')}"
        )

        y = 650
        for f_line in report.findings.split("\n"):
            p.drawString(50, y, f"- {f_line}")
            y -= 18

        p.showPage()
        p.save()
        return response
    except MLReport.DoesNotExist:
        raise Http404("Report not found")


@require_http_methods(["POST"])
@ensure_csrf_cookie
def save_combined_report(request):
    """
    Legacy endpoint: save combined report into MLReport and generate a simple PDF.
    (You can remove this if not needed anymore.)
    """
    data = json.loads(request.body)

    report = MLReport.objects.create(
        patient_name=data.get("patient_name"),
        analysis_type="Combined",
        risk_level=data.get("risk_level"),
        confidence=data.get("confidence"),
        findings="\n".join(data.get("findings", [])),
    )

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 800, "Feetal Health Analysis Report")
    p.setFont("Helvetica", 12)
    p.drawString(50, 760, f"Patient: {report.patient_name}")
    p.drawString(50, 740, f"Risk Level: {report.risk_level}")
    p.drawString(50, 720, f"Confidence: {report.confidence}%")

    y = 690
    for line in data.get("findings", []):
        p.drawString(50, y, "- " + line)
        y -= 18
    p.showPage()
    p.save()

    pdf_data = buffer.getvalue()
    buffer.close()

    pdf_path = f"reports/report_{report.id}.pdf"
    default_storage.save(pdf_path, ContentFile(pdf_data))

    return JsonResponse({"success": True})
