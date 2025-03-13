document.addEventListener("DOMContentLoaded", function () {
    // Get DOM elements
    const cityInput = document.getElementById("city");
    const weatherSubmitBtn = document.getElementById("weather-submit");
    const temperatureElement = document.querySelector(".weather-temp");
    const conditionElement = document.querySelector(".weather-condition");
    const descriptionElement = document.querySelector(".weather-description");
    const metricsElement = document.querySelector(".weather-metrics");
    const updatedElement = document.querySelector(".weather-updated");
    const weatherIcon = document.querySelector(".weather-icon");
    
    // API Key for Unsplash
    const API_KEY = "wTiIoiDTnotqM9RwIbp5GXrXfQx3nqngg5enW5S57lE";
    
    // Add event listener to the weather submit button
    weatherSubmitBtn.addEventListener("click", getWeather);
    
    // Allow enter key to submit
    cityInput.addEventListener("keypress", function(event) {
        if (event.key === "Enter") {
            event.preventDefault();
            getWeather();
        }
    });
    
    // Format date/time
    function formatDateTime(date) {
        const options = { 
            month: 'numeric', 
            day: 'numeric', 
            year: 'numeric',
            hour: 'numeric',
            minute: '2-digit',
            second: '2-digit',
            hour12: true
        };
        return new Date(date).toLocaleString('en-US', options);
    }
    
    // Function to fetch and display weather
    async function getWeather() {
        const cityId = cityInput.value.trim();
        
        if (cityId === "") {
            alert("Please enter a valid city name");
            return;
        }
        
        // Show loading state
        temperatureElement.textContent = "--°F";
        conditionElement.textContent = "Loading...";
        descriptionElement.textContent = "";
        metricsElement.textContent = "Humidity: --% | Wind: -- mph";
        updatedElement.textContent = "Last updated: --";
        weatherIcon.innerHTML = '<div class="loading-spinner"></div>';
        
        // Encode the city name
        const encodedCityId = encodeURIComponent(cityId);
        
        try {
            // Fetch location data
            const locationResponse = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodedCityId}&format=json`);
            if (!locationResponse.ok) throw new Error(`HTTP Error: ${locationResponse.status}`);
            const locationData = await locationResponse.json();
            
            if (locationData.length === 0) throw new Error("City not found.");
            
            // Extract location details
            const { lat, lon, display_name } = locationData[0];
            
            // Fetch weather data
            const pointsResponse = await fetch(`https://api.weather.gov/points/${lat},${lon}`);
            if (!pointsResponse.ok) throw new Error(`Weather service error: ${pointsResponse.status}`);
            const weatherData = await pointsResponse.json();
            
            const forecastResponse = await fetch(weatherData.properties.forecast);
            if (!forecastResponse.ok) throw new Error(`Forecast error: ${forecastResponse.status}`);
            const forecastData = await forecastResponse.json();
            
            const currentWeather = forecastData.properties.periods[0];
            
            // Fetch Weather Image
            const weatherImgResponse = await fetch(`https://api.unsplash.com/photos/random?query=${currentWeather.shortForecast}&client_id=${API_KEY}`);
            const weatherImgData = await weatherImgResponse.json();
            const weatherImgUrl = weatherImgData.urls.small;
            
            // Update the weather display
            temperatureElement.textContent = `${currentWeather.temperature}°${currentWeather.temperatureUnit}`;
            
            // Split the shortForecast into condition and description if possible
            const forecastParts = currentWeather.shortForecast.split(' ');
            let condition, description;
            
            if (forecastParts.length <= 2) {
                condition = currentWeather.shortForecast;
                description = "";
            } else {
                condition = forecastParts[0];
                description = forecastParts.slice(1).join(' ');
            }
            
            conditionElement.textContent = condition;
            descriptionElement.textContent = description;
            
            // Extract humidity from detailed forecast if available
            let humidity = "N/A";
            if (currentWeather.detailedForecast.includes("humidity")) {
                const humidityMatch = currentWeather.detailedForecast.match(/humidity (?:around |of |near )?(\d+)%/i);
                if (humidityMatch && humidityMatch[1]) {
                    humidity = humidityMatch[1];
                }
            }
            
            metricsElement.textContent = `Humidity: ${humidity}% | Wind: ${currentWeather.windSpeed}`;
            updatedElement.textContent = `Last updated: ${formatDateTime(new Date())}`;
            
            // Update weather icon
            weatherIcon.innerHTML = `<img src="${weatherImgUrl}" alt="${currentWeather.shortForecast}">`;
            
        } catch (error) {
            console.error("Weather error:", error);
            temperatureElement.textContent = "--°F";
            conditionElement.textContent = "Error";
            descriptionElement.textContent = error.message;
            metricsElement.textContent = "Humidity: --% | Wind: -- mph";
            updatedElement.textContent = "Last updated: --";
            weatherIcon.innerHTML = "";
        }
    }
    
    // Try to get user location on page load
    function tryGetUserLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                // Success
                async (position) => {
                    try {
                        const { latitude, longitude } = position.coords;
                        
                        // Get city name from coordinates
                        const reverseResponse = await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${latitude}&lon=${longitude}&format=json`);
                        const reverseData = await reverseResponse.json();
                        
                        // Extract city name
                        let cityName = "";
                        if (reverseData.address) {
                            cityName = reverseData.address.city || 
                                      reverseData.address.town || 
                                      reverseData.address.village || 
                                      reverseData.address.county;
                        }
                        
                        if (cityName) {
                            cityInput.value = cityName;
                            getWeather();
                        }
                    } catch (error) {
                        console.error("Error getting location:", error);
                    }
                },
                // Error
                (error) => {
                    console.error("Geolocation error:", error);
                }
            );
        }
    }
    
    // Try to get user location on page load
    tryGetUserLocation();
    
    // Add a loading spinner style
    const style = document.createElement('style');
    style.textContent = `
        .loading-spinner {
            width: 40px;
            height: 40px;
            border: 4px solid #f3f3f3;
            border-top: 4px solid #3498db;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: auto;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    `;
    document.head.appendChild(style);
});