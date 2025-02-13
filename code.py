# Standard library imports
import time
import math
import json
import struct
import os
from collections import deque

# Third-party imports
import board
import neopixel
import busio
import ulab.numpy as np
import adafruit_requests
import socketpool
import ssl
import wifi
import gc
import microcontroller
import adafruit_sdcard
import digitalio
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_bme280 import advanced as adafruit_bme280
import adafruit_tsl2591
import adafruit_ltr390
import adafruit_sgp40
import adafruit_icm20x

def connected(client, userdata, flags, rc):
    print("connected")
    #print("Connected to Adafruit IO! Listening for topic changes on %s" % onoff_feed)
    #client.subscribe(onoff_feed)

def disconnected(client, userdata, rc):
    print("Disconnected from Adafruit IO!")

def message(client, topic, message):
    print(f"New message on topic {topic}: {message}")

def get_sea_level(requests):
    status = "OK"
    try:
        response = requests.get(SEA_LEVEL_URL)
        sea_level_pressure = round(float(response.text.strip().replace("hPa", "")),0)
    except Exception as e:
        sea_level_pressure = 1023.0
        status = "FAILED"
    data= {
        "sea_level_pressure": sea_level_pressure,
        "sea_level_city": SEA_LEVEL_CITY,
        "status": status
    }
    print(json.dumps(data))
    return sea_level_pressure

def calculate_moving_average(values):
    return sum(values) / len(values)

def do_burn_in(bme280,sgp ):
    burn_in_time = BURN_IN
    data = {
        "burn_in_time": burn_in_time,
        "status": "STARTED"}
    print(json.dumps(data))
    
    start_time = time.time()
    curr_time = time.time()
    cycles = 0
    while curr_time - start_time < burn_in_time:
        # Poll the message queue
        mqtt_client.loop()
        curr_time = time.time()
        pixel[0] = COLOR
        time.sleep(DELAY)
        temperature =round( bme280.temperature , 1 )
        humidity = round(bme280.relative_humidity, 0)
        humidity_values.append(humidity)
        temperature_values.append(temperature)
        gas = sgp.measure_raw(temperature = temperature, relative_humidity = humidity)
        voc= sgp.measure_index(temperature = temperature, relative_humidity = humidity)
        pixel[0] = CLEAR
        time.sleep(.75)
        cycles=cycles + 1
    data = {
        "burn_in_time": burn_in_time,
        "cycles":cycles,
        "status": "OK"}
    print(json.dumps(data))  



client_mac_addr = "%x:%x:%x:%x:%x:%x" % struct.unpack("BBBBBB",wifi.radio.mac_address)
data = {
    "client_mac_addr": client_mac_addr,
    "status": "OK"
    }
print(json.dumps(data))

# Read values from settings.toml
SEA_LEVEL_CITY = os.getenv("SEA_LEVEL_CITY")
SEA_LEVEL_URL = os.getenv("SEA_LEVEL_URL").format(SEA_LEVEL_CITY)
MQTT_TOPIC = os.getenv("MQTT_TOPIC")
HIVE_URL = os.getenv("HIVE_URL")
HIVE_PORT = os.getenv("HIVE_PORT")
HIVE_USERNAME = os.getenv("HIVE_USERNAME")
HIVE_PASSWORD = os.getenv("HIVE_PASSWORD")
LOCATION = os.getenv("LOCATION")
BURN_IN = os.getenv("BURN_IN")


# Set up a MiniMQTT Client
pool = socketpool.SocketPool(wifi.radio)
mqtt_client = MQTT.MQTT(
    client_id  = client_mac_addr,
    broker= HIVE_URL,
    username=HIVE_USERNAME,
    password=HIVE_PASSWORD,
    port = HIVE_PORT,
    socket_pool=pool,
    is_ssl  = True,
    ssl_context=ssl.create_default_context()
)

mqtt_client.on_connect = connected
mqtt_client.on_disconnect = disconnected
mqtt_client.on_message = message
#try:
mqtt_client.connect()
#except (ValueError, RuntimeError) as e:
    #mqtt_client.reconnect()
    
# Circular buffer with a maximum length of 10
humidity_values = deque([],10)
temperature_values = deque([],10)

# Configure the setup
PIXEL_PIN =  board.NEOPIXEL # pin that the NeoPixel is connected to
ORDER = neopixel.RGB  # pixel color channel order
COLOR = (100, 0, 0)  # color to blink
RED = (0,100, 0)  # color to blink
BLUE = (0,0, 100)  # color to blink
CLEAR = (0, 0, 0)  # clear (or second color)
DELAY = 0.25  # blink rate in seconds

# Create the NeoPixel object
pixel = neopixel.NeoPixel(PIXEL_PIN, 1, pixel_order=ORDER)
# Define I2C pins (change if needed)
sda_pin = board.IO17  # Your chosen SDA pin
scl_pin = board.IO16  # Your chosen SCL pin
i2c = busio.I2C(scl=scl_pin, sda=sda_pin)

pixel[0] = BLUE
time.sleep(DELAY)    

data = {
    "message": "Setup sensors",
    "status": "STARTED"
}
print(json.dumps(data))

requests = adafruit_requests.Session(pool, ssl.create_default_context())

sgp = adafruit_sgp40.SGP40(i2c, 0x59)
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c,  0x76)

# Suggested settings for weather monitoring
bme280.sea_level_pressure = get_sea_level(requests)

bme280.overscan_pressure=adafruit_bme280.OVERSCAN_X1
bme280.overscan_humidity=adafruit_bme280.OVERSCAN_X1
bme280.overscan_temperature=adafruit_bme280.OVERSCAN_X1
bme280.iir_filter=adafruit_bme280.IIR_FILTER_DISABLE
bme280.mode = adafruit_bme280.MODE_FORCE

lux_sensor = adafruit_tsl2591.TSL2591(i2c)
#Code crashed when I used higher, default is adafruit_tsl2591.GAIN_MED (25x gain, the default)
lux_sensor.gain = adafruit_tsl2591.GAIN_LOW
ltr = adafruit_ltr390.LTR390(i2c)
icm = adafruit_icm20x.ICM20948(i2c, 0x68)

data = {
    "message": "Setup sensors",
    "status": "OK"
}
print(json.dumps(data)) 
   

do_burn_in(bme280,sgp)

last_temperature = -1
last_humidity = -1
last_pressure = -1
last_dlux = -1

cycles = 0
MAX_CYCLES = 1000
while True:
    # Poll the message queue
    try:
        mqtt_client.loop()
    except (ValueError, RuntimeError) as e:
        time.sleep(1)
        mqtt_client.reconnect()
        continue
    
    cycles=cycles + 1
    if cycles > MAX_CYCLES:
        bme280.sea_level_pressure = get_sea_level(requests)
        cycles = 0
        
    pixel[0] = COLOR
    #time.sleep(DELAY)
    temperature =round( bme280.temperature , 1 )
    humidity = round(bme280.relative_humidity, 0)
    pressure = round(bme280.pressure, 0)
    sea_level_pressure = bme280.sea_level_pressure
    dlux = round(lux_sensor.lux,1)
    if dlux < 0.0 :
        dlux = 0.0
    visible=lux_sensor.visible
    infrared=lux_sensor.infrared
    uvs=ltr.uvs
    als=ltr.light
    alux=round( ltr.lux,1)
    
    # Update values list
    humidity_values.append(humidity)
    temperature_values.append(temperature)
    
    # Calculate moving average
    moving_average_humidity = calculate_moving_average(humidity_values)
    moving_average_temperature = calculate_moving_average(temperature_values)
    
    if not (last_temperature == temperature
            and (abs(humidity - moving_average_humidity)  <= 3.00)
            and last_pressure ==pressure
            and round(last_dlux,0) == round(dlux,0))  :
        pixel[0] = BLUE
        gas = sgp.measure_raw(temperature = temperature, relative_humidity = humidity)
        voc= sgp.measure_index(temperature = temperature, relative_humidity = humidity)
        data = [{
            "temperature":temperature,
            "humidity": humidity,
            "pressure": pressure,
            "dlux": dlux,
            "visible": visible,
            "infrared": infrared,
            "uvs": uvs,
            "als": als,
            "alux": alux,
            "gas" : gas,
            "voc":voc,
            "sea_level_pressure":sea_level_pressure
            },
            {
                "tag": client_mac_addr,
                "location": LOCATION
            }
        ]
            #"humidity_values":list(humidity_values),
            #"moving_average_humidity":moving_average_humidity,
            #"temperature_values":list(temperature_values),
            #"moving_average_temperature":moving_average_temperature
        message = json.dumps(data)
        print(message)  
        mqtt_client.publish(MQTT_TOPIC,message)
        last_temperature = temperature
        last_humidity = humidity
        last_pressure = pressure
        last_dlux = dlux
        
    pixel[0] = CLEAR
    time.sleep(DELAY)
