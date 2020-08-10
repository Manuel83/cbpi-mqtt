# -*- coding: utf-8 -*-
""" cbpi3 MQTT module for Actors and Sensors """
import json
import os
import re
import threading
import time

import paho.mqtt.client as mqtt  # pylint: disable=import-error

from eventlet import Queue  # pylint: disable=import-error
from modules import cbpi, app, ActorBase  # pylint: disable=import-error
from modules.core.hardware import SensorActive  # pylint: disable=import-error
from modules.core.props import Property  # pylint: disable=import-error

q = Queue()


def on_connect(_client, _userdata, _flags, return_code):
    """
    MQTT on_connect callback
    """
    print(("MQTT Connected code=" + str(return_code)))


class MQTTThread(threading.Thread):
    """
    MQTT Thread
    """
    def __init__(self, server, port, username, password, tls):  #pylint: disable=too-many-arguments
        threading.Thread.__init__(self)
        self.server = server
        self.port = port
        self.username = username
        self.password = password
        self.tls = tls

    client = None

    def run(self):
        self.client = mqtt.Client()
        self.client.on_connect = on_connect

        if self.username != "username" and self.password != "password":
            self.client.username_pw_set(self.username, self.password)

        if self.tls.lower() == 'true':
            self.client.tls_set_context(context=None)

        self.client.connect(str(self.server), int(self.port), 60)
        self.client.loop_forever()


@cbpi.actor
class MQTTActor(ActorBase):
    """
    MQTT Actor
    """
    topic = Property.Text("Topic",
                          configurable=True,
                          default_value="",
                          description="MQTT TOPIC")

    def on(self,  # pylint: disable=invalid-name
           power=100):  # pylint: disable=unused-argument
        """
        turn actor on
        """
        self.api.cache["mqtt"].client.publish(self.topic,
                                              payload=json.dumps(
                                                  {"state": "on"}),
                                              qos=2,
                                              retain=True)

    def off(self):  # pylint: disable=invalid-name
        """
        turn actor off
        """
        self.api.cache["mqtt"].client.publish(self.topic,
                                              payload=json.dumps(
                                                  {"state": "off"}),
                                              qos=2,
                                              retain=True)


@cbpi.actor
class ESPEasyMQTT(ActorBase):
    """
    ESPEasy MQTT Actor
    """
    topic = Property.Text("Topic",
                          configurable=True,
                          default_value="",
                          description="MQTT TOPIC")

    def on(self,  # pylint: disable=invalid-name
           power=100):  # pylint: disable=unused-argument
        """
        turn actor on
        """
        self.api.cache["mqtt"].client.publish(self.topic,
                                              payload=1,
                                              qos=2,
                                              retain=True)

    def off(self):
        """
        turn actor off
        """
        self.api.cache["mqtt"].client.publish(self.topic,
                                              payload=0,
                                              qos=2,
                                              retain=True)


@cbpi.actor
class ESPHomeMQTT(ActorBase):
    """
    ESPHome MQTT Actor
    """
    topic = Property.Text("Topic",
                          configurable=True,
                          default_value="",
                          description="MQTT TOPIC")

    def on(self,  # pylint: disable=invalid-name
           power=100):  # pylint: disable=unused-argument
        """
        turn actor on
        """
        self.api.cache["mqtt"].client.publish(self.topic,
                                              payload='ON',
                                              qos=2,
                                              retain=True)

    def off(self):
        """
        turn actor off
        """
        self.api.cache["mqtt"].client.publish(self.topic,
                                              payload='OFF',
                                              qos=2,
                                              retain=True)


@cbpi.sensor
class MQTTSensor(SensorActive):
    """
    MQTT Sensor
    """
    a_topic = Property.Text("Topic",
                            configurable=True,
                            default_value="",
                            description="MQTT TOPIC")
    b_payload = Property.Text(
        "Payload Dictioanry",
        configurable=True,
        default_value="",
        description="Where to find msg in patload, leave blank for raw payload"
    )
    c_unit = Property.Text("Unit",
                           configurable=True,
                           default_value="",
                           description="Units to display")

    last_value = None
    unit = None
    topic = None
    payload_text = None


    def init(self):
        """
        init MQTT Sensor
        """
        self.topic = self.a_topic
        if self.b_payload == "":
            self.payload_text = None
        else:
            self.payload_text = self.b_payload.split('.')
        self.unit = self.c_unit[0:3]

        SensorActive.init(self)

        def on_message(_client, _userdata, msg):
            try:
                print(("payload " + msg.payload))
                json_data = json.loads(msg.payload)
                #print json_data
                val = json_data
                if self.payload_text is not None:
                    for key in self.payload_text:
                        val = val.get(key, None)
                #print val
                if isinstance(val, (int, float, str)):
                    q.put({"id": on_message.sensorid, "value": val})
            except AttributeError as exp:
                print(exp)

        on_message.sensorid = self.id
        self.api.cache["mqtt"].client.subscribe(self.topic)
        self.api.cache["mqtt"].client.message_callback_add(
            self.topic, on_message)

    def get_value(self):
        """
        return last value and unit
        """
        return {"value": self.last_value, "unit": self.unit}

    def get_unit(self):
        """
        return unit
        """
        return self.unit

    def stop(self):
        """
        stop sensor
        """
        self.api.cache["mqtt"].client.unsubscribe(self.topic)
        SensorActive.stop(self)

    def execute(self):
        '''
        Active sensor has to handle his own loop
        :return:
        '''
        self.sleep(5)


@cbpi.initalizer(order=0)
def init_mqtt(app):  # pylint: disable=redefined-outer-name
    """
    init MQTT
    """

    server = app.get_config_parameter("MQTT_SERVER", None)
    if server is None:
        server = "localhost"
        cbpi.add_config_parameter("MQTT_SERVER", "localhost", "text",
                                  "MQTT Server")

    port = app.get_config_parameter("MQTT_PORT", None)
    if port is None:
        port = "1883"
        cbpi.add_config_parameter("MQTT_PORT", "1883", "text",
                                  "MQTT Sever Port")

    username = app.get_config_parameter("MQTT_USERNAME", None)
    if username is None:
        username = "username"
        cbpi.add_config_parameter("MQTT_USERNAME", "username", "text",
                                  "MQTT username")

    password = app.get_config_parameter("MQTT_PASSWORD", None)
    if password is None:
        password = "password"
        cbpi.add_config_parameter("MQTT_PASSWORD", "password", "text",
                                  "MQTT password")

    tls = app.get_config_parameter("MQTT_TLS", None)
    if tls is None:
        tls = "false"
        cbpi.add_config_parameter("MQTT_TLS", "false", "text", "MQTT TLS")

    app.cache["mqtt"] = MQTTThread(server, port, username, password, tls)
    app.cache["mqtt"].daemon = True
    app.cache["mqtt"].start()

    def mqtt_reader(api):
        while True:
            try:
                message = q.get(timeout=0.1)
                api.cache.get("sensors")[message.get(
                    "id")].instance.last_value = message.get("value")
                api.receive_sensor_value(message.get("id"), message.get("value"))
            except AttributeError:
                pass

    cbpi.socketio.start_background_task(target=mqtt_reader, api=app)
