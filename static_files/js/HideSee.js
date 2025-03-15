// <!-- Add the necessary script for toggling password visibility -->

    // Toggle password visibility for password field
    document.getElementById('togglePassword').addEventListener('click', function () {
        var passwordField = document.getElementById('password');
        var type = passwordField.type === "password" ? "text" : "password";
        passwordField.type = type;
        this.classList.toggle('fa-eye-slash');
    });

    // Toggle password visibility for confirm password field
    document.getElementById('toggleConfirmPassword').addEventListener('click', function () {
        var confirmPasswordField = document.getElementById('confirm_password');
        var type = confirmPasswordField.type === "password" ? "text" : "password";
        confirmPasswordField.type = type;
        this.classList.toggle('fa-eye-slash');
    });
