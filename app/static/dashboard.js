const BASE_URL = 'https://ece140-wi25-api.frosty-sky-f43d.workers.dev';
const LLM_TEXT_API = `${BASE_URL}/api/v1/ai/complete`;  // Text generation endpoint
const LLM_IMAGE_API = `${BASE_URL}/api/v1/ai/image`;    // Image generation endpoint
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
async function renderChart(sensorType, chartId, label, color) {
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
    
    const last10Data = data.slice(-10);
    
    // Process timestamps and fix any issues
    const processedData = last10Data.map(item => {
        return {
            timestamp: ensureCorrectTimestampFormat(item),
            value: item.value
        };
    });
    
    // Format labels with date and time
    const formattedLabels = processedData.map(item => formatDateTime(item.timestamp));
    const values = processedData.map(item => item.value);
    
    // Display the processed values for debugging
    console.log("Formatted labels:", formattedLabels);
    console.log("Values:", values);

    const ctx = document.getElementById(chartId).getContext('2d');
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

// Add this function to get the latest sensor data
async function getLatestSensorData(sensorType) {
    try {
        // Try to get device-specific data first
        const deviceSelector = document.getElementById('device-selector');
        const deviceId = deviceSelector ? deviceSelector.value : null;
        
        let url = `/api/sensor/${sensorType}/latest`;
        if (deviceId) {
            url += `?device_id=${deviceId}`;
        }
        
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        
        const data = await response.json();
        return data.value;
    } catch (error) {
        console.error(`Error fetching latest ${sensorType} data:`, error);
        
        // Fallback to weather data if sensor data is unavailable
        if (sensorType === 'temperature') {
            const tempElement = document.querySelector('.weather-temp');
            if (tempElement) {
                const fahrenheit = parseFloat(tempElement.textContent.replace('°F', ''));
                return (fahrenheit - 32) * 5/9; // Convert to Celsius
            }
        } else if (sensorType === 'humidity') {
            const humidityText = document.querySelector('.weather-metrics').textContent;
            const humidityMatch = humidityText.match(/Humidity: (\d+)%/);
            if (humidityMatch) {
                return parseFloat(humidityMatch[1]);
            }
        }
        
        // Return default values if all else fails
        return sensorType === 'temperature' ? 20 : 50; // 20°C or 50% humidity as defaults
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

// Initialize charts and recommendation when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Add console output to see when this runs
    console.log("DOM loaded - initializing charts and recommendation");
    
    // Render charts
    renderChart('temperature', 'temperature_Chart', 'Temperature (°C)', 'rgba(255, 99, 132, 1)');
    renderChart('humidity', 'humidity_Chart', 'Humidity (%)', 'rgba(54, 162, 235, 1)');
    renderChart('light', 'light_Chart', 'Light Level (lux)', 'rgba(255, 206, 86, 1)');
    
    // Get initial outfit recommendation
    getOutfitRecommendation();
    
    // Set up event listener for recommendation button
    const recommendationButton = document.getElementById('generate-recommendation');
    if (recommendationButton) {
        recommendationButton.addEventListener('click', getOutfitRecommendation);
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

// Event listener for the send button
document.getElementById('send-button').addEventListener('click', async () => {
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

// Allow pressing Enter to send a message
document.getElementById('chat-input').addEventListener('keypress', async (e) => {
    if (e.key === 'Enter') {
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
    }
});
});