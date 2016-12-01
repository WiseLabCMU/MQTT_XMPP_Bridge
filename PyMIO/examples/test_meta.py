#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

################################################################################
## @package tests
#  Mortar IO (MIO) Python2 Library
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
################################################################################

# MIO Metadata example test

import unittest
import uuid

from mio import MIO
from mio_types import Unit, MetaType


class TestMetaData(unittest.TestCase):

	# Makes a random node name
	NODE_NAME = str(uuid.uuid4())

	def setUp(self):
		self.mio = MIO("testuser","sensor.andrew.cmu.edu","testuser")

		self.mio.node_create(self.NODE_NAME)
		
		# Add a Philips Hue device to the meta_example node
		self.mio.meta_add(self.NODE_NAME, meta_name="hue",
			node_type=MetaType.DEVICE, info="Philips Hue lightbulb")

	def tearDown(self):
		self.mio.node_delete(self.NODE_NAME)
		self.mio.stop()

	def test_meta_add(self):
		real = self.mio.meta_query(self.NODE_NAME)
		expected = {'info': 'Philips Hue lightbulb',
					'timestamp': 'change every time',
					'xmlns': 'http://jabber.org/protocol/mio',
					'type': 'device',
					'name': 'hue'}

		self.assertEqual(expected.keys(), real.keys())
		self.assertEqual(expected["info"], real["info"])
		self.assertEqual(expected["name"], real["name"])
		self.assertEqual(expected["type"], real["type"])
		self.assertEqual(expected["xmlns"], real["xmlns"])

	def test_meta_remove(self):
		self.mio.meta_remove(self.NODE_NAME)
		real = self.mio.meta_query(self.NODE_NAME)
		self.assertEqual(real, dict())

	def test_meta_transducer_add(self):
		# Add a brightness transducer
		self.mio.meta_transducer_add(self.NODE_NAME, "brightness",
			type="brightness", unit=Unit.PERCENT, min_value=0, max_value=100)

		real = self.mio.meta_query(self.NODE_NAME)
		expected = {'info': 'Philips Hue lightbulb',
					'xmlns': 'http://jabber.org/protocol/mio',
					'name': 'hue',
					'timestamp': 'changes every time', # ignore
					'type': 'device',
					'children': [
						{'transducer': {
							'type': 'brightness',
							'name': 'brightness',
							'unit':  Unit.PERCENT.value,
							'maxValue': '100'}}]}

		self.assertEqual(expected.keys(), real.keys())
		self.assertEqual(expected["children"], real["children"])

	def test_meta_transducer_update(self):
		# Add a brightness transducer
		self.mio.meta_transducer_add(self.NODE_NAME, "brightness",
			type="brightness", unit=Unit.PERCENT, min_value=0, max_value=100)
		# In case something changes or we forgot something, we can update
		# individual attributes of the device, transducer or property (Note that \
		# enum values are overwritten and not merged)
		self.mio.meta_transducer_add(self.NODE_NAME, "brightness", unit=Unit.LUX, 
			max_value=1000)
		
		real = self.mio.meta_query(self.NODE_NAME)
		expected = {'info': 'Philips Hue lightbulb',
					'xmlns': 'http://jabber.org/protocol/mio',
					'name': 'hue',
					'timestamp': 'change every time',
					'type': 'device',
					'children': [
						{'transducer': {
							'type': 'brightness',
							'name': 'brightness',
							'unit': Unit.LUX.value,
							'maxValue': '1000'}}]}

		self.assertEqual(expected.keys(), real.keys())
		self.assertEqual(expected["children"], real["children"])

	def test_meta_transducer_enum(self):
		# Add a color transducer. Note that we can add comma seperated 
		# enum values as units"
		self.mio.meta_transducer_add(self.NODE_NAME, info="testinfo",
			name="color", type="color", unit=Unit.ENUM,
			enum_unit_names="red,green,blue,white", enum_unit_values="0,1,2,3")
		
		real = self.mio.meta_query(self.NODE_NAME)
		expected = {'info': 'Philips Hue lightbulb',
					'xmlns': 'http://jabber.org/protocol/mio',
					'name': 'hue',
					'timestamp': '2015-02-19T19:43:11.510234',
					'type': 'device',
					'children': [
						{'transducer': {
							'info': 'testinfo',
							'type': 'color',
							'name': 'color',
							'unit': Unit.ENUM.value,
							'children': [
								{'map': {'name': 'red','value': '0'}},
								{'map': {'name': 'green', 'value': '1'}},
								{'map': {'name': 'blue', 'value': '2'}},
								{'map': {'name': 'white', 'value': '3'}}]}}]}

		self.assertEqual(expected.keys(), real.keys())
		self.assertEqual(expected["children"], real["children"])

	def test_meta_transducer_remove(self):
		# Remove a transducer
		self.mio.meta_transducer_add(self.NODE_NAME, "brightness")
		self.mio.meta_transducer_remove(self.NODE_NAME, "brightness")
		real = self.mio.meta_query(self.NODE_NAME)
		expected = {'info': 'Philips Hue lightbulb',
					'timestamp': 'change every time',
					'xmlns': 'http://jabber.org/protocol/mio',
					'type': 'device',
					'name': 'hue'}

		self.assertEqual(expected.keys(), real.keys())
		self.assertEqual(expected["info"], real["info"])
		self.assertEqual(expected["name"], real["name"])
		self.assertEqual(expected["type"], real["type"])
		self.assertEqual(expected["xmlns"], real["xmlns"])

	def test_meta_property_add(self):
		# Add a custom property to the device, indicating when it was installed
		self.mio.meta_property_add(self.NODE_NAME, "purchaseDate", "10/10/10")
		real = self.mio.meta_query(self.NODE_NAME)
		expected = {'info': 'Philips Hue lightbulb',
					'xmlns': 'http://jabber.org/protocol/mio',
					'name': 'hue',
					'timestamp': '2015-02-20T01:11:35.261920',
					'type': 'device',
					'children': [
						{'property': {
							'name': 'purchaseDate',
							'value': '10/10/10'}}]}
		self.assertEqual(expected.keys(), real.keys())
		self.assertEqual(expected["children"], real["children"])

	def test_meta_property_add_update(self):
		# Add a custom property to the device, indicating when it was installed
		self.mio.meta_property_add(self.NODE_NAME, "purchaseDate", "10/10/10")
		self.mio.meta_property_add(self.NODE_NAME, "purchaseDate", "12/34/56")
		real = self.mio.meta_query(self.NODE_NAME)
		expected = {'info': 'Philips Hue lightbulb',
					'xmlns': 'http://jabber.org/protocol/mio',
					'name': 'hue',
					'timestamp': '2015-02-20T01:11:35.261920',
					'type': 'device',
					'children': [
						{'property': {
							'name': 'purchaseDate',
							'value': '12/34/56'}}]}
		self.assertEqual(expected.keys(), real.keys())
		self.assertEqual(expected["children"], real["children"])

	def test_meta_property_add_to_transducer(self):
		# Add a custom property to the color transducer, indicating what color
		# space is being used"
		self.mio.meta_transducer_add(self.NODE_NAME, info="testinfo",
			name="color", type="color")
		self.mio.meta_property_add(self.NODE_NAME, "colorSpace","RGB",
			transducer_name="color")

		real = self.mio.meta_query(self.NODE_NAME)
		expected = {'info': 'Philips Hue lightbulb',
					'xmlns': 'http://jabber.org/protocol/mio',
					'name': 'hue',
					'timestamp': '2015-02-20T16:03:22.162693',
					'type': 'device',
					'children': [
						{'transducer': {
							'info': 'testinfo',
							'type': 'color',
							'name': 'color',
							'children': [
								{'property': {
									'name': 'colorSpace',
									'value': 'RGB'}}]}}]}

		self.assertEqual(expected.keys(), real.keys())
		self.assertEqual(expected["children"], real["children"])

		# Add a second custom property to the color transducer, indicating 
		# what the default color being used"
		self.mio.meta_property_add(self.NODE_NAME, "defaultColor", "White",
			transducer_name="color")
		real = self.mio.meta_query(self.NODE_NAME)
		expected = {'info': 'Philips Hue lightbulb',
					'xmlns': 'http://jabber.org/protocol/mio',
					'name': 'hue',
					'timestamp': '2015-02-20T16:10:26.517589',
					'type': 'device',
					'children': [
						{'transducer': {
							'info': 'testinfo',
							'type': 'color',
							'name': 'color',
							'children': [
							{'property': {
								'name': 'colorSpace',
								'value': 'RGB'}},
							{'property': {
								'name': 'defaultColor',
								'value': 'White'}}]}}]}

		self.assertEqual(expected.keys(), real.keys())
		self.assertEqual(expected["children"], real["children"])

	def test_meta_property_remove(self):
		# We can also remove properties from metadata
		self.mio.meta_property_add(self.NODE_NAME, "purchaseDate", "10/10/10")
		real = self.mio.meta_query(self.NODE_NAME)
		expected = {'info': 'Philips Hue lightbulb',
					'xmlns': 'http://jabber.org/protocol/mio',
					'name': 'hue',
					'timestamp': '2015-02-20T16:49:34.669631',
					'type': 'device',
					'children': [
						{'property':
							{'name': 'purchaseDate', 'value': '10/10/10'}}]}
		self.assertEqual(expected.keys(), real.keys())
		self.assertEqual(expected["children"], real["children"])

		self.mio.meta_property_remove(self.NODE_NAME, "purchaseDate")
		real = self.mio.meta_query(self.NODE_NAME)
		expected = {'info': 'Philips Hue lightbulb',
					'timestamp': '2015-02-20T16:41:24.964806',
					'xmlns': 'http://jabber.org/protocol/mio',
					'type': 'device',
					'name': 'hue'}
		self.assertEqual(expected.keys(), real.keys())

	def test_meta_property_remove_from_transducer(self):
		# We can also remove properties from transducer_metadata
		self.mio.meta_transducer_add(self.NODE_NAME, info="testinfo",
			name="color", type="color")
		self.mio.meta_property_add(self.NODE_NAME, "colorSpace","RGB",
			transducer_name="color")
		real = self.mio.meta_query(self.NODE_NAME)
		expected = {'info': 'Philips Hue lightbulb',
					'xmlns': 'http://jabber.org/protocol/mio',
					'name': 'hue',
					'timestamp': '2015-02-20T17:44:01.809569',
					'type': 'device',
					'children': [
						{'transducer':
							{'info': 'testinfo',
							'type': 'color',
							'name': 'color',
							'children': [
								{'property':
									{'name': 'colorSpace', 'value': 'RGB'}}]}}]}

		self.assertEqual(expected.keys(), real.keys())
		self.assertEqual(expected["children"], real["children"])

		self.mio.meta_property_remove(self.NODE_NAME, "colorSpace",
			transducer_name="color")
		real = self.mio.meta_query(self.NODE_NAME)
		expected = {'info': 'Philips Hue lightbulb',
					'xmlns': 'http://jabber.org/protocol/mio',
					'name': 'hue',
					'timestamp': '2015-02-20T17:44:01.809569',
					'type': 'device',
					'children': [
						{'transducer':
							{'info': 'testinfo',
							'type': 'color',
							'name': 'color'}}]}
		self.assertEqual(expected.keys(), real.keys())
		self.assertEqual(expected["children"], real["children"])

	def test_meta_geoloc_add(self):
		#Add the same geoloc to the metadata
		self.mio.meta_geoloc_add(self.NODE_NAME, accuracy="1.02", altitude="0",
			area="CMU", bearing="North", building="CIC", country="USA",
			country_code="US", datum="testdatum",description="Lux Sensor",
			floor="2",lattitude="11.52", locality="near", longitude="-5.3",
			zip_code="15213", region="WEST", room="333", speed="20 m/s",
			street="5th Avenue", text="this is text", time_zone_offset="-12",
			map_uri="testURL")
		
		real = self.mio.meta_query(self.NODE_NAME)
		expected = {'info': 'Philips Hue lightbulb',
					'xmlns': 'http://jabber.org/protocol/mio',
					'name': 'hue',
					'timestamp': '2015-02-23T12:25:30.613438',
					'type': 'device',
					'children': [
						{'geoloc':
							{'xmlns': 'http://jabber.org/protocol/geoloc',
							'children': {
								'bearing': 'North',
								'text': 'this is text',
								'datum': 'testdatum',
								'lat': '11.52',
								'street': '5th Avenue',
								'alt': '0',
								'speed': '20 m/s',
								'tzo': '-12',
								'countrycode': 'US',
								'area': 'CMU',
								'lon': '-5.3',
								'accuracy': '1.02',
								'description': 'Lux Sensor',
								'timestamp': '2015-02-23T12:25:30.647705',
								'floor': '2',
								'postalcode':'15213',
								'building': 'CIC',
								'room': '333',
								'country': 'USA',
								'region': 'WEST',
								'locality': 'near',
								'uri': 'testURL'}}}]}

		self.assertEqual(expected.keys(), real.keys())
		self.assertEqual(expected["children"][0].keys(),
			real["children"][0].keys())
		self.assertEqual(
			expected["children"][0]["geoloc"]["children"]["bearing"],
			real["children"][0]["geoloc"]["children"]["bearing"])
		self.assertEqual(
			expected["children"][0]["geoloc"]["children"]["text"],
			real["children"][0]["geoloc"]["children"]["text"])
		self.assertEqual(
			expected["children"][0]["geoloc"]["children"]["datum"],
			real["children"][0]["geoloc"]["children"]["datum"])
		self.assertEqual(
			expected["children"][0]["geoloc"]["children"]["lat"],
			real["children"][0]["geoloc"]["children"]["lat"])
		self.assertEqual(
			expected["children"][0]["geoloc"]["children"]["street"],
			real["children"][0]["geoloc"]["children"]["street"])
		self.assertEqual(
			expected["children"][0]["geoloc"]["children"]["alt"],
			real["children"][0]["geoloc"]["children"]["alt"])
		self.assertEqual(
			expected["children"][0]["geoloc"]["children"]["speed"],
			real["children"][0]["geoloc"]["children"]["speed"])
		self.assertEqual(
			expected["children"][0]["geoloc"]["children"]["tzo"],
			real["children"][0]["geoloc"]["children"]["tzo"])
		self.assertEqual(
			expected["children"][0]["geoloc"]["children"]["countrycode"],
			real["children"][0]["geoloc"]["children"]["countrycode"])
		self.assertEqual(
			expected["children"][0]["geoloc"]["children"]["area"],
			real["children"][0]["geoloc"]["children"]["area"])
		self.assertEqual(
			expected["children"][0]["geoloc"]["children"]["lon"],
			real["children"][0]["geoloc"]["children"]["lon"])
		self.assertEqual(
			expected["children"][0]["geoloc"]["children"]["accuracy"],
			real["children"][0]["geoloc"]["children"]["accuracy"])
		self.assertEqual(
			expected["children"][0]["geoloc"]["children"]["description"],
			real["children"][0]["geoloc"]["children"]["description"])
		self.assertEqual(
			expected["children"][0]["geoloc"]["children"]["floor"],
			real["children"][0]["geoloc"]["children"]["floor"])
		self.assertEqual(
			expected["children"][0]["geoloc"]["children"]["postalcode"],
			real["children"][0]["geoloc"]["children"]["postalcode"])
		self.assertEqual(
			expected["children"][0]["geoloc"]["children"]["building"],
			real["children"][0]["geoloc"]["children"]["building"])
		self.assertEqual(
			expected["children"][0]["geoloc"]["children"]["room"],
			real["children"][0]["geoloc"]["children"]["room"])
		self.assertEqual(
			expected["children"][0]["geoloc"]["children"]["country"],
			real["children"][0]["geoloc"]["children"]["country"])
		self.assertEqual(
			expected["children"][0]["geoloc"]["children"]["region"],
			real["children"][0]["geoloc"]["children"]["region"])
		self.assertEqual(
			expected["children"][0]["geoloc"]["children"]["locality"],
			real["children"][0]["geoloc"]["children"]["locality"])
		self.assertEqual(
			expected["children"][0]["geoloc"]["children"]["uri"],
			real["children"][0]["geoloc"]["children"]["uri"])

	def test_meta_geoloc_update(self):
		#Update some geoloc metadata
		self.mio.meta_geoloc_add(self.NODE_NAME, accuracy="1.02")
		self.mio.meta_geoloc_add(self.NODE_NAME, room="2221")

		real = self.mio.meta_query(self.NODE_NAME)
		expected = {'info': 'Philips Hue lightbulb',
					'xmlns': 'http://jabber.org/protocol/mio',
					'name': 'hue',
					'timestamp': '2015-02-23T12:41:55.065552',
					'type': 'device',
					'children': [
						{'geoloc': {
							'xmlns': 'http://jabber.org/protocol/geoloc',
							'children': {
								'timestamp': '2015-02-23T12:41:55.375759',
								'accuracy': '1.02',
								'room': '2221'}}}]}

		self.assertEqual(expected.keys(), real.keys())
		self.assertEqual(expected["children"][0].keys(),
			real["children"][0].keys())
		self.assertEqual(
			expected["children"][0]["geoloc"]["children"]["accuracy"],
			real["children"][0]["geoloc"]["children"]["accuracy"])
		self.assertEqual(
			expected["children"][0]["geoloc"]["children"]["room"],
			real["children"][0]["geoloc"]["children"]["room"])

	def test_meta_geoloc_add_to_transducer(self):
		# Add geoloc to the brightness transducer"
		self.mio.meta_transducer_add(self.NODE_NAME, "brightness")
		self.mio.meta_geoloc_add(self.NODE_NAME, transducer_name="brightness",
			accuracy="0.01")
		real = self.mio.meta_query(self.NODE_NAME)
		expected = {'info': 'Philips Hue lightbulb',
					'xmlns': 'http://jabber.org/protocol/mio',
					'name': 'hue',
					'timestamp': '2015-02-23T14:29:35.310389',
					'type': 'device',
					'children': [
						{'transducer':
							{'name': 'brightness',
							'children': [
								{'geoloc':
									{'xmlns': 'http://jabber.org/protocol/geoloc',
									'children': 
										{'timestamp': 'something',
										'accuracy': '0.01'}}}]}}]}
		self.assertEqual(expected.keys(), real.keys())
		self.assertEqual(expected["children"][0].keys(),
			real["children"][0].keys())
		self.assertEqual(
			expected["children"][0]["transducer"]["children"][0]["geoloc"]["children"]['accuracy'],
			real["children"][0]["transducer"]["children"][0]["geoloc"]["children"]['accuracy'])
		
	def test_meta_geoloc_remove(self):
		#Remove the geoloc data
		self.mio.meta_geoloc_add(self.NODE_NAME, accuracy="1.02")
		self.mio.meta_geoloc_remove(self.NODE_NAME)
		real = self.mio.meta_query(self.NODE_NAME)
		expected = {'info': 'Philips Hue lightbulb',
					'timestamp': '2015-02-23T15:05:33.547275',
					'xmlns': 'http://jabber.org/protocol/mio',
					'type': 'device',
					'name': 'hue'}
		self.assertEqual(expected.keys(), real.keys())

	def test_meta_geoloc_remove_from_transducer(self):
		# Remove the geoloc from the brightness transducer
		# Add geoloc to the brightness transducer"
		self.mio.meta_transducer_add(self.NODE_NAME, "brightness")
		self.mio.meta_geoloc_add(self.NODE_NAME, transducer_name="brightness",
			accuracy="0.01")
		self.mio.meta_geoloc_remove(self.NODE_NAME,transducer_name="brightness")
		real = self.mio.meta_query(self.NODE_NAME)
		expected = {'info': 'Philips Hue lightbulb',
					'xmlns': 'http://jabber.org/protocol/mio',
					'name': 'hue',
					'timestamp': '2015-02-23T15:51:45.019439',
					'type': 'device',
					'children': [
						{'transducer': 
							{'name': 'brightness'}}]}

		self.assertEqual(expected.keys(), real.keys())
		self.assertEqual(expected["children"], real["children"])

if __name__ == '__main__':

	suite = unittest.TestLoader().loadTestsFromTestCase(TestMetaData)
	unittest.TextTestRunner(verbosity=2).run(suite)

	#suite = unittest.TestSuite()
	#suite.addTest(TestMetaData("test_meta_transducer_add"))
	#runner = unittest.TextTestRunner()
	#runner.run(suite)
