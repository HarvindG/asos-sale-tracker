function getUserEmail() {
            var userEmail = document.getElementById('userEmail').value;
            console.log(userEmail)
            return userEmail
        }
        function deleteItem(element, productName, size) {
            var userEmail = getUserEmail()
            if (confirm("Are you sure you want to unsubscribe from receiving notifications for this product?")) {
                var xhr_request = new XMLHttpRequest();
                xhr_request.open("POST", "/delete_subscription", true);
                xhr_request.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
                xhr_request.onreadystatechange = function() {
                    if (this.readyState == XMLHttpRequest.DONE && this.status == 200) {
                        element.parentNode.parentNode.remove();
                        window.location.reload()
                    }
                }
                xhr_request.send("product_name=" + encodeURIComponent(productName) + "&user_email=" + encodeURIComponent(userEmail) + "&size=" + encodeURIComponent(size));
            }
        }
        function deleteAllItems(element, productName, size) {
            var userEmail = getUserEmail()
            var xhr_request = new XMLHttpRequest();
            xhr_request.open("POST", "/delete_subscription", true);
            xhr_request.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
            xhr_request.onreadystatechange = function() {
                if (this.readyState == XMLHttpRequest.DONE && this.status == 200) {
                    element.parentNode.parentNode.remove();
                    window.location.reload()
                }
            }
            xhr_request.send("product_name=" + encodeURIComponent(productName) + "&user_email=" + encodeURIComponent(userEmail) + "&size=" + encodeURIComponent(size));
        }
function deleteAllProducts() {
    if (confirm("Are you sure you want to unsubscribe from all products?")) {
        var table = document.querySelector('table tbody');
        Array.from(table.rows).forEach(row => {
            var productName = row.cells[1].textContent.trim();
            var size = row.cells[3].textContent.trim();
            var button = row.cells[0].getElementsByTagName('button')[0];
            deleteAllItems(button, productName, size);
        });
    }
}
