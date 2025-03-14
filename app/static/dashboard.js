const BASE_URL = 'https://ece140-wi25-api.frosty-sky-f43d.workers.dev';
const LLM_TEXT_API = `${BASE_URL}/api/v1/ai/complete`;  // Text generation endpoint
const LLM_IMAGE_API = `${BASE_URL}/api/v1/ai/image`;    // Image generation endpoint
let currentDataRange = 10; // Default to 10 data points

// Function to format date and time properly with timezone handling
function formatDateTime(isoString) {
    // Check if the timestamp is in ISO format, MySQL datetime format, or timestamp format
    const date = new Date(isoString);
    
    // Check if this is a valid date
    if (isNaN(date.getTime())) {
        console.warn(`Invalid date: ${isoString}`);
        return "Invalid date";
    }
    
    // For debugging - log original string and parsed date
    console.log("Original timestamp:", isoString);
    console.log("Parsed date object:", date);
    console.log("UTC time:", date.toUTCString());
    console.log("Local time:", date.toString());
    
    // Format date as MM/DD/YYYY
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const day = date.getDate().toString().padStart(2, '0');
    const year = date.getFullYear();
    
    // Format time as HH:MM AM/PM
    let hours = date.getHours();
    const minutes = date.getMinutes().toString().padStart(2, '0');
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12;
    hours = hours ? hours : 12; // Convert 0 to 12
    
    return `${month}/${day}/${year} ${hours}:${minutes} ${ampm}`;
}

// Fetch data from API
async function fetchData(sensorType) {
    try {
        const response = await fetch(`/api/${sensorType}`);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Log the data to see what format timestamps are in
        console.log(`${sensorType} data:`, data);
        
        return data;
    } catch (error) {
        console.error(`Error fetching ${sensorType} data:`, error);
        return [];
    }
}

// Inspect and fix timestamp format if needed
function ensureCorrectTimestampFormat(dataPoint) {
    // Check what format the timestamp is in
    if (dataPoint && dataPoint.timestamp) {
        // Display the original format for debugging
        console.log("Original timestamp format:", dataPoint.timestamp);
        
        // If timestamp is in MySQL format (YYYY-MM-DD HH:MM:SS)
        if (typeof dataPoint.timestamp === 'string' && 
            dataPoint.timestamp.match(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/)) {
            
            // MySQL format doesn't specify timezone, assume local time
            // Convert to a JavaScript date object
            const parts = dataPoint.timestamp.split(/[- :]/);
            const year = parseInt(parts[0]);
            const month = parseInt(parts[1]) - 1; // JavaScript months are 0-based
            const day = parseInt(parts[2]);
            const hour = parseInt(parts[3]);
            const minute = parseInt(parts[4]);
            const second = parseInt(parts[5]);
            
            // Create date using local timezone
            const date = new Date(year, month, day, hour, minute, second);
            console.log("Corrected timestamp:", date.toString());
            
            return date;
        } 
        // If it's an ISO string or any other format
        else {
            const date = new Date(dataPoint.timestamp);
            console.log("Parsed timestamp:", date.toString());
            return date;
        }
    }
    return new Date(); // Fallback to current time
}

// Render chart with properly formatted date/time
async function renderChart(sensorType, chartId, label, color, dataRange = currentDataRange) {
    const data = await fetchData(sensorType);
    if (!data || data.length === 0) {
        console.error(`No data received for ${sensorType}`);
        document.getElementById(chartId).innerHTML = `No ${sensorType} data available`;
        return;
    }
    
    // Ensure data has the expected structure
    if (!data[0].hasOwnProperty('timestamp') || !data[0].hasOwnProperty('value')) {
        console.error(`${sensorType} data has unexpected structure:`, data[0]);
        document.getElementById(chartId).innerHTML = `Invalid ${sensorType} data format`;
        return;
    }
    
    // Get the last N data points based on dataRange
    const lastNData = data.slice(-dataRange);
    
    // Process timestamps and fix any issues
    const processedData = lastNData.map(item => {
        return {
            timestamp: ensureCorrectTimestampFormat(item),
            value: item.value
        };
    });
    
    // Format labels with date and time
    const formattedLabels = processedData.map(item => formatDateTime(item.timestamp));
    const values = processedData.map(item => item.value);
    
    // Display the processed values for debugging
    console.log(`Showing last ${dataRange} data points for ${sensorType}`);
    
    const ctx = document.getElementById(chartId).getContext('2d');
    // Destroy existing chart if it exists to prevent duplicates
    const existingChart = Chart.getChart(ctx);
    if (existingChart) {
        existingChart.destroy();
    }
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: formattedLabels,
            datasets: [{
                label: label,
                data: values,
                fill: false,
                borderColor: color,
                backgroundColor: color,
                pointRadius: 5,
                pointHoverRadius: 7,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            animation: {
                duration: 1000,
                easing: 'easeInOutQuad'
            },
            plugins: { 
                legend: { display: true },
                tooltip: {
                    callbacks: {
                        title: function(tooltipItems) {
                            return tooltipItems[0].label;
                        }
                    }
                }
            },
            scales: {
                x: { 
                    title: { display: true, text: 'Date and Time' }, 
                    grid: { color: '#333' },
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45
                    }
                },
                y: { 
                    title: { display: true, text: 'Sensed Data' }, 
                    grid: { color: '#333' } 
                }
            }
        }
    });
}

// Function to refresh all charts with the current data range
function refreshAllCharts() {
    renderChart('temperature', 'temperature_Chart', 'Temperature (°C)', 'rgba(255, 99, 132, 1)', currentDataRange);
    renderChart('humidity', 'humidity_Chart', 'Humidity (%)', 'rgba(54, 162, 235, 1)', currentDataRange);
    renderChart('light', 'light_Chart', 'Light Level (lux)', 'rgba(255, 206, 86, 1)', currentDataRange);
}

// Update the getLatestSensorData function to always include the device_id parameter
async function getLatestSensorData(sensorType) {
    try {
        // Get the device ID from the selector if it exists
        const deviceSelector = document.getElementById('device-selector');
        const deviceId = deviceSelector ? deviceSelector.value : 'default'; // Use 'default' as fallback
        
        // Use the correct API endpoint with the device_id parameter
        const url = `/api/sensor/${sensorType}/latest?device_id=${deviceId}`;
        console.log(`Fetching ${sensorType} data from: ${url}`);
        
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log(`Device ${sensorType} data:`, data);
        return data.value;
    } catch (error) {
        console.error(`Error fetching latest ${sensorType} data:`, error);
        
        // Use fallback API as a secondary option
        try {
            const fallbackResponse = await fetch(`/api/${sensorType}`);
            if (fallbackResponse.ok) {
                const fallbackData = await fallbackResponse.json();
                if (Array.isArray(fallbackData) && fallbackData.length > 0) {
                    return fallbackData[0].value;
                }
            }
        } catch (fallbackError) {
            console.error('Fallback API also failed:', fallbackError);
        }
        
        // Return default values if all else fails
        return sensorType === 'temperature' ? 20 : 
               sensorType === 'humidity' ? 50 : 
               sensorType === 'light' ? 500 : 0;
    }
}
async function getOutfitRecommendation() {
    const recommendationElement = document.getElementById('recommendation-content');
    if (!recommendationElement) return;
    recommendationElement.innerHTML = '<div class="loading">Generating recommendation...</div>';

    try {
        const temperature = await getLatestSensorData('temperature');
        const humidity = await getLatestSensorData('humidity');
        const tempValue = parseFloat(temperature);
        const humidValue = parseFloat(humidity);

        console.log(`Using temperature: ${tempValue}°C and humidity: ${humidValue}%`);

        // Call the backend proxy endpoint
        const response = await fetch('/proxy/ai/complete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'email': 'nmulla@ucsd.edu',  // Include email header
                'pid': 'A17277029'           // Include PID header
            },
            body: JSON.stringify({
                prompt: `The temperature is ${tempValue}°C and humidity is ${humidValue}%. What should I wear today so that I am both comfortable and stylish?`
            })
        });

        if (!response.ok) {
            console.error(`Error status: ${response.status}`);
            const errorText = await response.text();
            console.error(`Error details: ${errorText}`);
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();
        if (data.result && data.result.response) {
            recommendationElement.innerHTML = `
                <div class="recommendation-text">
                    ${formatRecommendationText(data.result.response)}
                </div>
            `;
        } else {
            throw new Error('Invalid response format');
        }
    } catch (error) {
        console.error('Error getting outfit recommendation:', error);
        recommendationElement.innerHTML = `
            <div class="error-message">
                ${error.message || 'Unable to generate recommendation. Please try again later.'}
            </div>
        `;
    }
}

// Function to format the recommendation text
function formatRecommendationText(text) {
    // Add some basic formatting to the AI response
    // Replace newlines with <br> tags
    let formatted = text.replace(/\n/g, '<br>');
    
    // Bold any important keywords
    const keywords = ['wear', 'recommended', 'suggestion', 'outfit', 'clothing'];
    keywords.forEach(keyword => {
        const regex = new RegExp(`\\b${keyword}\\b`, 'gi');
        formatted = formatted.replace(regex, `<strong>${keyword}</strong>`);
    });
    
    return formatted;
}

// Function to add a message to the chat history
function addMessageToChatHistory(message, isUser) {
    const chatHistory = document.getElementById('chat-history');
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', isUser ? 'user' : 'ai');

    const messageContent = document.createElement('div');
    messageContent.classList.add('message-content');
    messageContent.textContent = message;

    messageDiv.appendChild(messageContent);
    chatHistory.appendChild(messageDiv);

    // Scroll to the bottom of the chat history
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

// Function to send a message to the AI API
async function sendMessageToAI(message) {
    try {
        const response = await fetch('/ai/chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'email': 'nmulla@ucsd.edu',  // Include email header
                'pid': 'A17277029'           // Include PID header
            },
            body: JSON.stringify({
                prompt: message
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();
        if (data.result && data.result.response) {
            return data.result.response;
        } else {
            throw new Error('Invalid response format');
        }
    } catch (error) {
        console.error('Error sending message to AI:', error);
        return "Sorry, I couldn't process your request. Please try again later.";
    }
}

// Initialize everything when the document is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log("DOM loaded - initializing charts and recommendation");
    
    // Render charts with default range
    refreshAllCharts();
    
    // Get initial outfit recommendation
    getOutfitRecommendation();
    
    // Set up event listener for recommendation button
    const recommendationButton = document.getElementById('generate-recommendation');
    if (recommendationButton) {
        recommendationButton.addEventListener('click', getOutfitRecommendation);
    }


    // Add event listeners for range buttons
    const rangeButtons = document.querySelectorAll('.range-button');
    rangeButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Update active button styling
            rangeButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // Update current data range
            currentDataRange = parseInt(this.getAttribute('data-range'));
            console.log(`Data range changed to: ${currentDataRange}`);
            
            // Refresh all charts with new range
            refreshAllCharts();
        });
    });

    // Event listener for the send button
    const sendButton = document.getElementById('send-button');
    if (sendButton) {
        sendButton.addEventListener('click', async () => {
            const chatInput = document.getElementById('chat-input');
            const message = chatInput.value.trim();

            if (message) {
                // Add the user's message to the chat history
                addMessageToChatHistory(message, true);

                // Clear the input field
                chatInput.value = '';

                // Send the message to the AI API
                const aiResponse = await sendMessageToAI(message);

                // Add the AI's response to the chat history
                addMessageToChatHistory(aiResponse, false);
            }
        });
    }

    // Allow pressing Enter to send a message
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.addEventListener('keypress', async (e) => {
            if (e.key === 'Enter') {
                const message = chatInput.value.trim();

                if (message) {
                    // Add the user's message to the chat history
                    addMessageToChatHistory(message, true);

                    // Clear the input field
                    chatInput.value = '';

                    // Send the message to the AI
                    const aiResponse = await sendMessageToAI(message);

            // Add the AI's response to the chat history
            addMessageToChatHistory(aiResponse, false);
            }
        }
        });
    }
})

// Auto-update variables
let autoUpdateEnabled = false;
let updateInterval = 30000; // Default to 30 seconds
let updateIntervalId = null;

// Function to toggle auto-updates
function toggleAutoUpdate() {
    autoUpdateEnabled = !autoUpdateEnabled;
    const toggleButton = document.getElementById('auto-update-toggle');
    
    if (autoUpdateEnabled) {
        // Start the auto-update interval
        updateIntervalId = setInterval(refreshAllCharts, updateInterval);
        toggleButton.textContent = 'Disable Auto-Update';
        toggleButton.classList.add('active');
        console.log(`Auto-update enabled with ${updateInterval/1000}s interval`);
    } else {
        // Clear the interval
        if (updateIntervalId) {
            clearInterval(updateIntervalId);
            updateIntervalId = null;
        }
        toggleButton.textContent = 'Enable Auto-Update';
        toggleButton.classList.remove('active');
        console.log('Auto-update disabled');
    }
}

// Function to change update frequency
function changeUpdateFrequency(seconds) {
    updateInterval = seconds * 1000;
    
    // Update the active button styling
    const frequencyButtons = document.querySelectorAll('.frequency-button');
    frequencyButtons.forEach(btn => {
        btn.classList.remove('active');
        if (parseInt(btn.getAttribute('data-seconds')) === seconds) {
            btn.classList.add('active');
        }
    });
    
    // Restart interval if auto-update is enabled
    if (autoUpdateEnabled) {
        if (updateIntervalId) {
            clearInterval(updateIntervalId);
        }
        updateIntervalId = setInterval(refreshAllCharts, updateInterval);
        console.log(`Update frequency changed to ${seconds} seconds`);
    }
}

// Add this to your existing DOMContentLoaded event listener
document.addEventListener('DOMContentLoaded', () => {
    // Your existing initialization code...
    
    // Add auto-update toggle button
    const controlsDiv = document.createElement('div');
    controlsDiv.className = 'update-controls';
    controlsDiv.innerHTML = `
        <h3>Auto-Update Controls</h3>
        <button id="auto-update-toggle" class="update-button">Enable Auto-Update</button>
        <div class="frequency-controls">
            <span>Update every: </span>
            <button class="frequency-button active" data-seconds="30">30s</button>
            <button class="frequency-button" data-seconds="60">1m</button>
            <button class="frequency-button" data-seconds="300">5m</button>
        </div>
    `;
    
    // Insert controls before the charts or in a specific container
    const contentContainer = document.querySelector('.content') || document.body;
    const firstChart = document.getElementById('temperature_Chart');
    if (firstChart && firstChart.parentNode) {
        firstChart.parentNode.parentNode.insertBefore(controlsDiv, firstChart.parentNode);
    } else {
        contentContainer.insertBefore(controlsDiv, contentContainer.firstChild);
    }
    
    // Add event listeners for auto-update controls
    document.getElementById('auto-update-toggle').addEventListener('click', toggleAutoUpdate);
    
    const frequencyButtons = document.querySelectorAll('.frequency-button');
    frequencyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const seconds = parseInt(this.getAttribute('data-seconds'));
            changeUpdateFrequency(seconds);
        });
    });
    
    // Set the initial update frequency
    changeUpdateFrequency(30);
    
    // Add last update timestamp display
    const timestampDiv = document.createElement('div');
    timestampDiv.id = 'last-update-time';
    timestampDiv.className = 'last-update';
    timestampDiv.textContent = 'Last updated: ' + new Date().toLocaleString();
    controlsDiv.appendChild(timestampDiv);
    
    // Modify refreshAllCharts to update the timestamp
    const originalRefreshAllCharts = refreshAllCharts;
    refreshAllCharts = function() {
        originalRefreshAllCharts();
        document.getElementById('last-update-time').textContent = 'Last updated: ' + new Date().toLocaleString();
    };
});

// Add a function to update recommendation automatically as well
function autoUpdateAll() {
    refreshAllCharts();
    getOutfitRecommendation();
    document.getElementById('last-update-time').textContent = 'Last updated: ' + new Date().toLocaleString();
}
