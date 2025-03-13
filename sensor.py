import time
import gc
import os
import json
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_bme280 import advanced as adafruit_bme280

MQTT_TOPIC = os.getenv("MQTT_TOPIC", "s3/env")
DEBUG = os.getenv("DEBUG",False)
HIVE_URL = os.getenv("HIVE_URL")
HIVE_PORT = os.getenv("HIVE_PORT")
#THINGSBOARD_URL = "http://172.17.30.2"
#THINGSBOARD_PORT = "8080"
#THINGSBOARD_DEVICE_TOKEN = "hZz9S1DYVTcWj1IwryLF"

def connected(client, userdata, flags, rc):
    if(DEBUG):
        data = {
            "message": "Connected to MQTT",
            "status": "STARTED"
        }
        print(json.dumps(data))

def disconnected(client, userdata, rc):
    if(DEBUG):
        data = {
            "message": "Disconnected to MQTT",
            "status": "OK"
        }
        print(json.dumps(data))

def message(client, topic, message):
    if(DEBUG):
        print(f"New message on topic {topic}: {message}")

def publish(client, userdata, topic, pid):
    if(DEBUG):
        message = 'MQTT published to {0} with PID {1}'.format(topic, pid)
        data = {
            "message": message,
            "status": "IP"
        }
        print(json.dumps(data))

def send_mqtt(client_mac_addr, pool, topic, message):
    try:
        mqtt_client = MQTT.MQTT(
            client_id  = client_mac_addr,
            broker= HIVE_URL,
            username="api",
            password="api",
            port = HIVE_PORT,
            socket_pool=pool,
            is_ssl  = False,
            #ssl_context=ssl.create_default_context()
        )
        #mqtt_client.enable_logger(logging, log_level=logging.DEBUG)
        mqtt_client.on_connect = connected
        mqtt_client.on_disconnect = disconnected
        mqtt_client.on_message = message
        mqtt_client.on_publish = publish
        #try:
        mqtt_client.connect()
        #except (ValueError, RuntimeError) as e:
        #mqtt_client.reconnect()
        mqtt_client.loop()
        mqtt_client.publish(topic,message)
        mqtt_client.disconnect()
    except (ValueError, RuntimeError) as e:
        print("error", e)
    #So we don't throttle our free connection
    #print("Wait 5 seconds")
    time.sleep(5)
    
