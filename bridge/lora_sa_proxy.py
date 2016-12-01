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
import signal

from lora_sa_clients import LoraSaXmppClient, LoraSaMqttClient
from xmpp_mqtt_bridge import XmppMqttBridge
from data_holders import Server

import common

from twisted.internet import task
from twisted.internet import reactor

#Define stop action
def signal_handler(signal, frame):
    print 'Stopping Xmpp Mqtt Bridge...'
    if "bridge" in globals():
        reactor.stop()
        bridge.stop()

signal.signal(signal.SIGINT, signal_handler)

class BridgeDaemon():
    def run(self):
        opts = common2.parse_arguments()

        xmpp_user = opts.jid.split('@')[0]
        xmpp_host = opts.jid.split('@')[1]

        xmpp_server = Server(xmpp_host,'5222', xmpp_user, opts.xmpp_user_pass)
        lora_server = Server(opts.lora_host, '8000',"", "")
        mqtt_server = Server(opts.mqtt_broker, '1883', opts.mqtt_broker_user, opts.mqtt_broker_password)
        
        xmppClient = LoraSaXmppClient(xmpp_server, opts.xmpp_node, lora_server)
        mqttClient = LoraSaMqttClient(mqtt_server)
        
        global bridge
        bridge = XmppMqttBridge(xmppClient, mqttClient)
    
        loopTask = task.LoopingCall(bridge.process_messages)
        loopDeferred = loopTask.start(1.0) #call every second
        loopDeferred.addErrback(self.handle_error)

        reactor.run() #Keeps the process running forever

    def handle_error(failure):
        print(failure.getBriefTraceback())
        bridge.stop()
        reactor.stop()


if __name__ == '__main__':
    daemon = BridgeDaemon()
    daemon.run()

