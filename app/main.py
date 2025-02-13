import os
from fastapi.responses import HTMLResponse
import mysql.connector as mysql
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime
from dotenv import load_dotenv
from app.database import populate_database
from contextlib import asynccontextmanager
@asynccontextmanager
async def lifespan(app: FastAPI):
    populate_database()
    yield
    # Shutdown
app = FastAPI(lifespan=lifespan)

@app.get("/", response_class = HTMLResponse)
def server() -> HTMLResponse:
    with open("app/index.html") as html_file:
        return HTMLResponse(content = html_file.read())

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    with open("app/dashboard.html") as html_file:
        return HTMLResponse(content = html_file.read())

# Helper function to validate date format
def correct_date_time(value: str):
    try:
        return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Expected format: YYYY-MM-DD HH:MM:SS")

# Function to get sensory data with filtering and sorting
def get_sensory_data(sensor_type, order_by=None, start_date=None, end_date=None):
    valid_sensory_types = ["temperature", "light", "humidity"]
    
    if sensor_type not in valid_sensory_types:
        raise HTTPException(status_code=404, detail="Sensor type not found")
    
    query = f"SELECT * FROM {sensor_type}"
    parameters = []
    
    if start_date:
        start_date = correct_date_time(start_date)
        query += " WHERE timestamp >= %s"
        parameters.append(start_date)
    
    if end_date:
        end_date = correct_date_time(end_date)
        query += " AND timestamp <= %s" if start_date else " WHERE timestamp <= %s"
        parameters.append(end_date)
    
    if order_by:
        if order_by == "value":
            query += " ORDER BY value"
        elif order_by == "timestamp":
            query += " ORDER BY timestamp"
    
    data_base = mysql.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_database
    )
    cursor = data_base.cursor()
    
    cursor.execute(query, tuple(parameters))
    result = cursor.fetchall()
    
    cursor.close() 
    data_base.close() 
    
    return result
  
# Route to get all data for a given sensor type with optional query parameters
@app.get("/api/{sensor_type}")
async def get_all_data(sensor_type: str, 
                       order_by: str = Query(None, alias="order-by"), 
                       start_date: str = Query(None), 
                       end_date: str = Query(None)):
    try:
        retrieved_data = get_sensory_data(sensor_type, order_by, start_date, end_date)
        return retrieved_data
    except HTTPException as e:
        raise e

@app.get("/api/{sensor_type}/count")
async def get_count(sensor_type: str):
    valid_sensor_types = ["temperature", "light", "humidity"]
    if sensor_type not in valid_sensor_types:
        raise HTTPException(status_code=404, detail="Sensor not found")
    
    try:
        # Open a new connection and cursor within the function
        data_base = mysql.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_database
        )
        cursor = data_base.cursor()
        
        query = f"SELECT COUNT(*) FROM {sensor_type}"
        cursor.execute(query)
        result = cursor.fetchone()
        
        cursor.close()  
        data_base.close()  
        
        return {"count": result[0]}
    except mysql.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")



if __name__ == "__main__":
   uvicorn.run(app="app.main:app", host="0.0.0.0", port=6543, reload=True)

