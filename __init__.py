# -*- coding: utf-8 -*-
import paho.mqtt.client as mqtt
from eventlet import Queue
from modules import cbpi, app, ActorBase
from modules.core.hardware import SensorActive
import json
import os, re, threading, time
from modules.core.props import Property

q = Queue()

def on_connect(client, userdata, flags, rc):
    print("MQTT Connected" + str(rc))

class MQTTThread (threading.Thread):
    client = None
    def run(self):
        self.client = mqtt.Client()
        self.client.on_connect = on_connect
        self.client.connect("localhost", 1883, 60)
        self.client.loop_forever()

@cbpi.actor
class MQTTActor(ActorBase):
    topic = Property.Text("Topic", configurable=True, default_value="", description="MQTT TOPIC")
    def on(self, power=100):
        self.api.cache["mqtt"].client.publish(self.topic, payload=json.dumps({"state": "on"}), qos=0, retain=False)

    def off(self):
        self.api.cache["mqtt"].client.publish(self.topic, payload=json.dumps({"state": "off"}), qos=0, retain=False)


@cbpi.sensor
class MQTT_SENSOR(SensorActive):
    topic = Property.Text("Topic", configurable=True, default_value="", description="MQTT TOPIC")
    last_value = None
    def init(self):
        SensorActive.init(self)
        def on_message(client, userdata, msg):
            try:
                json_data = json.loads(msg.payload)
                q.put({"id": on_message.sensorid, "value": json_data.get("temperature")})
            except:
                pass
        on_message.sensorid = self.id
        self.api.cache["mqtt"].client.subscribe(self.topic)
        self.api.cache["mqtt"].client.message_callback_add(self.topic, on_message)


    def get_value(self):
        return {"value": self.last_value, "unit": ""}

    def stop(self):
        self.api.cache["mqtt"].client.unsubscribe(self.topic)
        SensorActive.stop(self)

    def execute(self):
        '''
        Active sensor has to handle his own loop
        :return: 
        '''
        pass

@cbpi.initalizer(order=0)
def initMQTT(app):
    app.cache["mqtt"] = MQTTThread()
    app.cache["mqtt"].start()
    def mqtt_reader(api):
        while True:
            try:
                m = q.get(timeout=0.1)
                api.cache.get("sensors")[m.get("id")].instance.last_value = m.get("value")
                api.receive_sensor_value(m.get("id"), m.get("value"))
            except:
                pass

    cbpi.socketio.start_background_task(target=mqtt_reader, api=app)


