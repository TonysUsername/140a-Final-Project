from fastapi.responses import HTMLResponse
import mysql.connector as mysql
import uvicorn
from fastapi import FastAPI, HTTPException, Query, status, Body
from pydantic import BaseModel, validator
from datetime import datetime
from dotenv import load_dotenv
from app import database
from app.database import populate_database, cursor, data_base
from contextlib import asynccontextmanager
from datetime import datetime

async def lifespan(app: FastAPI):
    populate_database()
    yield
app = FastAPI(lifespan=lifespan)


@app.get("/", response_class=HTMLResponse)
def server() -> HTMLResponse:
    with open("app/index.html") as html_file:
        return HTMLResponse(content=html_file.read())


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    with open("app/dashboard.html") as html_file:
        return HTMLResponse(content=html_file.read())


class SensorData(BaseModel):
    value: float
    unit: str
    timestamp: str = None

    @validator('timestamp')
    def validate_timestamp(cls, value):
        if value is None:
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            return value
        except ValueError:
            raise ValueError("Invalid date format. Expected format: YYYY-MM-DD HH:MM:SS")

def correct_date_time(value: str):
    try:
        return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Expected format: YYYY-MM-DD HH:MM:SS")

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
        if start_date:
            query += " AND timestamp <= %s"
        else:
            query += " WHERE timestamp <= %s"
        parameters.append(end_date)

    if order_by:
        if order_by == "value":
            query += " ORDER BY value"
        elif order_by == "timestamp":
            query += " ORDER BY timestamp"

    cursor.execute(query, tuple(parameters))
    result = cursor.fetchall()

    column_names = [desc[0] for desc in cursor.description]
    data = [dict(zip(column_names, row)) for row in result]

    for row in data:
        if 'timestamp' in row:
            if isinstance(row['timestamp'], datetime):
                row['timestamp'] = row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            else:
                try:
                    datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    raise ValueError("Invalid date format in database. Expected format: YYYY-MM-DD HH:MM:SS")

    return data

@app.get("/api/{sensor_type}")
async def get_all_data(
    sensor_type: str,
    order_by: str = Query(None, alias="order-by"),
    start_date: str = Query(None, alias="start-date"),
    end_date: str = Query(None, alias="end-date")
):
    try:
        retrieved_data = get_sensory_data(
            sensor_type, order_by, start_date, end_date
        )
        return retrieved_data
    except HTTPException as e:
        raise e


@app.get("/api/{sensor_type}/count")
async def get_count(sensor_type: str):
    valid_sensor_types = ["temperature", "light", "humidity"]
    if sensor_type not in valid_sensor_types:
        raise HTTPException(status_code=404, detail="Sensor not found")

    query = f"SELECT COUNT(*) FROM {sensor_type}"
    cursor.execute(query)
    result = cursor.fetchone()
    return result[0]

@app.post("/api/{sensor_type}")
def put_data(sensor_type: str, sensor_data: SensorData):
    valid_sensor_types = ["temperature", "light", "humidity"]
    if sensor_type not in valid_sensor_types:
        raise HTTPException(status_code=404, detail="Sensor not found")

    if sensor_data.timestamp is None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sensor_data.timestamp = now

    try:
        query = f"INSERT INTO {sensor_type} (timestamp, value, unit) VALUES (%s, %s, %s)"
        values = (sensor_data.timestamp, sensor_data.value, sensor_data.unit)
        cursor = data_base.cursor(dictionary=True)
        cursor.execute(query, values)
        data_base.commit()
        new_id = cursor.lastrowid
        cursor.close()
        return {"id": new_id}
    except mysql.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")

@app.get("/api/{sensor_type}/{id}")
async def get_data_id(sensor_type: str, id: int):
    valid_sensor_types = ["temperature", "light", "humidity"]
    if sensor_type not in valid_sensor_types:
        raise HTTPException(status_code=404, detail="Sensor not found")
    query = f"SELECT * FROM {sensor_type} WHERE id = %s"
    cursor = data_base.cursor(dictionary=True)
    cursor.execute(query, (id,))
    result = cursor.fetchone()
    cursor.close()

    if result is None:
        raise HTTPException(status_code=404, detail="Data not found")

    return result

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

        cursor = data_base.cursor(dictionary=True)
        cursor.execute(query, tuple(values))
        data_base.commit()
        cursor.close()

        return {"message": "Data updated successfully"}
    except mysql.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    
@app.delete("/api/{sensor_type}/{id}")
async def delete_data(sensor_type: str, id: int):
    valid_sensor_types = ["temperature", "light", "humidity"]
    if sensor_type not in valid_sensor_types:
        raise HTTPException(status_code=404, detail="Sensor not found")

    try:
        query = f"DELETE FROM {sensor_type} WHERE id = %s"
        cursor = data_base.cursor(dictionary=True)
        cursor.execute(query, (id,))
        data_base.commit()
        cursor.close()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Data not found")

        return {"message": "Data deleted successfully"}
    except mysql.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")

if __name__ == "__main__":
    uvicorn.run(app="app.main:app", host="0.0.0.0", port=6543, reload=True)
