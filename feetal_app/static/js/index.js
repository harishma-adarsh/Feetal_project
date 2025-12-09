const PATIENT_PORTAL_URL = '/patient-portal/';

// Initialize AOS (Animate On Scroll)
document.addEventListener('DOMContentLoaded', function() {
    AOS.init({
        duration: 800,
        easing: 'ease-in-out',
        once: true,
        offset: 100
    });
    
    // Initialize navbar scroll effect
    initNavbarScrollEffect();
    
    // Set minimum date for appointment date input
    const appointmentDateInput = document.getElementById('appointmentDate');
    if (appointmentDateInput) {
        const today = new Date().toISOString().split('T')[0];
        appointmentDateInput.setAttribute('min', today);
    }
});

// Navbar scroll effect
function initNavbarScrollEffect() {
    const navbar = document.querySelector('.navbar');
    let lastScrollTop = 0;
    
    window.addEventListener('scroll', function() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        // Add scrolled class when scrolled down more than 100px
        if (scrollTop > 100) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
        
        lastScrollTop = scrollTop;
    });
}

// Mock user data for demonstration
const mockUsers = [
    {
        email: 'demo@fetoscope.com',
        password: 'demo123',
        name: 'Demo User',
        phone: '+1 (555) 123-4567'
    },
    {
        email: 'patient@example.com',
        password: 'patient123',
        name: 'John Smith',
        phone: '+1 (555) 987-6543'
    },
    {
        email: 'doctor@fetoscope.com',
        password: 'doctor123',
        name: 'Dr. Sarah Johnson',
        phone: '+1 (555) 456-7890'
    }
];

// Store registered users (in real app, this would be in a database)
let registeredUsers = [...mockUsers];

// Modal Functions
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
        
        // Add animation class
        const modalContent = modal.querySelector('.modal-content');
        modalContent.style.animation = 'modalSlideIn 0.3s ease';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
        
        // Clear form inputs
        const form = modal.querySelector('form');
        if (form) {
            form.reset();
        }
        
        // Clear any error messages
        clearErrorMessages();
    }
}

function switchModal(currentModalId, targetModalId) {
    closeModal(currentModalId);
    setTimeout(() => {
        openModal(targetModalId);
    }, 100);
}

// Close modal when clicking outside
window.addEventListener('click', function(event) {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        if (event.target === modal) {
            closeModal(modal.id);
        }
    });
});

// Close modal with Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            if (modal.style.display === 'block') {
                closeModal(modal.id);
            }
        });
    }
});

// Get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Login Handler
async function handleLogin(event) {
    event.preventDefault();
    
    const email = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPassword').value;
    
    // Clear previous error messages
    clearErrorMessages();
    
    // Validate inputs
    if (!email || !password) {
        showError('loginModal', 'Please fill in all fields.');
        return;
    }
    
    try {
        const response = await fetch('/patient/login/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Successful login
            showSuccess('loginModal', data.message);
            
            // Store user session
            // sessionStorage.setItem('currentUser', JSON.stringify(data.user));
            sessionStorage.removeItem('currentUser');   // clear old stored user
           sessionStorage.setItem(
                "currentUser",
                JSON.stringify({
                    name: data.user.name,
                    email: data.user.email,
                    phone: data.user.phone || ""
                })
            );
            console.log("User stored to sessionStorage:", sessionStorage.getItem("currentUser"));

            
            // Set flag to open booking modal after redirect
            sessionStorage.setItem('openBookingModal', 'true');
            
            // Close modal after delay and redirect to patient portal
            setTimeout(() => {
                closeModal('loginModal');
                window.location.href = PATIENT_PORTAL_URL;
            }, 1500);
        } else {
            showError('loginModal', data.message || 'Invalid email or password. Please try again.');
        }
    } catch (error) {
        console.error('Login error:', error);
        showError('loginModal', 'An error occurred. Please try again.');
    }
}

// Registration Handler
async function handleRegister(event) {
    event.preventDefault();
    
    const name = document.getElementById('registerName').value.trim();
    const email = document.getElementById('registerEmail').value.trim();
    const phone = document.getElementById('registerPhone').value.trim();
    const password = document.getElementById('registerPassword').value;
    
    // Clear previous error messages
    clearErrorMessages();
    
    // Validate inputs
    if (!name || !email || !phone || !password) {
        showError('registerModal', 'Please fill in all fields.');
        return;
    }
    
    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showError('registerModal', 'Please enter a valid email address.');
        return;
    }
    
    // Validate password length
    if (password.length < 6) {
        showError('registerModal', 'Password must be at least 6 characters long.');
        return;
    }
    
    try {
        const response = await fetch('/patient/register/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                name: name,
                email: email,
                phone: phone,
                password: password
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Show success message
            showSuccess('registerModal', data.message);
            
            // Store user session
            // sessionStorage.setItem('currentUser', JSON.stringify(data.user));
            sessionStorage.removeItem('currentUser');
                    sessionStorage.setItem(
                "currentUser",
                JSON.stringify({
                    name: data.user.name,
                    email: data.user.email,
                    phone: data.user.phone || ""
                })
            );
            console.log("User stored to sessionStorage:", sessionStorage.getItem("currentUser"));



            
            // Set flag to open booking modal after redirect
            sessionStorage.setItem('openBookingModal', 'true');
            
            // Close modal after delay and redirect to patient portal
            setTimeout(() => {
                closeModal('registerModal');
                window.location.href = PATIENT_PORTAL_URL;
            }, 1500);
        } else {
            showError('registerModal', data.message || 'Registration failed. Please try again.');
        }
    } catch (error) {
        console.error('Registration error:', error);
        showError('registerModal', 'An error occurred. Please try again.');
    }
}

// Doctor Registration Handler
async function handleDoctorRegister(event) {
    event.preventDefault();
    
    const name = document.getElementById('doctorName').value.trim();
    const email = document.getElementById('doctorEmail').value.trim();
    const phone = document.getElementById('doctorPhone').value.trim();
    const specialization = document.getElementById('specialization').value;
    const password = document.getElementById('regPasswordDoctor').value;
    const password2 = document.getElementById('regConfirmPasswordDoctor').value;
    
    // Clear previous messages
    const errorDiv = document.getElementById('doctorError');
    const successDiv = document.getElementById('doctorSuccess');
    if (errorDiv) errorDiv.style.display = 'none';
    if (successDiv) successDiv.style.display = 'none';
    
    // Validate inputs
    if (!name || !email || !phone || !specialization || !password || !password2) {
        if (errorDiv) {
            errorDiv.textContent = 'Please fill in all fields.';
            errorDiv.style.display = 'block';
        }
        return;
    }
    
    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        if (errorDiv) {
            errorDiv.textContent = 'Please enter a valid email address.';
            errorDiv.style.display = 'block';
        }
        return;
    }
    
    // Validate password length
    if (password.length < 6) {
        if (errorDiv) {
            errorDiv.textContent = 'Password must be at least 6 characters long.';
            errorDiv.style.display = 'block';
        }
        return;
    }
    
    // Validate password match
    if (password !== password2) {
        if (errorDiv) {
            errorDiv.textContent = 'Passwords do not match.';
            errorDiv.style.display = 'block';
        }
        return;
    }
    
    try {
        const response = await fetch('/api/doctor/register/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            credentials: 'include', // Include cookies in the request
            body: JSON.stringify({
                name: name,
                email: email,
                phone: phone,
                specialization: specialization,
                password: password,
                password2: password2
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            if (successDiv) {
                successDiv.textContent = data.message;
                successDiv.style.display = 'block';
            }
            
            // Close modal after delay and redirect to doctor dashboard
            setTimeout(() => {
                closeModal('doctorRegistrationModal');
                // Use redirect URL from response or default
                const redirectUrl = data.redirect_url || '/dashboard/doctor/';
                console.log('Redirecting to:', redirectUrl);
                window.location.replace(redirectUrl);
            }, 1500);
        } else {
            if (errorDiv) {
                const errorMsg = data.message || 'Registration failed. Please try again.';
                errorDiv.textContent = errorMsg;
                errorDiv.style.display = 'block';
                console.error('Registration failed:', data);
            }
        }
    } catch (error) {
        console.error('Doctor registration error:', error);
        if (errorDiv) {
            errorDiv.textContent = 'An error occurred. Please check the console for details and try again.';
            errorDiv.style.display = 'block';
        }
    }
}

// Utility Functions
function showError(modalId, message) {
    const modal = document.getElementById(modalId);
    if (!modal) {
        console.error(`Modal with id "${modalId}" not found`);
        alert(message); // Fallback to alert if modal not found
        return;
    }
    
    // Try to find form (could be .auth-form or .appointment-form)
    const form = modal.querySelector('.auth-form') || modal.querySelector('.appointment-form') || modal.querySelector('form');
    
    if (!form) {
        console.error('Form not found in modal');
        alert(message); // Fallback to alert if form not found
        return;
    }
    
    // Remove existing error messages
    const existingError = form.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }
    
    // Create error message element
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.style.cssText = `
        background: #fee2e2;
        color: #dc2626;
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 1rem;
        font-size: 0.9rem;
        border: 1px solid #fecaca;
    `;
    errorDiv.textContent = message;
    
    // Insert at the beginning of the form
    form.insertBefore(errorDiv, form.firstChild);
    
    // Scroll to error message
    errorDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function showSuccess(modalId, message) {
    const modal = document.getElementById(modalId);
    const form = modal.querySelector('.auth-form');
    
    // Remove existing messages
    const existingMessage = form.querySelector('.success-message, .error-message');
    if (existingMessage) {
        existingMessage.remove();
    }
    
    // Create success message element
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message';
    successDiv.style.cssText = `
        background: #d1fae5;
        color: #065f46;
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 1rem;
        font-size: 0.9rem;
        border: 1px solid #a7f3d0;
    `;
    successDiv.textContent = message;
    
    // Insert at the beginning of the form
    form.insertBefore(successDiv, form.firstChild);
}

function clearErrorMessages() {
    const errorMessages = document.querySelectorAll('.error-message, .success-message');
    errorMessages.forEach(msg => msg.remove());
}

function toggleCallDropdown() {
    const menu = document.getElementById('callDropdown');
    if (!menu) return;

    const isOpen = menu.classList.contains('open');
    document.querySelectorAll('.dropdown-menu.open').forEach(m => m.classList.remove('open'));

    if (!isOpen) {
        menu.classList.add('open');
    }
}

function ensureNavAuthButtons() {
    const navMenu = document.querySelector('.nav-menu[data-landing-nav="true"]');
    if (!navMenu) {
        return;
    }

    // Remove any legacy injected user menu
    navMenu.querySelectorAll('.user-menu').forEach(menu => {
        const parentLi = menu.closest('li');
        if (parentLi) {
            parentLi.remove();
        } else {
            menu.remove();
        }
    });

    if (!document.getElementById('navLoginItem')) {
        const loginLi = document.createElement('li');
        loginLi.id = 'navLoginItem';
        loginLi.innerHTML = `<button class="btn-login" onclick="openModal('loginModal')">Login</button>`;
        navMenu.appendChild(loginLi);
    }

    if (!document.getElementById('navRegisterItem')) {
        const registerLi = document.createElement('li');
        registerLi.id = 'navRegisterItem';
        registerLi.innerHTML = `<button class="btn-register" onclick="openModal('registerModal')">Register</button>`;
        navMenu.appendChild(registerLi);
    }
}

function updateUIForLoggedInUser(user) {
    // Show patient portal menu item
    const dashboardMenuItem = document.getElementById('dashboardMenuItem');
    if (dashboardMenuItem) {
        dashboardMenuItem.style.display = 'block';
        // Update the link text and icon
        dashboardMenuItem.innerHTML = `<a href="${PATIENT_PORTAL_URL}" class="dashboard-link"><i class="fas fa-user"></i> Patient Portal</a>`;
    }

    // Keep login/register buttons visible on the landing page; logout lives in portal UI.
}

function logout() {
    // Clear user session
    sessionStorage.removeItem('currentUser');
    
    // Hide dashboard menu item
    const dashboardMenuItem = document.getElementById('dashboardMenuItem');
    if (dashboardMenuItem) {
        dashboardMenuItem.style.display = 'none';
    }
    
    // Reload page to reset UI
    window.location.reload();
}

// Check if user is already logged in on page load
document.addEventListener('DOMContentLoaded', function() {
    ensureNavAuthButtons();
    const currentUser = sessionStorage.getItem('currentUser');
    if (currentUser) {
        const user = JSON.parse(currentUser);
        updateUIForLoggedInUser(user);
    }
});

// Smooth scrolling function
function scrollToSection(sectionId) {
    const element = document.getElementById(sectionId);
    if (element) {
        const offsetTop = element.offsetTop - 70; // Account for fixed navbar
        window.scrollTo({
            top: offsetTop,
            behavior: 'smooth'
        });
    }
}

// Notification system
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notif => notif.remove());
    
    const notification = document.createElement('div');
    notification.className = 'notification';
    
    const bgColor = type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#2563eb';
    
    notification.style.cssText = `
        position: fixed;
        top: 90px;
        right: 20px;
        background: ${bgColor};
        color: white;
        padding: 16px 24px;
        border-radius: 8px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
        z-index: 3000;
        font-weight: 500;
        animation: slideInRight 0.3s ease;
        max-width: 300px;
    `;
    
    notification.textContent = message;
    document.body.appendChild(notification);
    
    // Auto remove after 4 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 300);
    }, 4000);
}

// Add notification animations to CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(100%);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes slideOutRight {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(100%);
        }
    }
`;
document.head.appendChild(style);

// Mobile menu toggle (for future enhancement)
function toggleMobileMenu() {
    const navMenu = document.querySelector('.nav-menu');
    const hamburger = document.querySelector('.hamburger');
    
    navMenu.classList.toggle('active');
    hamburger.classList.toggle('active');
}

// Add click handler for hamburger menu
document.addEventListener('DOMContentLoaded', function() {
    const hamburger = document.querySelector('.hamburger');
    if (hamburger) {
        hamburger.addEventListener('click', toggleMobileMenu);
    }
});

// Form validation helpers
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePhone(phone) {
    const re = /^[\+]?[1-9][\d]{0,15}$/;
    return re.test(phone.replace(/\s/g, ''));
}

// Auto-fill demo credentials
function fillDemoCredentials() {
    document.getElementById('loginEmail').value = 'demo@fetoscope.com';
    document.getElementById('loginPassword').value = 'demo123';
}

// Add demo credentials click handler
document.addEventListener('DOMContentLoaded', function() {
    const demoCredentials = document.querySelector('.demo-credentials');
    if (demoCredentials) {
        demoCredentials.style.cursor = 'pointer';
        demoCredentials.addEventListener('click', fillDemoCredentials);
        demoCredentials.title = 'Click to auto-fill demo credentials';
    }
});

// Maternity service redirection
function redirectToMaternity() {
    const currentUser = sessionStorage.getItem('currentUser');
    
    if (currentUser) {
        // User is logged in, redirect to patient portal
        window.location.href = PATIENT_PORTAL_URL;
    } else {
        // User is not logged in, show login modal
        showNotification('Please login to access our Maternity services.', 'info');
        setTimeout(() => {
            openModal('loginModal');
        }, 500);
    }
}

// Appointment Booking Functionality
async function updateDoctorsList() {
    const departmentSelect = document.getElementById('appointmentDepartment');
    const doctorSelect = document.getElementById('appointmentDoctor');
    const selectedDepartment = departmentSelect.value;
    
    // Clear and reset doctor dropdown
    doctorSelect.innerHTML = '<option value="">Loading doctors...</option>';
    doctorSelect.disabled = true;
    
    if (!selectedDepartment) {
        doctorSelect.innerHTML = '<option value="">Select a department first</option>';
        doctorSelect.disabled = true;
        return;
    }
    
        try {
        // Map department values to specialization codes
        // If "all" is selected, don't pass specialization parameter to get all doctors
            const specializationMap = {
            'gynecology': 'obgyn'  // Legacy support
            };
        const specialization = selectedDepartment === 'all' ? '' : (specializationMap[selectedDepartment] || selectedDepartment);
        const url = `/api/doctors${specialization ? '?specialization=' + specialization : ''}`;
            
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include'
            });
            
            const data = await response.json();
            
            if (data.success && data.doctors.length > 0) {
                doctorSelect.innerHTML = '<option value="">Select Doctor</option>';
                doctorSelect.disabled = false;
                
                data.doctors.forEach(doctor => {
                    const option = document.createElement('option');
                    option.value = doctor.id;
                    option.textContent = `${doctor.name} - ${doctor.specialization}`;
                    doctorSelect.appendChild(option);
                });
            } else {
            doctorSelect.innerHTML = '<option value="">No doctors available for this department</option>';
                doctorSelect.disabled = true;
            }
        } catch (error) {
            console.error('Error fetching doctors:', error);
            doctorSelect.innerHTML = '<option value="">Error loading doctors</option>';
        doctorSelect.disabled = true;
    }
}

async function handleAppointmentBooking(event) {
    event.preventDefault();
    
    // Get form data
    const formData = {
        patientName: document.getElementById('patientName').value,
        patientPhone: document.getElementById('patientPhone').value,
        patientEmail: document.getElementById('patientEmail').value,
        patientAge: document.getElementById('patientAge').value,
        department: document.getElementById('appointmentDepartment').value,
        doctor: document.getElementById('appointmentDoctor').value,
        date: document.getElementById('appointmentDate').value,
        time: document.getElementById('appointmentTime').value,
        reason: document.getElementById('appointmentReason').value,
        notes: document.getElementById('appointmentNotes').value,
        terms: document.getElementById('appointmentTerms').checked
    };
    
    // Validate form
    if (!validateAppointmentForm(formData)) {
        return;
    }
    
    // Show loading state
    const submitBtn = event.target.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Booking...';
    
    try {
        // Get CSRF token
        const csrfToken = getCookie('csrftoken');
        if (!csrfToken) {
            console.error('CSRF token not found');
            showError('appointmentModal', 'Security token missing. Please refresh the page and try again.');
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
            return;
        }
        
        // Prepare request body
        const requestBody = {
            patientName: formData.patientName,
            patientPhone: formData.patientPhone,
            patientEmail: formData.patientEmail,
            patientAge: formData.patientAge,
            doctor: parseInt(formData.doctor), // Ensure doctor ID is an integer
            date: formData.date,
            time: formData.time,
            reason: formData.reason,
            notes: formData.notes || ''
        };
        
        console.log('Booking appointment with data:', requestBody);
        
        // Submit to backend
        const response = await fetch('/api/appointments/book/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            credentials: 'include',
            body: JSON.stringify(requestBody)
        });
        
        console.log('Response status:', response.status);
        
        // Check if response is OK
        if (!response.ok) {
            let errorMessage = 'Failed to book appointment. Please try again.';
            try {
                const errorData = await response.json();
                errorMessage = errorData.message || errorMessage;
            } catch (e) {
                errorMessage = `Server error (${response.status}). Please try again.`;
            }
            showError('appointmentModal', errorMessage);
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
            return;
        }
        
        const data = await response.json();
        
        if (data.success) {
            // Show success message
            showAppointmentConfirmation(data.appointment_id, {
                ...formData,
                appointment: data.appointment
            });
            
            // Reset form and button
            event.target.reset();
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
            
            // Close modal after delay
            setTimeout(() => {
                closeModal('appointmentModal');
            }, 3000);
        } else {
            // Show error message
            showError('appointmentModal', data.message || 'Failed to book appointment. Please try again.');
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    } catch (error) {
        console.error('Error booking appointment:', error);
        showError('appointmentModal', 'An error occurred while booking the appointment. Please check your connection and try again.');
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    }
}

function validateAppointmentForm(data) {
    // Check required fields
    const requiredFields = ['patientName', 'patientPhone', 'patientEmail', 'patientAge', 'department', 'doctor', 'date', 'time', 'reason'];
    
    for (let field of requiredFields) {
        const value = data[field];
        if (!value || (typeof value === 'string' && value.trim() === '')) {
            const fieldName = field.replace(/([A-Z])/g, ' $1').toLowerCase().replace(/^./, str => str.toUpperCase());
            showError('appointmentModal', `Please fill in the ${fieldName} field.`);
            return false;
        }
    }
    
    // Validate email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(data.patientEmail)) {
        showError('appointmentModal', 'Please enter a valid email address.');
        return false;
    }
    
    // Validate age
    const age = parseInt(data.patientAge);
    if (age < 1 || age > 120) {
        showError('appointmentModal', 'Please enter a valid age between 1 and 120.');
        return false;
    }
    
    // Validate date (must be future date)
    const selectedDate = new Date(data.date);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    if (selectedDate < today) {
        showError('appointmentModal', 'Please select a future date for your appointment.');
        return false;
    }
    
    // Validate terms agreement
    if (!data.terms) {
        showError('appointmentModal', 'Please agree to the Terms and Conditions to proceed.');
        return false;
    }
    
    return true;
}

function saveAppointment(appointmentId, data) {
    let appointments = JSON.parse(sessionStorage.getItem('appointments') || '[]');
    
    const appointment = {
        id: appointmentId,
        ...data,
        status: 'pending',
        createdAt: new Date().toISOString(),
        doctorName: getDoctorName(data.doctor, data),
        departmentName: getDepartmentName(data.department)
    };
    
    appointments.unshift(appointment);
    
    // Keep only last 20 appointments
    if (appointments.length > 20) {
        appointments = appointments.slice(0, 20);
    }
    
    sessionStorage.setItem('appointments', JSON.stringify(appointments));
}

function getDoctorName(doctorId, appointmentData) {
    // Try to get doctor name from appointment data first
    if (appointmentData && appointmentData.appointment && appointmentData.appointment.doctor) {
        return appointmentData.appointment.doctor;
    }
    // Fallback: try to get from stored doctor data or return default
    return 'Dr. Selected Doctor';
}

function getDepartmentName(deptId) {
    const departments = {
        gynecology: 'Gynecology & Maternity',
        cardiology: 'Cardiology',
        neurology: 'Neurology',
        pediatrics: 'Pediatrics',
        radiology: 'Radiology',
        emergency: 'Emergency Care'
    };
    return departments[deptId] || 'Unknown Department';
}

function showAppointmentConfirmation(appointmentId, data) {
    const modal = document.getElementById('appointmentModal');
    if (!modal) {
        console.error('Appointment modal not found');
        return;
    }
    
    const form = modal.querySelector('.appointment-form');
    if (!form) {
        console.error('Appointment form not found');
        return;
    }
    
    // Remove existing success messages
    const existingSuccess = form.querySelector('.appointment-success');
    if (existingSuccess) {
        existingSuccess.remove();
    }
    
    // Create success message
    const successDiv = document.createElement('div');
    successDiv.className = 'appointment-success';
    successDiv.style.cssText = `
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        text-align: center;
    `;
    
    // Format date
    let formattedDate = 'N/A';
    if (data.date) {
        try {
            formattedDate = new Date(data.date + 'T00:00:00').toLocaleDateString('en-US', { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
            });
        } catch (e) {
            formattedDate = data.date;
        }
    } else if (data.appointment && data.appointment.date) {
        formattedDate = data.appointment.date;
    }
    
    // Format time
    let formattedTime = 'N/A';
    if (data.time) {
        formattedTime = formatTime(data.time);
    } else if (data.appointment && data.appointment.time) {
        formattedTime = data.appointment.time;
    }
    
    // Get doctor name
    const doctorName = getDoctorName(data.doctor, data);
    
    // Get department name
    const departmentName = getDepartmentName(data.department || 'gynecology');
    
    successDiv.innerHTML = `
        <div style="font-size: 3rem; margin-bottom: 1rem;">
            <i class="fas fa-check-circle"></i>
        </div>
        <h3 style="margin-bottom: 1rem; font-size: 1.5rem;">Appointment Booked Successfully!</h3>
        <div style="background: rgba(255,255,255,0.2); padding: 1.5rem; border-radius: 8px; margin: 1rem 0;">
            <p style="margin: 0.5rem 0;"><strong>Appointment ID:</strong> ${appointmentId || 'N/A'}</p>
            <p style="margin: 0.5rem 0;"><strong>Date:</strong> ${formattedDate}</p>
            <p style="margin: 0.5rem 0;"><strong>Time:</strong> ${formattedTime}</p>
            <p style="margin: 0.5rem 0;"><strong>Doctor:</strong> ${doctorName}</p>
            <p style="margin: 0.5rem 0;"><strong>Department:</strong> ${departmentName}</p>
        </div>
        <p style="margin-top: 1rem; opacity: 0.9;">
            <i class="fas fa-envelope"></i> Confirmation details have been sent to ${data.patientEmail || 'your email'}
        </p>
        <p style="margin-top: 0.5rem; opacity: 0.9;">
            <i class="fas fa-sms"></i> SMS reminder will be sent to ${data.patientPhone || 'your phone'}
        </p>
    `;
    
    // Insert at the beginning of the form
    form.insertBefore(successDiv, form.firstChild);
    
    // Scroll to success message
    successDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    
    // Scroll to success message
    successDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    
    // Show notification
    showNotification('Appointment booked successfully!', 'success');
}

function formatTime(time) {
    const [hours, minutes] = time.split(':');
    const hour = parseInt(hours);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour % 12 || 12;
    return `${displayHour}:${minutes} ${ampm}`;
}

// Set minimum date to today
document.addEventListener('DOMContentLoaded', function() {
    const dateInput = document.getElementById('appointmentDate');
    if (dateInput) {
        const today = new Date();
        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);
        dateInput.min = tomorrow.toISOString().split('T')[0];
    }
});

// Auto-fill user data if logged in
// function prefillUserData() {
//     const currentUser = sessionStorage.getItem('currentUser');
//     if (currentUser) {
//         const user = JSON.parse(currentUser);
        
//         const nameField = document.getElementById('patientName');
//         const emailField = document.getElementById('patientEmail');
//         const phoneField = document.getElementById('patientPhone');
        
//         if (nameField && user.name) nameField.value = user.name;
//         if (emailField && user.email) emailField.value = user.email;
//         if (phoneField && user.phone) phoneField.value = user.phone;
//     }
// }

// function prefillUserData() {
//     const currentUser = sessionStorage.getItem('currentUser');
//     if (!currentUser) return;

//     const user = JSON.parse(currentUser);

//     const nameField = document.getElementById('patientName');
//     const emailField = document.getElementById('patientEmail');
//     const phoneField = document.getElementById('patientPhone');

//     if (nameField) nameField.value = user.name || "";
//     if (emailField) emailField.value = user.email || "";
//     if (phoneField) phoneField.value = user.phone || ""; // 🔥 Auto fill phone
// }

    function prefillUserData() {
    const user = JSON.parse(sessionStorage.getItem('currentUser') || "{}");
    if (!user) return;

    document.getElementById('patientName').value = user.name || "";
    document.getElementById('patientEmail').value = user.email || "";
    document.getElementById('patientPhone').value = user.phone || "";

    console.log("Auto-filled:", user);
    }



// Override the openModal function to handle appointment modal specifically
// const originalOpenModal = openModal;
// window.openModal = function(modalId) {
//     originalOpenModal(modalId);
    
//     if (modalId === 'appointmentModal') {
//         // Prefill user data if available
//         setTimeout(prefillUserData, 100);
//     }
// };
const originalOpenModal = openModal;
window.openModal = function(modalId) {
    originalOpenModal(modalId);

    if (modalId === 'appointmentModal') {
        setTimeout(() => {
            console.log("Prefilling user data...");
            prefillUserData();
        }, 300); // increased delay to ensure inputs are ready
    }
};


// Disable past time slots if selected date is today
document.addEventListener("DOMContentLoaded", function () {
    const dateInput = document.getElementById("appointmentDate");
    const timeSelect = document.getElementById("appointmentTime");

    if (!dateInput || !timeSelect) return;

    // Allow selecting today
    const today = new Date().toISOString().split('T')[0];
    dateInput.setAttribute('min', today);

    dateInput.addEventListener("change", function () {
        const selectedDate = new Date(this.value);
        if (isNaN(selectedDate.getTime())) return;

        const now = new Date();
        const currentMinutes = now.getHours() * 60 + now.getMinutes();

        const isToday =
            selectedDate.getFullYear() === now.getFullYear() &&
            selectedDate.getMonth() === now.getMonth() &&
            selectedDate.getDate() === now.getDate();

        // Reset all time options
        Array.from(timeSelect.options).forEach(option => {
            option.disabled = false;
            option.style.display = "block";
        });

        let availableTimeFound = false;

        if (isToday) {
            Array.from(timeSelect.options).forEach(option => {
                if (!option.value) return;

                const [h, m] = option.value.split(":").map(Number);
                const optionMinutes = h * 60 + m;

                if (optionMinutes <= currentMinutes) {
                    option.disabled = true;
                    option.style.display = "none"; // hide past time slot
                } else {
                    availableTimeFound = true;
                }
            });

            // If no time slots remain → disable dropdown
            if (!availableTimeFound) {
                timeSelect.disabled = true;
                timeSelect.value = "";
                timeSelect.title = "No available time slots today";
            } else {
                timeSelect.disabled = false;
                timeSelect.title = "";
            }
        } else {
            // For future dates → enable all times
            timeSelect.disabled = false;
            timeSelect.title = "";
        }
    });
});

// 👁 Toggle password visibility in Login Modal
document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.getElementById("toggleLoginPassword");
    const passwordField = document.getElementById("loginPassword");

    if (toggle && passwordField) {
        toggle.addEventListener("click", () => {
            const isHidden = passwordField.type === "password";
            passwordField.type = isHidden ? "text" : "password";
            toggle.className = isHidden ? "fas fa-eye-slash" : "fas fa-eye";
        });
    }
});


console.log('FetoScope Hospital Landing Page - JavaScript Loaded Successfully');
console.log('Available mock users:', mockUsers.map(u => ({ email: u.email, name: u.name })));
