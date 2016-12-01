#!/usr/bin/env python


################################################################################
## @package mio
# Mortar IO (MIO) Python2 Library
# 
#
#
#  Copyright (C) 2014, Carnegie Mellon University
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

import math
import re
import sys
import logging
import json
import os
import mio_meta_utils
from mio import MIO
from mio_types import MetaType, ReferenceType

#Constants
CACHE_FILE_NAME='mio_devices_tree.json'

# This method replaces all white spaces with underscore in node.name and appends it to path.
# So for path="root.Location" and node.name ="Floor 2", this method returns root.Location.Floor_2
def generate_path_name(path, node):
	if "name" in node:
		new_path = path+"/"+re.sub('\s+', '_',node["name"])
 	else:
		new_path = path+"/"+node["node"]
	return new_path

# A recursive function that iterates through the tree to find nodes with metaType = DEVICE
# and adds them to the devices dictionary object. The pathList entry for each device contains
# the path from root to the device node. 	
				
def get_device_nodes(mio, devices, parent_node, path): 
	if parent_node == 'root':
		return
	
	child_nodes = mio.reference_query(parent_node)
        for child in child_nodes:
		if not child["node"]:
			continue
		if child["type"] == ReferenceType.PARENT.value:
			continue
		newPath = generate_path_name(path, child)
		if child["metaType"] == MetaType.LOCATION.value:
			get_device_nodes(mio, devices, child["node"], newPath)
                elif child["metaType"] == MetaType.DEVICE.value:					
			uuid = child["node"]
			if uuid not in devices:
				node_meta = mio.meta_query(uuid)
                                if not node_meta:
                                        print "Child node " + uuid + "," + newPath + " does not have a meta. Skipping this node"
					continue
				
				devices[uuid] = dict()
				devices[uuid]["node"] = uuid
				devices[uuid]["pathList"] = list()
				devices[uuid]["tags"] = dict()
				devices[uuid]["tags"]["type"] = mio_meta_utils.get_type_property_from_meta(node_meta)

			devices[uuid]["pathList"].append(newPath)
			get_device_nodes(mio, devices, child["node"], newPath)
		else:
			# metaType is UNKNOWN, checking if there is a transducer definition in meta 
			node_meta = mio.meta_query(child["node"])
			if len(node_meta) == 0:
				print "Node " + child["node"]+ "," + newPath + " has unknown metaType and has no meta. Skipping this node"
			else:
				print node_meta	#TODO: read meta 
			get_device_nodes(mio, devices, child["node"], newPath)

def scan_root(mio):
    scan_node(mio,"root","") 

def scan_node(mio, uuid, path):
    cache_exists = False
    cache_file = uuid+"_"+CACHE_FILE_NAME
    cache_file_path = os.path.dirname(os.path.abspath(__file__)) +"/"+cache_file
    try:
        with open(cache_file_path,'r') as cache_file:
            devices = json.load(cache_file)
            print "Returning devices data from cache file " + CACHE_FILE_NAME + ". To rescan tree, delete the cache file and run the script again."
            cache_exists = True
    except IOError:
        print "Could not find cache file. Scanning tree. This will take a while ~ 15-20 minutes.."

    if cache_exists:
        return devices
    else:
        devices = dict()
        if uuid == "root":
            root_refs = mio.reference_query("root")
            for child in root_refs:
                if child["name"] == "Location" :
                    location_node = child["node"]
                if child["name"] == "Gateways" :
                    gateway_node = child["node"]
            get_device_nodes(mio, devices, location_node,"root.Location")	
            get_device_nodes(mio, devices, gateway_node,"root.Gateways")
        else:
            get_device_nodes(mio, devices, uuid, path)
		# Cache the tree to a file
        devices_json = json.dumps(devices, indent = 3)
        with open(cache_file_path, 'w') as cache_file:
            print >> cache_file, devices_json
        return devices
