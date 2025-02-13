from fastapi.responses import HTMLResponse
import mysql.connector as mysql
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime
from dotenv import load_dotenv
from app import database
from app.database import populate_database, cursor, data_base
from contextlib import asynccontextmanager


# @asynccontextmanager
async def lifespan(app: FastAPI):
    populate_database()
    yield
    # Shutdown

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

    def set_default_timestamp(self):
        if not self.timestamp:
            self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            try:
                # Ensure that the timestamp provided is in the correct format
                self.timestamp = datetime.strptime(self.timestamp, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Expected format: YYYY-MM-DD HH:MM:SS")
def correct_date_time(value: str):
    # Remove the 'T' character if it exists
    if 'T' in value:
        value = value.replace('T', ' ')  # Replace 'T' with a space to match the expected format

    try:
        return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Expected format: YYYY-MM-DD HH:MM:SS")



# Function to get sensory data with filtering and sorting


def get_sensory_data(sensor_type, order_by=None, start_date=None, end_date=None):
    valid_sensory_types = ["temperature", "light", "humidity"]

    if sensor_type not in valid_sensory_types:
        raise HTTPException(status_code=404, detail="Sensor type not found")

    query = f"SELECT * FROM {sensor_type} WHERE 1=1"
    parameters = []

    # Convert start_date using STR_TO_DATE in the SQL query
    if start_date:
        query += " AND timestamp >= STR_TO_DATE(%s, '%%Y-%%m-%%d %%H:%%i:%%s')"
        parameters.append(start_date)

    # Convert end_date using STR_TO_DATE in the SQL query
    if end_date:
        query += " AND timestamp <= STR_TO_DATE(%s, '%%Y-%%m-%%d %%H:%%i:%%s')"
        parameters.append(end_date)

    if order_by:
        if order_by == "value":
            query += " ORDER BY value"
        elif order_by == "timestamp":
            query += " ORDER BY timestamp"

    cursor = data_base.cursor(dictionary=True)
    cursor.execute(query, tuple(parameters))
    result = cursor.fetchall()
    cursor.close()

    return result



# Route to get all data for a given sensor type with optional query parameters
@app.get("/api/{sensor_type}")
async def get_all_data(sensor_type: str,
                       order_by: str = Query(None, alias="order-by"),
                       start_date: str = Query(None, alias="start-date"),
                       end_date: str = Query(None, alias="end-date")):
    try:
        retrieved_data = get_sensory_data(
            sensor_type, order_by, start_date, end_date)
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

    # Set timestamp to current time if not provided
    if sensor_data.timestamp is None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sensor_data.timestamp = now

    try:
        query = f"INSERT INTO {sensor_type} (timestamp, value, unit) VALUES (%s, %s, %s)"
        values = (sensor_data.timestamp, sensor_data.value, sensor_data.unit)
        cursor = data_base.cursor(dictionary=True)  # Ensure dictionary results
        cursor.execute(query, values)
        data_base.commit()
        new_id = cursor.lastrowid
        cursor.close()
        return {"id": new_id}
    except mysql.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")


# Route to fetch data by ID for a given sensor type
@app.get("/api/{sensor_type}/{id}")
async def get_data_id(sensor_type: str, id: int):
    valid_sensor_types = ["temperature", "light", "humidity"]
    if sensor_type not in valid_sensor_types:
        raise HTTPException(status_code=404, detail="Sensor not found")
    query = f"SELECT * FROM {sensor_type} WHERE id = %s"
    cursor = data_base.cursor(dictionary=True)  # Ensure dictionary results
    cursor.execute(query, (id,))
    result = cursor.fetchone()
    cursor.close()

    if result is None:
        raise HTTPException(status_code=404, detail="Data not found")

    return result


# Route to update data by ID for a given sensor type
@app.put("/api/{sensor_type}/{id}")
async def update_data(sensor_type: str, id: int, sensor_data: SensorData):
    valid_sensor_types = ["temperature", "light", "humidity"]
    if sensor_type not in valid_sensor_types:
        raise HTTPException(status_code=404, detail="Sensor type not found")

    try:
        # Build the update query
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

        cursor = data_base.cursor(dictionary=True)  # Ensure dictionary results
        cursor.execute(query, tuple(values))
        data_base.commit()
        cursor.close()

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
        cursor = data_base.cursor(dictionary=True)  # Ensure dictionary results
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