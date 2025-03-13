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
}

// Function to ensure the add button is always visible
function ensureAddButtonVisible() {
    // Make sure the button is positioned fixed at the bottom right
    addClothingBtn.classList.add("fixed-add-btn");
}

// Function to save wardrobe item to server
async function saveItemToServer(item) {
    // Skip items that already have an ID (they're already in the database)
    if (item.id) return item.id;
    
    try {
        const response = await fetch("/api/wardrobe", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                itemName: item.name,         // Match API expectation
                category: item.type,         // Match API expectation
                imageUrl: item.imageUrl
                // Remove userId - your backend gets this from the session
            }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            console.error("Server error:", errorData);
            throw new Error(errorData.error || "Failed to save item");
        }
        
        const data = await response.json();
        return data.id || null;
    } catch (error) {
        console.error("Error saving to server:", error);
        return null;
    }
}

// removeClothing function with better error handling
function removeClothing(index) {
    if (confirm("Are you sure you want to remove this item?")) {
        const item = wardrobe[index];
        
        // Find the card element based on the index
        const card = document.querySelector(`.clothing-card[data-index="${index}"]`);
        
        // Add a loading indication if card exists
        if (card) card.classList.add("deleting");
        
        // If the item has an ID, it exists on the server and should be deleted
        if (item && item.id) {
            // Remove the user_id parameter - your backend gets this from the session
            fetch(`/api/wardrobe/${item.id}`, {
                method: "DELETE",
                headers: {
                    "Content-Type": "application/json"
                },
                credentials: "same-origin"
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.error || `Server responded with status ${response.status}`);
                    });
                }
                return response.json();
            })
            .then(data => {
                // Server deletion was successful, now update local state
                console.log("Item deleted successfully:", data);
                wardrobe.splice(index, 1);
                renderWardrobe();
            })
            .catch(error => {
                console.error("Error deleting from server:", error);
                if (card) card.classList.remove("deleting");
                alert(`Failed to delete item: ${error.message}`);
            });
        } else {
            // Item only exists locally or doesn't have an ID
            console.log("Removing local-only item at index:", index);
            wardrobe.splice(index, 1);
            renderWardrobe();
        }
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
saveClothingBtn.addEventListener("click", async () => {
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
            
            let newItem = { 
                name, 
                type, 
                season, 
                color,
                imageUrl
            };
            
            if (editIndex !== null) {
                // Update existing item
                const oldItem = wardrobe[editIndex];
                newItem.id = oldItem.id; // Preserve the ID if it exists
                wardrobe[editIndex] = newItem;
                
                // If the item has an ID, we'll need to implement an update endpoint
                // For now we're just updating the local wardrobe
            } else {
                // Add new item - save to server first, then add to local wardrobe
                const itemId = await saveItemToServer(newItem);
                if (itemId) {
                    newItem.id = itemId;
                }
                wardrobe.push(newItem);
            }
            
            // Update local storage
            localStorage.setItem("wardrobe", JSON.stringify(wardrobe));
            
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

// Initial load - ONE DOMContentLoaded event handler
document.addEventListener("DOMContentLoaded", () => {
    // Make sure the add button is always visible
    ensureAddButtonVisible();
    
    // First, check if we have a valid user ID
    if (!currentUserId || currentUserId === "{{ user_id }}") {
        console.error("User ID not properly set. Template variable not rendered.");
        wardrobe = JSON.parse(localStorage.getItem("wardrobe")) || [];
        renderWardrobe();
        return;
    }
    
    // Load wardrobe from server first, fall back to localStorage
    fetch('/api/wardrobe')  // Remove the query parameter, backend gets user from session
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || `Server responded with status ${response.status}`);
            });
        }
        return response.json();
    })
    .then(data => {
        console.log("Received data from server:", data);
        
        // Check for the correct data structure from server
        if (data.items && Array.isArray(data.items)) {
            // Transform the server items format to match your frontend format
            wardrobe = data.items.map(item => ({
                id: item.id,
                name: item.item_name,
                type: item.category || "Other",
                imageUrl: item.image_url,
                // You may need to add defaults for season and color
                season: item.season || "All Seasons",
                color: item.color || "Various"
            }));
            localStorage.setItem("wardrobe", JSON.stringify(wardrobe));
        } else {
            console.warn("Unexpected data format from server:", data);
            wardrobe = JSON.parse(localStorage.getItem("wardrobe")) || [];
        }
        renderWardrobe();
    })
    .catch(error => {
        console.error("Error loading wardrobe:", error);
        wardrobe = JSON.parse(localStorage.getItem("wardrobe")) || [];
        renderWardrobe();
    });
});