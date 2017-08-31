# MQTT Plugin for CraftBeerPi 3.0

This plugins allows to connect to an MQTT Message broker to receive sensor data and invoke actors. 

## Installation


### Install missing python lib
After installation please install python MQTT lib paho

```pip install paho-mqtt```

https://pypi.python.org/pypi/paho-mqtt/1.1

### Install MQTT message broker

Second step is to install an MQTT message broker on your Raspberry Pi.
An open source message broker is mosquitto (https://mosquitto.org/)

```
sudo apt-get update
sudo apt-get install mosquitto

# Furhter commands to control mosquitto service
sudo service mosquitto status
sudo service mosquitto stop
sudo service mosquitto start
```

# MQTT Test Client 
A nice MQTT test client is mqtt.fx http://www.mqttfx.org/
