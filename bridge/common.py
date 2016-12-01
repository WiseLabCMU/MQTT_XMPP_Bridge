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

from optparse import OptionParser
import ConfigParser
import os 
CONFIG_FILE = os.path.dirname(os.path.abspath(__file__)) +"/bridge.conf"

def parse_arguments():
    config = ConfigParser.ConfigParser()
    config.read(CONFIG_FILE)

    optp = OptionParser()
    optp.add_option('-j','--jid', dest='jid', help='JID on XMPP server', default = config.get('Config','jid'))   
    optp.add_option('-p','--password', dest='xmpp_user_pass', help='Password of jid on xmpp server', default = config.get('Config','password'))
    #TODO: Check if there is a concept of home folder for user so that the node field is not required
    optp.add_option('-e','--node', dest='xmpp_node', help='UUID of bridge node on xmpp server', default = config.get('Config','node'))
    optp.add_option('-t','--path', dest='path', help='Path of bridge node on xmpp server', default = config.get('Config','path'))
#    optp.add_option('-l','--lora_host', dest='lora_host', help='LoRa REST endpoint host', default = config.get('Config','lora_host'))
    optp.add_option('-m','--mqtt_broker', dest='mqtt_broker', help='MQTT Broker', default = config.get('Config', 'mqtt_broker'))
    optp.add_option('-u','--mqtt_broker_user', dest='mqtt_broker_user', help='MQTT Broker User', default = config.get('Config', 'mqtt_broker_user'))
    optp.add_option('-s','--mqtt_broker_pass', dest='mqtt_broker_password', help='MQTT Broker User Password', default = config.get('Config', 'mqtt_broker_password'))
   
    opts, args = optp.parse_args()

    if opts.jid is None:
        optp.print_help()
        exit()
    if opts.xmpp_user_pass is None:
        optp.print_help()
        exit()
    if opts.xmpp_node is None:
        optp.print_help()
        exit()
    if opts.mqtt_broker is None:
        optp.print_help()
        exit()

    return opts    
   
