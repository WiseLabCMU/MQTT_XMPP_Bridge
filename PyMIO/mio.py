#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

################################################################################
## @package mio
# Mortar IO (MIO) Python2 Library
# This module converts the mio system calls into XMPP calls understood by the
# Jabber XMPP server. It uses the sleekxmpp library as an XMPP client.
#
# Dependencies: dnspython, sleekxmpp, enum34, pyasn1, pyasn1_modules
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
#  Artur Balanuta 		artur[dot]balanuta[at]tecnico[dot]pt
#
#  Max Buevich 			maximb[at]cmu[dot]edu
################################################################################



import re
import sys
import logging
import coloredlogs

from logging import getLogger
from datetime import datetime

from xml.etree import ElementTree
from xml.dom.minidom import parseString

from threading import Lock
from time import sleep

from sleekxmpp import ClientXMPP
from sleekxmpp.xmlstream import ET
from sleekxmpp.exceptions import IqError, IqTimeout

from sleekxmpp.plugins.xep_0004.stanza.form import Form
from sleekxmpp.plugins.xep_0060.stanza.pubsub_owner import OwnerAffiliations
from sleekxmpp.plugins.xep_0060.stanza.pubsub_owner import OwnerAffiliation
from sleekxmpp.plugins.xep_0060.stanza.pubsub import Options

from mio_types import MetaType, ReferenceType, Unit, AffiliationType

# Initialize the logger and handler.
logger = getLogger('coloredlogs')
coloredlogs.install(show_timestamps=False, show_hostname=False)

## Class used to interact with the XMPP Server
class MIO():

	## Is the Client running
	RUNNING 			= False
	## Is the Client in the connecting State
	CONNECTING 			= False
	## SleekXMPP instance used to connect to the server
	CLIENT 				= None
	## Username to connect to the XMPP Server
	USERNAME 			= None
	## Password to connect to the XMPP Server
	PASSWORD 			= None
	## Server URL
	SERVER 				= None
	## Time in seconds for the connection timeout
	TIMEOUT 			= 10
	## Variable used to store incoming objects from the server
	CACHE_VALUES		= dict()
	## Number of tries before assuming that the server is not reachable
	SOCK_RETRY			= 0		# Zero for infinity

	## Variable used to identify if the Client is listening for pub_sub messages
	CLIENT_LISTENING	= False
	
	## Default number of maximum Items in a node
	MAX_ITEMS_DEFAULT	= 1000

	## Lock used to synchronize access to the CACHE_VALUES variable
	CACHE_LOCK			= Lock()

	## The constructor.
	def __init__(self, username, server, password, log_level=logging.ERROR):

		coloredlogs.set_level(log_level)

		logging.info('MIO: Init')

		self.USERNAME = username
		self.PASSWORD = password
		self.SERVER   = "pubsub."+server

		#Socket statistics
		self.sock_retry = 0

		#XMPPClient
		self.CLIENT = ClientXMPP(username+"@"+server, password)
		self.CLIENT.register_plugin('xep_0030')
		self.CLIENT.register_plugin('xep_0059')
		self.CLIENT.register_plugin('xep_0060')
		self.CLIENT.ssl=False

		#EventHandlers
		self.CLIENT.add_event_handler("session_start", self.on_session_start)
		self.CLIENT.add_event_handler("ssl_invalid_cert", self.on_ssl_invalid_cert)
		self.CLIENT.add_event_handler("socket_error", self.on_socket_error)
		self.CLIENT.add_event_handler("stream_error", self.on_socket_error)
		self.CLIENT.add_event_handler("stream_negotiated", self.on_stream_negotiated)

		self.start()

	## Routine executed when the connections to the server starts
	def on_session_start(self, event):
		#self.CLIENT.send_presence()
		#self.CLIENT.get_roster()
		pass

	## Routine executed when the Server socket cant be reached
	def on_socket_error(self, event):
		logging.error("Error Connecting to Server")

		if self.SOCK_RETRY == 0 or self.sock_retry < self.SOCK_RETRY:
			logging.error("Retrying "+str(self.sock_retry+1)+" ...")
			self.sock_retry += 1
		else:
			sys.exit()

	## Routine executed when a stream socket is established with the server
	def on_stream_negotiated(self, event):

		# if waiting for pub_sub messages, resend the presence token
		# fixes stream connection drops
		if self.CLIENT_LISTENING:
			self.CLIENT.send_presence()


	## Routine executed when an invalid certificate is found
	def on_ssl_invalid_cert(self, event):
		#Ignore certificate errors
		pass

	## Starts the SleekXMPP client
	def start(self):
		if not self.RUNNING:
			self.CONNECTING = True
			self.CLIENT.connect()
			self.CLIENT.process(block=False)

			#Wait for the session to be established
			while not self.CLIENT.sessionstarted:
				sleep(0.05)
			self.RUNNING = True
			self.CONNECTING = False

		else:
			logging.error("XMPP Client already running")

	## Stops the SleekXMPP client
	def stop(self):

		#Wait for the session to be estabilished
		while self.CONNECTING:
			sleep(0.05)

		if self.RUNNING:
			self.CLIENT.disconnect(wait=True, send_close=True)
			self.RUNNING = False
		else:
			logging.error("XMPP Client is not running")

		logging.info('MIO: Stop')
		#sys.exit()

	## Queries affiliations from the event node
	def acl_affiliations_query(self, event_node):
		logging.info("acl_affiliations_query: Init")
		result_lst = list()
		try:
			result = self.CLIENT['xep_0060'].get_node_affiliations(self.SERVER,
				event_node, timeout=self.TIMEOUT)
			logging.debug("RCV:"+parseString(str(result)).toprettyxml())
			if "pubsub_owner" in result.keys():
				for x in result["pubsub_owner"]["affiliations"]:
					result_lst.append(
						{"jid" : str(x["jid"]),
						 "affiliation": str(x["affiliation"])})
		except IqError as e:
			logging.error("Error getting affiliations from event node %s" %
				event_node)
			logging.error("Error condition/type/text: %s/%s/%s" % (e.condition,
				e.etype, e.text))
		except IqTimeout:
			logging.error("Timeout getting affiliations from event node %s" %
				event_node)
		logging.info("acl_affiliations_query: End")
		return result_lst

	## @warning NotImplemented
	def acl_node_configure(self):
		raise NotImplementedError("error")

	## Adds a publisher to the affiliations of an the event node
	def acl_publisher_add(self, event_node, publisher_jid):
		logging.info("acl_publisher_add: Init")

		new_aff = [[publisher_jid, AffiliationType.PUBLISHER.value]]
		try:
			self.CLIENT['xep_0060'].modify_affiliations(self.SERVER, event_node,
				affiliations=new_aff, timeout=self.TIMEOUT)
		except IqError as e:
			logging.error("Error adding affiliation to event node %s" %
				event_node)
			logging.error("Error condition/type/text: %s/%s/%s" % (e.condition,
				e.etype, e.text))
		except IqTimeout:
			logging.error("Timeout adding affiliation to event node %s" %
				event_node)

		logging.info("acl_publisher_add: End")

	## Removes a publisher from the affiliations of an the event node
	def acl_publisher_remove(self, event_node, publisher_jid):
		logging.info("acl_publisher_remove: Init")

		aff_remove = [[publisher_jid, AffiliationType.NONE.value]]
		try:
			self.CLIENT['xep_0060'].modify_affiliations(self.SERVER, event_node,
				affiliations=aff_remove, timeout=self.TIMEOUT)
		except IqError as e:
			logging.error("Error adding affiliation to event node %s" %
				event_node)
			logging.error("Error condition/type/text: %s/%s/%s" % (e.condition,
				e.etype, e.text))
		except IqTimeout:
			logging.error("Timeout adding affiliation to event node %s" %
				event_node)

		logging.info("acl_publisher_remove: End")

	## Adds an collection reference to the childs configuration
	def collection_child_add(self, parent, child):
		logging.info("collection_child_add: Init")

		if not self.node_exists(parent):
			logging.error("Error parent node %s does not exist" % parent)
			return

		if not self.node_exists(child):
			logging.error("Error child node %s does not exist" % child)
			return

		#Child request values
		child_old_values = set(self.collection_parents_query(child))
		child_new_values = child_old_values | set([parent])
		child_submission_value = "\n".join(child_new_values)
		child_form = Form()
		child_form.set_type("submit")
		child_form.add_field(var="FORM_TYPE", ftype="hidden",
			value="http://jabber.org/protocol/pubsub#node_config")
		child_form.add_field(var="pubsub#collection",
			value=child_submission_value)

		#Parent request values
		parent_old_values = set(self.collection_children_query(parent))
		parent_new_values = parent_old_values | set([child])
		parent_submission_value = "\n".join(parent_new_values)
		parent_form = Form()
		parent_form.set_type("submit")
		parent_form.add_field(var="FORM_TYPE", ftype="hidden",
			value="http://jabber.org/protocol/pubsub#node_config")
		parent_form.add_field(var="pubsub#children",
			value=parent_submission_value)

		try:
			self.CLIENT['xep_0060'].set_node_config(self.SERVER, child,
				config=child_form, timeout=self.TIMEOUT)
		except IqError as e:
			logging.error("Error adding collection to event node %s" % child)
			logging.error("Error condition/type/text: %s/%s/%s" % (e.condition,
				e.etype, e.text))
			return
		except IqTimeout:
			logging.error("Timeout adding collection to event node %s" % child)
			return

		try:
			self.CLIENT['xep_0060'].set_node_config(self.SERVER, parent,
				config=parent_form, timeout=self.TIMEOUT)
		except IqError as e:
			logging.error("Error adding child to event node %s" % parent)
			logging.error("Error condition/type/text: %s/%s/%s" % (e.condition,
				e.etype, e.text))
		except IqTimeout:
			logging.error("Timeout adding child to event node %s" % parent)

		logging.info("collection_child_add: End")

	## @warning NotImplemented
	def collection_child_remove(self):
		raise NotImplementedError("error")

	## Returns the children that participate in collection
	def collection_children_query(self, collection_event):
		logging.info("collection_children_query: Init")
		ret_list = list()
		try:
			result = self.CLIENT['xep_0060'].get_node_config(self.SERVER,
				collection_event, timeout=self.TIMEOUT)

			#logging.debug("SEND:"+parseString(str(result)).toprettyxml())

			if result:
				fields = result["pubsub_owner"]["configure"]["form"]["fields"]

				print result["pubsub_owner"]["configure"]["form"]["values"].items()
				
				collections = fields["pubsub#collection"].get_value()
				if collections:
					ret_list = collections.split()

		except IqError as e:
			logging.error("Error adding affiliation to event node %s" %
				collection_event)
			logging.error("Error condition/type/text: %s/%s/%s" % (e.condition,
				e.etype, e.text))
		except IqTimeout:
			logging.error("Timeout adding affiliation to event node %s" %
				collection_event)
		logging.info("collection_children_query: End")
		return ret_list

	## Creates a collection node
	def collection_node_create(self, collection_event, collection_name):
		logging.info("collection_node_create: Init")

		form = Form()
		form.set_type("submit")
		form.add_field("pubsub#title", value=collection_name)
		self.CLIENT['xep_0060'].create_node(self.SERVER, collection_event,
			ntype="collection", config=form, timeout=self.TIMEOUT)

		logging.info("collection_node_create: End")

	## Returns the collections in which the event node participates
	def collection_parents_query(self, event_node):
		logging.info("collection_parents_query: Init")
		ret_list = list()
		try:
			result = self.CLIENT['xep_0060'].get_node_config(self.SERVER,
				event_node, timeout=self.TIMEOUT)

			logging.debug("SEND:"+parseString(str(result)).toprettyxml())
			
			if result:
				fields = result["pubsub_owner"]["configure"]["form"]["fields"]
				collections = fields["pubsub#collection"].get_value()
				if collections:
					ret_list = collections.split()

		except IqError as e:
			logging.error("Error adding affiliation to event node %s" %
				event_node)
			logging.error("Error condition/type/text: %s/%s/%s" % (e.condition,
				e.etype, e.text))
		except IqTimeout:
			logging.error("Timeout adding affiliation to event node %s" %
				event_node)
		logging.info("collection_parents_query: End")
		return ret_list

	## @warning NotImplemented
	def coll_query(self, event_node):
		result = self.CLIENT['xep_0030'].get_info(self.SERVER, event_node,
			timeout=self.TIMEOUT)
		logging.debug("RCV:"+parseString(str(result)).toprettyxml())

	## @warning NotImplemented
	def item_query(self):
		raise NotImplementedError("error")

	## @warning NotImplemented
	def item_query_stanza(self):
		raise NotImplementedError("error")

	## Adds meta information to and event node
	def meta_add(self, event_node, meta_name, node_type, info=None):
		logging.info("meta_add: Init")

		#Update or add the new meta to the event node
		item = '<meta'
		item += ' name="'+meta_name+'"'
		item += ' type="'+node_type.value+'"'
		if info:
			item += ' info="'+info+'"'
		item += ' timestamp="'+str(datetime.now().isoformat())+'"'
		item += ' xmlns="http://jabber.org/protocol/mio"'
		item += ' />'

		logging.debug("SEND:"+parseString(str(item)).toprettyxml())

		payld = ET.fromstring(item)

		try:
			self.CLIENT['xep_0060'].publish(self.SERVER, event_node,
				payload=payld, id="meta", timeout=self.TIMEOUT)
		except IqError as e:
			logging.error("Error adding meta to event node %s" % event_node)
			logging.error("Error condition/type/text: %s/%s/%s" % (e.condition,
				e.etype, e.text))
			return
		except IqTimeout:
			logging.error("Timeout adding meta information to event node %s" %
				event_node)
			return

		logging.info("meta_add: End")

	## Query the meta information of an event node
	def meta_query(self, event_node):
		logging.info("meta_query: Init")

		xml = self.get_item(event_node, "meta")
		if xml:
			logging.debug("RCV:"+parseString(str(xml)).toprettyxml())
			ret_dict = self._meta_query_xml_to_dict(xml)
			return ret_dict
		else:
			return dict()

	## Transforms an xml of Metadata into a Dictionary
	def _meta_query_xml_to_dict(self, xml):
		ret_dict = dict()

		if xml and "item" in xml["pubsub"]["items"].keys():
			meta = xml["pubsub"]["items"]["item"]["payload"]
			meta_dict = dict(meta.items())
			meta_xmlns = re.split('{|}',meta.tag)[1]

			meta_dict["xmlns"] = meta_xmlns
			ret_dict = meta_dict
			children = meta.getchildren()

			if len(children) > 0:
				meta_dict["children"] = list()
				for child in children:
					child_dict = self._meta_query_xml_child_to_dict(child)
					meta_dict["children"].append(child_dict)

		return ret_dict

	## Transforms an xml of Metadata child into a Dictionary
	def	_meta_query_xml_child_to_dict(self, child):
		child_dict = dict()

		child_xmlns, child_tag = re.split('{|}',child.tag)[1:]
		child_dict[child_tag] = dict()

		#Has sub_children
		if child_tag == "geoloc":
			child_dict[child_tag]["xmlns"] = child_xmlns
			sub_children = child.getchildren()

			if len(sub_children) > 0:
				child_dict[child_tag]["children"] = dict()
				for sub_child in sub_children:
					sub_tag = sub_child.tag.split("}")[1]
					sub_value = sub_child.text
					child_dict[child_tag]["children"][sub_tag] = sub_value

		#May have sub_children of type geoloc or property or enums
		elif child_tag == "transducer":
			child_dict[child_tag] = dict(child.items())
			sub_children = child.getchildren()

			if len(sub_children) > 0:
				child_dict[child_tag]["children"] = list()
				for sub_child in sub_children:
					child_dict[child_tag]["children"].append(
						self._meta_query_xml_child_to_dict(sub_child))

		#Does not have sub_children
		elif child_tag == "property":
			child_dict[child_tag] = dict(child.items())

		#Does not have sub_children
		elif child_tag == "map":
			child_dict[child_tag] = dict(child.items())

		return child_dict

	## Removes the metadata of and event node
	def meta_remove(self, event_node):
		logging.info("meta_remove: Init")

		# Delete child meta
		logging.debug("SEND: Null payload")
		try:
			self.CLIENT['xep_0060'].retract(self.SERVER, event_node, id="meta",
				timeout=self.TIMEOUT)
		except IqError as e:
			logging.error("Error removing meta from event node %s" % event_node)
			logging.error("Error condition/type/text: %s/%s/%s" % (e.condition,
				e.etype, e.text))
			return
		except IqTimeout:
			logging.error("Timeout removing meta from event node %s" %
				event_node)

		logging.info("meta_remove: End")

	## Transforms an Child dictionary into XML
	def _meta_child_dict_to_xml(self, child_dict):
		tag, values = child_dict.items()[0]
		item = "<"+str(tag)

		has_children = False
		for key, value in values.items():
			if key != "children":
				item += " "+str(key)+'="'+str(value)+'" '
			else:
				has_children = True
		item += ">"
		if has_children:
			if tag == "geoloc":
				for key, value in values["children"].items():
					item += "<"+str(key)+">"+str(value)+"</"+str(key)+">"
			else:
				for child in values["children"]:
					item += self._meta_child_dict_to_xml(child)
	
		item += "</"+str(tag)+">"
		return item

	## Converts matadata dictionaries into xml structures
	def _meta_dict_to_xml(self, dictionary):
		item = "<meta "
		
		#Add all meta info
		has_children = False
		for key, value in dictionary.items():
			if key != "children":
				item += " "+str(key)+'="'+str(value)+'" '
			else:
				has_children = True
		item += ">"
		
		if has_children:
			for child in dictionary["children"]:
				item += self._meta_child_dict_to_xml(child)
		item += "</meta>"
		return item

	## Adds an transducer to the metadata of an event node
	def meta_transducer_add(self, event_node, name, type=None, unit=None,
		enum_unit_names=None, enum_unit_values=None, min_value=None,
		max_value=None, resolution=None, precision=None, accuracy=None,
		serial_number=None, manufacturer=None, interface=None, info=None):
		logging.info("meta_transducer_add: Init")

		def get_dict_from_values(old_transd=None):
			
			if not old_transd:
				old_transd = dict()
				old_transd["transducer"] = dict()

			old_transd["transducer"]["name"] = str(name)
			if type:
				old_transd["transducer"]["type"] = str(type)
			if unit:
				old_transd["transducer"]["unit"] = str(unit.value)
			if min_value:
				old_transd["transducer"]["minValue"] = str(min_value)
			if max_value:
				old_transd["transducer"]["maxValue"] = str(max_value)
			if resolution:
				old_transd["transducer"]["resolution"] = str(resolution)
			if precision:
				old_transd["transducer"]["precision"] = str(precision)
			if accuracy:
				old_transd["transducer"]["accuracy"] = str(accuracy)
			if serial_number:
				old_transd["transducer"]["serial"] = str(serial_number)
			if manufacturer:
				old_transd["transducer"]["manufacturer"] = str(manufacturer)
			if interface:
				old_transd["transducer"]["interface"] = str(interface)
			if info:
				old_transd["transducer"]["info"] = str(info)

			if enum_unit_names and enum_unit_values:
				names = enum_unit_names.split(',')
				values = enum_unit_values.split(',')

				if len(names) == len(values):
					
					if "children" not in old_transd["transducer"].keys():
						old_transd["transducer"]["children"] = list()
					#delete old mappings
					for item in old_transd["transducer"]["children"]:
						#if "map" in item.names():
							old_transd["transducer"]["children"].remove(item)
					#add new mapping
					for x in range(len(names)):
						m_item = {"map":{"name":names[x], "value":values[x]}}
						old_transd["transducer"]["children"].append(m_item)
				else:
					logging.error("Enum names and values not of same length")
					
			return old_transd

		old_dict = self.meta_query(event_node)
		if len(old_dict) == 0:
			logging.error("Event node %s has no metadata" % event_node)
			return

		#Find if transducer exists
		transducer_exists = False
		transducer = None
		if "children" in old_dict.keys():
			for child in old_dict["children"]:
				if "transducer" in child.keys():
					if child["transducer"]["name"] == name:
						transducer_exists = True
						transducer = child
						break
		#Update values
		if transducer_exists:
			transducer = get_dict_from_values(transducer)

		#Create new dict
		else:
			if "children" not in old_dict.keys():
				old_dict["children"] = list()

			old_dict["children"].append(get_dict_from_values())

		item = self._meta_dict_to_xml(old_dict)
		logging.debug("SND:"+parseString(str(item)).toprettyxml())
		payld = ET.fromstring(item)

		try:
			self.CLIENT['xep_0060'].publish(self.SERVER, event_node,
				payload=payld, id="meta", timeout=self.TIMEOUT)
		except IqError as e:
			logging.error("Error adding transducer meta to event node %s" %
				event_node)
			logging.error("Error condition/type/text: %s/%s/%s" % (e.condition,
				e.etype, e.text))
		except IqTimeout:
			logging.error("Timeout adding transducer meta info to node %s" %
				event_node)

		logging.info("meta_transducer_add: End")

	## Removes transducer from event node
	def meta_transducer_remove(self, event_node, name=None):
		logging.info("meta_transducer_remove: Init")

		old_dict = self.meta_query(event_node)
		if len(old_dict) == 0 or "children" not in old_dict.keys():
			logging.error("Event node %s has no transducers" % event_node)
			return

		else:
			for child in old_dict["children"]:
				if "transducer" in child.keys() and \
					child["transducer"]["name"] == name:
					old_dict["children"].remove(child)
					if len(old_dict["children"]) == 0:
						del old_dict["children"]
					break

		item = self._meta_dict_to_xml(old_dict)
		logging.debug("SND:"+parseString(str(item)).toprettyxml())
		payld = ET.fromstring(item)

		try:
			self.CLIENT['xep_0060'].publish(self.SERVER, event_node,
				payload=payld, id="meta", timeout=self.TIMEOUT)
		except IqError as e:
			logging.error("Error removing transducer from event node %s" %
				event_node)
			logging.error("Error condition/type/text: %s/%s/%s" % (e.condition,
				e.etype, e.text))
		except IqTimeout:
			logging.error("Timeout removing transducer from node %s" %
				event_node)

		logging.info("meta_transducer_remove: End")

	## Adds geolocation to the metadata of an event node or transducer
	def meta_geoloc_add(self, event_node, transducer_name=None, accuracy=None,
		altitude=None, area=None, bearing=None, building=None, country=None,
		country_code=None, datum=None, description=None, floor=None,
		lattitude=None, locality=None, longitude=None, zip_code=None,
		region=None, room=None, speed=None, street=None, text=None,
		time_zone_offset=None, map_uri=None):
		logging.info("meta_geoloc_add: Init")
		
		def get_dict_from_values(old_trd=None):

			if not old_trd:
				old_trd = dict()
				old_trd["geoloc"] = dict()
				old_trd["geoloc"]["xmlns"] = 'http://jabber.org/protocol/geoloc'
				old_trd["geoloc"]["children"] = dict()

			#print old_trd
			geolist = old_trd["geoloc"]["children"]
			geolist["timestamp"] = str(datetime.now().isoformat())

			if accuracy:
				geolist["accuracy"] = accuracy
			if altitude:
				geolist["alt"] = altitude
			if area:
				geolist["area"] = area
			if bearing:
				geolist["bearing"] = bearing
			if building:
				geolist["building"] = building
			if country:
				geolist["country"] = country
			if country_code:
				geolist["countrycode"] = country_code
			if datum:
				geolist["datum"] = datum
			if description:
				geolist["description"] = description
			if floor:
				geolist["floor"] = floor
			if lattitude:
				geolist["lat"] = lattitude
			if locality:
				geolist["locality"] = locality
			if longitude:
				geolist["lon"] = longitude
			if zip_code:
				geolist["postalcode"] = zip_code
			if region:
				geolist["region"] = region
			if room:
				geolist["room"] = room
			if speed:
				geolist["speed"] = speed
			if street:
				geolist["street"] = street
			if text:
				geolist["text"] = text
			if time_zone_offset:
				geolist["tzo"] = time_zone_offset
			if map_uri:
				geolist["uri"] = map_uri

			return old_trd

		old_dict = self.meta_query(event_node)
		if len(old_dict) == 0:
			logging.error("Event node %s has no metadata" % event_node)
			return

		#Find if transducer exists
		transducer_exists = False
		transducer = None
		if transducer_name and "children" in old_dict.keys():
			for child in old_dict["children"]:
				if "transducer" in child.keys():
					if child["transducer"]["name"] == transducer_name:
						transducer_exists = True
						transducer = child["transducer"]
						break

		#Modify transducer
		if transducer_exists:
			if "children" not in transducer:
				transducer["children"] = list()

			geoloc = None
			for item in transducer["children"]:
				if "geoloc" in item.keys():
					geoloc = item
					break

			if geoloc:
				#Update values
				get_dict_from_values(geoloc)
			else:
				#Create new
				transducer["children"].append(get_dict_from_values())

		#Modify root metacode
		else:
			if "children" not in old_dict:
				old_dict["children"] = list()

			geoloc = None
			for item in old_dict["children"]:
				if "geoloc" in item.keys():
					geoloc = item
					break
			if geoloc:
				#Update values
				get_dict_from_values(geoloc)
			else:
				#Create new
				old_dict["children"].append(get_dict_from_values())

		item = self._meta_dict_to_xml(old_dict)
		logging.debug("SND:"+parseString(str(item)).toprettyxml())
		payld = ET.fromstring(item)

		try:
			self.CLIENT['xep_0060'].publish(self.SERVER, event_node,
				payload=payld, id="meta", timeout=self.TIMEOUT)
		except IqError as e:
			logging.error("Error adding geolocation meta to event node %s" %
				event_node)
			logging.error("Error condition/type/text: %s/%s/%s" % (e.condition,
				e.etype, e.text))
		except IqTimeout:
			logging.error("Timeout adding geolocation meta info to node %s" %
				event_node)

		logging.info("meta_geoloc_add: End")

	## Removes geolocation from the metadata of an event node or transducer
	def meta_geoloc_remove(self, event_node, transducer_name=None):
		logging.info("meta_transducer_remove: Init")

		old_dict = self.meta_query(event_node)
		if len(old_dict) == 0:
			logging.error("Event node %s has no metadata" % event_node)
			return

		if "children" in old_dict.keys():
			#Remove meta from transducer
			if transducer_name:
				for child in old_dict["children"]:
					if "transducer" in child.keys() and \
						child["transducer"]["name"] == transducer_name and \
						"children" in child["transducer"].keys():
						for sub_child in child["transducer"]["children"]:
							if "geoloc" in sub_child.keys():
								child["transducer"]["children"].remove(sub_child)
								if len(child["transducer"]["children"]) == 0:
									del child["transducer"]["children"]
								break
			#Remove meta from root
			else:
				for child in old_dict["children"]:
					if "geoloc" in child.keys():
						old_dict["children"].remove(child)
						if len(old_dict["children"]) == 0:
							del old_dict["children"]
						break
		else:
			logging.error("Event node %s has no metadata" % event_node)
			return

		item = self._meta_dict_to_xml(old_dict)
		logging.debug("SND:"+parseString(str(item)).toprettyxml())
		payld = ET.fromstring(item)

		try:
			self.CLIENT['xep_0060'].publish(self.SERVER, event_node,
				payload=payld, id="meta", timeout=self.TIMEOUT)
		except IqError as e:
			logging.error("Error removing geolocation meta from event node %s" %
				event_node)
			logging.error("Error condition/type/text: %s/%s/%s" % (e.condition,
				e.etype, e.text))
		except IqTimeout:
			logging.error("Timeout removing geolocation meta from node %s" %
				event_node)

		logging.info("meta_transducer_remove: End")

	## Adds an property to the metadata of an event node or transducer
	def meta_property_add(self, event_node, property_name, property_value,
		transducer_name=None):
		logging.info("meta_property_add: Init")
		
		def insert_or_update_values(old_dict):
			if not "children" in old_dict.keys():
				old_dict["children"] = list()
			
			updated = False
			for item in old_dict["children"]:
				if "property" in item.keys() and \
					item["property"]["name"] == property_name:
					item["property"]["value"] = property_value
					updated = True
					break

			if not updated:
				item = {"property":{"name": property_name,
					"value": property_value}}
				old_dict["children"].append(item)

		old_dict = self.meta_query(event_node)
		if len(old_dict) == 0:
			logging.error("Event node %s has no metadata" % event_node)
			return

		transducer_exists = False
		transducer = None
		#Search for transducer if present
		if transducer_name and "children" in old_dict.keys():
			for child in old_dict["children"]:
				if "transducer" in child.keys() and \
					child["transducer"]["name"] == transducer_name:
					transducer_exists = True
					transducer = child["transducer"]
					break

		if transducer_name and not transducer_exists:
			logging.error("Event node %s has no transducer %" %
				(event_node, transducer_name))
			return

		if transducer_exists:
			#Insert property into transducer dict
			insert_or_update_values(transducer)
		else:
			#Insert property into meta event
			insert_or_update_values(old_dict)

		item = self._meta_dict_to_xml(old_dict)
		logging.debug("SND:"+parseString(str(item)).toprettyxml())
		payld = ET.fromstring(item)

		try:
			self.CLIENT['xep_0060'].publish(self.SERVER, event_node,
				payload=payld, id="meta", timeout=self.TIMEOUT)
		except IqError as e:
			logging.error("Error adding property meta to event node %s" %
				event_node)
			logging.error("Error condition/type/text: %s/%s/%s" % (e.condition,
				e.etype, e.text))
		except IqTimeout:
			logging.error("Timeout adding property meta info to node %s" %
				event_node)

		logging.info("meta_property_add: End")

	## Removes an property rom the metadata of an event node or transducer
	def meta_property_remove(self, event_node, property_name,
		transducer_name=None):
		logging.info("meta_property_remove: Init")

		def del_prop_from_dict(dictionary):
			for child in dictionary["children"]:
				if "property" in child.keys() and \
					child["property"]["name"] == property_name:
					dictionary["children"].remove(child)
					if len(dictionary["children"]) == 0:
						del dictionary["children"]
					break

		old_dict = self.meta_query(event_node)
		if len(old_dict) == 0:
			logging.error("Event node %s has no metadata" % event_node)
			return

		transducer_processed = False
		#Search for transducer if present
		if transducer_name and "children" in old_dict.keys():
			for child in old_dict["children"]:
				if "transducer" in child.keys() and \
					child["transducer"]["name"] == transducer_name:
					del_prop_from_dict(child["transducer"])
					transducer_processed = True
					break

		if transducer_name and not transducer_processed:
			logging.error("Event node %s has no transducer %" %
				(event_node, transducer_name))
			return

		if not transducer_name:
			#Remove property from meta root
			del_prop_from_dict(old_dict)

		item = self._meta_dict_to_xml(old_dict)
		logging.debug("SND:"+parseString(str(item)).toprettyxml())
		payld = ET.fromstring(item)

		try:
			self.CLIENT['xep_0060'].publish(self.SERVER, event_node,
				payload=payld, id="meta", timeout=self.TIMEOUT)
		except IqError as e:
			logging.error("Error removing property meta from event node %s" %
				event_node)
			logging.error("Error condition/type/text: %s/%s/%s" % (e.condition,
				e.etype, e.text))
		except IqTimeout:
			logging.error("Timeout removing property meta info from node %s" %
				event_node)

		logging.info("meta_property_remove: Remove")

	## Creates a new event node 
	def node_create(self, new_event_node):
		logging.info("node_create: Init")

		# Define the maximum number of Items as MAX_ITEMS_DEFAULT
		form = Form()
		form.add_field(var="pubsub#max_items", value=str(self.MAX_ITEMS_DEFAULT))

		try:
			self.CLIENT['xep_0060'].create_node(self.SERVER, new_event_node,
				config=form, timeout=self.TIMEOUT)
			logging.info("node_create: Created event node %s" % new_event_node)
		except IqError as e:
			logging.error("Error creating event node %s" % new_event_node)
			logging.error("Error condition/type/text: %s/%s/%s" % (e.condition,
				e.etype, e.text))
		except IqTimeout:
			logging.error("Timeout creating event node %s" % new_event_node)

		logging.info("node_create: End")

	## Lists the event nodes present on the Server
	def node_query(self):
		logging.info("node_query: Init")

		ret_list = list()
		try:
			result = self.CLIENT['xep_0060'].get_nodes(self.SERVER, None,
				timeout=self.TIMEOUT)
			logging.debug("RCV:"+parseString(str(result)).toprettyxml())
			logging.info("node_query: Query complete")
			for item in result['disco_items']['items']:
				ret_list.append(str(item[1]))
		except IqTimeout:
			logging.error("Timeout querying nodes")

		logging.info("node_query: End")

		return ret_list

	## Deletes an event node
	def node_delete(self, event_node):
		logging.info("node_delete: Init")

		try:
			self.CLIENT['xep_0060'].delete_node(self.SERVER, event_node,
				timeout=self.TIMEOUT)
			logging.info("node_delete: %s deleted " % event_node)
		except IqError as e:
			logging.error("Error deleting event node %s" % event_node)
			logging.error("Error condition/type/text: %s/%s/%s" % (e.condition,
				e.etype, e.text))
		except IqTimeout:
			logging.error("Timeout deleting event node %s" % event_node)

		logging.info("node_delete: End")

	## Adds child reference to and event node
	def reference_child_add(self, parent, child, ref_type=ReferenceType.CHILD,
		add_ref_child=False):
		logging.info("reference_child_add: Init")

		#Get existing ref nodes on the parent and adds them for insertion
		refs = self.reference_query(parent)

		#Check if the child does already exist
		for ref in refs:
			if ref["node"] == child:
				logging.error("reference_child_add: reference to child %s "\
					"already exists", child)
				logging.info("reference_child_add: End")
				return
		item = '<references>'
		for ref in refs:
			item += '<reference'
			item += ' node="'+ref["node"]+'"'
			if "name" in ref.keys():
				item += ' name="'+ref["name"]+'"'
			item += ' type="'+ref["type"]+'"'
			item += ' />'

		#adds new child to the insertion string
		item += '<reference'
		item += ' node="'+child+'"'
		item += ' name="'+child+'"'
		item += ' type="'+ref_type.value+'"'
		item += ' />'
		item += '</references>'

		logging.debug("SEND:"+parseString(str(item)).toprettyxml())

		payld = ET.fromstring(item)

		try:
			self.CLIENT['xep_0060'].publish(self.SERVER, parent, payload=payld,
				id="references", timeout=self.TIMEOUT)
		except IqTimeout:
			logging.error("Timeout adding child reference to event node %s" %
				parent)
			return

		#Adds reference of the parent to the child
		if add_ref_child:
			logging.info("reference_child_add: reference of the parent to the"\
				+"child")
			self.reference_child_add(child, parent,
				ref_type=ReferenceType.PARENT)

		logging.info("reference_child_add: End")

	## Removes the child reference from an event node
	def reference_child_remove(self, parent, child):
		logging.info("reference_child_remove: Init")

		#Remove parent reference from child if exists
		refs = self.reference_query(child)
		item = '<references>'
		for ref in refs:
			if ref["node"] == parent and \
				ref["type"] == ReferenceType.PARENT.value:
				pass
			else:
				item += '<reference'
				item += ' node="'+ref["node"]+'"'
				if "name" in ref.keys():
					item += ' name="'+ref["name"]+'"'
				item += ' type="'+ref["type"]+'"'
				item += ' />'
		item += '</references>'

		logging.debug("SEND:"+parseString(str(item)).toprettyxml())

		payld = ET.fromstring(item)

		try:
			self.CLIENT['xep_0060'].publish(self.SERVER, child, payload=payld,
				id="references", timeout=self.TIMEOUT)
		except IqTimeout:
			logging.error("Timeout removing parent from event node %s" % parent)
			return

		#Remove child reference from parent
		refs = self.reference_query(parent)
		item = '<references>'
		for ref in refs:
			if ref["node"] == child and \
			ref["type"] == ReferenceType.CHILD.value:
				pass
			else:
				item += '<reference'
				item += ' node="'+ref["node"]+'"'
				if "name" in ref.keys():
					item += ' name="'+ref["name"]+'"'
				item += ' type="'+ref["type"]+'"'
				item += ' />'
		item += '</references>'

		logging.debug("SEND:"+parseString(str(item)).toprettyxml())

		payld = ET.fromstring(item)

		try:
			self.CLIENT['xep_0060'].publish(self.SERVER, parent, payload=payld,
				id="references", timeout=self.TIMEOUT)
		except IqTimeout:
			logging.error("Timeout removing child from event node %s" % parent)
			return

		logging.info("reference_child_remove: End")

	## Query the event node about reference information
	def reference_query(self, event_node):
		logging.info("reference_query: Init")

		ret_list = list()
		try:
			result = self.get_item(event_node, "references")

			if result:
				logging.debug(parseString(str(result)).toprettyxml())

			if result and "item" in result["pubsub"]["items"].keys():
				for x in result["pubsub"]["items"]["item"]["payload"]:
					ret_list.append(dict(x.items()))

		except IqError as e:
			logging.error("Error querying reference from event node %s" %
				event_node)
			logging.error("Error condition/type/text: %s/%s/%s" % (e.condition,
				e.etype, e.text))
		except IqTimeout:
			logging.error("Timeout querying reference from event node %s" %
				event_node)

		# Get the metaType of every child and update the return list
		for child_ref in ret_list:
			if not child_ref["node"]:
				continue
			child_meta = self.meta_query(child_ref["node"])
			if "type" in child_meta.keys():
				child_ref["metaType"] = child_meta["type"]
			else:
				child_ref["metaType"] = MetaType.UKNOWN.value

		logging.info("reference_query: End")
		return ret_list

	## Adds a new schedule element or updates an existing with the same id
	def schedule_event_add(self, event_node, transudcer_name, transducer_value,
		time, info=None, recurrence_frequency=None, recurrence_interval=None,
		recurrence_count=None, recurrence_until=None, recurrence_bymonth=None,
		recurrence_byday=None, recurrence_exdate=None, event_id=None):
		logging.info("schedule_event_add: Init")

		def create_or_update_event_dict(old_event=dict(), e_id=0):
			event = old_event
			event["transducerName"] = transudcer_name
			event["transducerValue"] = transducer_value
			event["time"] = time
			if "id" not in event.keys():
				event["id"] = e_id
			if info:
				event["info"] = info
			if recurrence_frequency or recurrence_interval or \
				recurrence_count or recurrence_until or recurrence_bymonth or \
				recurrence_byday or recurrence_exdate:
				if "recurrence" not in event.keys():
					event["recurrence"] = dict()
				if recurrence_frequency:
					event["recurrence"]["freq"] = recurrence_frequency
				if recurrence_interval:
					event["recurrence"]["interval"] = recurrence_interval
				if recurrence_count:
					event["recurrence"]["count"] = recurrence_count
				if recurrence_until:
					event["recurrence"]["until"] = recurrence_until
				if recurrence_bymonth:
					event["recurrence"]["bymonth"] = recurrence_bymonth
				if recurrence_byday:
					event["recurrence"]["byday"] = recurrence_byday
				if recurrence_exdate:
					event["recurrence"]["exdate"] = recurrence_exdate
			return event

		results = self.schedule_query(event_node)

		#Update or add the new schedule event
		if len(results) > 0:

			#Discover the max_id
			max_id = 0
			for event in results:
				if int(event["id"]) > max_id:
					max_id = int(event["id"])

			update_event = False
			if event_id and event_id <= max_id:
				update_event = True

			new_event_list = list()
			for event in results:

				#Updates existing event
				if update_event and int(event["id"]) == event_id:
					new_event_list.append(create_or_update_event_dict(event))
				
				#Insert the existing schedule events
				else:
					new_event_list.append(event)

			if not update_event:
				new_event_list.append(create_or_update_event_dict(e_id=max_id+1))

			item = self._schedule_event_dict_to_xml(new_event_list)

		#Add a new schedule event
		else:
			event_zero = create_or_update_event_dict()
			item = self._schedule_event_dict_to_xml([event_zero])
		
		#Send the new modifications
		logging.debug("SEND:"+parseString(str(item)).toprettyxml())
		payld = ET.fromstring(item)
		try:
			self.CLIENT['xep_0060'].publish(self.SERVER, event_node,
				payload=payld, id="schedule", timeout=self.TIMEOUT)
		except IqTimeout:
			logging.error("Timeout adding schedule event to event node %s" %
				event_node)

		logging.info("schedule_event_add: End")

	## Removes the schedule element with the especified event_id
	def schedule_event_remove(self, event_node, event_id):
		logging.info("schedule_event_remove: Init")

		results = self.schedule_query(event_node)
		new_event_list = list()
		new_id_counter = 0
		for event in results:
			if int(event["id"]) == int(event_id):
				pass
			else:
				event["id"] = new_id_counter
				new_id_counter += 1
				new_event_list.append(event)

		item = self._schedule_event_dict_to_xml(new_event_list)
		logging.debug("SEND:"+parseString(str(item)).toprettyxml())
		payld = ET.fromstring(item)
		try:
			self.CLIENT['xep_0060'].publish(self.SERVER, event_node,
				payload=payld, id="schedule", timeout=self.TIMEOUT)
		except IqTimeout:
			logging.error("Timeout removing schedule event from event node %s" %
				event_node)

		logging.info("schedule_event_remove: End")

	## List all schedule items of an event node
	def schedule_query(self, event_node):
		logging.info("schedule_query: Init")

		ret_list = list()
		try:
			result = self.get_item(event_node, "schedule")
			if result:
				logging.debug("RCV:"+parseString(str(result)).toprettyxml())
				
				schedule = result["pubsub"]["items"]["item"]["payload"]
				if schedule:
					for event in schedule.getchildren():
						
						new_element = dict(event.items())
						recurrence = event.getchildren()

						# If has recurrence information add it to the result
						if len(recurrence) > 0:
							new_element["recurrence"] = dict()
							for tag in recurrence[0].getchildren():
								tag_name = tag.tag.split('}')[1]
								value = tag.text
								new_element["recurrence"][tag_name] = value
						ret_list.append(new_element)

		except IqError as e:
			logging.error("Error querying schedule items from event node %s" %
				event_node)
			logging.error("Error condition/type/text: %s/%s/%s" % (e.condition,
				e.etype, e.text))
		except IqTimeout:
			logging.error("Timeout querying schedule items from event node %s" %
				event_node)

		logging.info("schedule_query: End")
		return ret_list

	## Converts schedule dictionaries into xml structures
	def _schedule_event_dict_to_xml(self, events):
		item = "<schedule>"
		for event in events:
			item += "<event "
			item += ' transducerName="'+str(event["transducerName"])+'"'
			item += ' transducerValue="'+str(event["transducerValue"])+'"'
			item += ' time="'+str(event["time"])+'"'
			item += ' id="'+str(event["id"])+'"'
			if "info" in event.keys():
				item += ' info="'+str(event["info"])+'"'

			sub_items = ''
			if "recurrence" in event.keys():
				if "freq" in event["recurrence"].keys():
					sub_items += "<freq>"+str(event["recurrence"]["freq"])+\
						"</freq>"
				if "interval" in event["recurrence"].keys():
					sub_items += "<interval>"+\
						str(event["recurrence"]["interval"])+"</interval>"
				if "count" in event["recurrence"].keys():
					sub_items += "<count>"+str(event["recurrence"]["count"])+\
						"</count>"
				if "until" in event["recurrence"].keys():
					sub_items += "<until>"+str(event["recurrence"]["until"])+\
						"</until>"
				if "bymonth" in event["recurrence"].keys():
					sub_items += "<bymonth>"+\
						str(event["recurrence"]["bymonth"])+"</bymonth>"
				if "byday" in event["recurrence"].keys():
					sub_items += "<byday>"+str(event["recurrence"]["byday"])+\
						"</byday>"
				if "exdate" in event["recurrence"].keys():
					sub_items += "<exdate>"+str(event["recurrence"]["exdate"])+\
						"</exdate>"
			if len(sub_items) > 0:
				item += "><recurrence>"
				item += sub_items
				item += "</recurrence></event>"
			else:
				item += "/>"
		item +="</schedule>"
		return item

	## Subscribes to an event node
	def subscribe(self, event_node):
		logging.info("subscribe: Init")

		try:
			self.CLIENT['xep_0060'].subscribe(self.SERVER, event_node,
				timeout=self.TIMEOUT)
			logging.info('Subscribed to node %s' % event_node)
		except IqError as e:
			logging.error("Error subscribing to event node %s" % event_node)
			logging.error("Error condition/type/text: %s/%s/%s" % (e.condition,
				e.etype, e.text))
		except IqTimeout:
			logging.error("Timeout subscribing to %s" % event_node)

		logging.info("subscribe: End")

	## List all current subscribers of a JID or event node
	def subscriptions_query(self):
		logging.info("subscriptions_query: Init")

		sub_list = list()
		try:
			result = self.CLIENT['xep_0060'].get_subscriptions(self.SERVER,
				timeout=self.TIMEOUT)
			logging.debug("RCV:"+parseString(str(result)).toprettyxml())
			for sub in result['pubsub']['subscriptions']:
				sub_list.append({"Subscription": sub['node'],
					"Sub ID": sub['subid']})
		except IqTimeout:
			logging.error("Timeout listing subscriptions")

		logging.info("subscriptions_query: End")
		return sub_list

	## Unsubscribes from an event node
	def unsubscribe(self, event_node, subid=None):
		logging.info("unsubscribe: Init")

		try:
			self.CLIENT['xep_0060'].unsubscribe(self.SERVER, event_node,
				subid=subid, timeout=self.TIMEOUT)
			logging.info('Unsubscribed from node %s' % event_node)
		except IqError as e:
			logging.error("Error unsubscribing from event node %s" % event_node)
			logging.error("Error condition/type/text: %s/%s/%s" % (e.condition,
				e.etype, e.text))
		except IqTimeout:
			logging.error("Timeout unsubscribing from %s" % event_node)

		logging.info("unsubscribe: End")

	## @warning NotImplemented
	def actuate(self):
		raise NotImplementedError("error")

	## Verifies if the user can be authenticated
	def authenticate(self):
		logging.info("authenticate: Init")
		
		try:
			self.CLIENT.get_roster(timeout=self.TIMEOUT)
		except:
			pass

		logging.info("authenticate: End")
		return self.CLIENT.authenticated

	## Publishes transducer values to a specific event node
	def publish_data(self, server, event_node, transducer_name, transducer_value,
		transducer_raw_value=None):
		logging.info("publish_data: Init")
		
		ts = datetime.now().isoformat()
		data = 	'<transducerData'
		data += ' name="'+str(transducer_name)+'"'
		data += ' value="'+str(transducer_value)+'"'
		data += ' timestamp="'+str(ts)+'"'
		if transducer_raw_value:
			data += ' raw_value="'+str(transducer_raw_value)+'"'
		data += ' />'

		logging.debug("SND:"+parseString(str(data)).toprettyxml())
		payld = ET.fromstring(data)
		if not server:
			server = self.SERVER
		try:
			self.CLIENT['xep_0060'].publish(server, event_node, 
				payload=payld, id="_"+str(transducer_name), timeout=self.TIMEOUT)
		except IqError as e:
			logging.error("Error publishing values to event %s" % event_node)
			logging.error("Error condition/type/text: %s/%s/%s" % (e.condition,
				e.etype, e.text))
		except IqTimeout:
			logging.error("Timeout publishing values to event %s" % event_node)

		logging.info("publish_data: End")

	## Listens for publish_data events and saves the values in a dictionary
	def subscribe_listener(self):
		logging.info("subscribe_listener: Init")
		self.CLIENT_LISTENING = True
		self.CLIENT.send_presence()
		self.CLIENT.add_event_handler('pubsub_publish',
			self._publish_received_to_cache)

		logging.info("subscribe_listener: End")


	## Callback function executed when an object is received from a subscription
	def _publish_received_to_cache(self, msg):
		if msg:
			items = msg['pubsub_event']['items']
			node = str(items['node'])
			if node.endswith('_act'):
				node = node[:-4]
				logging.info("stripped node "+node)
			i_dict = dict(items['item']['payload'].items())
			self.CACHE_LOCK.acquire()
			if node not in self.CACHE_VALUES.keys():
				self.CACHE_VALUES[node] = list()
			self.CACHE_VALUES[node].append(i_dict)
			self.CACHE_LOCK.release()

	## Returns the received object from subscription events
	def grab_cache_values(self):
		self.CACHE_LOCK.acquire()
		ret_val = self.CACHE_VALUES
		self.CACHE_VALUES = dict()
		self.CACHE_LOCK.release()
		return ret_val

	## Gets a specific item from an event node
	def get_item(self, event_node, item_type, server = None):
		logging.info("get_item: Init")
		if not server:
			server = self.SERVER

		result = None
		try:
			result = self.CLIENT['xep_0060'].get_item(server, event_node,
				item_type, timeout=self.TIMEOUT)
		except IqError as e:
			logging.error("Error getting item from event node %s" % event_node)
			logging.error("Error condition/type/text: %s/%s/%s" % (e.condition,
				e.etype, e.text))
		except IqTimeout:
			logging.error("Timeout getting item from event node %s" % event_node)

		logging.info("get_item: End")
		return result

	## Verifies if the event_node exists
	def node_exists(self, event_node):
		logging.info("node_exists: Init")
		res_bool = True
		try:
			self.CLIENT['xep_0060'].get_item(self.SERVER, event_node,"", timeout=self.TIMEOUT)
		except IqError as e:
			if str(e.condition) == "item-not-found":
				res_bool = False
			else:
				logging.error("Error condition/type/text: %s/%s/%s" %
					(e.condition, e.etype, e.text))
		except IqTimeout:
			logging.error("Timeout verifying node existence %s" % event_node)
			res_bool = False
		return res_bool

		logging.info("node_exists: End")
