document.addEventListener('DOMContentLoaded', function() {
    var form = document.querySelector('form');
    var firstNameInput = form.querySelector('input[name="firstName"]');
    var lastNameInput = form.querySelector('input[name="lastName"]');
    var emailInput = form.querySelector('input[name="email"]');
    var passwordInput = form.querySelector('input[name="password"]');
    var reEnterPasswordInput = form.querySelector('input[name="re-enter-password"]');

    var firstNameErrorMessage = document.getElementById('first-name-error-message');
    var lastNameErrorMessage = document.getElementById('last-name-error-message');
    var emailErrorMessage = document.getElementById('email-error-message');
    var passwordErrorMessage = document.getElementById('password-error-message');
    var reEnterPasswordErrorMessage = document.getElementById('re-enter-password-error-message');

    function checkPasswordsMatch() {
        return passwordInput.value === reEnterPasswordInput.value;
    }

    function checkInputValidity() {
        var isFirstNameValid = firstNameInput.value.trim() !== '';
        var isLastNameValid = lastNameInput.value.trim() !== '';
        var isEmailValid = emailInput.validity.valid;
        var isPasswordValid = passwordInput.value.trim() !== '';
        var isPasswordsMatch = checkPasswordsMatch();

        firstNameErrorMessage.style.display = isFirstNameValid ? 'none' : 'block';
        lastNameErrorMessage.style.display = isLastNameValid ? 'none' : 'block';
        emailErrorMessage.style.display = isEmailValid ? 'none' : 'block';
        passwordErrorMessage.style.display = isPasswordValid ? 'none' : 'block';
        reEnterPasswordErrorMessage.style.display = isPasswordsMatch ? 'none' : 'block';

        return isFirstNameValid && isLastNameValid && isEmailValid && isPasswordValid && isPasswordsMatch;
    }

    form.addEventListener('submit', function(event) {
        var isFormValid = checkInputValidity();
        if (!isFormValid) {
            event.preventDefault();
        }
    });

    Array.from(form.elements).forEach(function(element) {
        element.addEventListener('input', function() {
            firstNameErrorMessage.style.display = 'none';
            lastNameErrorMessage.style.display = 'none';
            emailErrorMessage.style.display = 'none';
            passwordErrorMessage.style.display = 'none';
            reEnterPasswordErrorMessage.style.display = 'none';
        });
    });
});
