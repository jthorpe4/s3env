import time
import gc
import os
import json
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_bme280 import advanced as adafruit_bme280

class Sensor:

    def __init__(self):
        self.MQTT_TOPIC = os.getenv("MQTT_TOPIC", "s3/env")
        self.DEBUG = os.getenv("DEBUG",False)
        self.HIVE_URL = os.getenv("HIVE_URL")
        self.HIVE_PORT = os.getenv("HIVE_PORT")
     #   self.MQTT_TOPIC = MQTT_TOPIC
        #self.DEBUG = DEBUG
        #self.HIVE_URL = HIVE_URL
        #self.HIVE_PORT = HIVE_PORT
        
        #THINGSBOARD_URL = "http://172.17.30.2"
        #THINGSBOARD_PORT = "8080"
        #THINGSBOARD_DEVICE_TOKEN = "hZz9S1DYVTcWj1IwryLF"

    def connected(self, client, userdata, flags, rc):
        if(self.DEBUG):
            data = {
                "message": "Connected to MQTT",
                "status": "STARTED"
            }
            print(json.dumps(data))

    def disconnected(self, client, userdata, rc):
        if(self.DEBUG):
            data = {
                "message": "Disconnected to MQTT",
                "status": "OK"
            }
            print(json.dumps(data))

    def message(self, client, topic, message):
        if(self.DEBUG):
            print(f"New message on topic {topic}: {message}")

    def publish(self, client, userdata, topic, pid):
        if(self.DEBUG):
            message = 'MQTT published to {0} with PID {1}'.format(topic, pid)
            data = {
                "message": message,
                "status": "IP"
            }
            print(json.dumps(data))

    def send_mqtt(self, client_mac_addr, pool, topic, message):
        try:
            print(self.HIVE_URL)
            print(self.HIVE_PORT)
            print(pool)
            mqtt_client = MQTT.MQTT(
              #  client_id  = client_mac_addr,
                broker= self.HIVE_URL,
                username="5tao4yz84tf0buo5ivir",
                password="",
                port = self.HIVE_PORT,
                socket_pool=pool,
                is_ssl  = False,
                #ssl_context=ssl.create_default_context()
            )
            #mqtt_client.enable_logger(logging, log_level=logging.DEBUG)
            mqtt_client.on_connect = self.connected
            mqtt_client.on_disconnect = self.disconnected
            mqtt_client.on_message = self.message
            mqtt_client.on_publish = self.publish
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
        

