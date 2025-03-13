const wardrobeContainer = document.getElementById("wardrobeContainer");
const addClothingBtn = document.getElementById("addClothingBtn");
const modal = document.getElementById("clothingModal");
const closeModal = document.querySelector(".close");
const saveClothingBtn = document.getElementById("saveClothingBtn");
const clothingNameInput = document.getElementById("clothingName");
const clothingTypeInput = document.getElementById("clothingType");
const clothingSeasonInput = document.getElementById("clothingSeason");
const clothingColorInput = document.getElementById("clothingColor");
const clothingImageUrlInput = document.getElementById("clothingImageUrl");

// Load wardrobe from localStorage
let wardrobe = JSON.parse(localStorage.getItem("wardrobe")) || [];

// Function to get emoji for clothing type
function getClothingEmoji(type) {
    switch (type) {
        case "Shirt": return "👕";
        case "Pants": return "👖";
        case "Dress": return "👗";
        case "Jacket": return "🧥";
        case "Shoes": return "👟";
        case "Hat": return "🧢";
        case "Accessory": return "💍";
        default: return "👕";
    }
}

// Function to get emoji for color
function getColorEmoji(color) {
    switch (color) {
        case "Black": return "⚫";
        case "White": return "⚪";
        case "Red": return "🔴";
        case "Blue": return "🔵";
        case "Green": return "🟢";
        case "Yellow": return "🟡";
        case "Purple": return "🟣";
        case "Brown": return "🟤";
        case "Pink": return "💖";
        case "Orange": return "🟠";
        case "Gray": return "⚪";
        default: return "";
    }
}

// Function to render wardrobe
function renderWardrobe() {
    wardrobeContainer.innerHTML = "";

    if (wardrobe.length === 0) {
        wardrobeContainer.innerHTML = "<p class='empty-message'>Your wardrobe is empty!</p>";
    } else {
        // Create a wrapper for the grid
        const gridWrapper = document.createElement("div");
        gridWrapper.classList.add("clothing-grid");
        
        wardrobe.forEach((item, index) => {
            const card = document.createElement("div");
            card.classList.add("clothing-card");
            card.setAttribute("data-index", index);
            
            // Add animation class
            card.classList.add("card-animation");

            // Get emoji for clothing type
            const typeEmoji = getClothingEmoji(item.type);
            const colorEmoji = getColorEmoji(item.color);

            // Determine whether to show an image or the emoji display
            const imageDisplay = item.imageUrl ? 
                `<div class="image-display">
                    <img src="${item.imageUrl}" alt="${item.name}" onerror="this.onerror=null; this.src=''; this.parentElement.innerHTML='<span class=\\'item-emoji\\'>${typeEmoji}</span><span class=\\'color-emoji\\'>${colorEmoji}</span>';">
                </div>` : 
                `<div class="emoji-display">
                    <span class="item-emoji">${typeEmoji}</span>
                    <span class="color-emoji">${colorEmoji}</span>
                </div>`;

            card.innerHTML = `
                ${imageDisplay}
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

            gridWrapper.appendChild(card);
        });
        
        wardrobeContainer.appendChild(gridWrapper);
    }

    // Ensure the addClothingBtn stays visible at the bottom of the page
    ensureAddButtonVisible();

    // Save updated wardrobe to localStorage
    localStorage.setItem("wardrobe", JSON.stringify(wardrobe));
    
    // Also save to server (if available)
    saveWardrobeToServer();
}

// Function to ensure the add button is always visible
function ensureAddButtonVisible() {
    // Make sure the button is positioned fixed at the bottom right
    addClothingBtn.classList.add("fixed-add-btn");
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
    clothingImageUrlInput.value = item.imageUrl || "";
    
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
    clothingImageUrlInput.value = "";
    
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
saveClothingBtn.addEventListener("click", () => {
    const name = clothingNameInput.value.trim();
    const type = clothingTypeInput.value.trim();
    const season = clothingSeasonInput.value.trim();
    const color = clothingColorInput.value.trim();
    const imageUrl = clothingImageUrlInput.value.trim();
    const editIndex = saveClothingBtn.getAttribute("data-edit-index");

    if (name && type) {
        try {
            // Show loading state
            saveClothingBtn.textContent = "Saving...";
            saveClothingBtn.disabled = true;
            
            if (editIndex !== null) {
                // Update existing item
                wardrobe[editIndex] = { 
                    name, 
                    type, 
                    season, 
                    color,
                    imageUrl
                };
            } else {
                // Add new item
                wardrobe.push({ 
                    name, 
                    type, 
                    season, 
                    color,
                    imageUrl
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

// Initial render
document.addEventListener("DOMContentLoaded", () => {
    // Make sure the add button is always visible
    ensureAddButtonVisible();
    
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