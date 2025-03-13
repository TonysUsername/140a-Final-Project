const wardrobeContainer = document.getElementById("wardrobeContainer");
const addClothingBtn = document.getElementById("addClothingBtn");
const modal = document.getElementById("clothingModal");
const closeModal = document.querySelector(".close");
const saveClothingBtn = document.getElementById("saveClothingBtn");
const clothingNameInput = document.getElementById("clothingName");
const clothingTypeInput = document.getElementById("clothingType");
const clothingSeasonInput = document.getElementById("clothingSeason");
const clothingColorInput = document.getElementById("clothingColor");
const getRecommendationBtn = document.getElementById("getRecommendationBtn");
const recommendationResult = document.getElementById("recommendationResult");

// Load wardrobe from localStorage
let wardrobe = JSON.parse(localStorage.getItem("wardrobe")) || [];

// Function to render wardrobe
function renderWardrobe() {
    wardrobeContainer.innerHTML = "";

    if (wardrobe.length === 0) {
        wardrobeContainer.innerHTML = "<p class='empty-message'>Your wardrobe is empty!</p>";
    } else {
        wardrobe.forEach((item, index) => {
            const card = document.createElement("div");
            card.classList.add("clothing-card");

            // Get emoji for clothing type
            let typeEmoji = "👕";
            if (item.type === "Pants") typeEmoji = "👖";
            else if (item.type === "Dress") typeEmoji = "👗";
            else if (item.type === "Jacket") typeEmoji = "🧥";
            else if (item.type === "Shoes") typeEmoji = "👟";
            else if (item.type === "Hat") typeEmoji = "🧢";
            else if (item.type === "Accessory") typeEmoji = "💍";

            card.innerHTML = `
                <div class="card-image">
                    <img src="${item.image || '/static/images/placeholder.png'}" alt="${item.name}">
                </div>
                <div class="card-content">
                    <h3>${item.name}</h3>
                    <p>${typeEmoji} ${item.type}</p>
                    <p><span class="label">Color:</span> ${item.color || 'N/A'}</p>
                    <p><span class="label">Season:</span> ${item.season || 'All Seasons'}</p>
                    <div class="card-actions">
                        <button class="edit-btn" onclick="editClothing(${index})">Edit</button>
                        <button class="remove-btn" onclick="removeClothing(${index})">Remove</button>
                    </div>
                </div>
            `;

            wardrobeContainer.appendChild(card);
        });
    }

    // Save updated wardrobe to localStorage
    localStorage.setItem("wardrobe", JSON.stringify(wardrobe));
    
    // Also save to server (if available)
    saveWardrobeToServer();
}

// Function to save wardrobe to server
async function saveWardrobeToServer() {
    try {
        const response = await fetch("/api/save-wardrobe", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ wardrobe }),
        });

        if (!response.ok) {
            console.error("Failed to save wardrobe to server");
        }
    } catch (error) {
        console.error("Error saving to server:", error);
    }
}

// Function to remove clothing
function removeClothing(index) {
    if (confirm("Are you sure you want to remove this item?")) {
        wardrobe.splice(index, 1);
        renderWardrobe();
    }
}

// Function to edit clothing
function editClothing(index) {
    const item = wardrobe[index];
    
    // Populate the modal inputs with existing values
    clothingNameInput.value = item.name;
    clothingTypeInput.value = item.type;
    clothingSeasonInput.value = item.season || "";
    clothingColorInput.value = item.color || "";
    
    // Show the modal
    modal.style.display = "block";
    
    // Update save button to handle edit
    saveClothingBtn.setAttribute("data-edit-index", index);
    saveClothingBtn.textContent = "Update";
}

// Show modal on add click
addClothingBtn.addEventListener("click", () => {
    // Reset form fields
    clothingNameInput.value = "";
    clothingTypeInput.value = "";
    clothingSeasonInput.value = "";
    clothingColorInput.value = "";
    
    // Reset save button
    saveClothingBtn.removeAttribute("data-edit-index");
    saveClothingBtn.textContent = "Save";
    
    modal.style.display = "block";
});

// Close modal
closeModal.addEventListener("click", () => {
    modal.style.display = "none";
});

// Close modal if clicked outside of modal
window.addEventListener("click", (event) => {
    if (event.target === modal) {
        modal.style.display = "none";
    }
});

// Save or update clothing
saveClothingBtn.addEventListener("click", async () => {
    const name = clothingNameInput.value.trim();
    const type = clothingTypeInput.value.trim();
    const season = clothingSeasonInput.value.trim();
    const color = clothingColorInput.value.trim();
    const editIndex = saveClothingBtn.getAttribute("data-edit-index");

    if (name && type) {
        try {
            // Show loading state
            saveClothingBtn.textContent = "Saving...";
            saveClothingBtn.disabled = true;
            
            // Get image URL - either generate new one or keep existing
            let imageUrl;
            if (editIndex !== null) {
                // Editing existing item - keep the same image
                imageUrl = wardrobe[editIndex].image;
            } else {
                // New item - generate an image
                try {
                    imageUrl = await generateImage(`${color} ${type} ${name}`);
                } catch (error) {
                    console.error("Failed to generate image:", error);
                    imageUrl = "/static/images/placeholder.png";
                }
            }

            if (editIndex !== null) {
                // Update existing item
                wardrobe[editIndex] = { 
                    name, 
                    type, 
                    season, 
                    color, 
                    image: imageUrl 
                };
            } else {
                // Add new item
                wardrobe.push({ 
                    name, 
                    type, 
                    season, 
                    color, 
                    image: imageUrl 
                });
            }
            
            renderWardrobe();
            modal.style.display = "none";

        } catch (error) {
            alert("Error: " + error.message);
        } finally {
            // Reset button state
            saveClothingBtn.textContent = "Save";
            saveClothingBtn.disabled = false;
        }
    } else {
        alert("Please fill out at least name and type!");
    }
});

async function generateImage(itemName) {
    // First try the AI API
    try {
        const response = await fetch("/api/generate-image/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ item_name: itemName }),
        });

        if (!response.ok) {
            throw new Error("Failed to generate image");
        }

        const data = await response.json();
        return data.image_url;
    } catch (error) {
        console.error("AI image generation failed:", error);
        
        // Fallback to placeholders
        const type = clothingTypeInput.value.toLowerCase();
        let placeholderPath = "/static/images/";
        
        if (type.includes("shirt")) placeholderPath += "shirt.png";
        else if (type.includes("pant")) placeholderPath += "pants.png";
        else if (type.includes("dress")) placeholderPath += "dress.png";
        else if (type.includes("jacket")) placeholderPath += "jacket.png";
        else if (type.includes("shoe")) placeholderPath += "shoes.png";
        else placeholderPath += "clothing.png";
        
        return placeholderPath;
    }
}

// Get clothing recommendation based on weather
getRecommendationBtn?.addEventListener("click", async () => {
    const temperature = document.getElementById("temperatureInput").value;
    const humidity = document.getElementById("humidityInput").value;
    
    if (!temperature || !humidity) {
        alert("Please enter both temperature and humidity values");
        return;
    }
    
    try {
        // Show loading state
        recommendationResult.innerHTML = "<p>Getting recommendation...</p>";
        getRecommendationBtn.disabled = true;
        
        // Try to get recommendation from server
        try {
            const recommendation = await getRecommendation(temperature, humidity);
            
            // Display the recommendation
            recommendationResult.innerHTML = `
                <div class="recommendation-card">
                    <h3>Today's Outfit Recommendation</h3>
                    <p>${recommendation}</p>
                </div>
            `;
        } catch (error) {
            // Fallback to local recommendation if server fails
            const localRecommendation = generateLocalRecommendation(temperature, humidity);
            
            recommendationResult.innerHTML = `
                <div class="recommendation-card">
                    <h3>Today's Outfit Recommendation</h3>
                    <p>${localRecommendation}</p>
                    <small>(Generated locally - connect to server for better recommendations)</small>
                </div>
            `;
        }
    } catch (error) {
        recommendationResult.innerHTML = `
            <div class="recommendation-card error">
                <p>Error getting recommendation: ${error.message}</p>
            </div>
        `;
    } finally {
        getRecommendationBtn.disabled = false;
    }
});

// Function to get clothing recommendation from server
async function getRecommendation(temperature, humidity) {
    const response = await fetch("/api/recommendation/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ 
            temperature: parseFloat(temperature), 
            humidity: parseFloat(humidity),
            wardrobe: wardrobe  // Send wardrobe data for personalized recommendations
        }),
    });

    if (!response.ok) {
        throw new Error("Failed to get recommendation");
    }

    const data = await response.json();
    return data.result.response;
}

// Fallback function for local recommendations
function generateLocalRecommendation(temperature, humidity) {
    const temp = parseFloat(temperature);
    
    if (temp < 5) {
        return "It's very cold! Wear a heavy winter coat, scarf, gloves, and a warm hat.";
    } else if (temp < 15) {
        return "It's cold. A jacket or light coat with a sweater would be appropriate.";
    } else if (temp < 25) {
        return "The weather is mild. Consider wearing long sleeves or a light sweater.";
    } else if (temp < 30) {
        return "It's warm. Short sleeves and light pants or skirts are recommended.";
    } else {
        return "It's hot! Wear light, breathable clothes like shorts and a t-shirt.";
    }
}

// Initial render
document.addEventListener("DOMContentLoaded", () => {
    // Load wardrobe from server first, fall back to localStorage
    fetch("/api/get-wardrobe")
        .then(response => {
            if (!response.ok) {
                throw new Error("Failed to get wardrobe from server");
            }
            return response.json();
        })
        .then(data => {
            if (data.wardrobe && data.wardrobe.length > 0) {
                wardrobe = data.wardrobe;
                localStorage.setItem("wardrobe", JSON.stringify(wardrobe));
            }
            renderWardrobe();
        })
        .catch(error => {
            console.error("Using local wardrobe:", error);
            renderWardrobe();
        });
});