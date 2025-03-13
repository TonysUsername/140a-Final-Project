document.getElementById("login-form").addEventListener("submit", async (event) => {
    event.preventDefault();

    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    // Show loading indicator
    const loginButton = document.querySelector("button[type='submit']");
    loginButton.disabled = true;
    loginButton.textContent = "Logging in...";

    try {
        // Create FormData and use URLSearchParams to ensure correct content type
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        const response = await fetch("/login", {
            method: "POST",
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData
        });

        if (response.ok) {
            // If login is successful, redirect to user page
            window.location.href = `/user/${username}`;
        } else {
            // Try to get error text
            const errorText = await response.text();
            
            // Display error message
            const errorDiv = document.createElement("div");
            errorDiv.classList.add("error-message");
            errorDiv.textContent = errorText || "Login failed. Please try again.";
            
            // Remove any existing error messages first
            const existingError = document.querySelector(".error-message");
            if (existingError) {
                existingError.remove();
            }
            
            document.querySelector(".login-container").appendChild(errorDiv);
        }
    } catch (error) {
        console.error("Login failed:", error);
        const errorDiv = document.createElement("div");
        errorDiv.classList.add("error-message");
        errorDiv.textContent = "An error occurred. Please try again.";
        document.querySelector(".login-container").appendChild(errorDiv);
    } finally {
        // Re-enable button and reset text
        loginButton.disabled = false;
        loginButton.textContent = "Login";
    }
});