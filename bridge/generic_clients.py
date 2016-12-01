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

import logging
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__))+'/../PyMIO/')
from mio import MIO
import mio_tree
from xmpp_mqtt_bridge import MqttClient, XmppClient

class GenericXmppClient(XmppClient):

    def __init__(self, xmpp_server, node_uuid, path):
        self.init(xmpp_server, node_uuid) 
        self.node_path = path
    
    def generate_bindings(self):
        devices = mio_tree.scan_node(self.mio, self.node_uuid, self.node_path) 
        for device in devices.values():
            uuid = device["node"]
            topic = "mio/"+ device["pathList"][0]+"/"+uuid
            logging.info("Subscribing to node :" +uuid)
            self.mio.subscribe(uuid)
            logging.info("Adding topic for node : "+uuid +" , topic : "+topic)
            self.parent.xmppMqttBindings.update({uuid : topic})

    def convert_to_json_format(self, msg):
        logging.info("Received message on xmpp subscribe listener "+ str(msg))
        return json.dumps(msg)


    def process_message(self, node, msgList):
        if node not in self.parent.xmppMqttBindings:
            logging.info('No mqtt topic binding found for this node. Ignoring messages from this node.')
            return
                
        topic  = self.parent.xmppMqttBindings[node]

        for msg in msgList:
            if not msg:
                logging.warning('Empty message received on XMPP listener..Ignoring..')
                continue
            json_msg = dict()
            json_msg['message'] = self.convert_to_json_format(msg)
            json_msg['topic'] = topic
            self.parent.mqttClient.publish(json_msg) 
    
    def handle_publish(self, msg):
        # Nothing is published to xmpp side
        pass

class GenericMqttClient(MqttClient):
       
        # This client pushes messages from xmpp to mqtt and does nothing in the other direction.
        # So it does not have to subscribe to any topics on mqtt side.
    def get_topics(self):
        topics = list()
        return topics
        
    def process_message(self, msg):
        # This client is not subscribed to any topics on mqtt side so it is not listening for any messages.
        # Nothing to process 
        pass

