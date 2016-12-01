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
from threading import Lock
import base64
import json
import sys
import requests
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__))+'/../PyMIO')
from mio import MIO
import mio_meta_utils
from mio_types import MetaType, ReferenceType
from data_holders import Server, LoraID
from xmpp_mqtt_bridge import MqttClient, XmppClient

class LoraSaXmppClient(XmppClient):

    def __init__(self, xmpp_server, node_uuid, lora_server):
        self.init(xmpp_server, node_uuid) 
        self.lora_server = lora_server
    
    def generate_bindings(self):
        child_nodes = self.mio.reference_query(self.node_uuid)
        for child in child_nodes:
            if not child["node"]:
                continue
            if child["type"] == ReferenceType.PARENT.value:
                continue
            if child["metaType"] == MetaType.DEVICE.value:
                uuid = child["node"] 
                node_meta = self.mio.meta_query(uuid)
                if not node_meta:
                    logging.warning('Meta not found for node '+uuid)
                    continue
                appEUI= mio_meta_utils.get_property_value_from_meta(node_meta,'appEUI')
                devEUI = mio_meta_utils.get_property_value_from_meta(node_meta,'devEUI')
                if not appEUI:
                    logging.error('Node '+uuid+' does not have an appEUI in its meta. Exiting..')
                    sys.exit(0)
                if not devEUI:
                    logging.error('Node '+uuid+' does not have a devEUI in its meta. Exiting..')
                    sys.exit(0)
                self.update_cache(uuid, appEUI, devEUI)

    def update_cache(self, xmpp_node_uuid, appEUI, devEUI):
        self.parent.xmppMqttBindings.update({xmpp_node_uuid : LoraID(appEUI, devEUI)})
        key = appEUI + '_'+ devEUI
        self.parent.mqttXmppBindings.update({ key : xmpp_node_uuid })

    def convert_to_lora_format(self, loraId, msg):
        logging.info("Received message on xmpp subscribe listener "+ str(msg))
        data = base64.b64encode(msg["value"])
        #TODO: Hackish.. fix the constants
        return '{"reference": "abcd1234","confirmed": true,"devEUI": "'+loraId.devEUI+'","fPort": 20,"data": "'+data+'"}'

    def invoke_loraserver_api_to_add_node(self, node, appEUI, devEUI, appKey):
        lora_host = self.lora_server.host
        port = self.lora_server.port
        rest_url ="http://"+ lora_host+":"+port+"/api/v1/node"
        post_data = {'appEUI': appEUI,
                     'appKey': appKey,
                     'devEUI': devEUI
                    }
        print rest_url 
        print post_data
        try:           
            requests.post(rest_url, json = post_data)
        except IOError as e:
            #TODO: Email alert if join fails
            print e
            print "Error in post request to LoRA host for creating a node" 
            return False

        logging.info("Successfully invoked LoRA REST api to add node with devEUI "+ devEUI)
        return True
        

    def handle_join_flow(self, node):
        node_meta = self.mio.meta_query(node)
        if not node_meta:
            logging.warning('Meta not found for node '+ node+ '. Ignoring xmpp message received from this node')
            return False
        
        appEUI = mio_meta_utils.get_property_value_from_meta(node_meta,'appEUI')
        devEUI = mio_meta_utils.get_property_value_from_meta(node_meta,'devEUI')
        appKey = mio_meta_utils.get_property_value_from_meta(node_meta,'appKey')

        if not appEUI:
            logging.warning('Node '+node+' does not have an appEUI in its meta. Cannot join this node to LoRa network')
            return False

        if not devEUI:
            logging.warning('Node '+node+' does not have a devEUI in its meta. Cannot join this node to LoRa network.')
            return False

        if not appKey:
            logging.warning('Node '+node+' does not have a appKey in its meta. Cannot join this node to LoRa network.')
            return False


        self.update_cache(node, appEUI, devEUI)
        result = self.invoke_loraserver_api_to_add_node(node, appEUI, devEUI, appKey)
        if not result:
            return False

        try:
            self.mio.reference_child_add(self.node_uuid, node)
        except IqError as e:       
            #TODO: email alert
            print e
            print "Error in adding child reference to node "+ self.node_uuid +". Most likely this is because the lorasaproxy user has not been given publisher access to this node."
            return False

        return True

    def process_message(self, node, msgList):
        if node not in self.parent.xmppMqttBindings:
            #handle join flow
            logging.info('New device found. Loading its meta to find its LoraID(AppEUI,DevEUI) tuple')
            join_successful = self.handle_join_flow(node)
            if not join_successful:
                logging.warning('XMPP message received from node '+node+', but could not complete the join process to lora server. Pubsub will not work for this node')
                return        
                
        loraId = self.parent.xmppMqttBindings[node]

        #TODO: Fix the topic hardcoding
        topic = 'application/'+loraId.appEUI+'/node/'+loraId.devEUI+'/tx'
        for msg in msgList:
            if 'value' not in msg:
                logging.warning('XMPP message does not have a value. Ignoring..'+ str(msg))
                continue
            json_msg = dict()
            json_msg['message'] = self.convert_to_lora_format(loraId, msg)
            json_msg['topic'] = topic
            self.parent.mqttClient.publish(json_msg)
    
    def handle_publish(self, msg):
        lora_id = msg['lora_id']
        if lora_id not in self.parent.mqttXmppBindings :
            logging.info('Ignoring message from lora_id '+ lora_id+ ' because no xmpp node found for this lora_id. To accept messages from this lora node, register this node in sensor andrew portal.')
            return
        xmpp_node_uuid = self.parent.mqttXmppBindings[lora_id]
        payload = msg['value']
        payload_json = json.loads(payload)
        #TODO: fix the transducer name constants
        self.mio.publish_data(xmpp_node_uuid, 'Raw Value', payload_json["data"])
        self.mio.publish_data(xmpp_node_uuid, 'rssi', payload_json["rssi"])



class LoraSaMqttClient(MqttClient):

       
    def get_topics(self):
        topics = list()
        topics.append('application/+/node/+/rx')
        return topics
        
    def process_message(self, msg):
        topic = msg.topic
        words = topic.split('/')
        appEUI= words[1]
        devEUI = words[3]
        xmpp_msg = dict()
        xmpp_msg['lora_id'] = appEUI+'_'+devEUI
        xmpp_msg['value'] = msg.payload
        return xmpp_msg


