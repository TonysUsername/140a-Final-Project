import uvicorn
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime
import mysql.connector as mysql
from app.database import populate_database, data_base, cursor

app = FastAPI()

def startup_event():
    populate_database()

class SensorData(BaseModel):
    value: float
    unit: str
    timestamp: str = None

def correct_date_time(value: str):
    try:
        return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid timestamp format. Use YYYY-MM-DD HH:MM:SS")

@app.get("/api/{sensor_type}")
async def get_all_data(
    sensor_type: str,
    order_by: str = Query(None, alias="order-by"),
    start_date: str = Query(None),
    end_date: str = Query(None)
):
    valid_types = ["temperature", "humidity", "light"]
    if sensor_type not in valid_types:
        raise HTTPException(status_code=404, detail="Invalid sensory type")

    query = f"SELECT * FROM `{sensor_type}`"
    params = []
    conditions = []

    if start_date:
        start = correct_date_time(start_date)
        conditions.append("`timestamp` >= %s")
        params.append(start)
    if end_date:
        end = correct_date_time(end_date)
        conditions.append("`timestamp` <= %s")
        params.append(end)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    if order_by in ["value", "timestamp"]:
        query += f" ORDER BY `{order_by}`"
    elif order_by:
        raise HTTPException(status_code=400, detail="Invalid param")

    try:
        cursor.execute(query, params)
        results = cursor.fetchall()
        return {"data": results}
    except mysql.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@app.post("/api/{sensor_type}")
async def create_data(sensor_type: str, data: SensorData):
    valid_types = ["temperature", "humidity", "light"]
    if sensor_type not in valid_types:
        raise HTTPException(status_code=404, detail="Invalid sensory type")

    timestamp = data.timestamp or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    query = f"INSERT INTO `{sensor_type}` (timestamp, value, unit) VALUES (%s, %s, %s)"
    values = (timestamp, data.value, data.unit)

    try:
        cursor.execute(query, values)
        data_base.commit()
        return {"id": cursor.lastrowid}
    except mysql.Error as e:
        data_base.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@app.get("/api/{sensor_type}/{id}")
async def get_data_by_id(sensor_type: str, id: int):
    valid_types = ["temperature", "humidity", "light"]
    if sensor_type not in valid_types:
        raise HTTPException(status_code=404, detail="Invalid sensory type")

    query = f"SELECT * FROM `{sensor_type}` WHERE id = %s"
    cursor.execute(query, (id,))
    result = cursor.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Data not found")
    return result

@app.put("/api/{sensor_type}/{id}")
async def update_data(sensor_type: str, id: int, data: SensorData):
    valid_types = ["temperature", "humidity", "light"]
    if sensor_type not in valid_types:
        raise HTTPException(status_code=404, detail="Invalid sensory type")

    updates = []
    params = []
    if data.value is not None:
        updates.append("`value` = %s")
        params.append(data.value)
    if data.unit is not None:
        updates.append("unit = %s")
        params.append(data.unit)
    if data.timestamp is not None:
        updates.append("`timestamp` = %s")
        params.append(data.timestamp)

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    query = f"UPDATE `{sensor_type}` SET {', '.join(updates)} WHERE id = %s"
    params.append(id)

    try:
        cursor.execute(query, params)
        data_base.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Data not found")
        return {"message": "Data updated"}
    except mysql.Error as e:
        data_base.rollback()
        raise HTTPException(status_code=500, detail=f"error: {e}")

@app.delete("/api/{sensor_type}/{id}")
async def delete_data(sensor_type: str, id: int):
    valid_types = ["temperature", "humidity", "light"]
    if sensor_type not in valid_types:
        raise HTTPException(status_code=404, detail="Invalid sensory type")

    query = f"DELETE FROM `{sensor_type}` WHERE id = %s"
    try:
        cursor.execute(query, (id,))
        data_base.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Data not found")
        return {"message": "Data deleted"}
    except mysql.Error as e:
        data_base.rollback()
        raise HTTPException(status_code=500, detail=f"error: {e}")

@app.get("/api/{sensor_type}/count")
async def get_count(sensor_type: str):
    valid_types = ["temperature", "humidity", "light"]
    if sensor_type not in valid_types:
        raise HTTPException(status_code=404, detail="Invalid sensory type")

    query = f"SELECT COUNT(*) FROM `{sensor_type}`"
    cursor.execute(query)
    count = cursor.fetchone()[0]
    return {"count": count}

if __name__ == "__main__":
    uvicorn.run(app="app.main:app", host="0.0.0.0", port=6543, reload=True)