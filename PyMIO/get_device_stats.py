#!/usr/bin/env python


import sys
import signal
import logging
from optparse import OptionParser

from influxdb import InfluxDBClient
from sleekxmpp.xmlstream import ET, tostring

from mio import MIO

import mio_tree
import mio_meta_utils
import math
import datetime
import iso8601
import pytz

# Constants
INFLUX_HOST = 'sensor.andrew.cmu.edu'
INFLUX_PORT = '8086'
INFLUX_USER = 'root'
INFLUX_PASSWORD = 'root'
INFLUX_DATABASE = 'mio1'

# Python versions before 3.0 do not use UTF-8 encoding
# by default. To ensure that Unicode is handled properly
# throughout SleekXMPP, we will set the default encoding
# ourselves to UTF-8.
if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')
else:
    raw_input = input

#--------------------------------------------

#Define stop action
def signal_handler(signal, frame):
    print '\nYou pressed Ctrl+C! stopping ...'

    if "mio" in globals():
        mio.stop()

    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)



# This method gets the last published timestamps of all the transducers for a given node
# and returns the most recent timestamp
def get_last_published_timestamp(mio, transducer_names, node):
	last_pub_time = None
	for name in transducer_names.keys():
		result = mio.get_item(node, "_"+name)
	        if result and "item" in result["pubsub"]["items"].keys():
			item  = result["pubsub"]["items"]["item"]
                	if "timestamp" in item["payload"].keys():
				timestamp = item["payload"].attrib['timestamp']
				dt = iso8601.parse_date(timestamp)
				if not last_pub_time:
					last_pub_time = dt
				else:
					if dt > last_pub_time:
						last_pub_time = dt
	return last_pub_time

def main():
	# Setup the command line arguments.
	optp = OptionParser()
	optp.usage = "%prog -j jid@host -p passwd"
	optp.add_option("-j", "--jid", dest="jid", help="JID to use")
	optp.add_option("-p", "--password", dest="password", help="password to use")
	opts, args = optp.parse_args()
	
	if opts.jid is None:
	        optp.print_help()
        	exit()
	if opts.password is None:
	        optp.print_help()
        	exit()

 	
	user = opts.jid.split('@')[0]
	server = opts.jid.split('@')[1]

	mio = MIO(user,server,opts.password)
	devices = mio_tree.scan_root(mio)	
	
	print "Discovered " +str(len(devices.keys())) + " device nodes"
	
	i =0 
	influx_client = InfluxDBClient(INFLUX_HOST, INFLUX_PORT, INFLUX_USER, INFLUX_PASSWORD, INFLUX_DATABASE)
	points = list()
	for device in devices.values():
		uuid = device["node"]
		device_meta = mio.meta_query(uuid);		
		if not device_meta:
                	print "Node with uuid " +uuid+ " does not have meta. Skipping this node"
                else:
			 transducer_names = mio_meta_utils.get_transducer_names_from_meta(device_meta)
			 if not transducer_names:
				print "Device "+ uuid+ " has no transducers in meta"
				continue
                         last_published_time = get_last_published_timestamp(mio, transducer_names, uuid)
			 if not last_published_time:
				i = i+1
				print "Device "+ uuid+ " has never published any data"
				continue
			 # TODO: Fix the hack below for timezone 
                         time_gap = pytz.UTC.localize(datetime.datetime.utcnow() + datetime.timedelta(hours = -24))
                         if last_published_time < time_gap:
                         	print device
				print " last published on "+ last_published_time.isoformat()
				i = i+1
	
	print "Number of devices that have not published in 24 hours " + str(i)		
	print "Writing " + str(len(points)) + " points to influxdb"

        influx_client.write_points(points,time_precision='s', tags = tags, batch_size=5000)

	mio.stop()
	


if __name__ == '__main__':
   main()
