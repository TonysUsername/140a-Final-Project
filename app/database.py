import os
import time
import logging
import mysql.connector as mysql
from typing import Optional, Dict
from dotenv import load_dotenv
from mysql.connector import Error
from datetime import datetime
import decimal

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConnectionError(Exception):
    """Custom exception for database connection failures"""
    pass

def get_db_connection(max_retries: int = 12, retry_delay: int = 5) -> mysql.MySQLConnection:
    """Create database connection with retry mechanism."""
    connection: Optional[mysql.MySQLConnection] = None
    attempt = 1
    last_error = None

    while attempt <= max_retries:
        try:
            connection = mysql.connect(
                host=os.getenv("MYSQL_HOST"),
                user=os.getenv("MYSQL_USER"),
                password=os.getenv("MYSQL_PASSWORD"),
                database=os.getenv("MYSQL_DATABASE"),
                port=int(os.getenv("MYSQL_PORT"))
                ssl_ca=os.getenv("MYSQL_SSL_CA")
            )
            connection.ping(reconnect=True, attempts=1, delay=0)
            logger.info("Database connection established successfully")
            return connection
        except Error as err:
            last_error = err
            logger.warning(f"Connection attempt {attempt}/{max_retries} failed: {err}. Retrying in {retry_delay} seconds...")
            if connection is not None:
                try:
                    connection.close()
                except Exception:
                    pass
            if attempt == max_retries:
                break
            time.sleep(retry_delay)
            attempt += 1
    raise DatabaseConnectionError(f"Failed to connect to database after {max_retries} attempts. Last error: {last_error}")

def create_tables():
    """Creates necessary tables if they do not exist."""
    table_schemas = {
        "temperature": """
            CREATE TABLE IF NOT EXISTS temperature (
                id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp DATETIME,
                value FLOAT,
                unit VARCHAR(50) DEFAULT 'Celsius'
            )
        """,
        "light": """
            CREATE TABLE IF NOT EXISTS light (
                id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp DATETIME,
                value FLOAT,
                unit VARCHAR(50) DEFAULT 'Lux'
            )
        """,
        "humidity": """
            CREATE TABLE IF NOT EXISTS humidity (
                id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp DATETIME,
                value FLOAT,
                unit VARCHAR(50) DEFAULT 'Percentage'
            )
        """,
        "wardrobe_items": """
            CREATE TABLE IF NOT EXISTS wardrobe_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                item_name VARCHAR(255) NOT NULL,
                category VARCHAR(100),
                image_url VARCHAR(512),
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            
        """,
        "devices": """
            CREATE TABLE IF NOT EXISTS devices (
                id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp DATETIME,
                value FLOAT,
                unit VARCHAR(50) DEFAULT 'Percentage'
            )
        """,
        "users": """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        "sessions": """
            CREATE TABLE IF NOT EXISTS sessions (
                id VARCHAR(36) PRIMARY KEY,
                user_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """
    }
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        for table_name, create_query in table_schemas.items():
            cursor.execute(create_query)
        connection.commit()
        logger.info("Tables created successfully.")
    except mysql.Error as err:
        logger.error(f"Error creating tables: {err}")
    finally:
        cursor.close()
        connection.close()

async def setup_database(initial_users: Dict[str, str] = None):
    """Creates user and session tables and populates initial user data if provided."""
    connection = None
    cursor = None

    try:
        # Get database connection
        connection = get_db_connection()
        cursor = connection.cursor()

        # Drop and recreate tables one by one
        for table_name in ["wardrobe_items","iot_devices", "sessions", "users"]:
            # Drop table if exists
            logger.info(f"Dropping table {table_name} if exists...")
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            connection.commit()

        # Recreate users and sessions tables
        users_query = """
            CREATE TABLE users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        sessions_query = """
            CREATE TABLE sessions (
                id VARCHAR(36) PRIMARY KEY,
                user_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """
        iot_devices_query = """
            CREATE TABLE iot_devices (
                id INT AUTO_INCREMENT PRIMARY KEY,
                device_id VARCHAR(255) NOT NULL,
                user_id INT NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """

        wardrobe_items_query = """
            CREATE TABLE IF NOT EXISTS wardrobe_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                item_name VARCHAR(255) NOT NULL,
                category VARCHAR(100),
                image_url VARCHAR(512),
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """

        # Create tables
        for table_name, create_query in [
            ("users", users_query), 
            ("sessions", sessions_query),
            ("iot_devices", iot_devices_query),
            ("wardrobe_items", wardrobe_items_query)
        ]:
            try:
                logger.info(f"Creating table {table_name}...")
                cursor.execute(create_query)
                connection.commit()
                logger.info(f"Table {table_name} created successfully")
            except Error as e:
                logger.error(f"Error creating table {table_name}: {e}")
                raise

        # Insert initial users if provided
        if initial_users:
            try:
                insert_query = "INSERT INTO users (username, password) VALUES (%s, %s)"
                for username, password in initial_users.items():
                    cursor.execute(insert_query, (username, password))
                connection.commit()
                logger.info(f"Inserted {len(initial_users)} initial users")
            except Error as e:
                logger.error(f"Error inserting initial users: {e}")
                raise

    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        raise

    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
            logger.info("Database connection closed")

def populate_database():
    """Initializes the database by creating tables."""
    create_tables()
    logger.info("Database populated.")

# Database utility functions for user and session management
async def create_user(username: str, password: str) -> Optional[int]:
    """
    Create a new user in the database.
    
    Args:
        username: The username for the new user
        password: The password for the new user
        
    Returns:
        Optional[int]: User ID if created successfully, None if username already exists
    """
    connection = None
    cursor = None
    try:
        # Check if username already exists
        existing_user = await get_user_by_username(username)
        if existing_user:
            return None
            
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Insert the new user
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)", 
            (username, password)
        )
        connection.commit()
        
        # Return the new user's ID
        user_id = cursor.lastrowid
        return user_id
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        if connection:
            connection.rollback()
        return None
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

async def get_user_by_username(username: str) -> Optional[Dict]:
    """Retrieve user from database by username."""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        return cursor.fetchone()
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

async def get_user_by_id(user_id: int) -> Optional[Dict]:
    """
    Retrieve user from database by ID.

    Args:
        user_id: The ID of the user to retrieve

    Returns:
        Optional[Dict]: User data if found, None otherwise
    """
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        return cursor.fetchone()
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

async def create_session(user_id: int, session_id: str) -> bool:
    """Create a new session in the database."""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO sessions (id, user_id) VALUES (%s, %s)", (session_id, user_id)
        )
        connection.commit()
        return True
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

async def get_session(session_id: str) -> Optional[Dict]:
    """Retrieve session from database."""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT s.id, u.username
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.id = %s
        """,
            (session_id,),
        )
        return cursor.fetchone()
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

async def delete_session(session_id: str) -> bool:
    """Delete a session from the database."""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM sessions WHERE id = %s", (session_id,))
        connection.commit()
        return True
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

async def create_iot_devices_table():
    """Create the IoT devices table if it doesn't exist."""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Create IoT devices table (removed device_type)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS iot_devices (
                id INT AUTO_INCREMENT PRIMARY KEY,
                device_id VARCHAR(255) NOT NULL,
                user_id INT NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        connection.commit()
        logger.info("IoT devices table created successfully")
    except Error as e:
        logger.error(f"Error creating IoT devices table: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

async def get_devices() -> list:
    """
    Get all devices registered.
    
    Returns:
        list: List of device objects
    """
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM iot_devices ORDER BY added_at DESC"
        )
        return cursor.fetchall()
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

async def add_device(device_id: str, user_id:int) -> bool:
    """
    Add a new device.
    
    Args:
        device_id: The device identifier
        
    Returns:
        bool: True if successful, False otherwise
    """
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO iot_devices (device_id, user_id) VALUES (%s, %s)",
            (device_id, user_id)
        )
        connection.commit()
        return True
    except Error as e:
        logger.error(f"Error adding device: {e}")
        if connection:
            connection.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

async def get_devices_by_user_id(user_id: int) -> list:
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM iot_devices WHERE user_id = %s ORDER BY added_at DESC",
            (user_id,)
        )
        result = cursor.fetchall()
        # Convert non-serializable types to strings for JSON serialization
        for row in result:
            for key, value in row.items():
                if isinstance(value, (decimal.Decimal)):
                    row[key] = float(value)
                elif isinstance(value, datetime):
                    row[key] = value.isoformat()
        return result
    except Exception as e:
        logger.error(f"Error fetching devices for user {user_id}: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

async def get_devices_by_device_id(device_id: str) -> list:
    """
    Get devices matching a specific device_id.
    
    Args:
        device_id: The device identifier
        
    Returns:
        list: List of device objects
    """
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT d.*, u.username FROM iot_devices d JOIN users u ON d.user_id = u.id WHERE d.device_id = %s",
            (device_id,)
        )
        return cursor.fetchall()
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

async def delete_device(device_id: str, user_id: int) -> bool:

    """
    Delete a device.
    
    Args:
        device_id: The device identifier
        
    Returns:
        bool: True if successful, False otherwise
    """
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "DELETE FROM iot_devices WHERE device_id = %s AND user_id = %s",
            (device_id, user_id)
        )
        connection.commit()
        return cursor.rowcount > 0
    except Error as e:
        logger.error(f"Error deleting device: {e}")
        if connection:
            connection.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

async def get_devices() -> list:
    """
    Get all devices registered.
    
    Returns:
        list: List of device objects
    """
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT d.*, u.username FROM iot_devices d JOIN users u ON d.user_id = u.id ORDER BY d.added_at DESC"
        )
        return cursor.fetchall()
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

async def add_wardrobe_item(user_id: int, item_name: str, category: str = None, image_url: str = None) -> int:
    """Add a new wardrobe item for a specific user"""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO wardrobe_items (user_id, item_name, category, image_url) VALUES (%s, %s, %s, %s)",
            (user_id, item_name, category, image_url)
        )
        connection.commit()
        return cursor.lastrowid  # Return the ID of the newly inserted item
    except Error as e:
        logger.error(f"Error adding wardrobe item: {e}")
        if connection:
            connection.rollback()
        return 0  # Indicates failure
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

async def get_wardrobe_items_by_user_id(user_id: int) -> list:
    """Get all wardrobe items for a specific user"""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM wardrobe_items WHERE user_id = %s ORDER BY added_at DESC",
            (user_id,)
        )
        result = cursor.fetchall()
        # Convert non-serializable types to strings for JSON serialization
        for row in result:
            for key, value in row.items():
                if isinstance(value, (decimal.Decimal)):
                    row[key] = float(value)
                elif isinstance(value, datetime):
                    row[key] = value.isoformat()
        return result
    except Exception as e:
        logger.error(f"Error fetching wardrobe items for user {user_id}: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

async def delete_wardrobe_item(item_id: int, user_id: int) -> bool:
    """Delete a wardrobe item (ensuring it belongs to the specified user)"""
    connection = None
    cursor = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "DELETE FROM wardrobe_items WHERE id = %s AND user_id = %s",
            (item_id, user_id)
        )
        connection.commit()
        return cursor.rowcount > 0
    except Error as e:
        logger.error(f"Error deleting wardrobe item: {e}")
        if connection:
            connection.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()