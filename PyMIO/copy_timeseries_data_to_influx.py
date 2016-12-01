#!/usr/bin/env python


import os
import re
import sys
import signal
import subprocess
import logging
from optparse import OptionParser

from sleekxmpp.xmlstream import ET
from influxdb import InfluxDBClient

from mio import MIO
import mio_tree
import mio_meta_utils

import urllib2
import json
import math
import time
import calendar
import datetime

# Constants
INFLUX_HOST = 'sensor.andrew.cmu.edu'
INFLUX_PORT = '8086'
INFLUX_USER = 'root'
INFLUX_PASSWORD = 'root'
INFLUX_DATABASE = 'mio_tsdb'

def get_ds_root(respawn_dir):
    return respawn_dir+"/mio/services/datastore"
 
def get_store_dir(ds_root):
    return ds_root+"/store.kvs"

def get_devices_dir(ds_root):
    return get_store_dir(ds_root)+"/1"

def is_float(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

#Define stop action
def signal_handler(signal, frame):
    print '\nYou pressed Ctrl+C! stopping ...'

    if "mio" in globals():
        mio.stop()

    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def copy_device_data_using_rest(influx_client, link, uuid, device_meta, transducer_names):
	info = json.loads(urllib2.urlopen(link+'/info.json').read())
   	tags = dict()
	tags["uuid"] = uuid
	for transducer in transducer_names :
		transducer = re.sub('\s+', '-', transducer)
		tags["transducer"] = transducer
		copy_timeseries_using_rest(influx_client, link, uuid, transducer, tags, info)			
				

def copy_timeseries_using_rest(influx_client, link, uuid, transducer, tags, info):
	devchan = uuid + '.' + transducer
	period = 2
	startt = info['channel_specs'][devchan]['channel_bounds']['min_time']
	endt = info['channel_specs'][devchan]['channel_bounds']['max_time']

	tiles = int((endt-startt)/512/period)

	# print meta information
	print '# device:  '+ uuid+ ' transducer:  '+ transducer
	print '# start time: '+ str(startt) + ' and end time: '+ str(endt)
	print '# tiles : '+str(tiles) +'('+str(512*tiles)+' points maximum capacity)'
	points = list()
	print str(datetime.datetime.utcnow())+' started: '+devchan+'\n'
   	for i in range(tiles):
      		if((startt + (i*512*period)) < endt ):
         		level = int(math.log(period,2))
         		offset = int(startt/512/period) + i
         		datastr = urllib2.urlopen(link+'/tiles/1/'+devchan+'/'+str(level)+'.'+str(offset)+'.json').read(); 
         		data = json.loads(datastr)
         		if(data['data'] == []):
            			continue
			# Data returned by respawn is in the following format:
			# entry[0] = timestamp, entry[1]= value, entry[2] = standard deviation, entry[3] = count
         		for entry in data['data']:
            			if(entry[1] == -1e+308):
					continue

				# The logic below drops the millisecond precision. Only seconds from epoch is used.
				ts = calendar.timegm(time.gmtime(entry[0]))
 				point = {
					"measurement": "devices1",
        				"time": ts,
        				"fields": {
            					"value": entry[1]
        					  }
    					}
				points.append(point)
	print "Writing " + str(len(points)) + " points to influxdb"
	influx_client.write_points(points,time_precision='s', tags = tags, batch_size=5000)
	print str(datetime.datetime.utcnow())+' finished writing '+devchan+'\n'

def copy_timeseries_using_export(influx_client, uuid, transducer, tags, ds_root):
    data = get_data_using_export(uuid, transducer, ds_root)
    if not data:
        print "No data found for " +uuid+"."+transducer
        return
    points = list()
    for line in data.splitlines():
         entry = line.split("\t")
         if not is_float(entry[0]):
            continue
         if float(entry[0]) == 0:
            continue
         ts = calendar.timegm(time.gmtime(float(entry[0])))
         point = {
                   "measurement": uuid,
                   "time": ts,
                   "fields": {
                       "value": entry[1]
                   }                  
                 }
         points.append(point)

    print "Writing " +str(len(points)) + " points to influxdb for "+uuid+"."+transducer
    influx_client.write_points(points, time_precision='s', tags = tags, batch_size=5000)
    print "Done"

def get_data_using_export(uuid, transducer, ds_root):
    cmd = ds_root + "/bt_datastore/export "+ get_store_dir(ds_root) +" 1 " + uuid+"."+transducer
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (out, err) = p.communicate()
    return out

def main():
	# Setup the command line arguments.
    optp = OptionParser()
    optp.usage = "%prog -j jid@host -p passwd -r respawn_directory"
    optp.add_option("-j", "--jid", dest="jid", help="JID to use")
    optp.add_option("-p", "--password", dest="password", help="password to use")
    optp.add_option("-r", "--respawn_directory", dest="respawn_dir", help=" Respawn directory")
    opts, args = optp.parse_args()	
    if opts.jid is None:
        optp.print_help()
        exit()
    if opts.password is None:
        optp.print_help()
        exit()
    if opts.respawn_dir is None:
        optp.print_help()
        exit()
     
    user = opts.jid.split('@')[0]
    server = opts.jid.split('@')[1]
    
    ds_root = get_ds_root(opts.respawn_dir)
    devices_dir = get_devices_dir(ds_root)

    mio = MIO(user, server, opts.password)
    devices = mio_tree.scan_root(mio)
    	
    #initialize InfluxDB client	
    influx_client = InfluxDBClient(INFLUX_HOST, INFLUX_PORT, INFLUX_USER, INFLUX_PASSWORD, INFLUX_DATABASE)	
    	
    for device_uuid in os.listdir(devices_dir):
        if device_uuid not in devices:
                print "Device uuid " + device_uuid + " not in mio tree. Skipping..."
                continue
        device_tags = devices[device_uuid]
        device_meta = mio.meta_query(device_uuid)
        transducer_tags = mio_meta_utils.get_transducer_names_from_meta(device_meta)
        for transducer in os.listdir(devices_dir+"/"+device_uuid):
                tags = dict()
                tags["transducer"] = transducer
                trans_with_space = transducer.replace("-"," ")
                if trans_with_space not in transducer_tags.keys():
                    print "Transducer " + transducer +" not found in device meta. Ignoring..."
                    continue
                tags["unit"] = transducer_tags[trans_with_space]["unit"]
                tags["sensor_type"] = device_tags["tags"]["type"]
                tags["path"] = device_tags["pathList"][0]
                copy_timeseries_using_export(influx_client, device_uuid, transducer, tags, ds_root) 
    
    mio.stop()
    
    
if __name__ == '__main__':
   main()
