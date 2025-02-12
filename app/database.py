import os
import mysql.connector as mysql
import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Read variables from the .env file
db_host = os.getenv("MYSQL_HOST")
db_user = os.getenv("MYSQL_USER")
db_database = os.getenv("MYSQL_DATABASE")
db_password = os.getenv("MYSQL_PASSWORD")

# Connect to MySQL using the variables we have just created
data_base = mysql.connect(
    host=db_host,
    user=db_user,
    password=db_password,
    database=db_database
)

# Create a cursor object to interact with the database
cursor = data_base.cursor()

# Let's check if the connection is viable
try:
    data_base.ping(reconnect=True)
    print("Connection is working")
except mysql.Error as warning:
    print(f"Error: {warning}")

# Create tables
def our_tables():
    create_temp_table = """
        CREATE TABLE IF NOT EXISTS temperature(
            id INT AUTO_INCREMENT PRIMARY KEY,
            timestamp DATETIME,
            temp_value FLOAT
        )
    """
    
    create_lite_table = """
        CREATE TABLE IF NOT EXISTS light(
            id INT AUTO_INCREMENT PRIMARY KEY,
            timestamp DATETIME,
            lite_val FLOAT
        )
    """
    
    create_humin_table = """
        CREATE TABLE IF NOT EXISTS humidity(
            id INT AUTO_INCREMENT PRIMARY KEY,
            timestamp DATETIME,
            humidity_value FLOAT
        )
    """
    
    # Execute table creation queries
    try:
        cursor.execute(create_temp_table)
        cursor.execute(create_lite_table)
        cursor.execute(create_humin_table)
        data_base.commit()  # Save the changes
        print("Tables created successfully.")
    except mysql.Error as err:
        print(f"Error creating tables: {err}")

# Retrieve data from CSV and insert it into the database
def retrieve_data():
    temperature_csv = "./sample/temperature.csv"
    humidity_csv = "./sample/humidity.csv"
    light_csv = "./sample/light.csv"

    try:
        # Load data from CSV files using pandas
        temperature_data = pd.read_csv(temperature_csv)
        humidity_data = pd.read_csv(humidity_csv)
        light_data = pd.read_csv(light_csv)
    except FileNotFoundError as err:
        print(f"Error: CSV file not found: {err}")
        return
  
    try:
        # Insert temperature data into the database
        temp_query = """
            INSERT INTO temperature (timestamp, temp_value)
            VALUES (%s, %s)
        """
        cursor.executemany(temp_query, temperature_data[['timestamp', 'temp_value']].values.tolist())

        # Insert light data into the database
        light_query = """
            INSERT INTO light (timestamp, lite_val)
            VALUES (%s, %s)
        """
        cursor.executemany(light_query, light_data[['timestamp', 'lite_val']].values.tolist())

        # Insert humidity data into the database
        humin_query = """
            INSERT INTO humidity (timestamp, humidity_value)
            VALUES (%s, %s)
        """
        cursor.executemany(humin_query, humidity_data[['timestamp', 'humidity_value']].values.tolist())

        # Commit the changes to the database
        data_base.commit()
        print("Data loaded into tables successfully.")
    except mysql.Error as err:
        print(f"Error inserting data into database: {err}")
# Populate the database by creating tables and retrieving data
def populate_database():
    our_tables()  # Ensure tables are created
    retrieve_data()  # Load the data

    # Close the database connection after operations are complete
    cursor.close()
    data_base.close()
    print("Database connection closed.")

