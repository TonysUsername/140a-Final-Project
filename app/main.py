import json
import os
import mysql.connector as mysql
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles  # Used for serving static files
from database import populate_database, cursor, data_base
from pydantic import BaseModel
app = FastAPI()
#initalize the databse by calling the function
populate_database()

#define the requests:
class SensorData(BaseModel):
    value: float
    unit: str
    timestamp: str = None

def get_sensory_data(sensor_type, order_by=None, start_date=None, end_date=None):
    valid_sensory_type = ["temperature", "light", "humidity"]
    if sensor_type not in valid_sensory_type:
        raise HTTPException(status_code=404, detail= "data cannot be found")
    query = f"select * FROM {sensor_type}"