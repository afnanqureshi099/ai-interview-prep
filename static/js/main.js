/**
 * Main Application JavaScript
 * Handles Theme Toggling, Client-Side Form Validations, Real-Time Password Checklist,
 * and Presentation Quick-Fill Helpers.
 */

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initPasswordToggles();
    initDemoCredentialsFill();
    initRegistrationValidation();
    initDomainSelectionUI();
});

/* ==========================================================================
   1. Theme Management (Dark / Light Mode)
   ========================================================================== */
function initTheme() {
    const themeBtn = document.getElementById('themeToggleBtn');
    if (!themeBtn) return;

    const savedTheme = localStorage.getItem('app-theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);

    themeBtn.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('app-theme', newTheme);
        updateThemeIcon(newTheme);
    });
}

function updateThemeIcon(theme) {
    const themeBtn = document.getElementById('themeToggleBtn');
    if (!themeBtn) return;
    const iconSpan = themeBtn.querySelector('.theme-icon');
    if (iconSpan) {
        iconSpan.textContent = theme === 'light' ? '☀️' : '🌙';
    }
}

/* ==========================================================================
   2. Password Visibility Toggles
   ========================================================================== */
function initPasswordToggles() {
    const toggleBtns = [
        { btnId: 'togglePasswordBtn', inputId: 'password' },
        { btnId: 'toggleLoginPasswordBtn', inputId: 'loginPassword' }
    ];

    toggleBtns.forEach(({ btnId, inputId }) => {
        const btn = document.getElementById(btnId);
        const input = document.getElementById(inputId);
        if (btn && input) {
            btn.addEventListener('click', () => {
                if (input.type === 'password') {
                    input.type = 'text';
                    btn.textContent = '🙈';
                } else {
                    input.type = 'password';
                    btn.textContent = '👁️';
                }
            });
        }
    });
}

/* ==========================================================================
   3. Quick-Fill Presentation Demo Credentials
   ========================================================================== */
function initDemoCredentialsFill() {
    const fillCandidateBtn = document.getElementById('fillCandidateBtn');
    const fillAdminBtn = document.getElementById('fillAdminBtn');
    const emailInput = document.getElementById('loginEmail');
    const passwordInput = document.getElementById('loginPassword');

    if (fillCandidateBtn && emailInput && passwordInput) {
        fillCandidateBtn.addEventListener('click', () => {
            emailInput.value = 'candidate@interviewprep.ai';
            passwordInput.value = 'Candidate@123';
            emailInput.focus();
        });
    }

    if (fillAdminBtn && emailInput && passwordInput) {
        fillAdminBtn.addEventListener('click', () => {
            emailInput.value = 'admin@interviewprep.ai';
            passwordInput.value = 'Admin@12345';
            emailInput.focus();
        });
    }
}

/* ==========================================================================
   4. Strict Registration Form Validation & Real-Time Password Checklist
   ========================================================================== */
function initRegistrationValidation() {
    const form = document.getElementById('registerForm');
    if (!form) return;

    const nameInput = document.getElementById('fullName');
    const emailInput = document.getElementById('email');
    const phoneInput = document.getElementById('phone');
    const passwordInput = document.getElementById('password');
    const confirmInput = document.getElementById('confirmPassword');
    const submitBtn = document.getElementById('submitRegisterBtn');

    // Checklist Elements
    const reqLength = document.getElementById('req-length');
    const reqUpper = document.getElementById('req-upper');
    const reqLower = document.getElementById('req-lower');
    const reqNumber = document.getElementById('req-number');
    const reqSpecial = document.getElementById('req-special');

    // Restrict phone input to numeric only as user types
    if (phoneInput) {
        phoneInput.addEventListener('input', (e) => {
            e.target.value = e.target.value.replace(/\D/g, '').slice(0, 10);
            validateAll();
        });
    }

    // Attach listeners
    [nameInput, emailInput, phoneInput, confirmInput].forEach(inp => {
        if (inp) {
            inp.addEventListener('input', validateAll);
            inp.addEventListener('blur', validateAll);
        }
    });

    if (passwordInput) {
        passwordInput.addEventListener('input', () => {
            updatePasswordChecklist(passwordInput.value);
            validateAll();
        });
    }

    function updatePasswordChecklist(pwd) {
        const hasLength = pwd.length >= 8;
        const hasUpper = /[A-Z]/.test(pwd);
        const hasLower = /[a-z]/.test(pwd);
        const hasNumber = /[0-9]/.test(pwd);
        const hasSpecial = /[!@#$%^&*]/.test(pwd);

        toggleRequirement(reqLength, hasLength);
        toggleRequirement(reqUpper, hasUpper);
        toggleRequirement(reqLower, hasLower);
        toggleRequirement(reqNumber, hasNumber);
        toggleRequirement(reqSpecial, hasSpecial);

        return hasLength && hasUpper && hasLower && hasNumber && hasSpecial;
    }

    function toggleRequirement(elem, isValid) {
        if (!elem) return;
        const icon = elem.querySelector('.check-icon');
        if (isValid) {
            elem.classList.add('valid');
            if (icon) icon.textContent = '✓';
        } else {
            elem.classList.remove('valid');
            if (icon) icon.textContent = '✕';
        }
    }

    function validateAll() {
        let isFormValid = true;

        // 1. Name: Letters & spaces only, min 3 chars
        const nameVal = nameInput ? nameInput.value.trim() : '';
        const nameRegex = /^[A-Za-z ]{3,60}$/;
        const nameFeedback = document.getElementById('nameFeedback');
        if (nameRegex.test(nameVal)) {
            setInputState(nameInput, nameFeedback, true, 'Name looks great!');
        } else {
            setInputState(nameInput, nameFeedback, false, 'Letters and spaces only, minimum 3 characters.');
            isFormValid = false;
        }

        // 2. Email: RFC standard email regex
        const emailVal = emailInput ? emailInput.value.trim() : '';
        const emailRegex = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/;
        const emailFeedback = document.getElementById('emailFeedback');
        if (emailRegex.test(emailVal)) {
            setInputState(emailInput, emailFeedback, true, 'Valid email format.');
        } else {
            setInputState(emailInput, emailFeedback, false, 'Please enter a valid email address.');
            isFormValid = false;
        }

        // 3. Phone: Exactly 10 digits
        const phoneVal = phoneInput ? phoneInput.value.trim() : '';
        const phoneRegex = /^\d{10}$/;
        const phoneFeedback = document.getElementById('phoneFeedback');
        if (phoneRegex.test(phoneVal)) {
            setInputState(phoneInput, phoneFeedback, true, '10-digit number verified.');
        } else {
            setInputState(phoneInput, phoneFeedback, false, 'Contact number must be exactly 10 digits.');
            isFormValid = false;
        }

        // 4. Password Criteria
        const pwdVal = passwordInput ? passwordInput.value : '';
        const isPwdValid = updatePasswordChecklist(pwdVal);
        if (!isPwdValid) {
            isFormValid = false;
        }

        // 5. Confirm Password
        const confirmVal = confirmInput ? confirmInput.value : '';
        const confirmFeedback = document.getElementById('confirmFeedback');
        if (confirmVal && confirmVal === pwdVal) {
            setInputState(confirmInput, confirmFeedback, true, 'Passwords match.');
        } else {
            setInputState(confirmInput, confirmFeedback, false, 'Passwords must match.');
            isFormValid = false;
        }

        // Toggle submit button state
        if (submitBtn) {
            submitBtn.disabled = !isFormValid;
        }
    }

    function setInputState(input, feedbackElem, isValid, message) {
        if (!input) return;
        if (input.value.length === 0) {
            input.classList.remove('is-valid', 'is-invalid');
            if (feedbackElem) {
                feedbackElem.classList.remove('valid', 'invalid');
            }
            return;
        }

        if (isValid) {
            input.classList.add('is-valid');
            input.classList.remove('is-invalid');
            if (feedbackElem) {
                feedbackElem.classList.add('valid');
                feedbackElem.classList.remove('invalid');
                feedbackElem.textContent = message;
            }
        } else {
            input.classList.add('is-invalid');
            input.classList.remove('is-valid');
            if (feedbackElem) {
                feedbackElem.classList.add('invalid');
                feedbackElem.classList.remove('valid');
                feedbackElem.textContent = message;
            }
        }
    }
}

/* ==========================================================================
   5. Dashboard Domain Radio UI Interaction
   ========================================================================== */
function initDomainSelectionUI() {
    const radioCards = document.querySelectorAll('.domain-radio-grid .radio-card');
    radioCards.forEach(card => {
        card.addEventListener('click', () => {
            radioCards.forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
        });
    });
}
