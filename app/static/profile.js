// Global variable for current username
let currentUsername = '';

// Function to load devices for the logged-in user
function loadDevices() {
    const deviceList = document.getElementById('device-list');
    
    
    // Show loading indicator
    deviceList.innerHTML = '<li class="loading">Loading devices...</li>';
    
    // Fetch devices from the API
    fetch('/api/devices')
        .then(response => {
            if (!response.ok) {
                if (response.status === 401) {
                    // Handle unauthorized access
                    window.location.href = '/login';
                    throw new Error('Authentication required');
                }
                return response.json().then(data => {
                    throw new Error(data.error || 'Failed to load devices');
            });
        }
            return response.json();
        })
        .then(data => {
            console.log('Devices data:', data);
            displayDevices(data.devices || []);
        })
        .catch(error => {
            console.error('Error loading devices:', error);
            deviceList.innerHTML = '<li class="error">Error loading devices. Please try again.</li>';
        });
}

// Function to display devices in the list with username
function displayDevices(devices) {
    const deviceList = document.getElementById('device-list');
    deviceList.innerHTML = '';

    if (devices.length === 0) {
        deviceList.innerHTML = '<li class="no-devices">No devices found</li>';
        return;
    }

    devices.forEach(device => {
        const li = document.createElement('li');
        li.className = 'device-item';

        const deviceInfo = document.createElement('span');
        deviceInfo.textContent = `${device.device_id}`;
        deviceInfo.className = 'device-info';
        
        // Show username if available (for admin views)
        if (device.username && device.username !== currentUsername) {
            const userBadge = document.createElement('span');
            userBadge.textContent = device.username;
            userBadge.className = 'user-badge';
            deviceInfo.appendChild(userBadge);
        }

        const deleteButton = document.createElement('button');
        deleteButton.textContent = 'Delete';
        deleteButton.className = 'delete-button';
        deleteButton.onclick = () => deleteDevice(device.device_id);

        li.appendChild(deviceInfo);
        li.appendChild(deleteButton);
        deviceList.appendChild(li);
    });

    showTemporaryMessage('Devices loaded successfully!', 'success-message');
}

// Function to add a new device
function addDevice() {
    const deviceIdInput = document.getElementById('deviceID');
    const deviceId = deviceIdInput.value.trim();

    if (!deviceId) {
        alert('Please enter a Device ID');
        return;
    }

    // Send request to add device
    fetch('/api/devices', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ deviceId }),
    })
    .then(response => {
        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = '/login';
                throw new Error('Authentication required');
            }
            throw new Error('Failed to add device');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            deviceIdInput.value = ''; // Clear the input field
            showTemporaryMessage('Device added successfully!', 'success-message');
            loadDevices(); // Reload the device list
        }
    })
    .catch(error => {
        console.error('Error adding device:', error);
        alert('Error adding device. Please try again.');
    });
}

// Function to delete a device
function deleteDevice(deviceId) {
    if (!confirm(`Are you sure you want to delete device ${deviceId}?`)) {
        return;
    }

    // Send request to delete device
    fetch(`/api/devices/${deviceId}`, {
        method: 'DELETE',
    })
    .then(response => {
        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = '/login';
                throw new Error('Authentication required');
            }
            throw new Error('Failed to delete device');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showTemporaryMessage('Device deleted successfully!', 'success-message');
            loadDevices(); // Reload the device list
        }
    })
    .catch(error => {
        console.error('Error deleting device:', error);
        alert('Error deleting device. Please try again.');
    });
}

// Function to show temporary success/error messages
function showTemporaryMessage(text, className) {
    const message = document.createElement('div');
    message.className = className;
    message.textContent = text;
    document.getElementById('device-management').appendChild(message);

    // Remove message after 3 seconds
    setTimeout(() => {
        message.remove();
    }, 3000);
}
// Initialize the page
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded');
    const deviceList = document.getElementById('device-list');
    console.log('Device list element:', deviceList);
    const usernameElement = document.getElementById('current-username');
    console.log('Username element:', usernameElement);
    
    if (usernameElement) {
        currentUsername = usernameElement.textContent || '';
        console.log('Current username:', currentUsername);
    }
    
    console.log('About to load devices');
    loadDevices();
});
