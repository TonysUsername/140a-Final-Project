import mysql.connector as mysql
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from app.database import populate_database, cursor, data_base
from pydantic import BaseModel
from datetime import datetime

# Initialize FastAPI app
app = FastAPI()

def on_startup():
    populate_database()

# Define the request model for inserting and updating data
class SensorData(BaseModel):
    value: float
    unit: str
    timestamp: str = None  # Optional timestamp

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
    
    cursor.execute(query, tuple(parameters))
    result = cursor.fetchall()
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



# Run the app
if __name__ == "__main__":
    uvicorn.run(app="app.main:app", host="0.0.0.0", port=6543, reload=True)
