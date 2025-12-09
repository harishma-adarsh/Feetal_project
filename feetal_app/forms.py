from django import forms
from django.contrib.auth.models import User
from .models import Patient, Doctor


class PatientRegistrationForm(forms.Form):
    """Registration form for patients."""
    name = forms.CharField(max_length=150, required=True, label="Full Name", widget=forms.TextInput(attrs={'placeholder': 'Enter your full name'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'Enter your email'}))
    phone = forms.CharField(max_length=20, required=True, widget=forms.TextInput(attrs={'placeholder': 'Enter your phone number'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Create a password'}), required=True, min_length=6)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def save(self):
        name = self.cleaned_data['name']
        email = self.cleaned_data['email']
        phone = self.cleaned_data['phone']
        password = self.cleaned_data['password']
        
        # Split name into first and last name
        name_parts = name.split(maxsplit=1)
        first_name = name_parts[0] if name_parts else ''
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Create User
        user = User.objects.create_user(
            username=email,  # Use email as username
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Create Patient profile
        patient = Patient.objects.create(
            user=user,
            phone=phone
        )
        
        return user


class DoctorRegistrationForm(forms.Form):
    """Registration form for doctors."""
    name = forms.CharField(max_length=150, required=True, label="Full Name", widget=forms.TextInput(attrs={'placeholder': 'Dr. Jane Doe'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'doctor@example.com'}))
    phone = forms.CharField(max_length=20, required=True, widget=forms.TextInput(attrs={'placeholder': '+1 (555) 123-4567'}))
    specialization = forms.ChoiceField(choices=Doctor.SPECIALIZATION_CHOICES, required=True, widget=forms.Select(attrs={'placeholder': 'Select specialization'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Create a password'}), required=True, min_length=6)
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Confirm password'}), required=True, label="Confirm Password")

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password2 = cleaned_data.get('password2')
        
        if password and password2 and password != password2:
            raise forms.ValidationError('Passwords do not match.')
        
        return cleaned_data

    def save(self):
        name = self.cleaned_data['name']
        email = self.cleaned_data['email']
        phone = self.cleaned_data['phone']
        specialization = self.cleaned_data['specialization']
        password = self.cleaned_data['password']
        
        # Remove "Dr." or "Dr" prefix if present (it will be added in display)
        name = name.strip()
        if name.lower().startswith('dr.'):
            name = name[3:].strip()
        elif name.lower().startswith('dr'):
            name = name[2:].strip()
        
        # Split name into first and last name
        name_parts = name.split(maxsplit=1)
        first_name = name_parts[0] if name_parts else ''
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Create User
        user = User.objects.create_user(
            username=email,  # Use email as username
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_staff=True  # Doctors are staff members
        )
        
        # Create Doctor profile
        doctor = Doctor.objects.create(
            user=user,
            phone=phone,
            specialization=specialization
        )
        
        return user


class AdminUserUpdateForm(forms.ModelForm):
    """Form used by admin to update basic user details."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'is_active']
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'user@example.com'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Another user with this email already exists.')
        return email


class DoctorAdminForm(forms.ModelForm):
    """Form used by admin to edit doctor profile basics."""

    first_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'placeholder': 'First name'}))
    last_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={'placeholder': 'Last name'}))

    class Meta:
        model = Doctor
        fields = ['phone', 'specialization']
        widgets = {
            'phone': forms.TextInput(attrs={'placeholder': '+1 (555) 123-4567'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name

    def save(self, commit=True):
        doctor = super().save(commit=False)
        user = doctor.user
        user.first_name = self.cleaned_data.get('first_name', user.first_name)
        user.last_name = self.cleaned_data.get('last_name', user.last_name)
        if commit:
            doctor.save()
            user.save()
        else:
            self.save_m2m()
        return doctor




class AdminUserUpdateForm(forms.ModelForm):
    """Form used by admin to update basic user details."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'is_active']
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'user@example.com'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Another user with this email already exists.')
        return email

