#!/usr/bin/env python


################################################################################
#
#  Copyright (C) 2016, Carnegie Mellon University
#  All rights reserved.
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, version 2.0 of the License.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#  Contributing Authors (specific to this file):
#
#  Khushboo Bhatia               khush[at]cmu[dot]edu
#
################################################################################

from threading import Lock
import ssl
import paho.mqtt.client as mqtt

import logging
import sys
import signal
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__))+'/../PyMIO/')
from mio import MIO
import mio_meta_utils
from data_holders import Server

class XmppMqttBridge():
    
    xmppMqttBindings = dict()
    mqttXmppBindings = dict()

    def __init__(self, xmppClient, mqttClient):
        logging.info('XmppMqttBridge: Init')
        
        self.xmppClient = xmppClient
        self.mqttClient = mqttClient
        self.xmppClient.parent = self
        self.mqttClient.parent = self
        self.xmppClient.generate_bindings() 
     
    def process_messages(self):
        self.mqttClient.process_messages()
        self.xmppClient.process_messages()

    def stop(self):    
        self.mqttClient.stop()
        self.xmppClient.stop()



class MqttClient():
    
    mqttMessageBuffer = list()
    mqtt_message_buffer_lock = Lock()

    def on_connect(self, client, userdata, flags, rc):
        logging.info('Connected to mqtt broker with result code '+str(rc))
        topics = self.get_topics()
        for topic in topics:
            logging.info('Subscibing to mqtt topic ' + topic)
            client.subscribe(topic)

    def on_message(self, client, userdata, msg):
        logging.info('Received message on mqtt client ' +msg.topic+' '+str(msg.payload))
        self.mqttMessageBuffer.append(msg)

    def __init__(self, mqtt_server):  
        logging.info('MqttClient : Init')
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.username_pw_set(mqtt_server.user, mqtt_server.password)
        self.client.tls_set('/etc/ssl/certs/ca-certificates.crt', tls_version=ssl.PROTOCOL_TLSv1)
        self.client.connect(mqtt_server.host, mqtt_server.port, 60)
        self.client.loop_start()
    
    def grab_cached_messages(self):
        self.mqtt_message_buffer_lock.acquire()
        messages = self.mqttMessageBuffer
        self.mqttMessageBuffer = list()
        self.mqtt_message_buffer_lock.release()
        return messages
        
    def process_messages(self):
        messages = self.grab_cached_messages()
        for msg in messages:
            logging.info('Processing message in mqtt client ' +str(msg))
            xmpp_message = self.process_message(msg)
            if xmpp_message:
                self.parent.xmppClient.publish(xmpp_message)
    
    
    def publish(self, msg):
        logging.info('MqttClient: publishing message '+str(msg))
        self.client.publish(msg["topic"], msg["message"], retain = True) 
    
    def stop(self):
        logging.info('Disconnecting MqttClient')
        self.client.loop_stop()

    def process_message(self, msg):
        # The derived class should override this method and do the conversion of mqtt message
        # to xmpp format so that the message can be published to xmpp side.
        pass

    def get_topics(self):    
        # The derived class should override this method and return a list of topics
        #that this mqtt client should subscribe to.
        pass


class XmppClient():

    def __init__(self, xmpp_server, node_uuid):
        # Derived class does the initialization and calls init method in this class
        pass

    def init(self, xmpp_server, node_uuid):    
        logging.info('XmppClient : init')
        self.node_uuid = node_uuid
        self.mio = MIO(xmpp_server.user, xmpp_server.host, xmpp_server.password, logging.INFO)
        self.mio.subscribe_listener() #Starts a non-blocking listener thread
    
    def generate_bindings(self):
        # Derived class should override this method to generate the bindings.
        pass
        
    def process_message(self, node, msgList):
        #Derived class should override this method
        pass

    def handle_publish(self, msg):
        #Derived class should handle publish
        pass

    def process_messages(self):
        messages = self.mio.grab_cache_values()
        for node, msgList in messages.items():
            self.process_message(node, msgList)
            
    def publish(self, msg):
        logging.info('XmppClient : publishing message '+ str(msg))
        self.handle_publish(msg)
        
    def stop(self):
        logging.info('Disconnecting XmppClient')
        self.mio.stop()



