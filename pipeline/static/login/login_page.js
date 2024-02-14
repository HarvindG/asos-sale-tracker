document.addEventListener('DOMContentLoaded', function() {
        var form = document.querySelector('form');
        var submitButton = form.querySelector('button[type="submit"]');
        var emailInput = form.querySelector('input[type="email"]');
        var emailErrorMessage = document.getElementById('email-error-message');
        var passwordErrorMessage = document.getElementById('password-error-message');


        function checkInputValidity() {
            var isEmailValid = emailInput.validity.valid;
            var isPasswordValid = passwordInput.value.trim() !== '';

            emailErrorMessage.style.display = isEmailValid ? 'none' : 'block';
            passwordErrorMessage.style.display = isPasswordValid ? 'none' : 'block';

            return isEmailValid && isPasswordValid;
        }

        form.addEventListener('submit', function(event) {
            var isFormValid = checkInputValidity();
            if (!isFormValid) {
                event.preventDefault();
            }
        });

        Array.from(form.elements).forEach(function(element) {
            element.addEventListener('input', function() {
                emailErrorMessage.style.display = 'none';
                passwordErrorMessage.style.display = 'none';
            });
        });
    });