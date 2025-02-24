#include "ECE140_WIFI.h"
#include "ECE140_MQTT.h"

// MQTT client - using descriptive client ID and topic
//#define CLIENT_ID "esp32-sensors"
//#define TOPIC_PREFIX "poop/ece140/sensors"
#include <Adafruit_BMP085.h>
const char* clientid = CLIENT_ID;
const char* topicprefix = TOPIC_PREFIX;


ECE140_MQTT mqtt(clientid, topicprefix);

// WiFi credentials
const char* ucsdUsername = UCSD_USERNAME;
const char* ucsdPassword = UCSD_PASSWORD;
const char* wifiSsid = WIFI_SSID;
const char* nonEnterpriseWifiPassword = NON_ENTERPRISE_WIFI_PASSWORD;

unsigned long lastPublish = 0;
Adafruit_BMP085 bmp;

void setup() {
    Serial.begin(115200);
    ECE140_WIFI wifi;
    //wifi.connectToWPAEnterprise(wifiSsid, ucsdUsername, ucsdPassword);
    wifi.connectToWiFi(wifiSsid, nonEnterpriseWifiPassword);
    if(!bmp.begin()){
        Serial.println("Sensor not found");
        while (1){}
    }

}

void loop() {
    mqtt.loop();
    Serial.print("Temperature :");
    Serial.print(bmp.readTemperature());
    Serial.print(" C");
    
    Serial.print("Pressure:");
    Serial.print(bmp.readPressure());
    Serial.print(" Pa");
   
    //collecting sensor data
    int pressure_values = bmp.readPressure();
    int temp = bmp.readTemperature();

    //formatting string
    String payload = "{\"temperature\":" + String(temp) + ", \"pressure\":" + String(pressure_values) + " } ";
    

    Serial.print("Published Sensor Reading: ");
    Serial.println(payload);
    mqtt.publishMessage("readings",payload);

    delay(10000);

    //mqtt.loop();

    //if (millis()-lastPublish > 5000)
        //lastPublish = millis();


    //collecting sensor data
    //int hall_value= hallRead();
    //float temp = temperatureRead();

    //formating string
    //String payload = "{\"timestamp\":" + String(millis()) + ", \"hall\":" + String(hall_value) + ", \"temp\":" + String(temp) + "}";

    //Serial.print("Published Sensor Reading: ");
    //Serial.println(payload);
    //mqtt.publishMessage("readings",payload);



}