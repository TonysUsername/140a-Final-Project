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

// Initialize charts when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Add console output to see when this runs
    console.log("DOM loaded - initializing charts");
    
    renderChart('temperature', 'temperature_Chart', 'Temperature (°C)', 'rgba(255, 99, 132, 1)');
    renderChart('humidity', 'humidity_Chart', 'Humidity (%)', 'rgba(54, 162, 235, 1)');
    renderChart('light', 'light_Chart', 'Light Level (lux)', 'rgba(255, 206, 86, 1)');
});