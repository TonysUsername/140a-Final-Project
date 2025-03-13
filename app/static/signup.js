
document.getElementById("signupForm").addEventListener("submit", function(event) {
    event.preventDefault();

    const name = document.getElementById("name").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value.trim();
    const location = document.getElementById("location").value.trim();
    const errorMessage = document.getElementById("errorMessage");

    errorMessage.textContent = "";

    if (!name || !email || !password || !location) {
        errorMessage.textContent = "All fields are required!";
        return;
    }

    if (!validateEmail(email)) {
        errorMessage.textContent = "Invalid email format!";
        return;
    }

    if (password.length < 6) {
        errorMessage.textContent = "Password must be at least 6 characters long!";
        return;
    }

    alert("Signup successful!");
    // Here, you can send data to the backend or store it in localStorage.
});

function validateEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}
