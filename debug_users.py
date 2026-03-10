import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'maternity.settings')
django.setup()

from django.contrib.auth import get_user_model

from django.db.models import Count

User = get_user_model()
duplicates = User.objects.values('email').annotate(email_count=Count('email')).filter(email_count__gt=1)

with open('results.txt', 'w') as f:
    f.write("Duplicates found:\n")
    for d in duplicates:
        email = d['email']
        count = d['email_count']
        f.write(f"Email: {email}, Count: {count}\n")
        matching_users = User.objects.filter(email__iexact=email)
        for u in matching_users:
            has_doctor = hasattr(u, 'doctor_profile')
            has_patient = hasattr(u, 'patient_profile')
            f.write(f"  ID: {u.id}, Username: '{u.username}', Email: '{u.email}', Staff: {u.is_staff}, SU: {u.is_superuser}, Dr: {has_doctor}, Pat: {has_patient}\n")



