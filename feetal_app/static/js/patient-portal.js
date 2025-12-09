/* ====================== DASHBOARD JS ====================== */

document.addEventListener("DOMContentLoaded", function () {
    AOS.init({ duration: 800, easing: "ease-in-out", once: true, offset: 100 });
    checkAuthentication();
    initializeUploads();
    loadReportHistory();
    initializeBooking();
    
    // Check if user just logged in and open booking modal
    const shouldOpenBooking = sessionStorage.getItem("openBookingModal");
    if (shouldOpenBooking === "true") {
        sessionStorage.removeItem("openBookingModal");
        setTimeout(() => {
            openModal("appointmentModal");
        }, 500);
    }
});

/* ====================== AUTH SYSTEM ====================== */

function checkAuthentication() {
    const currentUser = sessionStorage.getItem("currentUser");
    if (!currentUser) window.location.href = "/";
    else updateUserInfo(JSON.parse(currentUser));
}
function updateUserInfo(user) {
    const userName = document.getElementById("userName");
    if (userName) userName.textContent = `Welcome, ${user.name.split(" ")[0]}!`;
}
function logout() {
    sessionStorage.clear();
    window.location.href = "/";
}

/* ====================== FILE UPLOAD ====================== */

let uploadedScanningFiles = [];
let uploadedMedicalFiles = [];

function initializeUploads() {
    setupFileUpload(document.getElementById("scanningUpload"), document.getElementById("scanningFiles"), "scanning", (files) => {
        uploadedScanningFiles = files;
        updateCombinedBtnState();
    });
    setupFileUpload(document.getElementById("medicalUpload"), document.getElementById("medicalFiles"), "medical", (files) => {
        uploadedMedicalFiles = files;
        updateCombinedBtnState();
    });
}

function updateCombinedBtnState() {
    document.getElementById("combinedBtn").disabled =
        uploadedScanningFiles.length === 0 || uploadedMedicalFiles.length === 0;
}

function setupFileUpload(uploadArea, fileInput, type, callback) {
    const uploadLink = uploadArea.querySelector(".upload-link");
    let currentFiles = [];
    let isProcessing = false;

    // Prevent double-click by using stopPropagation
    if (uploadLink) {
        uploadLink.addEventListener("click", (e) => {
            e.stopPropagation();
            if (!isProcessing) {
                isProcessing = true;
                fileInput.value = ''; // Reset input to allow selecting same file again
                fileInput.click();
                setTimeout(() => { isProcessing = false; }, 100);
            }
        });
    }

    uploadArea.addEventListener("click", (e) => {
        // Only trigger if clicking directly on the upload area (not on child elements)
        if (e.target === uploadArea || e.target.classList.contains('upload-area')) {
            if (!isProcessing) {
                isProcessing = true;
                fileInput.value = ''; // Reset input to allow selecting same file again
                fileInput.click();
                setTimeout(() => { isProcessing = false; }, 100);
            }
        }
    });

    uploadArea.addEventListener("dragover", (e) => {
        e.preventDefault();
        uploadArea.classList.add("dragover");
    });
    uploadArea.addEventListener("dragleave", () => uploadArea.classList.remove("dragover"));
    uploadArea.addEventListener("drop", (e) => {
        e.preventDefault();
        uploadArea.classList.remove("dragover");
        handleFiles(e.dataTransfer.files);
    });

    fileInput.addEventListener("change", (e) => {
        if (e.target.files && e.target.files.length > 0) {
            handleFiles(e.target.files);
        }
    });

    function handleFiles(files) {
        currentFiles = [...currentFiles, ...Array.from(files)];
        displayFiles(currentFiles);
        callback(currentFiles);
    }

    function displayFiles(files) {
        uploadArea.classList.add("has-files");
        let fileList = uploadArea.querySelector(".file-list");
        if (!fileList) {
            fileList = document.createElement("div");
            fileList.className = "file-list";
            uploadArea.appendChild(fileList);
        }

        fileList.innerHTML = files
            .map((file, i) => `
                <div class="file-item">
                    <div><i class="fas fa-file"></i> ${file.name} (${(file.size / 1024 / 1024).toFixed(2)}MB)</div>
                    <i class="fas fa-times file-remove"></i>
                </div>
        `).join("");

        fileList.querySelectorAll(".file-remove").forEach((btn, index) => {
            btn.addEventListener("click", () => {
                currentFiles.splice(index, 1);
                displayFiles(currentFiles);
                callback(currentFiles);
            });
        });

        if (!files.length) uploadArea.classList.remove("has-files");
    }
}

/* ====================== CSRF ====================== */

function getCookie(name) {
    return document.cookie.split("; ").find((c) => c.startsWith(name + "="))?.split("=")[1];
}

/* ====================== ML INTEGRATION ====================== */

async function processScanningReports(isCombined = false) {
    if (!uploadedScanningFiles.length) {
        if (!isCombined) showNotification("Upload scanning reports first", "error");
        return null;
    }

    showLoadingModal("Analyzing ultrasound / scanning reports…");

    let formData = new FormData();
    uploadedScanningFiles.forEach((file) => formData.append("image", file));

    const response = await fetch("/api/predict/preterm-delivery/", {
        method: "POST",
        headers: { "X-CSRFToken": getCookie("csrftoken") },
        body: formData,
    });

    hideLoadingModal();
    const res = await response.json();
    if (!res.success) return null;

    return {
        overall_risk: res.risk_level,        // 🔥 CORRECT
        confidence: Math.round(res.probability * 100), // 🔥 CORRECT
        findings: [res.prediction],          // show model’s prediction text
        risks: res.risk_level !== "Low Risk" ? [res.risk_level] : []
    };
}


async function processMedicalReports(isCombined = false) {
    // This function is no longer used for combined analysis
    // Medical reports are now processed via combined_analysis_api which extracts values from uploaded files
    if (!isCombined) {
        showNotification("Please use the Combined Analysis option to process medical reports", "error");
    }
    return null;
}

/* ====================== COMBINED ANALYSIS ====================== */

async function processCombinedAnalysis() {
    if (!uploadedScanningFiles.length || !uploadedMedicalFiles.length) {
        showNotification("Upload both scanning and medical reports", "error");
        return;
    }

    showLoadingModal("Analyzing your reports and generating PDF...");

    try {
        // Prepare FormData with actual uploaded files
        const formData = new FormData();
        
        // Add scanning files
        uploadedScanningFiles.forEach((file) => {
            formData.append("scanning_files", file);
        });
        
        // Add medical report files
        uploadedMedicalFiles.forEach((file) => {
            formData.append("medical_files", file);
        });

        // Get current user info
        const currentUser = JSON.parse(sessionStorage.getItem("currentUser"));
        if (currentUser) {
            formData.append("patient_name", currentUser.name);
            formData.append("patient_email", currentUser.email);
        }

        // Call combined analysis API which:
        // - Extracts values from uploaded medical files (TXT/PDF/DOC/DOCX)
        // - Processes scanning images
        // - Generates PDF report
        // - Saves to doctor dashboard
        // - Returns only success message to patient
        const response = await fetch("/api/predict/combined-analysis/", {
        method: "POST",
        headers: {
            "X-CSRFToken": getCookie("csrftoken")
        },
            body: formData
        });

        hideLoadingModal();

        const data = await response.json();

        if (data.success) {
            // Show success message only - patient doesn't see results
            showNotification(data.message || "Your reports were analyzed successfully and forwarded to our medical team. They will review and contact you.", "success");
            
            // Clear uploaded files
            uploadedScanningFiles = [];
            uploadedMedicalFiles = [];
            updateCombinedBtnState();
            
            // Clear file displays
            const scanningUpload = document.getElementById("scanningUpload");
            const medicalUpload = document.getElementById("medicalUpload");
            if (scanningUpload) {
                scanningUpload.classList.remove("has-files");
                const fileList = scanningUpload.querySelector(".file-list");
                if (fileList) fileList.remove();
            }
            if (medicalUpload) {
                medicalUpload.classList.remove("has-files");
                const fileList = medicalUpload.querySelector(".file-list");
                if (fileList) fileList.remove();
            }
            
            // Clear file inputs
            document.getElementById("scanningFiles").value = "";
            document.getElementById("medicalFiles").value = "";
        } else {
            showNotification(data.message || "Analysis failed. Please try again.", "error");
        }
    } catch (error) {
        hideLoadingModal();
        console.error("Combined analysis error:", error);
        showNotification("An error occurred during analysis. Please try again.", "error");
    }
}

/* ====================== RESULT MODAL ====================== */

function showResults(results, type) {
    const modal = document.getElementById("resultModal");
    const modalContent = document.getElementById("resultModalContent");

    // Change circle color based on risk
    let riskColor =
        results.overall_risk === "High Risk" ? "#dc2626" :
        results.overall_risk === "Medium Risk" ? "#eab308" :
        "#10b981";

    modalContent.innerHTML = `
        <div class="result-header">
            <h2>${results.type} Results</h2>
            <button class="close-btn" onclick="closeResultModal()">
                <i class="fas fa-times"></i>
            </button>
        </div>

        <div class="result-score">
            <div class="score-circle" style="background:${riskColor};">${results.confidence}%</div>
            <h3 style="color:${riskColor};">Risk Level: ${results.overall_risk}</h3>
            <p>Confidence Score: ${results.confidence}%</p>
        </div>

        <div class="result-section">
            <h4>Key Findings:</h4>
            <ul>
                ${results.findings.map(f => `<li><i class="fas fa-check"></i> ${f}</li>`).join("")}
            </ul>
        </div>

        ${results.risks?.length > 0 ? `
        <div class="result-section">
            <h4>Identified Risks:</h4>
            <ul>
                ${results.risks.map(r => `<li><i class="fas fa-exclamation-triangle" style="color:#dc2626"></i> ${r}</li>`).join("")}
            </ul>
        </div>` : ""}

        <div class="result-section">
            <h4>Recommendations:</h4>
            <ul>
                ${results.recommendations.map(rc => `<li><i class="fas fa-stethoscope"></i> ${rc}</li>`).join("")}
            </ul>
        </div>
    `;

    modal.style.display = "block";
}


function closeResultModal() {
    document.getElementById("resultModal").style.display = "none";
}

/* ====================== LOADING & NOTIFICATION ====================== */

function showLoadingModal(msg) {
    document.getElementById("loadingText").textContent = msg;
    document.getElementById("loadingModal").style.display = "block";
    document.getElementById("progressFill").style.width = "0%";
    setTimeout(() => document.getElementById("progressFill").style.width = "100%", 80);
}
function hideLoadingModal() {
    document.getElementById("loadingModal").style.display = "none";
}

function showNotification(msg, type = "info") {
    // Create a notification element
    const notification = document.createElement("div");
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === "success" ? "#10b981" : type === "error" ? "#dc2626" : "#2563eb"};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        z-index: 10000;
        font-size: 0.95rem;
        max-width: 400px;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = msg;
    
    document.body.appendChild(notification);
    
    // Remove after 5 seconds
    setTimeout(() => {
        notification.style.animation = "slideOut 0.3s ease";
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

/* ====================== HISTORY ====================== */

function saveToHistory(type, files, results) {
    let history = JSON.parse(localStorage.getItem("analysisHistory") || "[]");
    history.push({ type, date: new Date().toISOString(), results });
    localStorage.setItem("analysisHistory", JSON.stringify(history));
    loadReportHistory();
}

function loadReportHistory() {
    let history = JSON.parse(localStorage.getItem("analysisHistory") || "[]");
    const container = document.getElementById("reportsHistory");
    container.innerHTML = "";

    if (!history.length) {
        container.innerHTML = `
            <div class="no-reports">
                <i class="fas fa-clipboard-list"></i>
                <h3>No Reports Yet</h3>
                <p>Upload your first report to begin analysis</p>
            </div>`;
        return;
    }

    history.forEach((item) => {
        container.innerHTML += `
            <div class="report-card">
                <h4>${item.type}</h4>
                <p>${new Date(item.date).toLocaleString()}</p>
                <button onclick='showResults(${JSON.stringify(item.results)})'>View Report</button>
            </div>`;
    });
}

/* ====================== MODAL FUNCTIONS ====================== */

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
        
        // Add animation class
        const modalContent = modal.querySelector('.modal-content');
        if (modalContent) {
            modalContent.style.animation = 'modalSlideIn 0.3s ease';
        }
        
        // If it's the appointment modal, initialize it
        if (modalId === 'appointmentModal') {
            initializeBooking();
        }
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        modal.classList.remove('active');
        
        // Remove any modal overlay
        const overlay = document.querySelector('.modal-overlay');
        if (overlay) {
            overlay.remove();
        }
        
        // Ensure body scroll is enabled
        document.body.style.overflow = 'auto';
        document.body.style.position = '';
        document.body.style.width = '';
        
        // Clear form inputs
        const form = modal.querySelector('form');
        if (form) {
            form.reset();
        }
        
        // Clear error messages
        const errorMessages = modal.querySelectorAll('.error-message, .success-message, .appointment-success');
        errorMessages.forEach(msg => msg.remove());
        
        // Remove any backdrop
        const backdrop = document.querySelector('.modal-backdrop');
        if (backdrop) {
            backdrop.remove();
        }
    }
}

// Close modal when clicking outside or on close button
window.addEventListener('click', function(event) {
    if (event.target.classList.contains('modal')) {
        closeModal(event.target.id);
    }
    // Close button
    if (event.target.classList.contains('close-modal') || event.target.closest('.close-modal')) {
        const modal = event.target.closest('.modal');
        if (modal) {
            closeModal(modal.id);
        }
    }
});

// Close modal with Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const openModal = document.querySelector('.modal[style*="block"], .modal.active');
        if (openModal) {
            closeModal(openModal.id);
        }
    }
});

/* ====================== BOOKING SYSTEM ====================== */

function initializeBooking() {
    // Set minimum date to today
    const dateInput = document.getElementById("appointmentDate");
    if (dateInput) {
        const today = new Date().toISOString().split("T")[0];
        dateInput.setAttribute("min", today);
    }
    
    // Pre-fill user information if available
    const currentUser = sessionStorage.getItem("currentUser");
    if (currentUser) {
        try {
            const user = JSON.parse(currentUser);
            const emailInput = document.getElementById("patientEmail");
            const nameInput = document.getElementById("patientName");
            if (emailInput) emailInput.value = user.email || "";
            if (nameInput) nameInput.value = user.name || "";
        } catch (e) {
            console.error("Error parsing user data:", e);
        }
    }
}

async function updateDoctorsList() {
    const departmentSelect = document.getElementById("appointmentDepartment");
    const doctorSelect = document.getElementById("appointmentDoctor");
    if (!departmentSelect || !doctorSelect) return;
    
    const selectedDepartment = departmentSelect.value;
    
    // Clear and reset doctor dropdown
    doctorSelect.innerHTML = '<option value="">Loading doctors...</option>';
    doctorSelect.disabled = true;
    
    if (!selectedDepartment) {
        doctorSelect.innerHTML = '<option value="">Select a department first</option>';
        return;
    }
    
    try {
        // Map department values to specialization codes
        // If "all" is selected, don't pass specialization parameter to get all doctors
        const specialization = selectedDepartment === 'all' ? '' : selectedDepartment;
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
            data.doctors.forEach(doctor => {
                const option = document.createElement('option');
                option.value = doctor.id;
                // Show doctor name with specialization
                option.textContent = `${doctor.name} - ${doctor.specialization}`;
                doctorSelect.appendChild(option);
            });
            doctorSelect.disabled = false;
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

function validateAppointmentForm(formData) {
    if (!formData.patientName || !formData.patientPhone || !formData.patientEmail || 
        !formData.patientAge || !formData.doctor || !formData.date || 
        !formData.time || !formData.reason || !formData.terms) {
        showNotification("Please fill in all required fields.");
        return false;
    }
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.patientEmail)) {
        showNotification("Please enter a valid email address.");
        return false;
    }
    
    return true;
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
            doctor: parseInt(formData.doctor),
            date: formData.date,
            time: formData.time,
            reason: formData.reason,
            notes: formData.notes || ''
        };
        
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
            
            // Re-initialize booking to set min date again
            initializeBooking();
            
            // Close modal after delay and redirect to patient portal page
            setTimeout(() => {
                closeModal('appointmentModal');
                // Redirect to patient portal page to show the main content
                window.location.href = '/patient-portal/';
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
    if (selectedDate <= today) {
        showError('appointmentModal', 'Please select a future date for your appointment.');
        return false;
    }
    
    // Validate terms
    if (!data.terms) {
        showError('appointmentModal', 'Please agree to the Terms and Conditions to proceed.');
        return false;
    }
    
    return true;
}

function showError(modalId, message) {
    const modal = document.getElementById(modalId);
    if (!modal) {
        console.error(`Modal with id "${modalId}" not found`);
        alert(message);
        return;
    }
    
    const form = modal.querySelector('.auth-form') || modal.querySelector('.appointment-form') || modal.querySelector('form');
    
    if (!form) {
        console.error('Form not found in modal');
        alert(message);
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
        const [hours, minutes] = data.time.split(':');
        const hour = parseInt(hours);
        const ampm = hour >= 12 ? 'PM' : 'AM';
        const displayHour = hour % 12 || 12;
        formattedTime = `${displayHour}:${minutes} ${ampm}`;
    } else if (data.appointment && data.appointment.time) {
        formattedTime = data.appointment.time;
    }
    
    successDiv.innerHTML = `
        <div style="font-size: 3rem; margin-bottom: 1rem;">✓</div>
        <h3 style="margin-bottom: 1rem; font-size: 1.5rem;">Appointment Booked Successfully!</h3>
        <p style="margin-bottom: 0.5rem;"><strong>Date:</strong> ${formattedDate}</p>
        <p style="margin-bottom: 0.5rem;"><strong>Time:</strong> ${formattedTime}</p>
        ${data.appointment && data.appointment.doctor ? `<p style="margin-bottom: 1rem;"><strong>Doctor:</strong> ${data.appointment.doctor}</p>` : ''}
        <p style="font-size: 0.9rem; opacity: 0.9;">You will receive a confirmation email shortly.</p>
    `;
    
    form.insertBefore(successDiv, form.firstChild);
    successDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}
