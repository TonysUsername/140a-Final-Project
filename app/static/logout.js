document.addEventListener("DOMContentLoaded", () => {
    const logoutButton = document.getElementById("logout-button");

    if (logoutButton) {
        logoutButton.addEventListener("click", async (event) => {
            event.preventDefault();

            // Show loading indicator
            logoutButton.disabled = true;
            logoutButton.textContent = "Logging out...";

            try {
                // Send a POST request to the logout endpoint
                const response = await fetch("/logout", {
                    method: "POST",
                    headers: {
                        'Content-Type': 'application/json',
                    },
                });

                if (response.ok) {
                    // If logout is successful, redirect to the homepage
                    window.location.href = "/"; // Redirect to the homepage
                } else {
                    // Display an error message if logout fails
                    const errorText = await response.text();
                    alert(`Logout failed: ${errorText || "Unknown error"}`);
                }
            } catch (error) {
                console.error("Logout failed:", error);
                alert("An error occurred during logout. Please try again.");
            } finally {
                // Re-enable the button and reset its text
                logoutButton.disabled = false;
                logoutButton.textContent = "Logout";
            }
        });
    }
});