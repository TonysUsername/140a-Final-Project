import paho.mqtt.client as mqtt
import json
from datetime import datetime
from collections import deque
import numpy as np
import os
from dotenv import load_dotenv
import requests
import time

load_dotenv()

# Get BASE_TOPIC from environment variable
base_topic = os.environ.get("BASE_TOPIC")


# MQTT Broker settings
BROKER = "broker.hivemq.com"
PORT = 1883
#BASE_TOPIC = "poop/ece140/sensors"
TOPIC = base_topic + "/#"

API_URL = "http://localhost:6543/api/temperature"  # Update host if running on different machine

# Time tracking for rate limiting (5 seconds)
last_post_time = 0
POST_INTERVAL = 5  # seconds

#if BASE_TOPIC == "poop/ece140/sensors":
 #   print("readings")
 #   exit()

def post_temperature_to_server(value, unit="C", timestamp=None):
    """Send temperature data to the FastAPI server via POST request."""
    if not timestamp:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    payload = {
        "value": value,
        "unit": unit,
        "timestamp": timestamp
    }

    try:
        response = requests.post(API_URL, json=payload)
        if response.status_code == 200:
            print(f"Temperature data posted: {payload}")
        else:
            print(f" Failed to post data. Status code: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f" Error posting data: {e}")

def on_connect(client, userdata, flags, rc):
    """Callback for when the client connects to the broker."""
    if rc == 0:
        print("Successfully connected to MQTT broker")
        client.subscribe(TOPIC)
        print(f"Subscribed to {TOPIC}")
    else:
        print(f"Failed to connect with result code {rc}")


        
def on_message(client, userdata, msg):
    """Callback for when a message is received."""
    global last_post_time
    try:
        payload = json.loads(msg.payload.decode())  # Attempt to parse payload as JSON
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Print readings if topic matches the readings subtopic
        if msg.topic == f"{base_topic}/readings":
            #hall = payload.get("hall", "N/A")
            temp = payload.get("temperature", "N/A")
            pressure = payload.get("pressure", "N/A")
            #timestamp = payload.get("timestamp", "N/A")
            if temp is not None:
                print(f"\n{current_time} Received Temperature: {temp} C")

                # Only send POST request if 5 seconds have passed
                if time.time() - last_post_time >= POST_INTERVAL:
                    post_temperature_to_server(value=temp, unit="C", timestamp=current_time)
                    last_post_time = time.time()
                else:
                    print(f"Skipping POST (waiting {POST_INTERVAL} seconds between requests)")
            else:
                print("Temperature value not found in payload")

            
            

            print(f"\n{current_time} Received Readings:")
            print(f"Topic: {msg.topic}")
            #print(f"Hall Sensor: {hall}")
            print(f"Pressure Sensor: {pressure} Pa" )
            print(f"Temperature: {temp} C")
           # print(f"ESP Timestamp: {timestamp} ms")

    except json.JSONDecodeError:
        print(f"\nReceived non-JSON message on {msg.topic}:")
        print(f"Payload: {msg.payload.decode()}")
        #payload_str = msg.payload.decode()
        #print(f"\nReceived raw payload: {payload_str}")
      

    #except json.JSONDecodeError:
        #print(f"\nNon-JSON message received on {msg.topic}: {msg.payload.decode()}")       
            


def main():
    # Create MQTT client
    print("Creating MQTT client...")
    client = mqtt.Client()
    # Set the callback functions onConnect and onMessage
    print("Setting callback functions...")
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        # Connect to broker
        print("Connecting to broker...")
        client.connect(BROKER, PORT, keepalive=60)
        
        # Start the MQTT loop
        print("Starting MQTT loop...")
        client.loop_start()
        while True:
            pass
    except KeyboardInterrupt:
        print("\nDisconnecting from broker...")
        # make sure to stop the loop and disconnect from the broker
        client.loop_stop()
        client.disconnect()
        print("Exited successfully")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()