import os
import mysql.connector as mysql
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

db_host = os.getenv("MYSQL_HOST")
db_user = os.getenv("MYSQL_USER")
db_database = os.getenv("MYSQL_DATABASE")
db_password = os.getenv("MYSQL_PASSWORD")

data_base = mysql.connect(
    host=db_host,
    user=db_user,
    password=db_password,
    database=db_database
)

cursor = data_base.cursor()


def create_tables():
    create_temp_table = """
    CREATE TABLE IF NOT EXISTS temperature(
        id INT AUTO_INCREMENT PRIMARY KEY,
        timestamp DATETIME,
        value FLOAT,
        unit VARCHAR(50) DEFAULT 'Celsius'
    )
    """

    create_lite_table = """
    CREATE TABLE IF NOT EXISTS light(
        id INT AUTO_INCREMENT PRIMARY KEY,
        timestamp DATETIME,
        value FLOAT,
        unit VARCHAR(50) DEFAULT 'Lux'
    )
    """

    create_humin_table = """
    CREATE TABLE IF NOT EXISTS humidity(
        id INT AUTO_INCREMENT PRIMARY KEY,
        timestamp DATETIME,
        value FLOAT,
        unit VARCHAR(50) DEFAULT 'Percentage'
    )
    """

    try:
        cursor.execute(create_temp_table)
        cursor.execute(create_lite_table)
        cursor.execute(create_humin_table)
        data_base.commit()
        print("Tables created successfully.")
    except mysql.Error as err:
        print(f"Error creating tables: {err}")


def load_data_from_csv():
    try:
        temperature_data = pd.read_csv("./sample/temperature.csv")
        humidity_data = pd.read_csv("./sample/humidity.csv")
        light_data = pd.read_csv("./sample/light.csv")
    except FileNotFoundError as err:
        print(f"Error reading CSV: {err}")
        return

    queries = {
        'temperature': ("INSERT INTO temperature (timestamp, value, unit) VALUES (%s, %s, %s)",
                        temperature_data[['timestamp', 'value']].assign(unit='Celsius').values.tolist()),
        'humidity': ("INSERT INTO humidity (timestamp, value, unit) VALUES (%s, %s, %s)",
                     humidity_data[['timestamp', 'value']].assign(unit='Percentage').values.tolist()),
        'light': ("INSERT INTO light (timestamp, value, unit) VALUES (%s, %s, %s)",
                  light_data[['timestamp', 'value']].assign(unit='Lux').values.tolist())
    }

    try:
        for sensor_type, (query, data) in queries.items():
            cursor.executemany(query, data)
        data_base.commit()
        print("Data loaded successfully.")
    except mysql.Error as err:
        print(f"Error inserting data: {err}")


def populate_database():
    create_tables()
    load_data_from_csv()
    print("Database populated.")
