import mysql.connector as mysql
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from app.database import populate_database, cursor, data_base
from pydantic import BaseModel
from datetime import datetime

app = FastAPI()

# Initialize the database by calling the function
populate_database()

# Define the request model
class SensorData(BaseModel):
    value: float
    unit: str
    timestamp: str = None  # optional timestamp

def correct_date_time(value: str):
    try:
        return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Expected format: YYYY-MM-DD HH:MM:SS")

# Function to get sensory data
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
        end_date =correct_date_time(end_date)
        query += " AND timestamp <= %s" if start_date else " WHERE timestamp <= %s"
        parameters.append(end_date)
    
    if order_by:
        if order_by == "value":
            query += " ORDER BY value" if sensor_type == "temperature" else " ORDER BY value" if sensor_type == "light" else " ORDER BY value"
        elif order_by == "timestamp":
            query += " ORDER BY timestamp"
    
    cursor.execute(query, tuple(parameters))
    result = cursor.fetchall()
    return result

@app.get("/api/{sensor_type}")
async def get_all_data(sensor_type: str, order_by: str = Query(None, alias="order-by"), 
                       start_date: str = Query(None), end_date: str = Query(None)):
    try:
        retrieved_data = get_sensory_data(sensor_type, order_by, start_date, end_date)
        return retrieved_data
    except HTTPException as e:
        raise e

# Route to insert new data for a sensor type
@app.post("/api/{sensor_type}")
async def put_data(sensor_type: str, sensor_data: SensorData):
    valid_sensor_types = ["temperature", "light", "humidity"]
    if sensor_type not in valid_sensor_types:
        raise HTTPException(status_code=404, detail="Sensor not found")
    
    try:
        timestamp = sensor_data.timestamp or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if sensor_type == "temperature":
            query = "INSERT INTO temperature (timestamp, value, unit) VALUES (%s, %s)"
            values = (timestamp, sensor_data.value)
        elif sensor_type == "light":
            query = "INSERT INTO light (timestamp, value, unit) VALUES (%s, %s)"
            values = (timestamp, sensor_data.value)
        elif sensor_type == "humidity":
            query = "INSERT INTO humidity (timestamp, value, unit) VALUES (%s, %s)"
            values = (timestamp, sensor_data.value)
        
        cursor.execute(query, values)
        data_base.commit()
        
        new_id = cursor.lastrowid
        return {"id": new_id}
    except mysql.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")

# Route to fetch data by ID for a given sensor type
@app.get("/api/{sensor_type}/{id}")
async def get_data_id(sensor_type: str, id: int):
    valid_sensor_types = ["temperature", "light", "humidity"]
    if sensor_type not in valid_sensor_types:
        raise HTTPException(status_code=404, detail="Sensor not found")
    
    try:
        query = f"SELECT id, timestamp, value, unit FROM {sensor_type} WHERE id = %s"
        cursor.execute(query, (id,))
        result = cursor.fetchone()
        
        if result is None:
            raise HTTPException(status_code=404, detail="Data not found")
        
        return result
    except mysql.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")

# Route to update data by ID for a given sensor type
@app.put("/api/{sensor_type}/{id}")
async def update_data(sensor_type: str, id: int, sensor_data: SensorData):
    valid_sensor_types = ["temperature", "light", "humidity"]
    if sensor_type not in valid_sensor_types:
        raise HTTPException(status_code=404, detail="Sensor type not found")
    
    try:
        query = f"UPDATE {sensor_type} SET "
        values = []
        
        if sensor_data.value is not None:
            query += "value = %s"
            values.append(sensor_data.value)
        
        if sensor_data.unit is not None:
            query += ", unit = %s"
            values.append(sensor_data.unit)
        
        if sensor_data.timestamp is not None:
            query += ", timestamp = %s"
            values.append(sensor_data.timestamp)
        
        query += " WHERE id = %s"
        values.append(id)
        
        cursor.execute(query, tuple(values))
        data_base.commit()
        
        return {"message": "Data updated successfully"}
    except mysql.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")

# Route to delete data by ID for a given sensor type
@app.delete("/api/{sensor_type}/{id}")
async def delete_data(sensor_type: str, id: int):
    valid_sensor_types = ["temperature", "light", "humidity"]
    if sensor_type not in valid_sensor_types:
        raise HTTPException(status_code=404, detail="Sensor not found")
    
    try:
        query = f"DELETE FROM {sensor_type} WHERE id = %s"
        cursor.execute(query, (id,))
        data_base.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Data not found")
        
        return {"message": "Data deleted successfully"}
    except mysql.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")

# Route to get the count of rows for a given sensor type
@app.get("/api/{sensor_type}/count")
async def get_count(sensor_type: str):
    valid_sensor_types = ["temperature", "light", "humidity"]
    if sensor_type not in valid_sensor_types:
        raise HTTPException(status_code=404, detail="Sensor not found")
    
    try:
        query = f"SELECT COUNT(*) FROM {sensor_type}"
        cursor.execute(query)
        result = cursor.fetchone()
        return {"count": result[0]}
    except mysql.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")

if __name__ == "__main__":
    uvicorn.run(app="app.main:app", host="0.0.0.0", port=6543, reload=True)
