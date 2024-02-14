document.addEventListener('DOMContentLoaded', function() {
        var form = document.querySelector('form');
        var submitButton = form.querySelector('button[type="submit"]');
        var urlInput = form.querySelector('input[type="url"]');
        var urlErrorMessage = document.getElementById('error-message');
        var validWebsites = ["www.asos.com"];

        function getDomain(url) {
            var hostname;
            if (url.indexOf("://") > -1) {
                hostname = url.split('/')[2];
            } else {
                hostname = url.split('/')[0];
            }
            hostname = hostname.split(':')[0];
            hostname = hostname.split('?')[0];
            return hostname;
        }

        function checkInputValidity() {
            var urlDomain = getDomain(urlInput.value);
            var isUrlValid = validWebsites.includes(urlDomain) && urlInput.value.trim() !== '';

            urlErrorMessage.style.display = isUrlValid ? 'none' : 'block';

            return isUrlValid;
        }

        form.addEventListener('submit', function(event) {
            var isFormValid = checkInputValidity();
            if (!isFormValid) {
                event.preventDefault();
            }
        });

        Array.from(form.elements).forEach(function(element) {
            element.addEventListener('input', function() {
                urlErrorMessage.style.display = 'none';
            });
        });
    });