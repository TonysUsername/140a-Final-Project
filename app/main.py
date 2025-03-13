import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, List

import mysql.connector as mysql
import requests
from dotenv import load_dotenv
from fastapi import (Body, FastAPI, HTTPException, Query, Request, Response,
                     status)
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, validator

from app.database import (add_device, create_session, delete_device,
                          delete_session, get_db_connection,
                          get_devices_by_device_id, get_devices_by_user_id,
                          get_session, get_user_by_id, get_user_by_username,
                          setup_database)
load_dotenv()
LLM_TEXT_API = os.getenv("LLM_TEXT_API")
LLM_IMAGE_API = os.getenv("LLM_IMAGE_API")
EMAIL = os.getenv("EMAIL")
PID = os.getenv("PID")
# Initial users for setup
INIT_USERS = {"alice": "pass123", "bob": "pass456", "tony": "tonypas123"}

api_key = os.environ.get("API_KEY", "")
# Sensor data model
class SensorData(BaseModel):
    value: float
    unit: str
    timestamp: str = None
    device_id: str

    @validator('timestamp')
    def validate_timestamp(cls, value):
        if value is None:
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            return value
        except ValueError:
            raise ValueError("Invalid date format. Expected format: YYYY-MM-DD HH:MM:SS")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for managing application startup and database setup."""
    try:
        await setup_database(INIT_USERS)
        print("Database setup completed")
        # Also set up sensor tables
        conn = get_db_connection()  # Remove the await here
        cursor = conn.cursor()
        
        # Create sensor tables if they don't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS temperature (
            id INT AUTO_INCREMENT PRIMARY KEY,
            device_id VARCHAR(255) NOT NULL,
            timestamp DATETIME NOT NULL,
            value FLOAT NOT NULL,
            unit VARCHAR(10) NOT NULL
        )
        """)
        
        
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS humidity (
            id INT AUTO_INCREMENT PRIMARY KEY,
            device_id VARCHAR(255) NOT NULL,
            timestamp DATETIME NOT NULL,
            value FLOAT NOT NULL,
            unit VARCHAR(10) NOT NULL
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS light (
            id INT AUTO_INCREMENT PRIMARY KEY,
            device_id VARCHAR(255) NOT NULL,
            timestamp DATETIME NOT NULL,
            value FLOAT NOT NULL,
            unit VARCHAR(10) NOT NULL
        )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        yield
    finally:
        print("Shutdown completed")

# Create the FastAPI application with the defined lifespan
app = FastAPI(lifespan=lifespan)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:6543"],  # Replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Helper functions
def read_html(file_path: str) -> str:
    with open(file_path, "r") as f:
        return f.read()

def get_error_html(username: str) -> str:
    error_html = read_html("app/static/error.html")
    return error_html.replace("{username}", username)

def correct_date_time(value: str):
    try:
        return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Expected format: YYYY-MM-DD HH:MM:SS")

# Session validation
async def require_authenticated_user(request: Request):
    """Ensure that the user is authenticated, otherwise redirect to the login page."""
    session_id = request.cookies.get("sessionID")
    
    if not session_id:
        raise HTTPException(
            status_code=303,
            detail="Redirecting to login",
            headers={"Location": "/login"}
        )

    user = await get_session(session_id)
    
    if not user:
        raise HTTPException(
            status_code=303,
            detail="Redirecting to login",
            headers={"Location": "/login"}
        )

    return user

# Routes
@app.get("/welcome", response_class=HTMLResponse)
def server() -> HTMLResponse:
    with open("app/welcome.html") as html_file:
        return HTMLResponse(content=html_file.read())

@app.get("/", response_class=HTMLResponse)
def server() -> HTMLResponse:
    """Root route, redirects to login"""
    return RedirectResponse(url="/welcome", status_code=303)

@app.get("/signup", response_class=HTMLResponse)
def server() -> HTMLResponse:
    with open("app/signup.html") as html_file:
        return HTMLResponse(content=html_file.read())

@app.post("/signup")
async def signup(request: Request):
    """Register a new user and redirect to login page"""
    form = await request.form()
    username = form.get("username")
    password = form.get("password")
    
    # Basic validation
    if not username or not password:
        return HTMLResponse(content="Username and password are required", status_code=400)
    
    # Create the user
    from app.database import create_user
    user_id = await create_user(username, password)
    
    if user_id is None:
        return HTMLResponse(content="Username already exists", status_code=400)
    
    # Redirect to login page with success message
    response = RedirectResponse(url="/login?registered=true", status_code=303)
    return response

@app.get("/api/devices/{device_id}")
async def get_device(device_id: str, request: Request):
    """Get all devices for a device ID"""
    try:
        # Authenticate user
        user = await require_authenticated_user(request)
        
        # Get devices from database
        devices = await get_devices_by_device_id(device_id)
        
        return JSONResponse(content={"devices": devices})
    except HTTPException as e:
        if e.status_code == 303:  # Redirect for authentication
            return JSONResponse(content={"error": "Authentication required"}, status_code=401)
        raise
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/api/devices")
async def get_all_devices(request: Request):
    """Get all devices"""
    try:
        # Authenticate user
        user = await require_authenticated_user(request)
        
        # Get user ID from session
        user_details = await get_user_by_username(user["username"])
        
        if not user_details:
            return JSONResponse(content={"error": "User not found"}, status_code=404)
            
        user_id = user_details["id"]

        # Get devices from database
        devices = await get_devices_by_user_id(user_id)
        
        return JSONResponse(content={"devices": devices})
    except HTTPException as e:
        if e.status_code == 303:  # Redirect for authentication
            return JSONResponse(content={"error": "Authentication required"}, status_code=401)
        raise
    except Exception as e:
        import traceback
        print(f"Error in get_all_devices: {str(e)}")
        print(traceback.format_exc())
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/api/devices")
async def add_device_api(
    request: Request,
    data: dict = Body(...)
):
    """Add a new device"""
    try:
        # Authenticate user
        user = await require_authenticated_user(request)
        
        # Get user ID from session
        user_details = await get_user_by_username(user["username"])
        user_id = user_details["id"]

        # Validate request data
        device_id = data.get("deviceId")
        
        if not device_id:
            return JSONResponse(
                content={"error": "Device ID is required"}, 
                status_code=400
            )
        
        # Add device to database - now without device_type parameter
        success = await add_device(device_id, user_id)
        
        if success:
            return JSONResponse(content={"success": True})
        else:
            return JSONResponse(
                content={"error": "Failed to add device"}, 
                status_code=500
            )
    except HTTPException as e:
        if e.status_code == 303:  # Redirect for authentication
            return JSONResponse(content={"error": "Authentication required"}, status_code=401)
        raise
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.delete("/api/devices/{device_id}")
async def delete_device_api(
    device_id: str,
    request: Request
):
    """Delete a device"""
    try:
        # Authenticate user
        user = await require_authenticated_user(request)
        
        # Get user ID from session
        user_details = await get_user_by_username(user["username"])
        user_id = user_details["id"]

        # Delete device from database
        success = await delete_device(device_id, user_id)
        
        if success:
            return JSONResponse(content={"success": True})
        else:
            return JSONResponse(
                content={"error": "Device not found or deletion failed"}, 
                status_code=404
            )
    except HTTPException as e:
        if e.status_code == 303:  # Redirect for authentication
            return JSONResponse(content={"error": "Authentication required"}, status_code=401)
        raise
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# Protected route: Dashboard, accessible only after login
@app.get("/user/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Show the dashboard if authenticated"""
    # Check if the user is authenticated
    user = await require_authenticated_user(request)
    
    # If the user is authenticated, show the dashboard
    html_content = read_html("app/dashboard.html").replace("{username}", user["username"])
    return HTMLResponse(content=html_content)

@app.get("/user/wardrobe", response_class=HTMLResponse)
async def wardrobe(request: Request):
    """Show the wardrobe if authenticated"""
    user = await require_authenticated_user(request)
    html_content = read_html("app/wardrobe.html").replace("{username}", user["username"])
    return HTMLResponse(content=html_content)

@app.get("/user/profile", response_class=HTMLResponse)
async def profile(request: Request):
    """Show the user profile if authenticated"""
    user = await require_authenticated_user(request)
    html_content = read_html("app/profile.html").replace("{username}", user["username"])
    return HTMLResponse(content=html_content)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Show login page or redirect to user profile if already logged in"""
    session_id = request.cookies.get("sessionID")
    if session_id:
        user = await get_session(session_id)
        
        if user:
            return RedirectResponse(url=f"/user/{user['username']}", status_code=303)

    with open("app/login.html") as html:
        return HTMLResponse(content=html.read())

@app.post("/login")
async def login(request: Request):
    """Validate credentials and create a new session"""
    form = await request.form()
    user_name = form.get("username")
    pass_word = form.get("password")

    user = await get_user_by_username(user_name)
    if not user or user["password"] != pass_word:
        return HTMLResponse(content="Invalid username or password", status_code=401)

    session_id = str(uuid.uuid4())
    await create_session(user["id"], session_id)

    response = RedirectResponse(url=f"/user/{user_name}", status_code=303)
    response.set_cookie(key="sessionID", value=session_id, httponly=True, max_age=3600)
    return response

@app.post("/logout")
async def logout(request: Request):
    """Clear session and redirect to login page"""
    session_id = request.cookies.get("sessionID")
    
    if session_id:
        await delete_session(session_id)

    redirect_response = RedirectResponse(url="/login", status_code=303)
    redirect_response.delete_cookie("sessionID")
    
    return redirect_response

# Static routes for HTML pages
@app.get("/user/{username}", response_class=HTMLResponse)
async def user_page(username: str, request: Request):
    """Show user profile if authenticated"""
    user = await require_authenticated_user(request)

    if user["username"] != username:
        return HTMLResponse(get_error_html(username), status_code=403)

    html_content = read_html("app/profile.html").replace("{username}", username)
    return HTMLResponse(content=html_content)

@app.get("/dashboard")
def dashboard_redirect():
    return RedirectResponse(url="/user/dashboard", status_code=303)

#------------- INTEGRATED SENSOR API ENDPOINTS -------------#

async def get_sensory_data(sensor_type, device_id=None, order_by=None, start_date=None, end_date=None):
    """Get sensor data with optional filtering"""
    valid_sensory_types = ["temperature", "light", "humidity"]
    if sensor_type not in valid_sensory_types:
        raise HTTPException(status_code=404, detail="Sensor type not found")

    conn =  get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = f"SELECT * FROM {sensor_type}"
    parameters = []

    where_clauses = []
    
    if device_id:
        where_clauses.append("device_id = %s")
        parameters.append(device_id)

    if start_date:
        start_date = correct_date_time(start_date)
        where_clauses.append("timestamp >= %s")
        parameters.append(start_date)

    if end_date:
        end_date = correct_date_time(end_date)
        where_clauses.append("timestamp <= %s")
        parameters.append(end_date)
        
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    if order_by:
        if order_by == "value":
            query += " ORDER BY value"
        elif order_by == "timestamp":
            query += " ORDER BY timestamp DESC"
            
    # Default ordering if none specified
    else:
        query += " ORDER BY timestamp DESC"

    cursor.execute(query, tuple(parameters))
    result = cursor.fetchall()

    # Process datetime objects to strings
    for row in result:
        if 'timestamp' in row and isinstance(row['timestamp'], datetime):
            row['timestamp'] = row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')

    cursor.close()
    conn.close()
    return result

@app.get("/api/sensor/{sensor_type}")
async def get_sensor_data(
    request: Request,
    sensor_type: str,
    device_id: str = None,
    order_by: str = Query(None, alias="order-by"),
    start_date: str = Query(None, alias="start-date"),
    end_date: str = Query(None, alias="end-date")
):
    """Get sensor data with optional filtering"""
    try:
        # Authenticate user
        user =  require_authenticated_user(request)
        
        # Get user ID from session
        user_details = await get_user_by_username(user["username"])
        user_id = user_details["id"]
        
        # If device_id is specified, verify user owns this device
        if device_id:
            devices = await get_devices_by_user_id(user_id)
            if not any(device['device_id'] == device_id for device in devices):
                return JSONResponse(
                    content={"error": "Device not found or not authorized"}, 
                    status_code=403
                )
        
        # Get sensor data
        retrieved_data = await get_sensory_data(
            sensor_type, device_id, order_by, start_date, end_date
        )
        return JSONResponse(content=retrieved_data)
    except HTTPException as e:
        if e.status_code == 303:  # Redirect for authentication
            return JSONResponse(content={"error": "Authentication required"}, status_code=401)
        raise
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/api/sensor/{sensor_type}")
async def add_sensor_data(
    sensor_type: str,
    sensor_data: SensorData,
    request: Request = None
):
    """Add new sensor data - can be called by device or authenticated user"""
    valid_sensor_types = ["temperature", "light", "humidity"]
    if sensor_type not in valid_sensor_types:
        raise HTTPException(status_code=404, detail="Sensor type not found")

    # Check if device exists in our system
    device = await get_devices_by_device_id(sensor_data.device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not registered in the system")
    
    # Set timestamp if not provided
    if sensor_data.timestamp is None:
        sensor_data.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        conn =  get_db_connection()
        cursor = conn.cursor()
        
        query = f"INSERT INTO {sensor_type} (device_id, timestamp, value, unit) VALUES (%s, %s, %s, %s)"
        values = (sensor_data.device_id, sensor_data.timestamp, sensor_data.value, sensor_data.unit)
        
        cursor.execute(query, values)
        conn.commit()
        new_id = cursor.lastrowid
        
        cursor.close()
        conn.close()
        
        return {"id": new_id, "success": True}
    except mysql.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")

@app.get("/api/sensor/{sensor_type}/latest")
async def get_latest_sensor_data(
    request: Request,
    sensor_type: str,
    device_id: str = Query(None)
):
    """Get latest sensor reading for a device"""
    try:
        # Authenticate user
        user = await require_authenticated_user(request)
        
        # Get user ID from session
        user_details = await get_user_by_username(user["username"])
        user_id = user_details["id"]
        
        # If device_id is not specified, return an error
        if not device_id:
            return JSONResponse(
                content={"error": "Device ID is required"}, 
                status_code=400
            )
            
        # Verify user owns this device
        devices = await get_devices_by_user_id(user_id)
        if not any(device['device_id'] == device_id for device in devices):
            return JSONResponse(
                content={"error": "Device not found or not authorized"}, 
                status_code=403
            )
        
        # Get latest reading
        conn =  get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = f"SELECT * FROM {sensor_type} WHERE device_id = %s ORDER BY timestamp DESC LIMIT 1"
        cursor.execute(query, (device_id,))
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not result:
            return JSONResponse(content={"error": "No data found for this device"}, status_code=404)
        
        # Convert datetime to string
        if 'timestamp' in result and isinstance(result['timestamp'], datetime):
            result['timestamp'] = result['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            
        return JSONResponse(content=result)
    except HTTPException as e:
        if e.status_code == 303:  # Redirect for authentication
            return JSONResponse(content={"error": "Authentication required"}, status_code=401)
        raise
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/api/temperature")
async def get_temperature(request: Request, device_id: str = Query(None)):
    """Get temperature data (authenticated)"""
    try:
        # If device_id is specified, get actual data
        if device_id:
            return await get_latest_sensor_data(request, "temperature", device_id)
            
        # Otherwise return mock data (for backward compatibility)
        user = await require_authenticated_user(request)
        
        # Mock data - replace with actual database queries
        import random
        from datetime import datetime, timedelta

        # Generate last 10 data points
        data = []
        for i in range(10):
            timestamp = datetime.now() - timedelta(minutes=i*5)
            data.append({
                "timestamp": timestamp.isoformat(),
                "value": round(random.uniform(18.0, 25.0), 1)  # Random temperature between 18-25°C
            })
        
        # Return in reverse order (newest first)
        return data
    except HTTPException as e:
        if e.status_code == 303:  # Redirect for authentication
            return JSONResponse(content={"error": "Authentication required"}, status_code=401)
        raise
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/api/humidity")
async def get_humidity(request: Request, device_id: str = Query(None)):
    """Get humidity data (authenticated)"""
    try:
        # If device_id is specified, get actual data
        if device_id:
            return await get_latest_sensor_data(request, "humidity", device_id)
            
        # Otherwise return mock data (for backward compatibility)
        user = await require_authenticated_user(request)
        
        # Mock data - replace with actual database queries
        import random
        from datetime import datetime, timedelta

        # Generate last 10 data points
        data = []
        for i in range(10):
            timestamp = datetime.now() - timedelta(minutes=i*5)
            data.append({
                "timestamp": timestamp.isoformat(),
                "value": round(random.uniform(40.0, 60.0), 1)  # Random humidity between 40-60%
            })
        
        # Return in reverse order (newest first)
        return data
    except HTTPException as e:
        if e.status_code == 303:  # Redirect for authentication
            return JSONResponse(content={"error": "Authentication required"}, status_code=401)
        raise
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/api/light")
async def get_light(request: Request, device_id: str = Query(None)):
    """Get light data (authenticated)"""
    try:
        # If device_id is specified, get actual data
        if device_id:
            return await get_latest_sensor_data(request, "light", device_id)
            
        # Otherwise return mock data (for backward compatibility)
        user = await require_authenticated_user(request)
        
        # Mock data - replace with actual database queries
        import random
        from datetime import datetime, timedelta

        # Generate last 10 data points
        data = []
        for i in range(10):
            timestamp = datetime.now() - timedelta(minutes=i*5)
            data.append({
                "timestamp": timestamp.isoformat(),
                "value": round(random.uniform(200, 800))  # Random light level between 200-800 lux
            })
        
        # Return in reverse order (newest first)
        return data
    except HTTPException as e:
        if e.status_code == 303:  # Redirect for authentication
            return JSONResponse(content={"error": "Authentication required"}, status_code=401)
        raise
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/user/sensors", response_class=HTMLResponse)
async def sensors_dashboard(request: Request):
    """Show the sensors dashboard if authenticated"""
    user = await require_authenticated_user(request)
    html_content = read_html("app/sensors.html").replace("{username}", user["username"])
    return HTMLResponse(content=html_content)

from fastapi import Header

@app.post("/ai/recommendation/")
async def get_ai_recommendation(
    request: Request,
    email: str = Header(..., alias="email"),  # Extract email from header
    pid: str = Header(..., alias="pid")       # Extract pid from header
):
    try:
        data = await request.json()
        temperature = float(data.get('temperature', 0))
        humidity = float(data.get('humidity', 0))
        
        prompt = f"The temperature is {temperature}°C and humidity is {humidity}%. What should I wear today?"
        
        # Use extracted headers
        headers = {
            "email": email,
            "pid": pid,
            "Content-Type": "application/json"
        }
        
        payload = {"prompt": prompt}
        
        # Use the correct API endpoint
        response = requests.post(LLM_TEXT_API, json=payload, headers=headers)
        response.raise_for_status()
        
        ai_response = response.json()
        if ai_response.get("success"):
            return {"result": {"response": ai_response["result"]["response"]}}
        else:
            raise HTTPException(status_code=500, detail="AI API returned failure")
    
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid values")
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/proxy/ai/complete")
async def proxy_ai_complete(
    request: Request,
    email: str = Header(..., alias="email"),  # Extract email from header
    pid: str = Header(..., alias="pid")       # Extract pid from header
):
    try:
        data = await request.json()
        
        # Forward the request to the AI API
        headers = {
            "email": email,
            "pid": pid,
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            "https://ece140-wi25-api.frosty-sky-f43d.workers.dev/api/v1/ai/complete",
            json=data,
            headers=headers
        )
        response.raise_for_status()
        
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/weather", response_class=HTMLResponse)
def get_weather():
    with open("Weather/weather.html") as html_file:
        return HTMLResponse(content = html_file.read())
# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)