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

# MIO Publish/Listener example test

import unittest
import logging
import uuid

from mio import MIO

class TestMetaData(unittest.TestCase):

	PUBLISH_EX1 = str(uuid.uuid4())
	PUBLISH_EX2 = str(uuid.uuid4())
	maxDiff = None

	def setUp(self):
		self.mio = MIO("testuser","sensor.andrew.cmu.edu","testuser")
		

		#Clean subscriptions
		for sub in self.mio.subscriptions_query():
			self.mio.unsubscribe(sub["Subscription"])

		self.mio.node_create(self.PUBLISH_EX1)
		self.mio.node_create(self.PUBLISH_EX2)

		#start listener
		self.mio.subscribe_listener()

		self.mio.subscribe(self.PUBLISH_EX1)
		self.mio.subscribe(self.PUBLISH_EX2)

	def tearDown(self):
		self.mio.node_delete(self.PUBLISH_EX1)
		self.mio.node_delete(self.PUBLISH_EX2)
		self.mio.stop()

	def test_publish_1(self):

		self.mio.publish_data(self.PUBLISH_EX1, "random","123 %", "123")
		self.mio.publish_data(self.PUBLISH_EX2, "volts","220 volts", "220")

		real = self.mio.grab_cache_values()
		expected = {
			self.PUBLISH_EX2 : [{
				'timestamp': '2015-03-04T00:38:27.756638',
				'name': 'volts',
				'value': '220 volts',
				'raw_value': '220'}],
			self.PUBLISH_EX1 : [{
				'timestamp': '2015-03-04T00:38:27.721277',
				'name': 'random',
				'value': '123 %',
				'raw_value': '123'}]}

		self.assertEqual(expected.keys(), real.keys())

		self.assertEqual(expected[self.PUBLISH_EX1][0].keys(),
				real[self.PUBLISH_EX1][0].keys())
		self.assertEqual(expected[self.PUBLISH_EX2][0].keys(),
				real[self.PUBLISH_EX2][0].keys())

		#Ignore timestamps
		del expected[self.PUBLISH_EX1][0]["timestamp"]
		del expected[self.PUBLISH_EX2][0]["timestamp"]

		del real[self.PUBLISH_EX1][0]["timestamp"]
		del real[self.PUBLISH_EX2][0]["timestamp"]

		self.assertEqual(expected, real)



if __name__ == '__main__':

	suite = unittest.TestLoader().loadTestsFromTestCase(TestMetaData)
	unittest.TextTestRunner(verbosity=2).run(suite)

	#suite = unittest.TestSuite()
	#suite.addTest(TestMetaData("test_acl_affiliations_remove_1"))
	#runner = unittest.TextTestRunner()
	#runner.run(suite)
